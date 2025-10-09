# CodeRunner Docker 部署指南

本文档介绍如何使用原生Docker容器部署CodeRunner项目，无需Docker Compose。

## 🏗️ 架构概述

CodeRunner使用两个独立的Docker容器：
- **backend**: FastAPI后端服务 (Python 3.11)
- **frontend**: React前端服务 (Nginx + 静态文件)

两个容器通过Docker网络进行通信。

## 📋 前置要求

- Docker 20.10+
- Docker Engine运行中
- 至少2GB可用内存
- 至少2GB可用磁盘空间

## 🚀 快速开始

### 1. 使用管理脚本（推荐）

```bash
# 启动服务
./docker-manager.sh start

# 查看状态
./docker-manager.sh status

# 查看日志
./docker-manager.sh logs backend -f

# 停止服务
./docker-manager.sh stop
```

### 2. 使用单独的启动脚本

```bash
# 启动服务
./docker-start.sh

# 停止服务
./docker-stop.sh
```

## 📚 详细使用说明

### 服务管理

#### 启动服务
```bash
# 正常启动
./docker-manager.sh start

# 重启服务
./docker-manager.sh restart

# 强制重新构建镜像并启动
./docker-manager.sh start -b
```

#### 查看状态
```bash
# 显示服务状态
./docker-manager.sh status
```

#### 查看日志
```bash
# 查看后端日志
./docker-manager.sh logs backend

# 实时跟踪后端日志
./docker-manager.sh logs backend -f

# 查看前端日志
./docker-manager.sh logs frontend

# 查看所有日志
./docker-manager.sh logs all
```

#### 进入容器
```bash
# 进入后端容器
./docker-manager.sh exec backend

# 进入前端容器
./docker-manager.sh exec frontend
```

#### 停止服务
```bash
# 停止服务
./docker-manager.sh stop

# 停止服务并清理镜像
./docker-manager.sh stop --clean-images
```

#### 清理资源
```bash
# 清理所有相关资源
./docker-manager.sh cleanup
```

## 🔧 配置选项

### 环境变量

可以通过环境变量配置后端服务：

```bash
# 设置JWT密钥
export SECRET_KEY="your-secret-key"

# 启动服务
./docker-manager.sh start
```

### 端口配置

默认端口配置：
- 前端: 3000
- 后端: 8000

如需修改端口，请编辑脚本中的配置：
```bash
# docker-manager.sh
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

### 数据持久化

后端容器的数据挂载到项目根目录的 `data/` 文件夹：
- 数据库文件: `data/coderunner.db`
- 临时文件: `data/temp/`

## 🌐 访问地址

服务启动后，可通过以下地址访问：

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **API Schema**: http://localhost:8000/openapi.json

## 🔍 故障排除

### 常见问题

#### 1. 容器启动失败
```bash
# 查看详细日志
./docker-manager.sh logs backend
./docker-manager.sh logs frontend

# 重新构建镜像
./docker-manager.sh start -b
```

#### 2. 端口冲突
```bash
# 检查端口占用
lsof -i :3000
lsof -i :8000

# 修改脚本中的端口配置
```

#### 3. Docker权限问题
```bash
# 确保用户在docker组中
sudo usermod -aG docker $USER
# 重新登录或刷新组权限
newgrp docker
```

#### 4. 数据库问题
```bash
# 检查数据目录权限
ls -la data/

# 重新初始化数据库
docker exec -it coderunner_backend python -c "from database import init_db; init_db()"
```

### 重置服务

如需完全重置服务：

```bash
# 停止并清理所有资源
./docker-manager.sh cleanup

# 重新启动
./docker-manager.sh start
```

## 📁 文件结构

```
CodeRunner/
├── backend/
│   ├── Dockerfile              # 后端Docker配置
│   ├── .dockerignore          # 后端忽略文件
│   ├── requirements.txt       # Python依赖
│   └── ...                    # 后端源码
├── frontend/
│   ├── Dockerfile             # 前端Docker配置
│   ├── .dockerignore         # 前端忽略文件
│   ├── nginx.conf            # Nginx配置
│   ├── package.json          # Node.js依赖
│   └── ...                   # 前端源码
├── data/                     # 数据持久化目录
├── docker-manager.sh         # 主管理脚本
├── docker-start.sh          # 简单启动脚本
├── docker-stop.sh           # 停止脚本
└── DOCKER_README.md         # 本文档
```

## 🔒 安全注意事项

1. **生产环境部署**
   - 修改默认的SECRET_KEY
   - 使用HTTPS
   - 配置防火墙规则
   - 定期更新基础镜像

2. **网络安全**
   - 不要将8000端口暴露到公网
   - 使用反向代理（如Nginx）处理HTTPS

3. **数据安全**
   - 定期备份数据目录
   - 确保数据目录权限正确

## 📈 监控和维护

### 健康检查

两个容器都配置了健康检查：
- 后端: 检查根路径响应
- 前端: 检查主页响应

### 日志管理

```bash
# 查看容器资源使用
docker stats

# 清理未使用的Docker资源
docker system prune -f
```

### 更新部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
./docker-manager.sh restart -b
```

## 🆘 获取帮助

如遇到问题：

1. 查看日志：`./docker-manager.sh logs all`
2. 检查Docker状态：`docker ps -a`
3. 查看项目README.md了解更多信息
4. 提交Issue到项目仓库

---

**注意**: 本Docker配置仅用于开发和测试环境，生产环境部署请参考生产环境配置指南。