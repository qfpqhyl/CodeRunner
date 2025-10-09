# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CodeRunner is a remote Python code execution platform built with FastAPI (backend) and React + Ant Design (frontend). It features user authentication, multi-tier user levels, and secure Python code execution with limits based on user permissions.

## Architecture

### Backend (FastAPI)
- **main.py**: Main FastAPI application with all API endpoints
- **database.py**: SQLAlchemy models, database configuration, and initialization
- **models.py**: Pydantic data models for request/response validation
- **auth.py**: JWT authentication, password hashing, and user authentication functions
- **user_levels.py**: User tier configuration (Free, Basic, Premium, Enterprise) with execution limits

### Frontend (React)
- **App.js**: Main application with routing and authentication context
- **components/**: Shared components (AuthContext.js for authentication state, Layout.js for navigation)
- **pages/**: Page components (HomePage, ProductHomePage, LoginPage, UserManagement)
- **services/api.js**: Axios HTTP client for API communication

### Database Schema
- **User**: id, username, email, hashed_password, full_name, is_active, is_admin, user_level, created_at
- **CodeExecution**: id, user_id, code, result, status, execution_time, memory_usage, created_at

## Development Commands

### Backend Development
```bash
cd backend
python -m venv venv  # Create virtual environment (recommended)
source venv/bin/activate  # Activate virtual environment (Linux/Mac)
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

## Key Features

### User Levels System
- **Level 1 (Free)**: 10 daily executions, 30s timeout, 128MB memory
- **Level 2 (Basic)**: 50 daily executions, 60s timeout, 256MB memory
- **Level 3 (Premium)**: 200 daily executions, 120s timeout, 512MB memory
- **Level 4 (Enterprise)**: Unlimited executions, 300s timeout, 1024MB memory

### Authentication & Authorization
- JWT token-based authentication
- Admin/user role separation
- Protected routes requiring authentication
- Admin-only endpoints for user management

### Code Execution
- Secure temporary file execution
- User-level based timeouts and resource limits
- Daily execution quotas
- Execution history tracking
- Error handling for timeouts and exceptions

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login (returns JWT token)
- `GET /users/me` - Get current user info
- `GET /users` - List all users (admin only)

### Code Execution
- `POST /execute` - Execute Python code (with user limits)
- `GET /executions` - Get user's execution history
- `GET /admin/executions` - Get all executions (admin only)

### User Management (Admin Only)
- `POST /admin/users` - Create user
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user

### System Info
- `GET /user-levels` - Get all user level configurations
- `GET /user-stats` - Get current user's statistics and limits

## Security Notes

- Default admin user: username="admin", password="admin123" (change after first login)
- Code execution uses temporary files that are cleaned up after execution
- JWT tokens expire based on `ACCESS_TOKEN_EXPIRE_MINUTES` setting
- User cannot deactivate/delete themselves through admin endpoints
- Database file (coderunner.db) is excluded from git

## Environment Variables
- `SECRET_KEY`: JWT signing key (change in production)
- `DATABASE_URL`: SQLite database connection string

## Development Workflow

1. Backend and frontend run independently on different ports
2. Frontend proxy configuration routes API calls to backend
3. Database auto-initializes with default admin user on first run
4. User levels determine execution limits and quotas
5. All code execution is sandboxed with timeout protection