#!/bin/bash

# CCTV 监控系统 - Uptime Kuma 快速部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    print_message $BLUE "================================"
    print_message $BLUE "$1"
    print_message $BLUE "================================"
}

# 检查依赖
check_dependencies() {
    print_header "检查系统依赖"
    
    if ! command -v docker &> /dev/null; then
        print_message $RED "错误: Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_message $RED "错误: Docker Compose 未安装"
        exit 1
    fi
    
    print_message $GREEN "✓ Docker 和 Docker Compose 已安装"
}

# 检查端口占用
check_ports() {
    print_header "检查端口占用"
    
    if ss -tulpn | grep :3001 &> /dev/null; then
        print_message $YELLOW "警告: 端口 3001 已被占用"
        print_message $YELLOW "请检查是否已有监控服务运行"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_message $GREEN "✓ 端口 3001 可用"
    fi
}

# 创建必要的目录
create_directories() {
    print_header "创建必要目录"
    
    mkdir -p backup
    mkdir -p uptime-kuma-config
    
    print_message $GREEN "✓ 目录创建完成"
}

# 创建示例配置
create_example_config() {
    print_header "创建设备配置示例"
    
    if [[ ! -f "configs/devices.yml" ]]; then
        mkdir -p configs
        cat > configs/devices.yml << 'EOF'
# CCTV 设备配置示例
# 你可以参考此文件配置你的设备，然后使用迁移脚本导入到 Uptime Kuma

- name: "大门摄像头"
  ip: "192.168.1.101"
  type: "ip_camera"
  check_type: "http"
  http_port: 80
  description: "主要入口监控摄像头"

- name: "停车场摄像头"
  ip: "192.168.1.102" 
  type: "ip_camera"
  check_type: "http"
  http_port: 80
  description: "停车场监控摄像头"

- name: "主楼NVR"
  ip: "192.168.1.200"
  type: "nvr"
  check_type: "http"
  http_port: 80
  description: "网络视频录像机"

- name: "核心交换机"
  ip: "192.168.1.1"
  type: "switch"
  check_type: "icmp"
  description: "网络核心交换设备"
EOF
        print_message $GREEN "✓ 设备配置示例已创建: configs/devices.yml"
    else
        print_message $YELLOW "设备配置文件已存在，跳过创建"
    fi
}

# 启动服务
start_services() {
    print_header "启动 Uptime Kuma 服务"
    
    docker-compose -f docker-compose-uptime-kuma.yml up -d
    
    # 等待服务启动
    print_message $YELLOW "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose -f docker-compose-uptime-kuma.yml ps | grep -q "Up"; then
        print_message $GREEN "✓ 服务启动成功"
    else
        print_message $RED "错误: 服务启动失败"
        docker-compose -f docker-compose-uptime-kuma.yml logs
        exit 1
    fi
}

# 显示完成信息
show_completion() {
    print_header "部署完成"
    
    print_message $GREEN "🎉 Uptime Kuma 已成功部署！"
    echo
    print_message $BLUE "访问地址: http://localhost:3001"
    print_message $BLUE "管理指南: 查看 MIGRATION_GUIDE.md"
    echo
    print_message $YELLOW "接下来的步骤:"
    echo "1. 访问 http://localhost:3001 创建管理员账户"
    echo "2. 手动添加监控项，或使用设备配置文件批量导入"
    echo "3. 配置通知方式 (钉钉、微信、飞书)"
    echo "4. 验证所有监控项正常工作"
    echo
    if [[ -f "configs/devices.yml" ]]; then
        print_message $YELLOW "💡 提示: 可以使用以下命令批量导入设备配置:"
        echo "   python3 scripts/migrate_to_uptime_kuma.py"
        echo "   然后在 Uptime Kuma 中导入生成的配置文件"
        echo
    fi
    echo
    print_message $BLUE "获取帮助:"
    echo "./deploy.sh --help"
}

# 显示帮助信息
show_help() {
    echo "CCTV 监控系统 - Uptime Kuma 部署脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  --help, -h        显示此帮助信息"
    echo "  --stop            停止服务"
    echo "  --restart         重启服务"
    echo "  --logs            查看服务日志"
    echo "  --status          查看服务状态"
    echo "  --backup          备份数据"
    echo "  --clean           清理旧服务（谨慎使用）"
    echo
    echo "示例:"
    echo "  $0                部署 Uptime Kuma"
    echo "  $0 --stop         停止服务"
    echo "  $0 --logs         查看日志"
}

# 停止服务
stop_services() {
    print_header "停止服务"
    docker-compose -f docker-compose-uptime-kuma.yml down
    print_message $GREEN "✓ 服务已停止"
}

# 重启服务
restart_services() {
    print_header "重启服务"
    docker-compose -f docker-compose-uptime-kuma.yml restart
    print_message $GREEN "✓ 服务已重启"
}

# 查看日志
show_logs() {
    print_header "查看服务日志"
    docker-compose -f docker-compose-uptime-kuma.yml logs -f
}

# 查看状态
show_status() {
    print_header "服务状态"
    docker-compose -f docker-compose-uptime-kuma.yml ps
}

# 备份数据
backup_data() {
    print_header "备份数据"
    
    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    if docker ps | grep -q cctv-uptime-kuma; then
        docker exec cctv-uptime-kuma tar -czf /tmp/backup.tar.gz -C /app/data .
        docker cp cctv-uptime-kuma:/tmp/backup.tar.gz "$BACKUP_DIR/"
        print_message $GREEN "✓ 数据已备份到: $BACKUP_DIR"
    else
        print_message $YELLOW "警告: 容器未运行，无法备份数据"
    fi
}

# 清理旧服务
clean_old_services() {
    print_header "清理旧服务"
    
    print_message $YELLOW "⚠️  这将删除旧的监控服务和数据"
    read -p "确认清理? 输入 'yes' 继续: " -r
    
    if [[ $REPLY == "yes" ]]; then
        if [[ -f "docker-compose.yml" ]]; then
            docker-compose down -v
        fi
        
        docker system prune -f
        print_message $GREEN "✓ 清理完成"
    else
        print_message $YELLOW "清理已取消"
    fi
}

# 主函数
main() {
    case "${1:-deploy}" in
        --help|-h)
            show_help
            ;;
        --stop)
            stop_services
            ;;
        --restart)
            restart_services
            ;;
        --logs)
            show_logs
            ;;
        --status)
            show_status
            ;;
        --backup)
            backup_data
            ;;
        --clean)
            clean_old_services
            ;;
        deploy|"")
            check_dependencies
            check_ports
            create_directories
            create_example_config
            start_services
            show_completion
            ;;
        *)
            print_message $RED "错误: 未知选项 $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"