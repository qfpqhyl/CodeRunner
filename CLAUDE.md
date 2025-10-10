# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeRunner is a remote Python code execution platform built with FastAPI (backend) and React + Ant Design (frontend). It features user authentication, multi-tier user levels, AI-powered code generation, secure Python code execution with limits based on user permissions, code library management, API key management, and comprehensive system logging.

## Architecture

### Backend (FastAPI)
- **main.py**: Main FastAPI application with all API endpoints, authentication, and business logic
- **database.py**: SQLAlchemy models, database configuration, and initialization
- **models.py**: Pydantic data models for request/response validation
- **auth.py**: JWT authentication, Argon2 password hashing, and user authentication functions
- **user_levels.py**: User tier configuration (Free, Basic, Premium, Enterprise) with execution limits

### Frontend (React)
- **App.js**: Main application with routing, authentication context, and protected routes
- **components/AuthContext.js**: Authentication state management using React Context
- **components/Layout.js**: Navigation and layout components
- **pages/**: Page components (HomePage, ProductHomePage, LoginPage, UserManagement, SystemManagement, CodeLibraryPage, APIKeyPage, AIConfigPage)
- **services/api.js**: Axios HTTP client with interceptors for authentication

### Database Schema
- **User**: id, username, email, hashed_password, full_name, is_active, is_admin, user_level, created_at
- **CodeExecution**: id, user_id, code, result, status, execution_time, memory_usage, created_at, is_api_call, code_library_id
- **CodeLibrary**: id, user_id, title, description, code, language, is_public, tags, created_at, updated_at
- **APIKey**: id, user_id, key_name, key_value, is_active, last_used, usage_count, created_at, expires_at
- **AIConfig**: id, user_id, config_name, provider, model_name, api_key, base_url, is_active, created_at, updated_at
- **SystemLog**: id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, status, created_at

## Development Commands

### Backend Development
```bash
cd backend
python -m venv venv  # Create virtual environment (recommended)
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt  # Install dependencies
python main.py  # Start backend server on http://localhost:8000
```

### Frontend Development
```bash
cd frontend
npm install  # Install dependencies
npm start  # Start development server on http://localhost:3000
npm test  # Run tests
npm run build  # Build for production
```

### Docker Development
```bash
# Using management scripts (recommended)
./docker-manager.sh start  # Start services
./docker-manager.sh status  # Check status
./docker-manager.sh logs backend -f  # View logs
./docker-manager.sh stop  # Stop services

# Using individual scripts
./docker-start.sh  # Start services
./docker-stop.sh  # Stop services
```

## Key Features

### User Levels System
- **Level 1 (Free)**: 10 daily executions, 20 daily API calls, 30s timeout, 128MB memory, 5 saved codes, 2 API keys
- **Level 2 (Basic)**: 50 daily executions, 100 daily API calls, 60s timeout, 256MB memory, 20 saved codes, 5 API keys
- **Level 3 (Premium)**: 200 daily executions, 500 daily API calls, 120s timeout, 512MB memory, 100 saved codes, 10 API keys
- **Level 4 (Enterprise)**: Unlimited executions, unlimited API calls, 300s timeout, 1024MB memory, unlimited saved codes and API keys

### Authentication & Authorization
- JWT token-based authentication with 30-minute expiration
- Argon2 password hashing for security
- Admin/user role separation with protected routes
- API key authentication for external access

### Code Execution
- Secure temporary file execution with cleanup
- User-level based timeouts and resource limits
- Daily execution quotas and API call quotas
- Execution history tracking with memory usage tracking
- System logging for all actions with IP tracking

### AI Integration
- Multiple AI provider support (Qwen, OpenAI, Claude, custom OpenAI-compatible APIs)
- User-configurable AI models with API key management
- Code generation with customizable parameters (temperature, max_tokens)
- Active AI configuration management

### Code Library
- Personal code snippet storage with tagging
- Public/private code sharing
- API access to saved code for external execution
- Search and organization features

### System Management
- Comprehensive system logging with filtering
- User management by administrators
- Execution monitoring and statistics
- API key usage tracking

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login (returns JWT token)
- `GET /users/me` - Get current user info
- `GET /users` - List all users (admin only)
- `POST /change-password` - Change password
- `POST /admin/users/{user_id}/change-password` - Admin password change

### Code Execution
- `POST /execute` - Execute Python code (with user limits)
- `GET /executions` - Get user's execution history
- `GET /admin/executions` - Get all executions (admin only)
- `GET /user-stats` - Get user statistics and limits

### AI Features
- `POST /ai-configs` - Create AI configuration
- `GET /ai-configs` - Get AI configurations
- `PUT /ai-configs/{id}` - Update AI configuration
- `DELETE /ai-configs/{id}` - Delete AI configuration
- `POST /ai/generate-code` - Generate code using AI

### Code Library
- `POST /code-library` - Save code to library
- `GET /code-library` - Get code library with pagination
- `GET /code-library/{id}` - Get specific code
- `PUT /code-library/{id}` - Update code
- `DELETE /code-library/{id}` - Delete code

### API Keys
- `POST /api-keys` - Create API key
- `GET /api-keys` - Get API keys (without values)
- `PUT /api-keys/{id}/toggle` - Enable/disable API key
- `DELETE /api-keys/{id}` - Delete API key

### External API
- `POST /api/v1/execute` - Execute code via API key
- `GET /api/v1/codes` - Get code library via API key
- `GET /api/v1/codes/{id}` - Get specific code via API key

### System Management (Admin Only)
- `GET /admin/logs` - Get system logs with filtering
- `GET /admin/logs/stats` - Get log statistics
- `GET /admin/logs/actions` - Get available log actions
- `GET /admin/logs/resource-types` - Get available resource types

### System Info
- `GET /user-levels` - Get all user level configurations
- `GET /user-stats` - Get current user's statistics and limits

## Security Notes

- Default admin user: username="admin", password="admin123" (change after first login)
- Code execution uses temporary files that are cleaned up after execution
- JWT tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- API keys have usage tracking and optional expiration dates
- All system actions are logged with IP addresses and user agents
- Database file (coderunner.db) is excluded from git

## Environment Variables
- `SECRET_KEY`: JWT signing key (change in production)
- `DATABASE_URL`: SQLite database connection string (default: sqlite:///./coderunner.db)
- `NODE_ENV`: React environment (development/production)

## Docker Configuration

The project uses multi-stage Docker builds:
- **Backend**: Python 3.11 slim image with non-root user
- **Frontend**: Node.js 18 Alpine builder + Nginx Alpine for production
- **Network**: Custom Docker network for container communication
- **Health checks**: Configured for both containers
- **Data persistence**: Backend data mounted to `./data/` directory

## Database Initialization

The database auto-initializes on first run with:
1. Database schema creation
2. Default admin user (admin/admin123)
3. Index creation for performance

All database operations use SQLAlchemy ORM with proper session management and error handling.