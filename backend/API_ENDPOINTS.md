# CodeRunner 后端 API 接口文档

> 本文档基于对 `main.py` 的完整分析，包含了系统中所有 81 个 API 接口的详细清单，用于指导后端重构工作。

## 📊 系统概览

- **总接口数量**: 81 个
- **主要文件**: `main.py` (4300+ 行代码)
- **数据库**: SQLite，包含 13 个核心表
- **认证方式**: JWT Token、API Key、管理员权限
- **用户等级**: 四级权限体系 (Free/Basic/Premium/Enterprise)

---

## 🔐 用户认证与管理 (10个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/register` | `UserResponse` | 用户注册 | 无 |
| POST | `/login` | `Token` | 用户登录 | 无 |
| GET | `/users/me` | `UserResponse` | 获取当前用户信息 | JWT |
| POST | `/change-password` | - | 修改密码 | JWT |
| GET | `/users` | `list[UserResponse]` | 获取所有用户列表 | 管理员 |
| POST | `/admin/users/{user_id}/change-password` | - | 管理员修改用户密码 | 管理员 |
| POST | `/admin/users` | `UserResponse` | 创建用户(管理员) | 管理员 |
| PUT | `/admin/users/{user_id}` | `UserResponse` | 更新用户信息 | 管理员 |
| DELETE | `/admin/users/{user_id}` | - | 删除用户 | 管理员 |
| GET | `/user-levels` | `dict` | 获取用户等级配置 | 无 |

**关键功能**:
- JWT Token 认证 (30分钟过期)
- Argon2 密码哈希
- 四级用户权限系统
- 管理员权限控制

---

## 💻 代码执行 (3个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/execute` | `CodeExecutionResponse` | 执行Python代码 | JWT |
| GET | `/executions` | `list[CodeExecutionResponse]` | 获取用户执行历史 | JWT |
| GET | `/admin/executions` | `list[CodeExecutionResponse]` | 获取所有执行记录 | 管理员 |

**关键功能**:
- 安全的临时文件执行
- 用户等级限制 (执行时间、内存、每日配额)
- Conda环境支持
- 性能监控 (执行时间、内存使用)

---

## 📚 代码库管理 (6个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/code-library` | `CodeLibraryResponse` | 保存代码到库 | JWT |
| GET | `/code-library` | `list[CodeLibraryResponse]` | 获取用户代码库 | JWT |
| GET | `/code-library/{code_id}` | `CodeLibraryResponse` | 获取特定代码 | JWT |
| PUT | `/code-library/{code_id}` | `CodeLibraryResponse` | 更新代码 | JWT |
| DELETE | `/code-library/{code_id}` | - | 删除代码 | JWT |
| POST | `/code-library/save` | `CodeLibrarySaveResponse` | 保存分享的代码 | JWT |

**关键功能**:
- 个人代码片段存储
- 公开/私有权限控制
- 环境关联存储
- 标签分类管理

---

## 🔑 API密钥管理 (4个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/api-keys` | `APIKeyResponse` | 创建API密钥 | JWT |
| GET | `/api-keys` | `list[APIKeyInfo]` | 获取API密钥列表(无值) | JWT |
| PUT | `/api-keys/{key_id}/toggle` | - | 启用/禁用API密钥 | JWT |
| DELETE | `/api-keys/{key_id}` | - | 删除API密钥 | JWT |

**关键功能**:
- 外部程序化访问
- 使用次数统计
- sk- 前缀格式
- 用户等级限制 (不同等级可创建数量不同)

---

## 🌐 外部API访问 (3个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/api/v1/execute` | `CodeExecuteByAPIResponse` | 通过API密钥执行代码 | API Key |
| GET | `/api/v1/codes` | `list[CodeLibraryResponse]` | 通过API密钥获取代码库 | API Key |
| GET | `/api/v1/codes/{code_id}` | `CodeLibraryResponse` | 通过API密钥获取特定代码 | API Key |

**关键功能**:
- 完全通过API Key认证
- 独立的配额计算
- 支持外部工具集成

---

## 🐍 Conda环境管理 (9个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/conda-environments` | `list[str]` | 获取可用conda环境 | JWT |
| GET | `/environments/available` | - | 获取可用环境列表 | JWT |
| POST | `/user-environments` | `UserEnvironmentResponse` | 创建用户环境 | JWT |
| GET | `/user-environments` | `list[UserEnvironmentResponse]` | 获取用户环境 | JWT |
| GET | `/user-environments/{env_id}` | `UserEnvironmentResponse` | 获取特定环境 | JWT |
| PUT | `/user-environments/{env_id}` | `UserEnvironmentResponse` | 更新环境 | JWT |
| DELETE | `/user-environments/{env_id}` | - | 删除环境 | JWT |
| GET | `/admin/user-environments` | `list[UserEnvironmentResponse]` | 获取所有环境 | 管理员 |
| DELETE | `/admin/user-environments/{env_id}` | - | 删除环境 | 管理员 |

