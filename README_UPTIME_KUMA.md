# CCTV 监控系统 - Uptime Kuma 方案

## 快速开始

这是一个基于 Uptime Kuma 的轻量级 CCTV 监控方案，相比传统的多服务架构（Zabbix + Prometheus + Grafana + Redis 等），提供了：

- ✅ **极简部署**：单容器解决方案
- ✅ **资源轻量**：内存占用 < 256MB  
- ✅ **现代界面**：直观的 Web 管理界面
- ✅ **多种监控**：HTTP/TCP/Ping/DNS 等
- ✅ **丰富通知**：钉钉/微信/飞书/邮件等 40+ 种方式

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd cctv-allin

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

### 手动部署

```bash
# 启动服务
docker-compose -f docker-compose-uptime-kuma.yml up -d

# 检查状态
docker-compose -f docker-compose-uptime-kuma.yml ps
```

### 初始化配置

1. **访问管理界面**：http://localhost:3001
2. **创建管理员账户**：首次访问时设置
3. **添加监控项**：点击 "Add New Monitor"
4. **配置通知**：Settings → Notifications

## 监控配置示例

### IP 摄像头监控

```yaml
类型: HTTP/HTTPS
URL: http://192.168.1.101
名称: 大门摄像头
检查间隔: 60秒
超时: 10秒
标签: camera, entrance
```

### NVR 设备监控

```yaml
类型: HTTP/HTTPS  
URL: http://192.168.1.200
名称: 主楼NVR
检查间隔: 120秒
超时: 15秒
标签: nvr, critical
```

### 网络设备监控

```yaml
类型: Ping
主机: 192.168.1.1
名称: 核心交换机
检查间隔: 30秒
超时: 5秒
标签: network, switch
```

### RTSP 流监控

```yaml
类型: TCP Port
主机: 192.168.1.101
端口: 554
名称: 摄像头RTSP流
检查间隔: 180秒
标签: camera, rtsp
```

## 通知配置

### 钉钉机器人
1. 在钉钉群中添加自定义机器人
2. 获取 Webhook URL
3. 在 Uptime Kuma 中选择 "DingDing" 类型
4. 填入 Webhook URL 和安全设置

### 微信企业版
1. 创建企业微信应用
2. 获取企业ID、应用ID、应用Secret
3. 在 Uptime Kuma 中选择 "WeChat Work" 类型
4. 填入相关参数

### 飞书机器人
1. 在飞书群中添加机器人
2. 获取 Webhook URL  
3. 在 Uptime Kuma 中选择 "Feishu" 类型
4. 填入 Webhook URL

## 常用命令

```bash
# 查看服务状态
./deploy.sh --status

# 查看日志
./deploy.sh --logs

# 重启服务
./deploy.sh --restart

# 停止服务
./deploy.sh --stop

# 备份数据
./deploy.sh --backup
```

## 目录结构

```
cctv-allin/
├── docker-compose-uptime-kuma.yml  # Uptime Kuma 配置
├── deploy.sh                       # 一键部署脚本
├── MIGRATION_GUIDE.md              # 详细部署指南
├── CLAUDE.md                       # 开发指南
├── configs/                        # 参考配置文件
│   ├── devices.yml                 # 设备清单示例
│   └── notification/               # 通知配置示例
├── scripts/                        # 工具脚本
│   └── migrate_to_uptime_kuma.py   # 配置迁移工具
└── backup/                         # 备份目录
```

## 性能对比

| 对比项 | 复杂架构 | Uptime Kuma |
|--------|----------|-------------|
| 服务数量 | 8个 | 1个 |
| 内存使用 | ~2GB | ~256MB |
| 启动时间 | 2-5分钟 | 10-30秒 |
| 配置复杂度 | 很高 | 很低 |
| 维护难度 | 困难 | 简单 |
| 故障点 | 多个 | 单一 |

## 高级功能

### 状态页面
- 创建公开的设备状态展示页面
- 支持自定义域名和SSL证书
- 可配置访问权限

### 监控组管理
- 使用标签对设备分类
- 批量操作监控项
- 分组告警策略

### API 集成
- RESTful API 支持
- 自动化脚本集成
- 第三方系统对接

## 故障排查

### 常见问题

**容器无法启动**
```bash
# 检查端口占用
netstat -tlnp | grep :3001

# 查看错误日志
docker logs cctv-uptime-kuma
```

**监控检查失败**
- 检查网络连通性：`ping 目标IP`
- 检查防火墙设置
- 验证服务端口开放

**通知发送失败**
- 验证 Webhook URL 有效性
- 检查网络访问权限
- 查看通知历史记录

## 支持与帮助

- 📖 **详细指南**：查看 `MIGRATION_GUIDE.md`
- 🔧 **开发文档**：查看 `CLAUDE.md`
- 💬 **问题反馈**：GitHub Issues
- 📧 **技术支持**：查看项目文档

## 许可证

MIT License