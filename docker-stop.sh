#!/bin/bash

# CodeRunner Docker 停止脚本
# 停止并清理所有相关容器

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="coderunner"
NETWORK_NAME="${PROJECT_NAME}_network"
BACKEND_CONTAINER="${PROJECT_NAME}_backend"
FRONTEND_CONTAINER="${PROJECT_NAME}_frontend"

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止并删除容器
stop_containers() {
    log_info "停止CodeRunner容器..."

    local stopped=false

    # 停止并删除容器
    if docker ps -q -f name=$BACKEND_CONTAINER | grep -q .; then
        log_info "停止后端容器: $BACKEND_CONTAINER"
        docker stop $BACKEND_CONTAINER
        docker rm $BACKEND_CONTAINER
        stopped=true
    fi

    if docker ps -q -f name=$FRONTEND_CONTAINER | grep -q .; then
        log_info "停止前端容器: $FRONTEND_CONTAINER"
        docker stop $FRONTEND_CONTAINER
        docker rm $FRONTEND_CONTAINER
        stopped=true
    fi

    # 停止可能存在的容器（即使不在运行中）
    docker rm $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true

    if [ "$stopped" = true ]; then
        log_success "容器已停止并删除"
    else
        log_warning "没有找到运行中的容器"
    fi
}

# 删除网络
remove_network() {
    log_info "清理Docker网络..."

    if docker network ls -q -f name=$NETWORK_NAME | grep -q .; then
        docker network rm $NETWORK_NAME
        log_success "网络已删除"
    else
        log_warning "没有找到相关网络"
    fi
}

# 清理镜像（可选）
clean_images() {
    if [ "$1" = "--clean-images" ]; then
        log_info "清理Docker镜像..."
        docker rmi ${PROJECT_NAME}_backend ${PROJECT_NAME}_frontend 2>/dev/null || true
        log_success "镜像已清理"
    fi
}

# 显示帮助信息
show_help() {
    echo "CodeRunner Docker 停止脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help         显示此帮助信息"
    echo "  --clean-images     同时清理相关镜像"
    echo ""
    echo "此脚本将停止并删除所有CodeRunner相关的容器和网络"
    echo ""
}

# 主函数
main() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --clean-images)
                clean_images_flag="--clean-images"
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    log_info "开始停止CodeRunner Docker服务..."

    stop_containers
    remove_network
    clean_images $clean_images_flag

    log_success "CodeRunner Docker服务已停止"
    echo ""
    echo "💡 提示: 使用 ./docker-start.sh 重新启动服务"
}

# 执行主函数
main "$@"