**关键功能**:
- 虚拟环境隔离
- 非管理员用户限制 (1个环境)
- 公开环境共享
- Python版本管理

---

## 📦 环境包管理 (5个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/environments/{env_name}/info` | `EnvironmentInfo` | 获取环境信息 | JWT |
| GET | `/environments/{env_name}/packages` | `list[PackageInfo]` | 获取已安装包列表 | JWT |
| POST | `/environments/{env_name}/packages/install` | - | 安装包 | JWT |
| DELETE | `/environments/{env_name}/packages/{package_name}` | - | 卸载包 | JWT |
| PUT | `/environments/{env_name}/packages/{package_name}/upgrade` | - | 升级包 | JWT |

**关键功能**:
- 包安装/卸载/升级
- 依赖隔离
- 版本控制
- 用量统计

---

## 🤖 AI配置与代码生成 (5个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/ai-configs` | `AIConfigResponse` | 创建AI配置 | JWT |
| GET | `/ai-configs` | `list[AIConfigResponse]` | 获取AI配置列表 | JWT |
| PUT | `/ai-configs/{config_id}` | `AIConfigResponse` | 更新AI配置 | JWT |
| DELETE | `/ai-configs/{config_id}` | - | 删除AI配置 | JWT |
| POST | `/ai/generate-code` | `AICodeGenerateResponse` | 使用AI生成代码 | JWT |

**支持的AI提供商**:
- Qwen (阿里云)
- OpenAI (GPT系列)
- Claude (Anthropic)
- 自定义OpenAI兼容API

**关键功能**:
- 多AI提供商支持
- 自定义参数配置 (temperature, max_tokens)
- 活跃配置切换 (每个用户只能有一个活跃配置)
- 使用量跟踪

---

## 👤 用户资料管理 (8个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/profile` | `UserProfileResponse` | 获取用户资料 | JWT |
| PUT | `/profile` | `UserProfileResponse` | 更新用户资料 | JWT |
| POST | `/profile/upload-avatar` | - | 上传头像 | JWT |
| GET | `/api/avatars/{filename}` | `FileResponse` | 提供头像文件 | 无 |
| DELETE | `/profile/avatar` | - | 删除头像 | JWT |
| GET | `/user-stats` | `dict` | 获取用户统计信息 | JWT |
| GET | `/profile/stats` | `dict` | 获取资料统计 | JWT |
| GET | `/profile/enhanced-stats` | `UserStatsResponse` | 获取增强统计信息 | JWT |

**关键功能**:
- 头像上传管理
- 个人简介编辑
- 统计信息展示
- 公开/私有信息控制

---

## 🏘️ 社区功能 (11个接口)

### 帖子管理
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/community/posts` | `PostResponse` | 创建社区帖子 | JWT |
| GET | `/community/posts` | `dict` | 获取社区帖子 | JWT |
| GET | `/community/posts/{post_id}` | `PostResponse` | 获取特定帖子 | JWT |
| DELETE | `/community/posts/{post_id}` | - | 删除帖子 | JWT |

### 帖子互动
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/community/posts/{post_id}/like` | - | 点赞/取消点赞帖子 | JWT |
| POST | `/community/posts/{post_id}/favorite` | - | 收藏/取消收藏帖子 | JWT |

### 评论系统
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/community/posts/{post_id}/comments` | `CommentResponse` | 创建评论 | JWT |
| GET | `/community/posts/{post_id}/comments` | `dict` | 获取帖子评论 | JWT |
| POST | `/community/comments/{comment_id}/like` | - | 点赞/取消点赞评论 | JWT |

### 用户关注
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/community/follow/{user_id}` | `FollowResponse` | 关注/取消关注用户 | JWT |

**关键功能**:
- Markdown内容支持
- 代码片段嵌入
- 嵌套评论系统
- 点赞/收藏功能
- 关注系统
- 公开/私密帖子控制

---

## 👥 用户发现与互动 (7个接口)

| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/users/{user_id}/followers` | `dict` | 获取用户粉丝 | JWT |
| GET | `/users/{user_id}/following` | `dict` | 获取关注的人 | JWT |
| GET | `/users/{user_id}/follow-status` | `dict` | 获取关注状态 | JWT |
| GET | `/users/by-username/{username}` | `dict` | 通过用户名查找用户 | JWT |
| GET | `/users/{user_id}/posts` | `dict` | 获取用户帖子 | JWT |
| GET | `/users/{user_id}/code-library` | `dict` | 获取用户代码库 | JWT |
| GET | `/users/{user_id}/stats` | `dict` | 获取用户公开统计 | JWT |

**关键功能**:
- 用户搜索发现
- 社交关系查看
- 内容浏览
- 统计信息展示

---

## 📋 系统管理 (10个接口)

### 系统监控
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/` | `dict` | 健康检查 | 无 |
| GET | `/admin/logs` | `list[dict]` | 获取系统日志 | 管理员 |
| GET | `/admin/logs/stats` | `dict` | 获取日志统计 | 管理员 |
| GET | `/admin/logs/actions` | `list[str]` | 获取可用日志操作 | 管理员 |
| GET | `/admin/logs/resource-types` | `list[str]` | 获取可用资源类型 | 管理员 |

### 数据库管理
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| POST | `/admin/database/export` | `StreamingResponse` | 导出数据库 | 管理员 |
| POST | `/admin/database/import` | `dict` | 导入数据库 | 管理员 |
| GET | `/admin/database/info` | `dict` | 获取数据库信息 | 管理员 |

### 用户活动日志
| 方法 | 路径 | 响应模型 | 功能描述 | 认证要求 |
|------|------|----------|----------|----------|
| GET | `/profile/logs` | `dict` | 获取用户活动日志 | JWT |
| GET | `/profile/logs/actions` | `list[str]` | 获取用户日志操作 | JWT |
| GET | `/profile/logs/resource-types` | `list[str]` | 获取用户日志资源类型 | JWT |

**关键功能**:
- 全面的审计日志
- IP地址和User-Agent跟踪
- 数据库备份恢复
- 系统状态监控
- 用户活动分析

---

## 🏗️ 数据库模型概览

### 核心表结构
1. **User** - 用户信息和权限
2. **CodeExecution** - 代码执行记录
3. **CodeLibrary** - 代码片段存储
4. **APIKey** - API密钥管理
5. **AIConfig** - AI配置管理
6. **UserEnvironment** - Conda环境管理
7. **SystemLog** - 系统审计日志
8. **Post** - 社区帖子
9. **Comment** - 评论系统
10. **PostLike** - 帖子点赞
11. **PostFavorite** - 帖子收藏
12. **CommentLike** - 评论点赞
13. **Follow** - 用户关注关系

---

## 🔒 安全特性

### 认证机制
- **JWT Token**: 30分钟过期，可配置
- **API Key**: sk-前缀格式，支持外部访问
- **管理员权限**: 严格的权限分离

### 安全措施
- **密码哈希**: Argon2算法
- **输入验证**: Pydantic模型验证
- **CORS配置**: 支持Vercel部署
- **审计日志**: 完整的用户操作记录
- **资源限制**: 基于用户等级的配额控制

---

## 📋 重构建议

### 🎯 模块化拆分

