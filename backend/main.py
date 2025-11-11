"""Main FastAPI application with modular routers."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import auth, users, execution, code_library, api_keys, external_api, environments, ai, admin, profile, community, misc

app = FastAPI(title="CodeRunner API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Include routers
app.include_router(misc.router)  # Root endpoint and misc routes
app.include_router(auth.router)  # Authentication routes
app.include_router(users.router)  # User management (admin)
app.include_router(execution.router)  # Code execution
app.include_router(code_library.router)  # Code library management
app.include_router(api_keys.router)  # API key management
app.include_router(external_api.router)  # External API (API key auth)
app.include_router(environments.router)  # Environment management
app.include_router(ai.router)  # AI configuration and generation
app.include_router(admin.router)  # Admin endpoints (logs, database)
app.include_router(profile.router)  # User profile
app.include_router(community.router)  # Community features

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
