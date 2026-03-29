# ============ IMPORTS ============
# FastAPI: Main web framework for building REST APIs with automatic validation, documentation, and async support
# Depends: Dependency injection system - enables automatic request validation, database session management, etc.
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models
from .database import engine, get_db
from .routers import post, user, auth, vote
from fastapi.middleware.cors import CORSMiddleware




# ============ APP INITIALIZATION ============
# Create FastAPI app instance - this is the entire API application
# All endpoints (@app.get, @app.post, @app.delete, etc.) are registered with this instance
# FastAPI automatically generates OpenAPI docs at /docs and handles routing to the right handler
app = FastAPI()

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== AUTO-CREATE DATABASE TABLES AT STARTUP ==========
# Create all database tables based on SQLAlchemy ORM models (if they don't exist)
# See Models_Schemas.md for explanation of ORM approach vs Alembic migrations
#models.Base.metadata.create_all(bind=engine) 
# Above is now handled by Alembic migrations

# ============ INCLUDE ROUTERS ============
# Associate api routers for modular endpoint organization
# Routers are defined in routers/ with their own business logic and models
app.include_router(post.router)
app.include_router(user.router)
app.include_router(auth.router)
app.include_router(vote.router)

# ============ HEALTH CHECK ENDPOINT ============
@app.get("/")
def root():
    """Root endpoint for API health check"""
    return {"message": "FastAPI Server is running!"}



