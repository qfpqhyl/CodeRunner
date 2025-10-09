#!/bin/bash

# CodeRunner Docker 启动脚本
# 使用原生Docker命令运行前后端容器

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
BACKEND_PORT=8000
FRONTEND_PORT=3000

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

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker服务未运行，请启动Docker服务"
        exit 1
    fi
}

# 停止并清理现有容器
stop_containers() {
    log_info "停止现有容器..."

    # 停止并删除容器
    docker stop $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true
    docker rm $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true

    # 删除网络（如果存在）
    docker network rm $NETWORK_NAME 2>/dev/null || true

    log_success "现有容器已清理"
}

# 创建Docker网络
create_network() {
    log_info "创建Docker网络..."
    docker network create $NETWORK_NAME || true
    log_success "Docker网络创建完成"
}

# 构建并启动后端容器
start_backend() {
    log_info "构建并启动后端容器..."

    # 构建后端镜像
    docker build -t ${PROJECT_NAME}_backend ./backend

    # 启动后端容器
    docker run -d \
        --name $BACKEND_CONTAINER \
        --network $NETWORK_NAME \
        -p $BACKEND_PORT:8000 \
        -v $(pwd)/data:/app/data \
        -e SECRET_KEY="${SECRET_KEY:-your-secret-key-change-in-production}" \
        -e DATABASE_URL="sqlite:///./data/coderunner.db" \
        --restart unless-stopped \
        ${PROJECT_NAME}_backend

    log_success "后端容器已启动，端口: $BACKEND_PORT"
}

# 构建并启动前端容器
start_frontend() {
    log_info "构建并启动前端容器..."

    # 构建前端镜像
    docker build -t ${PROJECT_NAME}_frontend ./frontend

    # 启动前端容器
    docker run -d \
        --name $FRONTEND_CONTAINER \
        --network $NETWORK_NAME \
        -p $FRONTEND_PORT:80 \
        --restart unless-stopped \
        ${PROJECT_NAME}_frontend

    log_success "前端容器已启动，端口: $FRONTEND_PORT"
}

# 等待容器启动
wait_for_containers() {
    log_info "等待容器启动..."

    # 等待后端启动
    log_info "等待后端服务启动..."
    for i in {1..30}; do
        if curl -f http://localhost:$BACKEND_PORT/ &>/dev/null; then
            log_success "后端服务已启动"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "后端服务启动超时"
            return 1
        fi
        sleep 2
    done

    # 等待前端启动
    log_info "等待前端服务启动..."
    for i in {1..30}; do
        if curl -f http://localhost:$FRONTEND_PORT/ &>/dev/null; then
            log_success "前端服务已启动"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "前端服务启动超时"
            return 1
        fi
        sleep 2
    done
}

# 显示服务状态
show_status() {
    echo ""
    echo "=========================================="
    echo "🚀 CodeRunner Docker 服务已启动"
    echo "=========================================="
    echo "📊 前端地址: http://localhost:$FRONTEND_PORT"
    echo "🔧 后端API: http://localhost:$BACKEND_PORT"
    echo "📖 API文档: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "🐳 容器状态:"
    docker ps --filter "name=$PROJECT_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "📝 查看日志:"
    echo "  后端: docker logs -f $BACKEND_CONTAINER"
    echo "  前端: docker logs -f $FRONTEND_CONTAINER"
    echo ""
    echo "🛑 停止服务:"
    echo "  ./docker-stop.sh"
    echo "=========================================="
}

# 显示帮助信息
show_help() {
    echo "CodeRunner Docker 启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -r, --restart  重启服务（停止现有容器并重新启动）"
    echo "  -b, --build    强制重新构建镜像"
    echo ""
    echo "环境变量:"
    echo "  SECRET_KEY     JWT密钥（默认: your-secret-key-change-in-production）"
    echo ""
}

# 主函数
main() {
    local restart=false
    local rebuild=false

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -r|--restart)
                restart=true
                shift
                ;;
            -b|--build)
                rebuild=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 检查Docker
    check_docker

    # 停止现有容器（如果是重启模式）
    if [ "$restart" = true ]; then
        stop_containers
    fi

    # 创建网络
    create_network

    # 构建并启动容器
    if [ "$rebuild" = true ]; then
        log_info "强制重新构建镜像..."
        docker rmi ${PROJECT_NAME}_backend ${PROJECT_NAME}_frontend 2>/dev/null || true
    fi

    start_backend
    start_frontend

    # 等待容器启动
    wait_for_containers

    # 显示状态
    show_status
}

# 执行主函数
main "$@"