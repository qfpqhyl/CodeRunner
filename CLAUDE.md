# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeRunner is a remote Python code execution platform built with FastAPI (backend) and React + Ant Design (frontend). It features user authentication, multi-tier user levels, AI-powered code generation, secure Python code execution, code library management, API key management, and comprehensive system logging.

## Architecture

### Backend (FastAPI) - Monolithic Architecture
The core FastAPI application follows a monolithic architecture pattern with a single large `main.py` file (2700+ lines) containing all API endpoints, middleware, and business logic. This design centralizes functionality for easier maintenance in a medium-sized application.

**Core Files:**
- **main.py**: Main FastAPI application with all API endpoints, authentication, and business logic (2700+ lines)
- **database.py**: SQLAlchemy models (User, CodeExecution, CodeLibrary, APIKey, AIConfig, UserEnvironment, SystemLog) and database configuration
- **models.py**: Pydantic data models for request/response validation with comprehensive type hints
- **auth.py**: JWT authentication (30-minute expiration), Argon2 password hashing, and user authentication functions
- **user_levels.py**: User tier configuration (Free, Basic, Premium, Enterprise) with execution limits and quotas

**Key Backend Features:**
- Secure code execution in temporary files with conda environment support
- Comprehensive system logging with IP tracking and audit trails
- AI integration with multiple providers (Qwen, OpenAI, Claude, custom OpenAI-compatible APIs)
- User environment management with conda virtual environments
- Database import/export functionality for administrators
- Package management (install/uninstall/upgrade) in isolated environments

**Backend Architecture Patterns:**
- **Dependency Injection**: FastAPI's dependency system for database sessions and authentication
- **Repository Pattern**: SQLAlchemy ORM with proper session management
- **Middleware Layer**: CORS, authentication, client IP tracking, and request logging
- **Service Layer**: Business logic embedded directly in endpoint functions
- **Security Layer**: JWT tokens, Argon2 hashing, role-based access control

### Frontend (React + Ant Design)
Modern React application with Chinese localization and comprehensive UI components following a component-based architecture:

