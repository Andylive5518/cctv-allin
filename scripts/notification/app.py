import os
import json
import logging
import requests
from flask import Flask, request, jsonify
import yaml
import redis
import hashlib
from datetime import datetime, timedelta

app = Flask(__name__)

# 配置日志
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(level=LOG_LEVEL,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(), # 输出到控制台
                        # logging.FileHandler('/app/logs/notification.log') # 输出到文件 (确保目录存在且可写)
                    ])

# 从环境变量或配置文件加载Webhook URL
CONFIG_FILE_PATH = '/app/config/notification_config.yml'

DEFAULT_DINGTALK_WEBHOOK = os.environ.get('DINGTALK_WEBHOOK')
DEFAULT_WECHAT_WEBHOOK = os.environ.get('WECHAT_WEBHOOK')
DEFAULT_FEISHU_WEBHOOK = os.environ.get('FEISHU_WEBHOOK')

config = {}
if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, 'r') as f:
            config = yaml.safe_load(f) or {}
        logging.info(f"Loaded configuration from {CONFIG_FILE_PATH}")
    except Exception as e:
        logging.error(f"Error loading config file {CONFIG_FILE_PATH}: {e}")

DINGTALK_WEBHOOK = config.get('dingtalk_webhook', DEFAULT_DINGTALK_WEBHOOK)
WECHAT_WEBHOOK = config.get('wechat_webhook', DEFAULT_WECHAT_WEBHOOK)
FEISHU_WEBHOOK = config.get('feishu_webhook', DEFAULT_FEISHU_WEBHOOK)

# --- 辅助函数：发送通知 --- #
def send_dingtalk_message(webhook_url, title, message_markdown, at_mobiles=None, is_at_all=False):
    if not webhook_url:
        logging.warning("DingTalk webhook URL is not configured.")
        return False, "DingTalk webhook URL not configured"
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": message_markdown
        },
        "at": {
            "atMobiles": at_mobiles if at_mobiles else [],
            "isAtAll": is_at_all
        }
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status() # 如果HTTP状态码是4xx/5xx，则抛出异常
        result = response.json()
        if result.get("errcode") == 0:
            logging.info(f"DingTalk message sent successfully: {title}")
            return True, "Sent"
        else:
            logging.error(f"Failed to send DingTalk message: {result.get('errmsg')}")
            return False, result.get('errmsg')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending DingTalk message: {e}")
        return False, str(e)

def send_wechat_message(webhook_url, content_markdown):
    if not webhook_url:
        logging.warning("WeChat webhook URL is not configured.")
        return False, "WeChat webhook URL not configured"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content_markdown
        }
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("errcode") == 0:
            logging.info(f"WeChat message sent successfully.")
            return True, "Sent"
        else:
            logging.error(f"Failed to send WeChat message: {result.get('errmsg')}")
            return False, result.get('errmsg')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending WeChat message: {e}")
        return False, str(e)

def send_feishu_message(webhook_url, title, text_content):
    if not webhook_url:
        logging.warning("Feishu webhook URL is not configured.")
        return False, "Feishu webhook URL not configured"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "msg_type": "interactive", # 或者 "text", "post" 等
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": text_content
                    }
                }
            ]
        }
    }
    # 如果使用text类型:
    # payload = {
    #     "msg_type": "text",
    #     "content": {
    #         "text": f"{title}\n{text_content}"
    #     }
    # }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        result = response.json()
        if result.get("StatusCode") == 0 or result.get("code") == 0: # 飞书API成功响应码可能不同
            logging.info(f"Feishu message sent successfully: {title}")
            return True, "Sent"
        else:
            logging.error(f"Failed to send Feishu message: {result.get('msg') or result.get('message')}")
            return False, result.get('msg') or result.get('message')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Feishu message: {e}")
        return False, str(e)

# --- Alertmanager Webhook处理函数 --- #
def format_alertmanager_payload(payload, platform):
    alerts_markdown = []
    title_prefix = "Prometheus告警"
    common_summary = payload.get('commonAnnotations', {}).get('summary', 'N/A')

    for alert in payload.get('alerts', []):
        status = alert.get('status', 'firing').upper()
        summary = alert.get('annotations', {}).get('summary', common_summary)
        description = alert.get('annotations', {}).get('description', '无详细描述')
        instance = alert.get('labels', {}).get('instance', 'N/A')
        alertname = alert.get('labels', {}).get('alertname', 'N/A')
        severity = alert.get('labels', {}).get('severity', 'N/A').upper()
        starts_at = alert.get('startsAt', 'N/A')
        
        grafana_link = payload.get('externalURL', '') # Alertmanager的externalURL，可以指向Grafana
        # 尝试从告警标签或注释中获取更具体的Grafana链接
        if 'grafana_link' in alert.get('annotations', {}):
            grafana_link = alert['annotations']['grafana_link']
        elif grafana_link and alertname != 'N/A' and instance != 'N/A':
             # 尝试构建一个通用的Grafana explore链接
            query_expr = f"{{alertname='{alertname}', instance='{instance}'}}"
            grafana_link = f"{grafana_link.replace('/alerts', '/explore')}?orgId=1&left=%5B%22now-1h%22,%22now%22,%22Prometheus%22,%7B%22expr%22:%22{requests.utils.quote(alertname + query_expr)}%22%7D%5D"

        title = f"[{status}] {alertname} - {instance}"
        if platform == "dingtalk":
            md = f"#### {title}\n\n"
            md += f"- **级别**: {severity}\n"
            md += f"- **摘要**: {summary}\n"
            md += f"- **详情**: {description}\n"
            md += f"- **开始时间**: {starts_at.split('.')[0].replace('T', ' ')}\n"
            if grafana_link:
                md += f"- **[查看Grafana]({grafana_link})**\n"
            alerts_markdown.append(md)
        elif platform == "wechat":
            md = f"**{title}**\n"
            md += f">级别: <font color=\"warning\">{severity}</font>\n"
            md += f">摘要: {summary}\n"
            md += f">详情: {description}\n"
            md += f">开始时间: {starts_at.split('.')[0].replace('T', ' ')}\n"
            if grafana_link:
                md += f">[查看Grafana]({grafana_link})\n"
            alerts_markdown.append(md)
        elif platform == "feishu":
            md = f"**{title}**\n"
            md += f"- **级别**: {severity}\n"
            md += f"- **摘要**: {summary}\n"
            md += f"- **详情**: {description}\n"
            md += f"- **开始时间**: {starts_at.split('.')[0].replace('T', ' ')}\n"
            if grafana_link:
                md += f"- **[查看Grafana]({grafana_link})**\n"
            alerts_markdown.append(md)

    full_message = "\n\n---\n\n".join(alerts_markdown)
    if not full_message and payload.get('status') == 'resolved':
        title = f"[{payload.get('status','resolved').upper()}] {payload.get('commonLabels',{}).get('alertname','Alert')} Resolved"
        full_message = f"告警 **{payload.get('commonLabels',{}).get('alertname','N/A')}** 已恢复.\n实例: {payload.get('commonLabels',{}).get('instance','N/A')}"
        if platform == "dingtalk":
            full_message = f"#### {title}\n\n{full_message}"

    return title_prefix, full_message

