#!/bin/bash

# CodeRunner Docker 管理脚本
# 提供完整的Docker容器管理功能

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

log_header() {
    echo -e "${PURPLE}$1${NC}"
}

# 显示横幅
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    CodeRunner Docker 管理器                    ║"
    echo "║                     原生Docker容器管理工具                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
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

# 显示服务状态
show_status() {
    log_header "📊 CodeRunner 服务状态"
    echo ""

    # 检查容器状态
    local backend_running=false
    local frontend_running=false

    if docker ps -q -f name=$BACKEND_CONTAINER | grep -q .; then
        backend_running=true
    fi

    if docker ps -q -f name=$FRONTEND_CONTAINER | grep -q .; then
        frontend_running=true
    fi

    # 显示状态
    echo "容器状态:"
    if [ "$backend_running" = true ]; then
        echo "  ✅ 后端: 运行中 (端口: $BACKEND_PORT)"
    else
        echo "  ❌ 后端: 未运行"
    fi

    if [ "$frontend_running" = true ]; then
        echo "  ✅ 前端: 运行中 (端口: $FRONTEND_PORT)"
    else
        echo "  ❌ 前端: 未运行"
    fi

    echo ""

    # 显示访问地址
    if [ "$backend_running" = true ] || [ "$frontend_running" = true ]; then
        echo "访问地址:"
        if [ "$frontend_running" = true ]; then
            echo "  🌐 前端应用: http://localhost:$FRONTEND_PORT"
        fi
        if [ "$backend_running" = true ]; then
            echo "  🔧 后端API: http://localhost:$BACKEND_PORT"
            echo "  📖 API文档: http://localhost:$BACKEND_PORT/docs"
        fi
        echo ""
    fi

    # 显示容器详情
    local containers=$(docker ps -a --filter "name=$PROJECT_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}")
    if [ -n "$containers" ]; then
        echo "容器详情:"
        echo "$containers"
    else
        echo "没有找到相关容器"
    fi
}

# 启动服务
start_service() {
    log_header "🚀 启动 CodeRunner 服务"
    echo ""

    local restart=false
    local rebuild=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
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
                exit 1
                ;;
        esac
    done

    # 停止现有容器（如果是重启模式）
    if [ "$restart" = true ]; then
        log_info "重启模式: 停止现有容器..."
        docker stop $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true
        docker rm $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true
    fi

    # 创建网络
    log_info "创建Docker网络..."
    docker network create $NETWORK_NAME 2>/dev/null || true

    # 构建并启动后端
    log_info "构建并启动后端容器..."
    if [ "$rebuild" = true ]; then
        docker rmi ${PROJECT_NAME}_backend 2>/dev/null || true
    fi

    docker build -t ${PROJECT_NAME}_backend ./backend

    # 创建数据目录
    mkdir -p data

    docker run -d \
        --name $BACKEND_CONTAINER \
        --network $NETWORK_NAME \
        -p $BACKEND_PORT:8000 \
        -v $(pwd)/data:/app/data \
        -e SECRET_KEY="${SECRET_KEY:-your-secret-key-change-in-production}" \
        -e DATABASE_URL="sqlite:///./data/coderunner.db" \
        --restart unless-stopped \
        ${PROJECT_NAME}_backend

    # 构建并启动前端
    log_info "构建并启动前端容器..."
    if [ "$rebuild" = true ]; then
        docker rmi ${PROJECT_NAME}_frontend 2>/dev/null || true
    fi

    docker build -t ${PROJECT_NAME}_frontend ./frontend

    docker run -d \
        --name $FRONTEND_CONTAINER \
        --network $NETWORK_NAME \
        -p $FRONTEND_PORT:80 \
        --restart unless-stopped \
        ${PROJECT_NAME}_frontend

    log_success "服务启动完成!"

    # 等待服务就绪
    log_info "等待服务启动..."
    sleep 5

    # 显示状态
    echo ""
    show_status
}

# 停止服务
stop_service() {
    log_header "🛑 停止 CodeRunner 服务"
    echo ""

    local clean_images=false

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean-images)
                clean_images=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    # 停止容器
    log_info "停止容器..."
    docker stop $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true
    docker rm $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true

    # 删除网络
    log_info "清理网络..."
    docker network rm $NETWORK_NAME 2>/dev/null || true

    # 清理镜像
    if [ "$clean_images" = true ]; then
        log_info "清理镜像..."
        docker rmi ${PROJECT_NAME}_backend ${PROJECT_NAME}_frontend 2>/dev/null || true
    fi

    log_success "服务已停止"
}

