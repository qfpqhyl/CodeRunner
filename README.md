# CodeRunner - 远程Python代码执行平台

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docker)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)

CodeRunner是一个基于FastAPI（后端）和React + Ant Design（前端）构建的远程Python代码执行平台。它提供了用户认证、多层级用户权限、AI代码生成、安全的Python代码执行、代码库管理、API密钥管理和全面的系统日志记录功能。

## ✨ 主要特性

### 🔐 用户系统
- JWT令牌认证，30分钟过期
- Argon2密码哈希加密
- 管理员/用户角色分离
- 多层级用户权限系统

### 👥 用户等级系统
- **Level 1 (免费)**: 10次/日执行，20次/日API调用，30s超时，128MB内存，5个保存代码，2个API密钥
- **Level 2 (基础)**: 50次/日执行，100次/日API调用，60s超时，256MB内存，20个保存代码，5个API密钥
- **Level 3 (高级)**: 200次/日执行，500次/日API调用，120s超时，512MB内存，100个保存代码，10个API密钥
- **Level 4 (企业)**: 无限执行，无限API调用，300s超时，1024MB内存，无限保存代码和API密钥

### 🚀 代码执行
- 安全的临时文件执行，自动清理
- 基于用户级别的超时和资源限制
- 每日执行配额和API调用配额
- 执行历史记录和内存使用跟踪
- 所有操作的系统日志记录，包含IP跟踪

### 🤖 AI集成
- 多AI提供商支持（Qwen、OpenAI、Claude、自定义OpenAI兼容API）
- 用户可配置的AI模型和API密钥管理
- 可自定义参数的代码生成（temperature、max_tokens）
- 活跃AI配置管理

### 📚 代码库
- 个人代码片段存储和标签管理
- 公开/私有代码分享
- API访问保存的代码以供外部执行
- 搜索和组织功能

### 🔧 系统管理
- 全面的系统日志过滤
- 管理员用户管理
- 执行监控和统计
- API密钥使用跟踪

## 🛠️ 技术栈

### 后端技术
- **FastAPI** - 高性能异步Web框架
- **SQLAlchemy** - 强大的Python ORM
- **SQLite** - 轻量级关系型数据库
- **JWT** - 无状态用户认证
- **Pydantic** - 数据验证和序列化
- **OpenAI SDK** - AI模型集成

### 前端技术
- **React 18** - 现代化前端框架
- **Ant Design 5** - 企业级UI组件库
- **React Router** - 单页应用路由管理
- **Axios** - HTTP请求客户端

### AI集成
- **通义千问** - 阿里云大语言模型
- **OpenAI** - GPT系列模型支持
- **Claude** - Anthropic AI模型
- **自定义配置** - 支持任意OpenAI兼容的API

## 📁 项目结构

```
CodeRunner/
├── backend/                    # FastAPI后端服务
│   ├── main.py                # 主应用入口
│   ├── database.py            # 数据库模型和配置
│   ├── models.py              # Pydantic数据模型
│   ├── auth.py                # 用户认证逻辑
│   ├── user_levels.py         # 用户等级配置
│   └── requirements.txt       # Python依赖包
├── frontend/                   # React前端应用
│   ├── public/                # 静态资源
│   ├── src/
│   │   ├── components/        # 可复用组件
│   │   │   ├── AuthContext.js # 认证上下文
│   │   │   └── Layout.js      # 布局组件
│   │   ├── pages/            # 页面组件
│   │   │   ├── HomePage.js   # 主页面
│   │   │   ├── LoginPage.js  # 登录页面
│   │   │   ├── ProductHomePage.js # 产品展示页
│   │   │   ├── UserManagement.js  # 用户管理
│   │   │   ├── SystemManagement.js # 系统管理
│   │   │   ├── CodeLibraryPage.js  # 代码库
│   │   │   ├── APIKeyPage.js       # API密钥管理
│   │   │   └── AIConfigPage.js     # AI配置管理
│   │   ├── services/         # API服务层
│   │   │   └── api.js        # HTTP请求封装
│   │   └── App.js            # 应用主组件
│   └── package.json          # Node.js依赖
├── README.md                  # 项目文档
└── .gitignore                 # Git忽略文件
```

## 🚀 快速开始

### 方法1: 使用阿里云镜像（推荐）

```bash
# 拉取镜像
docker pull crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:backend
docker pull crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:frontend

# 创建网络
docker network create coderunner-network

# 启动后端
docker run -d \
  --name coderunner_backend \
  --network coderunner-network \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DATABASE_URL=sqlite:///./data/coderunner.db \
  -e SECRET_KEY=your-secret-key-change-this \
  crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:backend

# 启动前端
docker run -d \
  --name coderunner_frontend \
  --network coderunner-network \
  -p 3000:80 \
  crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:frontend
```

### 方法2: 本地开发

#### 后端开发
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
python main.py
```

#### 前端开发
```bash
cd frontend
npm install
npm start
```

### 方法3: Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  coderunner_backend:
    image: crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:backend
    container_name: coderunner-backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/coderunner.db
      - SECRET_KEY=your-secret-key-change-this
    networks:
      - coderunner-network
    restart: unless-stopped

  coderunner_frontend:
    image: crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:frontend
    container_name: coderunner-frontend
    ports:
      - "3000:80"
    depends_on:
      - coderunner_backend
    networks:
      - coderunner-network
    restart: unless-stopped

networks:
  coderunner-network:
    driver: bridge
```

