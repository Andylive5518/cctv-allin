# CLAUDE.md

这个文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个基于 Uptime Kuma 的简化 CCTV 监控运维平台：
- **Uptime Kuma**: 一体化监控解决方案，包含监控、告警、可视化功能
- **支持多种监控类型**: HTTP/HTTPS、TCP、Ping、DNS等
- **内置通知系统**: 支持钉钉、微信、飞书、邮件等多种通知方式
- **现代化界面**: 直观的Web界面和状态页面
- **轻量级架构**: 单容器部署，维护简单

## 常用命令

### 启动和管理服务
```bash
# 使用简化的Uptime Kuma方案启动
docker-compose -f docker-compose-uptime-kuma.yml up -d

# 查看服务状态
docker-compose -f docker-compose-uptime-kuma.yml ps

# 查看Uptime Kuma日志
docker-compose -f docker-compose-uptime-kuma.yml logs -f uptime-kuma

# 停止服务
docker-compose -f docker-compose-uptime-kuma.yml down

# 重启服务
docker-compose -f docker-compose-uptime-kuma.yml restart

# 备份数据
docker exec cctv-uptime-kuma tar -czf /app/data/backup.tar.gz -C /app/data .
docker cp cctv-uptime-kuma:/app/data/backup.tar.gz ./backup/

# 恢复数据
docker cp ./backup/backup.tar.gz cctv-uptime-kuma:/app/data/
docker exec cctv-uptime-kuma tar -xzf /app/data/backup.tar.gz -C /app/data/
```

### 从复杂架构迁移
```bash
# 1. 停止旧服务（可选，可以并行运行一段时间）
docker-compose down

# 2. 启动Uptime Kuma
docker-compose -f docker-compose-uptime-kuma.yml up -d

# 3. 使用迁移脚本导入设备配置
python scripts/migrate_to_uptime_kuma.py

# 4. 验证监控正常后，清理旧服务
docker system prune -f
```

## 项目架构

### 简化架构设计
```
网络设备 → Uptime Kuma → 通知渠道
(摄像头/NVR/交换机)     ↓        (钉钉/微信/飞书)
                     Web界面
                     状态页面
```

### 监控能力
- **HTTP/HTTPS监控**: 摄像头Web界面、NVR管理页面
- **TCP端口监控**: RTSP流、ONVIF协议端口
- **ICMP Ping监控**: 网络设备连通性检查
- **DNS监控**: 域名解析检查
- **关键词监控**: 网页内容变化检测
- **证书监控**: HTTPS证书过期提醒

### 告警策略
- **灵活的检查间隔**: 从20秒到24小时可配置
- **重试机制**: 可配置重试次数，避免误报
- **维护窗口**: 支持设置维护时间，暂停告警
- **告警升级**: 支持多级通知策略
- **状态页面**: 公开或私有的设备状态展示

### 关键文件和目录

#### 新架构文件
- `docker-compose-uptime-kuma.yml`: Uptime Kuma服务配置
- `scripts/migrate_to_uptime_kuma.py`: 从旧架构迁移的脚本
- `backup/`: 数据备份目录

#### 保留的配置文件（参考用）
- `configs/devices.yml`: 原设备清单，用于迁移参考
- `configs/notification/notification_config.yml`: 原通知配置参考

#### 数据存储
- Docker Volume: `uptime-kuma-data` 存储所有配置和历史数据
- 内置SQLite数据库，无需外部数据库

### 通知配置

Uptime Kuma内置多种通知方式：

#### 支持的通知渠道
- **钉钉机器人**: 支持群聊机器人和自定义机器人
- **微信企业应用**: 企业微信应用推送
- **飞书机器人**: 飞书群机器人通知
- **邮件**: SMTP邮件通知
- **Webhook**: 自定义HTTP POST通知
- **其他**: Slack、Telegram、Discord等40+种通知方式

#### 通知配置方法
1. 在Uptime Kuma Web界面中进入 "Settings" → "Notifications"
2. 添加通知方式，配置相应的Webhook URL或凭据
3. 在监控项中绑定通知方式
4. 设置通知条件（故障、恢复、维护等）

### 设备监控配置

#### 通过Web界面添加监控
1. 访问 `http://localhost:3001`
2. 注册管理员账户（首次访问）
3. 点击 "Add New Monitor" 添加监控项
4. 选择监控类型并配置参数

#### 常见设备监控配置

**IP摄像头监控**:
- 类型: HTTP/HTTPS
- URL: `http://192.168.1.101` (摄像头IP)
- 检查间隔: 60秒
- 超时: 10秒

**NVR设备监控**:
- 类型: HTTP/HTTPS  
- URL: `http://192.168.1.200` (NVR管理界面)
- 检查间隔: 120秒

**交换机监控**:
- 类型: Ping
- 主机名: `192.168.1.1`
- 检查间隔: 30秒

**RTSP流监控**:
- 类型: TCP Port
- 主机名: `192.168.1.101`
- 端口: `554`

### 访问端点

- **Uptime Kuma**: http://localhost:3001 (首次访问需注册管理员)
- **状态页面**: http://localhost:3001/status/[页面名称] (可选，需在设置中启用)
- **API端点**: http://localhost:3001/api/ (用于自动化脚本)

### 环境变量配置

Uptime Kuma 的配置主要通过 Web 界面完成，无需复杂的环境变量：

```bash
# 创建 .env 文件（可选）
TZ=Asia/Shanghai
UPTIME_KUMA_DISABLE_FRAME_SAMEORIGIN=true

# 如果使用 Nginx 反向代理
DOMAIN=monitor.yourcompany.com
SSL_CERT_PATH=./nginx/ssl/cert.pem
SSL_KEY_PATH=./nginx/ssl/key.pem
```

### 维护注意事项

#### 系统监控
- **CPU使用率**: 通常 < 10%（单容器轻量级）
- **内存使用**: 通常 < 256MB
- **磁盘空间**: 监控数据增长，定期清理历史数据
- **网络连通性**: 确保到监控目标的网络可达

#### 数据管理
1. **定期备份**: 建议每天备份 Uptime Kuma 数据
2. **清理历史**: 可在设置中配置数据保留期限
3. **导入导出**: 支持配置的导入导出功能

#### 高可用性（可选）
- 使用外部数据库（PostgreSQL/MySQL）替代内置SQLite
- 配置 Nginx 反向代理和SSL证书
- 设置多个监控节点进行冗余检查

#### 故障排查
1. **容器无法启动**: 检查端口占用和数据卷权限
2. **监控失效**: 检查网络连通性和目标服务状态  
3. **通知失败**: 验证Webhook URL和认证信息
4. **性能问题**: 调整监控间隔和并发数

#### 从旧系统迁移的优势对比

| 对比项 | 旧架构(8服务) | 新架构(1服务) |
|--------|---------------|---------------|
| 部署复杂度 | 很高 | 很低 |
| 资源消耗 | ~2GB RAM | ~256MB RAM |
| 维护工作量 | 很大 | 很小 |
| 故障点数量 | 8个 | 1个 |
| 启动时间 | 2-5分钟 | 10-30秒 |
| 配置复杂度 | 很高 | 很低 |
| 升级难度 | 困难 | 简单 |