# --- Webhook端点 --- #
@app.route('/webhook/<platform>', methods=['POST'])
def webhook_receiver(platform):
    try:
        payload = request.json
        logging.info(f"Received webhook for {platform}: {json.dumps(payload, indent=2)}")

        title, message = format_alertmanager_payload(payload, platform.lower())
        if not message: # 如果没有告警内容 (例如，空的firing或resolved消息)
            logging.info(f"No specific alert message to send for {platform}.")
            return jsonify({"status": "success", "message": "No alerts to send"}), 200

        success = False
        response_message = "Unknown platform or not configured"

        if platform.lower() == 'dingtalk':
            if DINGTALK_WEBHOOK:
                success, response_message = send_dingtalk_message(DINGTALK_WEBHOOK, title, message)
            else:
                logging.warning("DingTalk webhook not configured for this route.")
        elif platform.lower() == 'wechat':
            if WECHAT_WEBHOOK:
                success, response_message = send_wechat_message(WECHAT_WEBHOOK, message)
            else:
                logging.warning("WeChat webhook not configured for this route.")
        elif platform.lower() == 'feishu':
            if FEISHU_WEBHOOK:
                success, response_message = send_feishu_message(FEISHU_WEBHOOK, title, message)
            else:
                logging.warning("Feishu webhook not configured for this route.")
        elif platform.lower() == 'default' or platform.lower() == 'zabbix': # 示例：Zabbix也用钉钉
            # 可以为Zabbix定义不同的格式化逻辑和发送目标
            logging.info(f"Handling '{platform}' alert, using DingTalk as default for now.")
            if DINGTALK_WEBHOOK:
                success, response_message = send_dingtalk_message(DINGTALK_WEBHOOK, f"Zabbix告警: {title}", message)
            else:
                logging.warning(f"Default/Zabbix DingTalk webhook not configured.")
        else:
            logging.warning(f"Unsupported platform: {platform}")
            return jsonify({"status": "error", "message": "Unsupported platform"}), 400

        if success:
            return jsonify({"status": "success", "message": response_message}), 200
        else:
            return jsonify({"status": "error", "message": response_message}), 500

    except Exception as e:
        logging.error(f"Error processing webhook for {platform}: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Redis连接
redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

def should_send_alert(alert_key, alert_status):
    """告警去重检查"""
    cache_key = f"alert:{alert_key}"
    
    if alert_status == 'firing':
        # 检查是否在5分钟内已发送相同告警
        last_sent = redis_client.get(cache_key)
        if last_sent:
            return False
        
        # 记录告警发送时间，TTL 5分钟
        redis_client.setex(cache_key, 300, datetime.now().isoformat())
        return True
    
    elif alert_status == 'resolved':
        # 告警恢复时删除缓存，确保下次能正常发送
        redis_client.delete(cache_key)
        return True
    
    return False

def cache_device_status(device_ip, status, ttl=30):
    """缓存设备状态"""
    cache_key = f"device_status:{device_ip}"
    redis_client.setex(cache_key, ttl, status)

def get_cached_device_status(device_ip):
    """获取缓存的设备状态"""
    cache_key = f"device_status:{device_ip}"
    return redis_client.get(cache_key)

# 在webhook处理函数中使用告警去重
@app.route('/webhook/alertmanager', methods=['POST'])
def alertmanager_webhook():
    try:
        data = request.get_json()
        for alert in data.get('alerts', []):
            alert_key = f"{alert.get('labels', {}).get('instance', 'unknown')}_{alert.get('labels', {}).get('alertname', 'unknown')}"
            alert_status = alert.get('status', 'unknown')
            
            # 检查是否需要发送告警
            if should_send_alert(alert_key, alert_status):
                # 发送告警逻辑
                send_notification(alert)
            
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"处理Alertmanager webhook失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8888))
    app.run(host='0.0.0.0', port=port, debug= (LOG_LEVEL == 'DEBUG') )