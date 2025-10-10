# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeRunner is a remote Python code execution platform built with FastAPI (backend) and React + Ant Design (frontend). It features user authentication, multi-tier user levels, AI-powered code generation, secure Python code execution with limits based on user permissions, code library management, API key management, and comprehensive system logging.

## Architecture

### Backend (FastAPI) - main.py
The core FastAPI application with 2700+ lines containing all API endpoints, authentication middleware, and business logic:

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

### Frontend (React + Ant Design)
Modern React application with Chinese localization and comprehensive UI components:

**Core Files:**
- **App.js**: Main application with React Router, authentication context, and protected routes
- **components/AuthContext.js**: Authentication state management using React Context API
- **components/Layout.js**: Navigation and layout components with Ant Design components
- **pages/**: Page components (HomePage, ProductHomePage, LoginPage, UserManagement, SystemManagement, CodeLibraryPage, APIKeyPage, AIConfigPage, EnvironmentPage)
- **services/api.js**: Axios HTTP client with interceptors for authentication and error handling

**Key Frontend Features:**
- Chinese language interface (zhCN locale)
- Protected routes with authentication checks
- Real-time code execution with environment selection
- Comprehensive admin panel for system management
- AI configuration and code generation interface

### Database Schema (SQLite)
Comprehensive database design with 7 core tables supporting multi-tenant code execution:

- **User**: id, username, email, hashed_password, full_name, is_active, is_admin, user_level (1-4), created_at
- **CodeExecution**: id, user_id, code, result, status (success/error/timeout), execution_time (ms), memory_usage (MB), created_at, is_api_call, code_library_id, conda_env
- **CodeLibrary**: id, user_id, title, description, code, language (python), is_public, tags, conda_env, created_at, updated_at
- **APIKey**: id, user_id, key_name, key_value (sk- prefix), is_active, last_used, usage_count, created_at, expires_at
- **AIConfig**: id, user_id, config_name, provider (qwen/openai/claude), model_name, api_key, base_url, is_active, created_at, updated_at
- **UserEnvironment**: id, user_id, env_name (unique), display_name, description, python_version, conda_yaml, is_active, is_public, created_at, updated_at, last_used
- **SystemLog**: id, user_id, action, resource_type, resource_id, details (JSON), ip_address, user_agent, status (success/error/warning), created_at

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
# FastAPI web framework with Uvicorn ASGI server
# SQLAlchemy ORM with SQLite database
# Pydantic for data validation
# JWT authentication with python-jose
# Argon2 password hashing
# OpenAI SDK for AI integration
```

### Frontend Development
```bash
cd frontend
npm install  # Install dependencies
npm start  # Start development server on http://localhost:3000
npm test  # Run tests
npm run build  # Build for production

# Frontend Stack
# React 18 with functional components and hooks
# Ant Design UI component library (Chinese locale)
# React Router for client-side routing
# Axios for HTTP requests
# Context API for authentication state
```

### Docker Development (Recommended)
```bash
# Using comprehensive management script (recommended)
./docker-manager.sh start          # Start services
./docker-manager.sh status         # Check service status
./docker-manager.sh logs backend -f    # View real-time backend logs
./docker-manager.sh logs frontend -f   # View real-time frontend logs
./docker-manager.sh exec backend   # Enter backend container
./docker-manager.sh restart -b     # Rebuild and restart
./docker-manager.sh stop           # Stop services
./docker-manager.sh cleanup        # Clean all resources

# Using simple scripts
./docker-start.sh                  # Start services
./docker-stop.sh                   # Stop services

# Docker Architecture
# Backend: miniconda3 with Python 3.11 in 'runner' environment
# Frontend: Multi-stage build with Node.js builder + Nginx Alpine
# Data persistence: ./data/ directory mounted to backend container
# Network: Custom Docker network for container communication
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
- Conda virtual environment creation and management
- Package installation/uninstallation/upgrade in isolated environments
- Environment sharing (public environments for non-admin users)
- Python version selection (default: 3.11)
- Environment usage tracking and monitoring

### System Administration
- Comprehensive system logging with advanced filtering (action, resource_type, status, date_range)
- User management with admin controls
- Database import/export functionality (SQLite backup/restore)
- Real-time execution monitoring and statistics
- System resource monitoring and health checks
- API key usage tracking and management

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