```bash
docker-compose up -d
```

## 🌐 访问地址

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🔑 默认账号

- **用户名**: admin
- **密码**: admin123

⚠️ **重要**: 首次登录后请立即修改默认密码

## 📋 系统要求

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (可选)
- SQLite (默认数据库)

## 📊 数据库模式

- **User**: 用户信息表
- **CodeExecution**: 代码执行记录表
- **CodeLibrary**: 代码库表
- **APIKey**: API密钥表
- **AIConfig**: AI配置表
- **SystemLog**: 系统日志表

## 🛠️ 管理命令

### Docker管理脚本
```bash
./docker-manager.sh start    # 启动服务
./docker-manager.sh status   # 检查状态
./docker-manager.sh logs backend -f  # 查看日志
./docker-manager.sh stop     # 停止服务
```

### 前端开发
```bash
npm install    # 安装依赖
npm start      # 启动开发服务器
npm test       # 运行测试
npm run build  # 构建生产版本
```

## 📡 API端点

### 认证
- `POST /register` - 用户注册
- `POST /login` - 用户登录（返回JWT令牌）
- `GET /users/me` - 获取当前用户信息
- `GET /users` - 列出所有用户（仅管理员）
- `POST /change-password` - 修改密码
- `POST /admin/users/{user_id}/change-password` - 管理员修改密码

### 代码执行
- `POST /execute` - 执行Python代码（带用户限制）
- `GET /executions` - 获取用户执行历史
- `GET /admin/executions` - 获取所有执行记录（仅管理员）
- `GET /user-stats` - 获取用户统计和限制

### AI功能
- `POST /ai-configs` - 创建AI配置
- `GET /ai-configs` - 获取AI配置
- `PUT /ai-configs/{id}` - 更新AI配置
- `DELETE /ai-configs/{id}` - 删除AI配置
- `POST /ai/generate-code` - 使用AI生成代码

### 代码库
- `POST /code-library` - 保存代码到库
- `GET /code-library` - 获取代码库（分页）
- `GET /code-library/{id}` - 获取特定代码
- `PUT /code-library/{id}` - 更新代码
- `DELETE /code-library/{id}` - 删除代码

### API密钥
- `POST /api-keys` - 创建API密钥
- `GET /api-keys` - 获取API密钥（不包含值）
- `PUT /api-keys/{id}/toggle` - 启用/禁用API密钥
- `DELETE /api-keys/{id}` - 删除API密钥

### 外部API
- `POST /api/v1/execute` - 通过API密钥执行代码
- `GET /api/v1/codes` - 通过API密钥获取代码库
- `GET /api/v1/codes/{id}` - 通过API密钥获取特定代码

### 系统管理（仅管理员）
- `GET /admin/logs` - 获取系统日志（可过滤）
- `GET /admin/logs/stats` - 获取日志统计
- `GET /admin/logs/actions` - 获取可用日志操作
- `GET /admin/logs/resource-types` - 获取可用资源类型

## 🔒 安全说明

- 默认管理员用户: username="admin", password="admin123"（首次登录后修改）
- 代码执行使用临时文件，执行后自动清理
- JWT令牌30分钟后过期（可通过`ACCESS_TOKEN_EXPIRE_MINUTES`配置）
- API密钥具有使用跟踪和可选过期日期
- 所有系统操作都记录IP地址和用户代理
- 数据库文件（coderunner.db）已从git中排除

## 🌍 环境变量

- `SECRET_KEY`: JWT签名密钥（生产环境中请更改）
- `DATABASE_URL`: SQLite数据库连接字符串（默认: sqlite:///./coderunner.db）
- `NODE_ENV`: React环境（development/production）

## 🐳 Docker配置

项目使用多阶段Docker构建：
- **后端**: Python 3.11 slim镜像，非root用户
- **前端**: Node.js 18 Alpine构建器 + Nginx Alpine生产环境
- **网络**: 用于容器通信的自定义Docker网络
- **健康检查**: 两个容器都配置了健康检查
- **数据持久化**: 后端数据挂载到`./data/`目录

## 📝 数据库初始化

首次运行时数据库自动初始化：
1. 数据库模式创建
2. 默认管理员用户（admin/admin123）
3. 性能索引创建

所有数据库操作都使用SQLAlchemy ORM，具有适当的会话管理和错误处理。

## 🤝 贡献

欢迎提交问题报告和拉取请求。在提交之前，请确保：

1. 代码符合项目风格
2. 添加适当的测试
3. 更新相关文档
4. 通过所有测试

## 📄 许可证

本项目采用MIT许可证。详情请见 [LICENSE](LICENSE) 文件。

## 📞 支持

如果您遇到任何问题或有任何建议，请：

1. 查看 [常见问题](docs/FAQ.md)
2. 搜索现有的 [问题](https://github.com/your-username/CodeRunner/issues)
3. 创建新的问题并提供详细信息

---

**⭐ 如果这个项目对您有帮助，请给它一个星标！**