# 显示日志
show_logs() {
    local container=$1
    local follow=false

    if [ "$2" = "--follow" ] || [ "$2" = "-f" ]; then
        follow=true
    fi

    case $container in
        backend|后端)
            if [ "$follow" = true ]; then
                docker logs -f $BACKEND_CONTAINER
            else
                docker logs $BACKEND_CONTAINER
            fi
            ;;
        frontend|前端)
            if [ "$follow" = true ]; then
                docker logs -f $FRONTEND_CONTAINER
            else
                docker logs $FRONTEND_CONTAINER
            fi
            ;;
        all|全部)
            if [ "$follow" = true ]; then
                log_info "显示所有容器日志 (Ctrl+C 退出)..."
                docker logs -f $BACKEND_CONTAINER $FRONTEND_CONTAINER
            else
                echo "=== 后端日志 ==="
                docker logs $BACKEND_CONTAINER
                echo ""
                echo "=== 前端日志 ==="
                docker logs $FRONTEND_CONTAINER
            fi
            ;;
        *)
            log_error "无效的容器名称: $container"
            echo "可用选项: backend(后端), frontend(前端), all(全部)"
            exit 1
            ;;
    esac
}

# 进入容器
exec_container() {
    local container=$1
    local command=${2:-/bin/bash}

    case $container in
        backend|后端)
            docker exec -it $BACKEND_CONTAINER $command
            ;;
        frontend|前端)
            docker exec -it $FRONTEND_CONTAINER $command
            ;;
        *)
            log_error "无效的容器名称: $container"
            echo "可用选项: backend(后端), frontend(前端)"
            exit 1
            ;;
    esac
}

# 清理资源
cleanup() {
    log_header "🧹 清理 CodeRunner 资源"
    echo ""

    log_info "停止并删除所有容器..."
    docker stop $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true
    docker rm $BACKEND_CONTAINER $FRONTEND_CONTAINER 2>/dev/null || true

    log_info "删除网络..."
    docker network rm $NETWORK_NAME 2>/dev/null || true

    log_info "删除镜像..."
    docker rmi ${PROJECT_NAME}_backend ${PROJECT_NAME}_frontend 2>/dev/null || true

    log_info "清理未使用的Docker资源..."
    docker system prune -f

    log_success "清理完成!"
}

# 显示帮助信息
show_help() {
    echo "CodeRunner Docker 管理脚本"
    echo ""
    echo "用法: $0 <命令> [选项]"
    echo ""
    echo "命令:"
    echo "  status              显示服务状态"
    echo "  start [选项]        启动服务"
    echo "    选项:"
    echo "      -r, --restart   重启服务"
    echo "      -b, --build     强制重新构建镜像"
    echo ""
    echo "  stop [选项]         停止服务"
    echo "    选项:"
    echo "      --clean-images  同时清理相关镜像"
    echo ""
    echo "  restart [选项]      重启服务"
    echo "    选项:"
    echo "      -b, --build     强制重新构建镜像"
    echo ""
    echo "  logs <容器> [选项]  查看日志"
    echo "    容器: backend(后端), frontend(前端), all(全部)"
    echo "    选项:"
    echo "      -f, --follow    实时跟踪日志"
    echo ""
    echo "  exec <容器> [命令]  进入容器"
    echo "    容器: backend(后端), frontend(前端)"
    echo "    命令: 默认为 /bin/bash"
    echo ""
    echo "  cleanup             清理所有相关资源"
    echo "  help                显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 status           # 查看状态"
    echo "  $0 start            # 启动服务"
    echo "  $0 restart -b       # 重启并重新构建"
    echo "  $0 logs backend -f  # 实时查看后端日志"
    echo "  $0 exec backend     # 进入后端容器"
    echo ""
}

# 主函数
main() {
    # 检查Docker
    check_docker

    # 显示横幅
    show_banner

    # 解析命令
    case $1 in
        status|状态|"")
            show_status
            ;;
        start|启动)
            shift
            start_service "$@"
            ;;
        stop|停止)
            shift
            stop_service "$@"
            ;;
        restart|重启)
            shift
            stop_service
            start_service "$@"
            ;;
        logs|日志)
            shift
            show_logs "$@"
            ;;
        exec|进入)
            shift
            exec_container "$@"
            ;;
        cleanup|清理)
            cleanup
            ;;
        help|帮助|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"