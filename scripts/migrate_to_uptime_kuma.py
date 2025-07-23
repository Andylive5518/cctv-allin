#!/usr/bin/env python3
"""
设备配置迁移脚本 - 从复杂架构迁移到 Uptime Kuma
将原 devices.yml 中的设备配置转换为 Uptime Kuma 导入格式
"""

import yaml
import json
import argparse
import sys
from pathlib import Path

def load_devices_config(config_path):
    """加载原设备配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            devices = yaml.safe_load(f)
        return devices if devices else []
    except FileNotFoundError:
        print(f"错误: 找不到配置文件 {config_path}")
        return []
    except yaml.YAMLError as e:
        print(f"错误: YAML文件解析失败 {e}")
        return []

def convert_device_to_uptime_kuma(device):
    """将单个设备配置转换为 Uptime Kuma 监控项"""
    monitors = []
    
    name = device.get('name', '未知设备')
    ip = device.get('ip', '')
    device_type = device.get('type', 'unknown')
    
    if not ip:
        print(f"警告: 设备 {name} 没有IP地址，跳过")
        return monitors
    
    # 基础Ping监控 - 所有设备都添加
    ping_monitor = {
        "name": f"{name} - Ping检查",
        "type": "ping",
        "hostname": ip,
        "port": None,
        "interval": 60,
        "retryInterval": 60,
        "maxRetries": 3,
        "timeout": 10,
        "active": True,
        "tags": [device_type, "ping"],
        "description": f"{device_type}设备的网络连通性检查"
    }
    monitors.append(ping_monitor)
    
    # 根据设备类型和配置添加特定监控
    check_type = device.get('check_type', 'icmp')
    modules = device.get('modules', [])
    
    # HTTP/HTTPS 监控
    if check_type in ['http', 'https'] or 'http_2xx' in modules:
        http_port = device.get('http_port', 80 if check_type == 'http' else 443)
        http_path = device.get('http_path', '/')
        
        http_monitor = {
            "name": f"{name} - Web界面",
            "type": "http",
            "url": f"{check_type}://{ip}:{http_port}{http_path}",
            "interval": 120,
            "retryInterval": 120,
            "maxRetries": 3,
            "timeout": 15,
            "active": True,
            "tags": [device_type, "web"],
            "description": f"{device_type}设备的Web管理界面检查"
        }
        monitors.append(http_monitor)
    
    # RTSP/摄像头特殊检查
    if device_type == 'ip_camera':
        # RTSP端口检查
        rtsp_monitor = {
            "name": f"{name} - RTSP流",
            "type": "port",
            "hostname": ip,
            "port": 554,
            "interval": 180,
            "retryInterval": 180,
            "maxRetries": 2,
            "timeout": 10,
            "active": True,
            "tags": ["camera", "rtsp"],
            "description": "摄像头RTSP视频流端口检查"
        }
        monitors.append(rtsp_monitor)
        
        # 如果有摄像头特定的HTTP检查
        camera_http_port = device.get('camera_http_port', 80)
        if camera_http_port != device.get('http_port', 80):
            camera_http_monitor = {
                "name": f"{name} - 摄像头API",
                "type": "http",
                "url": f"http://{ip}:{camera_http_port}/",
                "interval": 300,
                "retryInterval": 300,
                "maxRetries": 2,
                "timeout": 20,
                "active": True,
                "tags": ["camera", "api"],
                "description": "摄像头API接口检查"
            }
            monitors.append(camera_http_monitor)
    
    # NVR特殊检查
    elif device_type == 'nvr':
        # NVR通常有多个端口需要检查
        nvr_ports = [80, 8000, 8080, 37777]  # 常见NVR端口
        
        for port in nvr_ports:
            port_monitor = {
                "name": f"{name} - 端口{port}",
                "type": "port", 
                "hostname": ip,
                "port": port,
                "interval": 240,
                "retryInterval": 240,
                "maxRetries": 2,
                "timeout": 15,
                "active": True,
                "tags": ["nvr", f"port-{port}"],
                "description": f"NVR设备端口{port}检查"
            }
            monitors.append(port_monitor)
    
    # 交换机SNMP检查（转换为端口检查）
    elif device_type == 'switch':
        snmp_monitor = {
            "name": f"{name} - SNMP",
            "type": "port",
            "hostname": ip,
            "port": 161,
            "interval": 120,
            "retryInterval": 120,
            "maxRetries": 3,
            "timeout": 10,
            "active": True,
            "tags": ["switch", "snmp"],
            "description": "交换机SNMP服务检查"
        }
        monitors.append(snmp_monitor)
    
    return monitors

def generate_uptime_kuma_config(devices):
    """生成 Uptime Kuma 导入配置"""
    all_monitors = []
    
    for device in devices:
        monitors = convert_device_to_uptime_kuma(device)
        all_monitors.extend(monitors)
    
    # 生成配置文件结构
    config = {
        "version": "1.21.0",
        "monitors": all_monitors,
        "notifications": [],  # 通知配置需要手动在界面中设置
        "tags": []
    }
    
    return config

def create_usage_guide(output_dir):
    """创建使用指南文件"""
    guide_content = """# Uptime Kuma 设备监控配置指南

## 配置导入