**建议的新目录结构**:
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用初始化
│   ├── config.py              # 配置管理
│   ├── database.py            # 数据库配置
│   ├── models/                # Pydantic模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── code.py
│   │   ├── community.py
│   │   └── admin.py
│   ├── schemas/               # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── code.py
│   │   └── community.py
│   ├── routes/                # API路由
│   │   ├── __init__.py
│   │   ├── auth.py           # 认证相关 (10个接口)
│   │   ├── code_execution.py # 代码执行 (3个接口)
│   │   ├── code_library.py   # 代码库 (6个接口)
│   │   ├── api_keys.py       # API密钥 (4个接口)
│   │   ├── external_api.py   # 外部API (3个接口)
│   │   ├── environments.py   # 环境管理 (14个接口)
│   │   ├── ai_config.py      # AI配置 (5个接口)
│   │   ├── profile.py        # 用户资料 (8个接口)
│   │   ├── community.py      # 社区功能 (11个接口)
│   │   ├── users.py          # 用户发现 (7个接口)
│   │   └── admin.py          # 系统管理 (10个接口)
│   ├── services/             # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── code_service.py
│   │   ├── ai_service.py
│   │   └── community_service.py
│   ├── middleware/           # 中间件
│   │   ├── __init__.py
│   │   ├── cors.py
│   │   ├── auth.py
│   │   └── logging.py
│   ├── dependencies.py       # FastAPI依赖
│   └── exceptions.py         # 自定义异常
├── requirements.txt
└── README.md
```

### 🔧 拆分优先级

1. **高优先级** - 核心功能模块
   - 认证系统 (`routes/auth.py`)
   - 代码执行 (`routes/code_execution.py`)
   - 用户管理 (`routes/users.py`)

2. **中优先级** - 业务功能模块
   - 代码库管理 (`routes/code_library.py`)
   - 环境管理 (`routes/environments.py`)
   - 社区功能 (`routes/community.py`)

3. **低优先级** - 辅助功能模块
   - API密钥管理 (`routes/api_keys.py`)
   - 外部API (`routes/external_api.py`)
   - 系统管理 (`routes/admin.py`)

### ⚠️ 重构注意事项

1. **保留现有功能**: 确保81个接口全部迁移
2. **API兼容性**: 保持现有API路径和响应格式
3. **数据库兼容**: 不修改现有数据库结构
4. **测试覆盖**: 每个模块都要有对应的测试
5. **渐进迁移**: 建议分模块逐步重构

### 🐛 发现的问题

1. **缺失的接口**: 评论更新/删除功能在数据库模型中定义了，但没有对应的API端点
   - 建议添加: `PUT /comments/{comment_id}` 更新评论
   - 建议添加: `DELETE /comments/{comment_id}` 删除评论

2. **潜在的改进点**:
   - 可以添加API版本控制 (`/api/v1/`, `/api/v2/`)
   - 可以添加更多的错误处理和自定义异常
   - 可以优化数据库查询性能
   - 可以添加缓存机制

---

## 📝 重构检查清单

### ✅ 认证模块 (10个接口)
- [ ] 用户注册
- [ ] 用户登录
- [ ] 获取当前用户信息
- [ ] 修改密码
- [ ] 用户列表 (管理员)
- [ ] 管理员修改密码
- [ ] 创建用户 (管理员)
- [ ] 更新用户 (管理员)
- [ ] 删除用户 (管理员)
- [ ] 用户等级配置

### ✅ 代码执行模块 (3个接口)
- [ ] 代码执行
- [ ] 执行历史
- [ ] 管理员执行记录

### ✅ 代码库模块 (6个接口)
- [ ] 保存代码
- [ ] 获取代码库
- [ ] 获取特定代码
- [ ] 更新代码
- [ ] 删除代码
- [ ] 保存分享代码

### ✅ API密钥模块 (4个接口)
- [ ] 创建密钥
- [ ] 获取密钥列表
- [ ] 启用/禁用密钥
- [ ] 删除密钥

### ✅ 外部API模块 (3个接口)
- [ ] API执行代码
- [ ] API获取代码库
- [ ] API获取特定代码

### ✅ 环境管理模块 (14个接口)
- [ ] 获取conda环境
- [ ] 获取可用环境
- [ ] 创建用户环境
- [ ] 获取用户环境列表
- [ ] 获取特定环境
- [ ] 更新环境
- [ ] 删除环境
- [ ] 管理员获取所有环境
- [ ] 管理员删除环境
- [ ] 获取环境信息
- [ ] 获取包列表
- [ ] 安装包
- [ ] 卸载包
- [ ] 升级包

### ✅ AI配置模块 (5个接口)
- [ ] 创建AI配置
- [ ] 获取AI配置列表
- [ ] 更新AI配置
- [ ] 删除AI配置
- [ ] AI生成代码

### ✅ 用户资料模块 (8个接口)
- [ ] 获取用户资料
- [ ] 更新用户资料
- [ ] 上传头像
- [ ] 提供头像文件
- [ ] 删除头像
- [ ] 用户统计信息
- [ ] 资料统计
- [ ] 增强统计信息

### ✅ 社区功能模块 (11个接口)
- [ ] 创建帖子
- [ ] 获取帖子列表
- [ ] 获取特定帖子
- [ ] 删除帖子
- [ ] 点赞帖子
- [ ] 收藏帖子
- [ ] 创建评论
- [ ] 获取评论
- [ ] 点赞评论
- [ ] 关注用户

### ✅ 用户发现模块 (7个接口)
- [ ] 获取用户粉丝
- [ ] 获取关注列表
- [ ] 获取关注状态
- [ ] 通过用户名查找
- [ ] 获取用户帖子
- [ ] 获取用户代码库
- [ ] 获取用户统计

### ✅ 系统管理模块 (10个接口)
- [ ] 健康检查
- [ ] 系统日志
- [ ] 日志统计
- [ ] 日志操作类型
- [ ] 日志资源类型
- [ ] 导出数据库
- [ ] 导入数据库
- [ ] 数据库信息
- [ ] 用户活动日志
- [ ] 用户日志操作
- [ ] 用户日志资源类型

---

## 🎯 总结

CodeRunner 是一个功能丰富的代码执行平台，包含了完整的用户管理、代码执行、AI集成、社区功能和系统管理。当前的单体架构需要模块化重构以提高可维护性。

**重构的关键目标**:
1. 保持所有81个API接口的完整性
2. 提高代码的可维护性和可测试性
3. 改善代码组织和模块分离
4. 保持API的向后兼容性
5. 补充缺失的功能接口

通过模块化重构，系统将更容易理解、维护和扩展，同时保持现有的所有功能完整性。