# CCTV 监控系统架构迁移指南

## 迁移概述

本指南将帮助你从复杂的多服务监控架构（Zabbix + Prometheus + Grafana + Redis 等8个服务）迁移到简化的 Uptime Kuma 单服务方案。

### 迁移收益
- **服务数量**: 从8个减少到1个
- **资源消耗**: 内存使用从 ~2GB 降至 ~256MB
- **维护复杂度**: 大幅降低
- **故障点**: 从8个减少到1个
- **启动时间**: 从2-5分钟缩短到10-30秒

## 迁移前准备

### 1. 环境检查
```bash
# 检查Docker和Docker Compose版本
docker --version
docker-compose --version

# 检查端口占用情况
netstat -tlnp | grep :3001

# 检查磁盘空间
df -h
```

### 2. 数据备份
```bash
# 创建备份目录
mkdir -p backup/$(date +%Y%m%d)
cd backup/$(date +%Y%m%d)

# 备份当前配置文件
cp -r ../../configs .
cp ../../docker-compose.yml .

# 备份数据库（如果需要）
docker-compose exec mysql mysqldump -u root -p zabbix > zabbix_backup.sql

# 备份Grafana配置和仪表板
docker cp cctv-grafana:/var/lib/grafana ./grafana_backup

# 备份Prometheus数据（可选，数据量可能很大）
# docker cp cctv-prometheus:/prometheus ./prometheus_backup
```

### 3. 记录当前告警配置
```bash
# 导出当前的通知配置供参考
cp ../../configs/notification/notification_config.yml .

# 记录Webhook地址
echo "钉钉Webhook: $DINGTALK_WEBHOOK"
echo "微信Webhook: $WECHAT_WEBHOOK" 
echo "飞书Webhook: $FEISHU_WEBHOOK"
```

## 迁移步骤

### 第一阶段：部署 Uptime Kuma

#### 1.1 启动新系统
```bash
# 返回项目根目录
cd ../../

# 启动 Uptime Kuma（与旧系统并行运行）
docker-compose -f docker-compose-uptime-kuma.yml up -d

# 检查服务状态
docker-compose -f docker-compose-uptime-kuma.yml ps
docker logs cctv-uptime-kuma
```

#### 1.2 初始化管理界面
1. 访问 http://localhost:3001
2. 创建管理员账户
3. 设置时区为 Asia/Shanghai
4. 记录登录凭据

### 第二阶段：配置迁移

#### 2.1 运行迁移脚本
```bash
# 安装Python依赖
pip install pyyaml

# 运行迁移脚本（先预览）
python scripts/migrate_to_uptime_kuma.py --dry-run

# 生成配置文件
python scripts/migrate_to_uptime_kuma.py

# 检查生成的文件
ls -la uptime-kuma-config/
```

#### 2.2 导入监控配置
1. 在 Uptime Kuma 界面中，进入 **Settings** → **Import & Export**
2. 选择 **Import** 选项卡
3. 上传 `uptime-kuma-config/uptime-kuma-config.json` 文件
4. 确认导入的监控项数量
5. 点击 **Import** 按钮

#### 2.3 配置通知方式

**钉钉机器人配置：**
1. 进入 **Settings** → **Notifications**
2. 点击 **Add New notification**
3. 选择 **DingDing**
4. 填写以下信息：
   - Friendly Name: `CCTV钉钉告警`
   - Webhook URL: 你的钉钉机器人Webhook地址
   - Secret: 机器人安全设置中的加签密钥（如果启用）
5. 点击 **Test** 测试通知
6. 保存配置

**微信企业版配置：**
1. 添加新通知，选择 **WeChat Work**
2. 填写企业信息：
   - 企业ID (corpid)
   - 应用Secret
   - 应用ID (agentid)
   - 用户ID或部门ID
3. 测试并保存

**飞书机器人配置：**
1. 添加新通知，选择 **Feishu**
2. 填写飞书机器人Webhook URL
3. 测试并保存

### 第三阶段：监控项配置

#### 3.1 检查自动生成的监控项
1. 在主界面查看所有监控项状态
2. 确认设备名称和类型正确
3. 调整检查间隔（建议值）：
   - Ping检查：60秒
   - HTTP检查：120秒
   - 端口检查：180秒

#### 3.2 为监控项绑定通知
1. 编辑每个监控项
2. 在 **Notifications** 部分选择要接收告警的通知方式
3. 配置通知条件：
   - ✅ **Down** (设备故障时通知)
   - ✅ **Up** (设备恢复时通知)
   - ⭕ **Maintenance** (维护模式，根据需要)

#### 3.3 设置监控组和标签
1. 使用标签对设备进行分类：
   - `camera` - 摄像头
   - `nvr` - NVR设备
   - `switch` - 交换机
   - `critical` - 关键设备
2. 创建监控组便于管理

### 第四阶段：验证和测试