### 1. 启动服务
```bash
# 启动 Uptime Kuma
docker-compose -f docker-compose-uptime-kuma.yml up -d

# 检查服务状态
docker-compose -f docker-compose-uptime-kuma.yml ps
```

### 2. 初始化设置
1. 访问 http://localhost:3001
2. 创建管理员账户
3. 登录后进入主界面

### 3. 导入配置
1. 进入 Settings → Import/Export
2. 选择 Import 选项卡
3. 点击 "Choose File" 选择 `uptime-kuma-config.json`
4. 点击 "Import" 按钮
5. 确认导入成功

## 通知配置

### 钉钉机器人
1. 进入 Settings → Notifications
2. 点击 "Setup Notification"
3. 选择 "DingDing"
4. 填写配置:
   - Friendly Name: `CCTV告警-钉钉`
   - Webhook URL: 你的钉钉机器人Webhook地址
   - Secret: 机器人安全设置中的加签密钥（如果启用）
5. 点击 "Test" 测试
6. 保存配置

### 微信企业版
1. 选择 "WeChat Work"
2. 填写配置:
   - 企业ID (Corp ID)
   - 应用Secret (Agent Secret)
   - 应用ID (Agent ID)
   - 用户ID (To User)
3. 测试并保存

### 飞书机器人
1. 选择 "Feishu"
2. 填写 Webhook URL
3. 测试并保存

## 监控项配置

### 为监控项绑定通知
1. 点击监控项名称进入编辑页面
2. 滚动到 "Notifications" 部分
3. 点击通知方式旁的开关启用
4. 保存设置

### 调整监控参数
根据实际情况调整：
- **检查间隔**: 建议60-300秒
- **重试次数**: 建议2-3次
- **超时时间**: 根据设备响应时间调整

## 状态页面（可选）

### 创建公开状态页面
1. 进入 "Status Pages"
2. 点击 "New Status Page"
3. 配置页面信息：
   - 页面名称: "CCTV设备状态"
   - 描述: "安防监控设备实时状态"
   - 主题: 选择合适的主题
4. 添加监控组
5. 保存并发布

## 日常使用

### 查看监控状态
- 主界面显示所有监控项的实时状态
- 绿色：正常运行
- 红色：故障或不可达
- 灰色：暂停监控

### 处理告警
1. 收到告警通知时，先检查设备物理状态
2. 登录 Uptime Kuma 查看详细信息
3. 如需临时暂停告警，可设置维护模式

### 查看历史数据
- 点击监控项查看详细统计
- 可用率、响应时间趋势
- 故障历史记录

## 故障排查

### 监控检查失败
1. 确认设备网络连通性: `ping 设备IP`
2. 检查设备服务状态
3. 验证防火墙设置
4. 调整超时参数

### 通知发送失败
1. 验证 Webhook URL 正确性
2. 检查网络访问权限
3. 查看通知历史记录中的错误信息

### 性能优化
1. 合理设置检查间隔
2. 避免同时检查过多设备
3. 定期清理历史数据

## 备份与恢复

### 数据备份
```bash
# 备份配置和数据
./deploy.sh --backup
```

### 配置导出
1. 进入 Settings → Import/Export
2. 点击 "Export" 
3. 下载配置文件保存

## 高级配置

### 自定义检查
- HTTP 关键词检查
- JSON API 响应验证
- 证书到期监控

### 监控组管理
- 使用标签分类设备
- 批量管理监控项
- 分组告警策略
"""
    
    guide_path = output_dir / "usage_guide.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"使用指南已生成: {guide_path}")

def main():
    parser = argparse.ArgumentParser(description='CCTV监控系统配置迁移工具')
    parser.add_argument('--input', '-i', default='configs/devices.yml',
                       help='输入的设备配置文件路径 (默认: configs/devices.yml)')
    parser.add_argument('--output', '-o', default='uptime-kuma-config',
                       help='输出目录 (默认: uptime-kuma-config)')
    parser.add_argument('--dry-run', action='store_true',
                       help='仅显示转换结果，不写入文件')
    
    args = parser.parse_args()
    
    # 加载设备配置
    print(f"正在加载设备配置: {args.input}")
    devices = load_devices_config(args.input)
    
    if not devices:
        print("没有找到设备配置，退出")
        sys.exit(1)
    
    print(f"找到 {len(devices)} 个设备")
    
    # 转换配置
    uptime_kuma_config = generate_uptime_kuma_config(devices)
    
    if args.dry_run:
        print("\n=== 转换结果预览 ===")
        print(json.dumps(uptime_kuma_config, indent=2, ensure_ascii=False))
        return
    
    # 创建输出目录
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # 写入配置文件
    config_file = output_dir / "uptime-kuma-config.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(uptime_kuma_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Uptime Kuma配置文件已生成: {config_file}")
    print(f"   生成了 {len(uptime_kuma_config['monitors'])} 个监控项")
    
    # 生成迁移指南（改为使用指南）
    create_usage_guide(output_dir)
    
    print("\n🚀 接下来的步骤:")
    print("1. 启动 Uptime Kuma: docker-compose -f docker-compose-uptime-kuma.yml up -d")
    print("2. 访问 http://localhost:3001 并创建管理员账户")
    print("3. 导入配置文件: Settings → Import/Export → Import")
    print("4. 配置通知方式: Settings → Notifications")
    print("5. 验证所有监控项正常工作")

if __name__ == "__main__":
    main()