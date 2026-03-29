# ============ USER REGISTRATION & PROFILE ENDPOINTS ============
# This router handles user account creation and retrieval.
# Endpoints:
#   - POST /users/          → Register new user
#   - GET /users/{id}       → Get user profile by ID

from fastapi import status, HTTPException, Depends, APIRouter
from ..schemas import UserCreate, User
from sqlalchemy.orm import Session
from .. import models
from ..utils import hash_pass
from ..database import get_db


router = APIRouter(
    prefix="/users",                    # All routes in this file prefixed with /users
    tags=["Users"]                      # Group all user endpoints under "Users" tag in Swagger UI
)


@router.post("/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account
    
    Endpoint: POST /users
    
    Request Body (JSON):
        {
            "email": "user@example.com",
            "password": "securePassword123"
        }
    
    Response (201 Created):
        {
            "id": 1,
            "email": "user@example.com",
            "created_at": "2024-01-15T10:30:00.000000"
        }
    
    Error Codes:
        - 422: Invalid email format or missing fields
        - 409: Conflict - email already registered (UNIQUE constraint violation)
    
    Security:
        - Password is hashed with Argon2 (see utils.py)
        - Plaintext password is never stored
        - Hashed password is never returned in response
    
    How it works:
        1. Validate request body (Pydantic UserCreate schema)
        2. Hash the plaintext password using Argon2
        3. Create new Users ORM model instance
        4. Insert into database
        5. Return user profile (without password)
    """
    # Hash plaintext password before storage
    # Argon2 is the recommended algorithm (stronger than bcrypt)
    hashed_password = hash_pass(user.password)
    
    # Replace plaintext password with hashed version
    user.password = hashed_password
    
    # Convert Pydantic model to dict and create SQLAlchemy model
    new_user = models.Users(**user.model_dump())
    
    # Add to session (staging area - not yet in database)
    db.add(new_user)
    
    # Commit transaction - INSERT statement executed here
    # If email already exists (UNIQUE violation), SQLAlchemy raises IntegrityError
    db.commit()
    
    # Refresh object to populate auto-generated fields (id, created_at)
    db.refresh(new_user)
    
    # Return user profile (Pydantic schema serializes to JSON, excludes password)
    return new_user


@router.get("/{id}", response_model=User)
def get_user(id: int, db: Session = Depends(get_db)):
    """Retrieve user profile by ID
    
    Endpoint: GET /users/{id}
    
    Path Parameters:
        - id (int): User ID (auto-validated, must be positive integer)
    
    Response (200 OK):
        {
            "id": 1,
            "email": "user@example.com",
            "created_at": "2024-01-15T10:30:00.000000"
        }
    
    Error Codes:
        - 404: Not Found - user with this ID doesn't exist
        - 422: Invalid ID format (non-integer)
    
    Note:
        This endpoint is public (no authentication required).
        In production, might want to:
        - Require authentication
        - Limit to fetching current user's own profile
        - Add email privacy mask: "use***@example.com"
    
    How it works:
        1. Query database for user with matching ID
        2. Return user if found, otherwise raise 404
    """
    # Query database for user with this ID
    # .filter(): WHERE clause - filter by id
    # .first(): Get first (and only) matching row, or None if not found
    user = db.query(models.Users).filter(models.Users.id == id).first()
    
    # Check if user exists
    if user is None:
        # Raise 404 - FastAPI converts this to HTTP response automatically
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id: {id} was not found"
        )
    
    # Return user (Pydantic schema excludes password)
    return user