**Core Files:**
- **App.js**: Main application with React Router, authentication context, and protected routes
- **components/AuthContext.js**: Authentication state management using React Context API
- **components/Layout.js**: Navigation and layout components with Ant Design components
- **components/Comment.js**: Reusable comment component for posts
- **components/BackendConfig.js**: Backend configuration management UI
- **components/DeploymentTutorial.js**: Deployment guide and tutorial component
- **pages/**: Page components (HomePage, ProductHomePage, LoginPage, UserManagement, SystemManagement, CodeLibraryPage, APIKeyPage, AIConfigPage, EnvironmentPage, CommunityPage, CreatePostPage, PostDetailPage, ProfilePage, FollowListPage)
- **services/api.js**: Axios HTTP client with interceptors for authentication and error handling

**Key Frontend Features:**
- Chinese language interface (zhCN locale) with full localization
- Protected routes with authentication checks using AuthContext
- Real-time code execution with environment selection
- Comprehensive admin panel for system management
- AI configuration and code generation interface
- Deployment tutorial and configuration management
- Community features with posts, comments, likes, and follows
- User profiles with avatars and bios
- Social interactions (follow users, like/favorite posts, comment on posts)
- Code sharing between posts and code library

**Frontend Architecture Patterns:**
- **SPA (Single Page Application)**: React Router for client-side routing
- **Context API**: Global authentication state management
- **Component Composition**: Modular React components with Ant Design
- **Service Layer**: Axios interceptors for authentication and error handling
- **Protected Routes**: Route guards based on authentication status

### Project Structure & Key Files

```
CodeRunner/
├── backend/                    # FastAPI backend service
│   ├── main.py                # Core API application (2700+ lines)
│   ├── database.py            # SQLAlchemy models + DB setup
│   ├── models.py              # Pydantic request/response models
│   ├── auth.py                # JWT authentication functions
│   ├── user_levels.py         # User tier system configuration
│   └── requirements.txt       # Python dependencies
├── frontend/                   # React frontend application
│   ├── public/               # Static assets and favicon
│   ├── src/
│   │   ├── components/       # Reusable React components
│   │   ├── pages/           # Page-level components
│   │   ├── services/        # API layer (Axios configuration)
│   │   └── App.js           # Main app with routing
│   ├── build/               # Production build output
│   └── package.json         # Node.js dependencies and scripts
├── data/                    # Persistent data directory (SQLite DB)
├── docker-manager.sh        # Comprehensive Docker management (11k lines)
├── docker-start.sh         # Simple Docker startup script
├── docker-stop.sh          # Simple Docker shutdown script
├── README.md               # Detailed project documentation (Chinese)
├── DOCKER_README.md        # Docker deployment guide
└── CLAUDE.md              # This file - AI assistant guidance
```

### Database Schema (SQLite)
Comprehensive database design with 12 core tables supporting multi-tenant code execution and social features:

- **User**: id, username, email, hashed_password, full_name, is_active, is_admin, user_level (1-4), avatar_url, bio, created_at
- **CodeExecution**: id, user_id, code, result, status (success/error/timeout), execution_time (ms), memory_usage (MB), created_at, is_api_call, code_library_id, conda_env
- **CodeLibrary**: id, user_id, title, description, code, language (python), is_public, tags, conda_env, created_at, updated_at
- **APIKey**: id, user_id, key_name, key_value (sk- prefix), is_active, last_used, usage_count, created_at, expires_at
- **AIConfig**: id, user_id, config_name, provider (qwen/openai/claude), model_name, api_key, base_url, is_active, created_at, updated_at
- **UserEnvironment**: id, user_id, env_name (unique), display_name, description, python_version, conda_yaml, is_active, is_public, created_at, updated_at, last_used
- **Post**: id, user_id, title, content, code_snippet, language, tags, is_public, view_count, like_count, created_at, updated_at
- **PostLike**: id, user_id, post_id, created_at
- **PostFavorite**: id, user_id, post_id, created_at
- **Comment**: id, user_id, post_id, content, created_at, updated_at
- **CommentLike**: id, user_id, comment_id, created_at
- **PostCodeShare**: id, post_id, code_library_id, created_at
- **Follow**: id, follower_id, following_id, created_at
- **SystemLog**: id, user_id, action, resource_type, resource_id, details (JSON), ip_address, user_agent, status (success/error/warning), created_at

### Key Development Patterns

**Backend Patterns:**
- **Single File Architecture**: All API endpoints in `main.py` - use Ctrl+F to find specific endpoints
- **FastAPI Dependencies**: Authentication and database sessions handled via dependency injection
- **SQLAlchemy Models**: All database models in `database.py` with proper relationships
- **Pydantic Validation**: Request/response models in `models.py` with comprehensive type hints
- **Error Handling**: Consistent HTTP status codes and error messages across endpoints
- **Security**: All endpoints require authentication except `/register`, `/login`, and health endpoints

**Frontend Patterns:**
- **Context-based Auth**: `AuthContext.js` provides global authentication state
- **Axios Interceptors**: Automatic token handling and error response processing
- **Ant Design Components**: Consistent UI components with Chinese localization
- **Protected Routes**: Route guards in `App.js` redirect unauthenticated users
- **Component Organization**: Page components in `/pages`, shared components in `/components`

**Database Patterns:**
- **SQLite with Auto-initialization**: Database and admin user created on first run
- **Audit Logging**: All user actions logged in `SystemLog` table with IP tracking
- **User Quotas**: Daily limits tracked per user level in `CodeExecution` table
- **Multi-tenancy**: User isolation via `user_id` foreign keys throughout schema

## Development Commands

### Backend Development
```bash
cd backend
python -m venv venv  # Create virtual environment (recommended)
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt  # Install dependencies
python main.py  # Start backend server on http://localhost:8000

# Backend Dependencies
# FastAPI 0.104.1 web framework with Uvicorn 0.24.0 ASGI server
# SQLAlchemy 2.0.23 ORM with SQLite database
# Pydantic 2.5.0 for data validation
# JWT authentication with python-jose[cryptography] 3.3.0
# Argon2-cffi 23.1.0 password hashing
# OpenAI 2.2.0 SDK for AI integration
# python-multipart for file uploads
# aiofiles for async file operations
# requests for HTTP client operations
# python-dotenv for environment variable management
```

### Frontend Development
```bash
cd frontend
npm install  # Install dependencies
npm start  # Start development server on http://localhost:3000
npm test  # Run tests in watch mode
npm run build  # Build for production

# Available npm scripts:
# npm start          - Development server (React dev server)
# npm test           - Run tests in watch mode
# npm run build      - Production build to /build directory
# npm run eject      - Eject from Create React App (irreversible)

# Frontend Stack
# React 18 with functional components and hooks
# Ant Design 5.12.8 UI component library (Chinese locale)
# React Router 6.6.1 for client-side routing
# Axios 1.6.2 for HTTP requests with interceptors
# Context API for authentication state
# dayjs and moment for date/time handling
```

### Testing
```bash
# Frontend tests (React Testing Library)
cd frontend
npm test  # Run tests in interactive watch mode
npm test -- --coverage  # Run tests with coverage report
npm test -- --watchAll=false  # Run tests once (CI mode)
npm test -- --testNamePattern="<pattern>"  # Run specific tests

# Backend testing
# Currently uses manual testing via FastAPI auto-generated docs
# Access http://localhost:8000/docs for interactive API testing
# Access http://localhost:8000/redoc for alternative API documentation
# Note: Backend lacks automated unit/integration tests - consider adding pytest suite
```

### Docker Development (Recommended)
```bash
# Using comprehensive management script (recommended)
./docker-manager.sh start          # Start services
./docker-manager.sh status         # Check service health and access URLs
./docker-manager.sh logs backend -f    # View real-time backend logs
./docker-manager.sh logs frontend -f   # View real-time frontend logs
./docker-manager.sh logs all -f        # View all container logs
./docker-manager.sh exec backend       # Enter backend container (bash shell)
./docker-manager.sh exec frontend      # Enter frontend container (sh shell)
./docker-manager.sh restart -b         # Rebuild and restart all services
./docker-manager.sh restart            # Restart services without rebuilding
./docker-manager.sh stop               # Stop services
./docker-manager.sh cleanup            # Clean all Docker resources

# Docker management commands accept both English and Chinese:
# ./docker-manager.sh logs backend     # or: ./docker-manager.sh logs 后端
# ./docker-manager.sh exec frontend    # or: ./docker-manager.sh exec 前端

# Using simple scripts
./docker-start.sh      # Start services (basic)
./docker-stop.sh       # Stop services (basic)

# Docker Architecture
# Backend: miniconda3 with Python 3.11 in 'runner' conda environment
# Frontend: Multi-stage build (Node.js 18 builder + Nginx Alpine production)
# Data persistence: ./data/ directory mounted to backend container
# Network: Custom Docker network for secure container communication
# Health checks: Both containers have configured health endpoints
```

## Key Features

### User Levels System (4-Tier Architecture)
- **Level 1 (Free)**: 10 daily executions, 20 daily API calls, 30s timeout, 128MB memory, 5 saved codes, 2 API keys
- **Level 2 (Basic)**: 50 daily executions, 100 daily API calls, 60s timeout, 256MB memory, 20 saved codes, 5 API keys
- **Level 3 (Premium)**: 200 daily executions, 500 daily API calls, 120s timeout, 512MB memory, 100 saved codes, 10 API keys
- **Level 4 (Enterprise)**: Unlimited executions, unlimited API calls, 300s timeout, 1024MB memory, unlimited saved codes and API keys

### Authentication & Security
- JWT token-based authentication with 30-minute expiration (configurable via ACCESS_TOKEN_EXPIRE_MINUTES)
- Argon2 password hashing for enhanced security
- Role-based access control (admin/user separation)
- API key authentication for external programmatic access
- Comprehensive system logging with IP address and user agent tracking
- Secure temporary file execution with automatic cleanup

### Code Execution Engine
- Secure Python code execution in isolated temporary files
- Conda environment support (base + user-created environments)
- User-level based execution timeouts and memory limits
- Daily execution quotas and API call quota tracking
- Execution history with performance metrics (execution time, memory usage)
- Real-time output streaming and error handling

### AI Integration & Code Generation
- Multi-provider AI support (Qwen/Alibaba Cloud, OpenAI, Claude, custom OpenAI-compatible APIs)
- User-configurable AI models with API key management
- Code generation with customizable parameters (temperature, max_tokens)
- Active AI configuration switching (only one config active per user)
- AI usage tracking and logging

### Code Library Management
- Personal code snippet storage with tagging and categorization
- Public/private code sharing with access controls
- Environment-specific code storage (conda_env field)
- API access to saved code for external execution
- Search and organization features with pagination

### Environment Management (Advanced Feature)
- Conda virtual environment creation and management (non-admin users: 1 environment limit)
- Package installation/uninstallation/upgrade in isolated environments
- Environment sharing (public environments for non-admin users)
- Python version selection (default: 3.11)
- Environment usage tracking and monitoring
- Admin-level environment oversight and control

### System Administration
- Comprehensive system logging with advanced filtering (action, resource_type, status, date_range)
- User management with admin controls
- Database import/export functionality (SQLite backup/restore)
- Real-time execution monitoring and statistics
- System resource monitoring and health checks
- API key usage tracking and management

### Community & Social Features
- User posts with code snippets, markdown content, and tagging
- Social interactions: like posts, favorite posts, comment on posts
- User following system and follower management
- User profiles with avatar uploads, bio, and statistics
- Post commenting with nested comments and like functionality
- Code sharing between community posts and personal code library
- Public/private post visibility controls
- User activity feeds and engagement metrics

## API Endpoints (Comprehensive REST API)

### Authentication & User Management
- `POST /register` - User registration with email validation
- `POST /login` - User login (returns JWT token with 30-minute expiration)
- `GET /users/me` - Get current user info and permissions
- `GET /users` - List all users (admin only)
- `POST /change-password` - Change current user password
- `POST /admin/users/{user_id}/change-password` - Admin password change for any user
- `PUT /admin/users/{user_id}` - Update user information (admin only)
- `DELETE /admin/users/{user_id}` - Delete user (admin only)

### Code Execution (Core Feature)
- `POST /execute` - Execute Python code with user limits and environment selection
- `GET /executions` - Get user's execution history with pagination
- `GET /admin/executions` - Get all executions (admin only)
- `GET /user-stats` - Get user statistics and remaining quotas
- `GET /conda-environments` - Get available conda environments for current user

### AI Integration & Code Generation
- `POST /ai-configs` - Create AI configuration (max 5 per user)
- `GET /ai-configs` - Get user's AI configurations
- `PUT /ai-configs/{id}` - Update AI configuration
- `DELETE /ai-configs/{id}` - Delete AI configuration
- `POST /ai/generate-code` - Generate code using AI with customizable parameters

### Code Library Management
- `POST /code-library` - Save code to library with environment association
- `GET /code-library` - Get user's code library with pagination and search
- `GET /code-library/{id}` - Get specific code from library
- `PUT /code-library/{id}` - Update code in library
- `DELETE /code-library/{id}` - Delete code from library

### API Key Management
- `POST /api-keys` - Create API key with limits based on user level
- `GET /api-keys` - Get API keys (without values for security)
- `PUT /api-keys/{id}/toggle` - Enable/disable API key
- `DELETE /api-keys/{id}` - Delete API key

### External API (Programmatic Access)
- `POST /api/v1/execute` - Execute code via API key (uses quotas)
- `GET /api/v1/codes` - Get code library via API key
- `GET /api/v1/codes/{id}` - Get specific code via API key

### Environment Management (Advanced)
- `POST /user-environments` - Create new conda environment (non-admin: 1 limit)
- `GET /user-environments` - Get user's accessible environments
- `GET /user-environments/{id}` - Get specific environment details
- `PUT /user-environments/{id}` - Update environment metadata
- `DELETE /user-environments/{id}` - Delete environment
- `GET /environments/{env_name}/info` - Get environment information and packages
- `GET /environments/{env_name}/packages` - List installed packages
- `POST /environments/{env_name}/packages/install` - Install package in environment
- `DELETE /environments/{env_name}/packages/{package_name}` - Uninstall package
- `PUT /environments/{env_name}/packages/{package_name}/upgrade` - Upgrade package

### System Administration (Admin Only)
- `GET /admin/logs` - Get system logs with advanced filtering
- `GET /admin/logs/stats` - Get log statistics for time period
- `GET /admin/logs/actions` - Get available log actions for filtering
- `GET /admin/logs/resource-types` - Get available resource types
- `POST /admin/database/export` - Export database to ZIP file
- `POST /admin/database/import` - Import database from uploaded file
- `GET /admin/database/info` - Get database information and statistics
- `GET /admin/user-environments` - Get all user environments (admin view)
- `DELETE /admin/user-environments/{env_id}` - Admin delete any environment

### Community & Social Features
- `GET /posts` - Get public posts with pagination and filtering
- `POST /posts` - Create new post (authenticated users)
- `GET /posts/{id}` - Get specific post details
- `PUT /posts/{id}` - Update post (author only)
- `DELETE /posts/{id}` - Delete post (author/admin only)
- `POST /posts/{post_id}/like` - Like/unlike a post
- `POST /posts/{post_id}/favorite` - Favorite/unfavorite a post
- `GET /posts/{post_id}/comments` - Get comments for a post
- `POST /posts/{post_id}/comments` - Add comment to a post
- `PUT /comments/{comment_id}` - Update comment (author only)
- `DELETE /comments/{comment_id}` - Delete comment (author/admin only)
- `POST /comments/{comment_id}/like` - Like/unlike a comment
- `POST /users/{username}/follow` - Follow/unfollow a user
- `GET /users/{username}/profile` - Get user profile and stats
- `PUT /users/profile` - Update current user profile (bio, avatar_url)
- `GET /users/{username}/posts` - Get user's posts
- `GET /users/{username}/followers` - Get user's followers
- `GET /users/{username}/following` - Get users that user follows
- `POST /posts/{post_id}/share-to-library` - Share post code to personal library

### System Information
- `GET /user-levels` - Get all user level configurations
- `GET /user-stats` - Get current user's statistics and limits
- `GET /` - Root endpoint for health check

## Security & Production Considerations

### Authentication & Access Control
- **Default admin user**: username="admin", password="admin123" (change immediately after first login)
- **JWT tokens**: 30-minute expiration (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Password hashing**: Argon2 for enhanced security
- **API keys**: Secure format (sk- prefix) with usage tracking and optional expiration
- **Role-based access**: Strict separation between admin and user privileges

### Code Execution Security
- **Sandboxed execution**: Temporary files with automatic cleanup
- **Resource limits**: User-level based timeouts and memory constraints
- **Environment isolation**: Conda environments for package separation
- **Audit logging**: All actions logged with IP addresses and user agents

### Data Protection
- **Database**: SQLite file (coderunner.db) excluded from git for security
- **Sensitive data**: API keys and passwords hashed/encrypted
- **Session management**: Proper SQLAlchemy session handling
- **Input validation**: Comprehensive Pydantic model validation

## Environment Configuration

### Required Environment Variables
- `SECRET_KEY`: JWT signing key (change in production, use strong random string)
- `DATABASE_URL`: SQLite database connection string (default: sqlite:///./coderunner.db)
- `NODE_ENV`: React environment (development/production)

### Docker Configuration (Production-Ready)
Multi-stage Docker builds optimized for security and performance:

- **Backend**: miniconda3 with Python 3.11, non-root user, 'runner' conda environment
- **Frontend**: Node.js 18 Alpine builder + Nginx Alpine for production serving
- **Network**: Custom Docker network for secure container communication
- **Health checks**: Configured for both containers with proper intervals
- **Data persistence**: Backend data mounted to `./data/` directory
- **Security**: Non-root users, minimal attack surface, health monitoring

### Container Registry & Deployment
- **Alibaba Cloud Registry**: Pre-built images available at `crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:{backend|frontend}`
- **Production Images**: Optimized multi-stage builds with security hardening
- **Docker Compose Ready**: Reference configuration in README.md for quick deployment
- **Management Scripts**: Comprehensive `docker-manager.sh` with English/Chinese command support

## Database Setup & Management

### Automatic Initialization
The database auto-initializes on first run with:
1. Complete schema creation for all 7 tables
2. Default admin user creation (admin/admin123)
3. Proper index creation for performance optimization
4. Foreign key relationships and constraints

### Database Operations
- **ORM**: SQLAlchemy with proper session management
- **Migrations**: Manual schema updates (no automated migrations currently)
- **Backup**: Admin panel provides database export/import functionality
- **Integrity**: All operations wrapped in proper error handling

## Production Deployment Guidelines

### Security Checklist
- [ ] Change default admin password immediately
- [ ] Set strong SECRET_KEY environment variable
- [ ] Configure firewall rules (only expose necessary ports)
- [ ] Set up HTTPS with reverse proxy
- [ ] Regular database backups
- [ ] Monitor system logs for suspicious activity
- [ ] Keep Docker images updated
- [ ] Configure resource limits and monitoring

### Performance Optimization
- **Frontend**: Static files served by Nginx with gzip compression
- **Backend**: Uvicorn ASGI server with optimized worker configuration
- **Database**: Proper indexing and query optimization
- **Caching**: Consider Redis for session storage in production
- **Monitoring**: Health checks and logging for all services

## Development Notes & Best Practices

### Code Navigation Tips
- **Backend**: All API endpoints are in `main.py` - use Ctrl+F to find specific endpoints
- **Database Models**: All SQLAlchemy models are defined in `database.py`
- **Frontend Components**: Page components are in `/pages`, shared components in `/components`
- **API Layer**: HTTP requests are centralized in `frontend/src/services/api.js`

### Common Development Tasks
- **Adding New API Endpoints**: Add to `main.py`, create corresponding Pydantic models in `models.py`
- **Frontend Route Changes**: Update `App.js` routing and create page component in `/pages`
- **Database Schema Changes**: Modify models in `database.py` (manual migrations currently)
- **New UI Components**: Add to appropriate `/components` or `/pages` directory using Ant Design

### Testing Strategy
- **Frontend**: React Testing Library setup available, needs expanded test coverage
- **Backend**: Consider adding pytest with test database for comprehensive API testing
- **Integration**: Test critical user flows like code execution, AI generation, and authentication

### Production Considerations
- **Missing Features**: No automated backend tests, no CI/CD pipeline, no database migrations
- **Security**: Default admin password should be changed immediately in production
- **Scaling**: Current monolithic architecture suitable for medium-sized applications

### Community Features Development Notes
- **Content Rendering**: Posts support markdown content with code snippet embedding
- **Avatar Management**: User avatars stored as file uploads with URL references
- **Privacy Controls**: Posts can be public or private with visibility restrictions
- **Content Moderation**: Admins can moderate posts and comments via deletion endpoints
- **Engagement Metrics**: View counts, like counts, and follower statistics tracked
- **Code Integration**: Posts can be shared to personal code library with one click