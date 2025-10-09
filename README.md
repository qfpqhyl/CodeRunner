# CodeRunner - 智能Python代码执行平台

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![Ant Design](https://img.shields.io/badge/Ant%20Design-5.x-red.svg)](https://ant.design)

一个现代化的远程Python代码执行平台，集成了AI智能代码生成功能，支持用户认证、代码管理、API调用等企业级特性。

## ✨ 核心特性

### 🔐 用户管理系统
- **多级用户体系**：免费版、基础版、高级版、企业版
- **安全认证**：JWT令牌认证，密码哈希存储
- **权限管理**：管理员/普通用户角色分离
- **个人资料**：用户信息管理和密码修改

### 🐍 智能代码执行
- **远程执行**：安全沙箱环境执行Python代码
- **实时反馈**：即时显示执行结果和性能指标
- **历史记录**：完整的代码执行历史追踪
- **资源限制**：基于用户等级的执行时长和内存限制
- **执行配额**：每日执行次数管理

### 🤖 AI智能助手
- **多模型支持**：支持通义千问、OpenAI、Claude等主流AI模型
- **智能生成**：根据自然语言描述生成Python代码
- **参数调节**：可控制创造性和输出长度
- **实时预览**：生成结果即时预览和应用
- **个人配置**：用户自定义AI模型配置

### 💾 代码库管理
- **代码保存**：个人代码片段收藏和管理
- **分类标签**：支持自定义标签分类
- **公开分享**：代码公开/私有权限控制
- **快速调用**：一键加载历史代码

### 🔑 API服务
- **密钥管理**：个人API密钥生成和管理
- **远程调用**：支持通过API执行代码
- **使用统计**：API调用次数和状态追踪
- **安全控制**：API密钥权限和过期管理

### 📊 系统管理
- **用户监控**：全面的用户行为监控
- **系统日志**：详细的操作日志记录
- **统计分析**：用户使用情况和系统性能分析
- **安全管理**：登录日志和异常行为追踪

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
- **Monaco Editor** - 专业代码编辑器（可选）

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

### 环境要求
- Python 3.8+
- Node.js 14+
- npm 或 yarn

### 1. 克隆项目
```bash
git clone <repository-url>
cd CodeRunner
```

### 2. 后端启动
```bash
# 进入后端目录
cd backend

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动后端服务
python main.py
```
后端服务将在 `http://localhost:8000` 启动

### 3. 前端启动
```bash
# 新开终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```
前端应用将在 `http://localhost:3000` 启动

### 4. 访问应用
打开浏览器访问 `http://localhost:3000`，使用以下默认管理员账户登录：
- **用户名**：`admin`
- **密码**：`admin123`

> ⚠️ **安全提醒**：首次登录后请立即修改默认管理员密码！

## 📖 使用指南

### 新手入门
1. **注册账户**：访问注册页面创建新用户
2. **登录系统**：使用用户名密码登录
3. **代码执行**：在主页面编写Python代码并执行
4. **探索功能**：浏览各个功能模块

### AI代码生成
1. **配置AI模型**：在"AI配置"页面添加您的AI模型API密钥
2. **编写需求描述**：在代码编辑器中展开AI助手面板
3. **生成代码**：输入需求描述，点击"生成代码"
4. **应用代码**：预览生成的代码并应用到编辑器

### API调用
1. **生成API密钥**：在"API密钥"页面创建密钥
2. **调用接口**：使用API密钥调用远程代码执行
3. **监控使用**：查看API调用统计和历史记录

## 🔧 配置说明

### 环境变量
```bash
# JWT密钥（生产环境必须修改）
SECRET_KEY=your-secret-key-here

# 数据库连接（可选，默认使用SQLite）
DATABASE_URL=sqlite:///./coderunner.db

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

### AI模型配置
支持的AI模型配置：
- **通义千问**：`https://dashscope.aliyuncs.com/compatible-mode/v1`
- **OpenAI**：`https://api.openai.com/v1`
- **其他兼容模型**：任意OpenAI API格式的服务

### 用户等级配置
| 等级 | 每日执行次数 | 执行时长限制 | 内存限制 | 说明 |
|------|-------------|-------------|----------|------|
| 免费版 | 10次 | 30秒 | 128MB | 基础功能 |
| 基础版 | 50次 | 60秒 | 256MB | 进阶用户 |
| 高级版 | 200次 | 120秒 | 512MB | 专业用户 |
| 企业版 | 无限制 | 300秒 | 1024MB | 企业用户 |

## 🔌 API文档

### 认证接口
```http
POST /register          # 用户注册
POST /login             # 用户登录
GET  /users/me          # 获取当前用户信息
PUT  /change-password   # 修改密码
```

### 代码执行
```http
POST /execute           # 执行Python代码
GET  /executions        # 获取执行历史
GET  /user-stats        # 获取用户统计
```

### AI功能
```http
POST /ai-configs        # 创建AI配置
GET  /ai-configs        # 获取AI配置列表
PUT  /ai-configs/{id}   # 更新AI配置
DELETE /ai-configs/{id} # 删除AI配置
POST /ai/generate-code  # AI生成代码
```

### 代码库
```http
POST /code-library      # 保存代码到库
GET  /code-library      # 获取代码库列表
PUT  /code-library/{id} # 更新代码库
DELETE /code-library/{id} # 删除代码库
```

### API密钥
```http
POST /api-keys          # 创建API密钥
GET  /api-keys          # 获取API密钥列表
PUT  /api-keys/{id}/toggle # 启用/禁用密钥
DELETE /api-keys/{id}   # 删除API密钥
```

## 🛡️ 安全特性

- **认证安全**：JWT令牌认证，自动过期机制
- **密码安全**：bcrypt哈希加密，强度验证
- **代码安全**：沙箱执行环境，资源限制
- **API安全**：密钥管理，调用频率限制
- **数据安全**：敏感信息加密存储
- **审计安全**：完整的操作日志记录

## 🎯 开发路线图

### 已完成功能 ✅
- [x] 用户认证和权限管理
- [x] Python代码远程执行
- [x] 多级用户等级系统
- [x] 代码库管理功能
- [x] API密钥管理
- [x] AI智能代码生成
- [x] 系统日志和监控
- [x] 响应式前端界面

### 计划功能 🚧
- [ ] 支持更多编程语言（JavaScript、Java等）
- [ ] 代码分享和协作功能
- [ ] 文件上传和管理
- [ ] 代码性能分析
- [ ] 容器化部署支持
- [ ] 微服务架构重构
- [ ] 移动端应用

## 🤝 贡献指南

欢迎参与项目贡献！请遵循以下步骤：

1. **Fork** 项目到您的GitHub账户
2. **Clone** 您的Fork到本地
3. **创建分支**：`git checkout -b feature/amazing-feature`
4. **提交更改**：`git commit -m 'Add amazing feature'`
5. **推送分支**：`git push origin feature/amazing-feature`
6. **创建Pull Request**

### 开发规范
- 遵循PEP 8 Python代码规范
- 使用ESLint和Prettier格式化前端代码
- 编写单元测试覆盖新功能
- 更新相关文档

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持与反馈

- **问题反馈**：[GitHub Issues](https://github.com/your-repo/issues)
- **功能建议**：[GitHub Discussions](https://github.com/your-repo/discussions)
- **技术支持**：support@coderunner.com

---

⭐ 如果这个项目对您有帮助，请给我们一个Star！