#### 4.1 功能验证
```bash
# 测试网络连通性
ping -c 3 192.168.1.101  # 替换为你的设备IP

# 测试HTTP服务
curl -I http://192.168.1.101  # 替换为你的设备IP
```

#### 4.2 告警测试
1. 临时断开一台测试设备的网络
2. 等待监控检测到故障（通常1-3分钟）
3. 验证告警通知是否正常发送
4. 恢复设备网络连接
5. 验证恢复通知

#### 4.3 创建状态页面（可选）
1. 进入 **Status Pages**
2. 创建新的状态页面
3. 选择要展示的监控项
4. 配置页面样式和访问权限
5. 获取状态页面链接分享给相关人员

### 第五阶段：切换和清理

#### 5.1 监控切换
1. 确认新系统运行稳定（建议观察1-2天）
2. 逐步停用旧系统的告警通知
3. 更新相关文档和操作手册

#### 5.2 系统清理（谨慎操作）
```bash
# 停止旧的监控服务
docker-compose down

# 清理未使用的Docker镜像和容器
docker system prune -f

# 清理未使用的数据卷（⚠️ 这会删除所有数据！）
# docker volume prune -f

# 重命名旧的配置文件作为备份
mv docker-compose.yml docker-compose.yml.old
mv docker-compose-uptime-kuma.yml docker-compose.yml
```

## 配置优化建议

### 监控间隔优化
根据设备重要性调整检查频率：

| 设备类型 | 推荐间隔 | 说明 |
|----------|----------|------|
| 关键摄像头 | 30-60秒 | 需要快速发现故障 |
| 普通摄像头 | 2-5分钟 | 平衡及时性和性能 |
| NVR设备 | 1-2分钟 | 影响多个摄像头 |
| 网络交换机 | 1分钟 | 网络基础设施 |
| 服务器 | 30秒 | 核心基础设施 |

### 告警策略优化
1. **重试次数**：设置2-3次重试，避免网络抖动误报
2. **超时时间**：根据设备响应特性调整
3. **维护窗口**：为定期维护设置免打扰时间
4. **告警分级**：区分关键告警和一般告警

### 性能优化
```bash
# 调整容器资源限制
docker-compose -f docker-compose-uptime-kuma.yml up -d --force-recreate

# 监控系统资源使用
docker stats cctv-uptime-kuma

# 定期清理历史数据（在Web界面设置中配置）
```

## 故障排查

### 常见问题

#### 1. 容器启动失败
```bash
# 检查端口占用
netstat -tlnp | grep :3001

# 检查容器日志
docker logs cctv-uptime-kuma

# 检查数据卷权限
ls -la /var/lib/docker/volumes/cctv-allin_uptime-kuma-data/
```

#### 2. 监控项无法正常检查
- 检查网络连通性：`ping 目标IP`
- 检查防火墙设置
- 验证端口开放状态：`telnet 目标IP 端口`
- 调整超时时间和重试次数

#### 3. 通知发送失败
- 验证Webhook URL的有效性
- 检查网络访问权限
- 查看通知历史记录中的错误信息
- 使用curl命令手动测试Webhook

#### 4. 数据导入失败
- 检查JSON文件格式是否正确
- 确认配置文件编码为UTF-8
- 查看浏览器控制台错误信息

### 回滚方案
如果迁移过程中遇到严重问题，可以快速回滚：

```bash
# 停止新系统
docker-compose -f docker-compose-uptime-kuma.yml down

# 恢复旧系统
docker-compose up -d

# 从备份恢复配置（如果需要）
cp backup/$(date +%Y%m%d)/configs/* configs/
```

## 维护建议

### 日常维护
1. **每日检查**：查看监控状态，处理告警
2. **每周备份**：导出配置和数据
3. **每月优化**：检查资源使用，清理历史数据
4. **每季度更新**：升级系统版本，审查监控策略

### 备份策略
```bash
# 创建定期备份脚本
cat > /scripts/backup_uptime_kuma.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backup/uptime-kuma/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 导出配置
docker exec cctv-uptime-kuma tar -czf /tmp/backup.tar.gz -C /app/data .
docker cp cctv-uptime-kuma:/tmp/backup.tar.gz "$BACKUP_DIR/"

# 清理30天前的备份
find /backup/uptime-kuma -type d -mtime +30 -exec rm -rf {} \;
EOF

chmod +x /scripts/backup_uptime_kuma.sh

# 添加到crontab
echo "0 2 * * * /scripts/backup_uptime_kuma.sh" | crontab -
```

### 监控系统的监控
为确保监控系统本身的可用性，建议：
1. 设置外部监控检查 Uptime Kuma 的可用性
2. 配置系统资源告警
3. 设置数据库文件大小监控

## 总结

通过迁移到 Uptime Kuma，你获得了：
- ✅ 大幅简化的架构
- ✅ 更低的资源消耗
- ✅ 更简单的维护
- ✅ 现代化的Web界面
- ✅ 丰富的通知选项

这个迁移将使你的CCTV监控系统更加稳定、易于维护，同时保持所有必要的监控功能。