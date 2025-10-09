# CodeRunner - 远端Python代码执行平台

一个基于 FastAPI + React + Ant Design 的远程Python代码执行平台，支持用户注册、登录和管理功能。

## 功能特性

- 🔐 用户认证系统（注册/登录/JWT认证）
- 🐍 远程Python代码执行
- 📊 执行历史记录
- 👥 用户管理界面
- 🎨 响应式Ant Design UI
- 💾 SQLite数据库存储
- ⚡ 实时代码执行结果

## 技术栈

### 后端
- **FastAPI** - 现代、快速的Web框架
- **SQLAlchemy** - Python SQL工具包和ORM
- **SQLite** - 轻量级数据库
- **JWT** - 用户认证
- **Pydantic** - 数据验证和序列化

### 前端
- **React 18** - 用户界面库
- **Ant Design** - 企业级UI设计语言
- **React Router** - 路由管理
- **Axios** - HTTP客户端

## 项目结构

```
CodeRunner/
├── backend/                    # FastAPI后端
│   ├── main.py                # 主应用文件
│   ├── database.py            # 数据库配置和模型
│   ├── models.py              # Pydantic数据模型
│   └── auth.py                # 认证相关功能
├── frontend/                  # React前端
│   ├── public/
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/            # 页面组件
│   │   ├── services/         # API服务
│   │   └── App.js            # 主应用组件
│   └── package.json
├── requirements.txt           # Python依赖
└── README.md                 # 项目说明
```

## 安装和运行

### 1. 克隆项目

```bash
git clone <repository-url>
cd CodeRunner
```

### 2. 后端设置

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\\Scripts\\activate   # Windows

# 安装Python依赖
pip install -r requirements.txt

# 启动后端服务器
cd backend
python main.py
```

后端将在 `http://localhost:8000` 运行

### 3. 前端设置

```bash
# 在新终端中
cd frontend

# 安装Node.js依赖
npm install

# 启动前端开发服务器
npm start
```

前端将在 `http://localhost:3000` 运行

## 使用说明

### 注册和登录
1. 访问 `http://localhost:3000`
2. 点击"Register"创建新账户
3. 使用用户名和密码登录

### 执行Python代码
1. 在主页的代码编辑器中输入Python代码
2. 点击"Execute Code"按钮执行
3. 查看执行结果和输出
4. 查看执行历史记录

### 用户管理
1. 点击导航栏中的"Users"
2. 查看所有注册用户列表
3. 查看用户状态和注册时间

## API端点

### 认证
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /users/me` - 获取当前用户信息
- `GET /users` - 获取所有用户列表

### 代码执行
- `POST /execute` - 执行Python代码
- `GET /executions` - 获取执行历史

## 安全特性

- JWT令牌认证
- 密码哈希存储
- 代码执行超时限制（30秒）
- 临时文件安全管理

## 开发说明

### 环境变量
可以通过环境变量配置：
- `SECRET_KEY` - JWT密钥（生产环境请更改）
- `DATABASE_URL` - 数据库连接字符串

### 扩展功能
- 代码执行时间限制
- 支持更多编程语言
- 代码分享功能
- 文件上传支持

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

MIT License