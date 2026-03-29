# ============ AUTHENTICATION ENDPOINTS ============
# This router handles user login and JWT token generation.
# Endpoints:
#   - POST /login          → User login, returns JWT access token

from fastapi import Response, status, HTTPException, Depends, APIRouter
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from ..schemas import UserLogin
from typing import List
from sqlalchemy.orm import Session
from .. import models, oauth2, schemas
from ..database import get_db
from ..utils import verify_pass


router = APIRouter(
    tags=["Auth"]
)

@router.post("/login", response_model=schemas.Token)
def login(userData: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """User login endpoint - returns JWT access token
    
    Endpoint: POST /login
    
    Content-Type: application/x-www-form-urlencoded (NOT JSON)
    
    Form Data:
        username: str       # Email address (OAuth2 standard calls it 'username')
        password: str       # Plaintext password
        scope: str (optional)  # Unused in this implementation
    
    Response (200 OK):
        {
            "access_token": "eyJhbGc...",      # JWT token string
            "token_type": "bearer"
        }
    
    Error Codes:
        - 403: Forbidden - invalid email or password
        - 422: Invalid form data format
    
    About OAuth2PasswordRequestForm:
        - Standard form-based authentication per OAuth2 spec
        - Automatically parsed from application/x-www-form-urlencoded
        - Required for Swagger UI "Try it out" button to work
        - More standard than custom JSON schema
    
    JWT Token Usage:
        1. Client receives token from response
        2. Client stores token (localStorage, memory, httpOnly cookie)
        3. Client sends token in Authorization header: "Authorization: Bearer <token>"
        4. Server verifies token and extracts user_id (oauth2.get_current_user)
        5. Token expires after 30 minutes (configured in settings)
    
    Security Considerations:
        - Password is cleared from memory after verification (see utils.verify_pass)
        - Returned token is signed but NOT encrypted (payload is readable)
        - HTTPS is required in production (prevents token interception)
        - Short token expiration (30 min) reduces impact if token is stolen
    
    Flow:
        1. Look up user by email
        2. Verify password matches stored hash
        3. Generate and sign JWT with user_id
        4. Return token to client
    """
    
    # ========== STEP 1: LOOK UP USER BY EMAIL ==========
    # OAuth2PasswordRequestForm uses 'username' field (even though we use email)
    # This is standard OAuth2 - username field is repurposed for email in email-based systems
    user = db.query(models.Users).filter(models.Users.email == userData.username).first()
    
    # ========== STEP 2: VERIFY CREDENTIALS ==========
    # Check two conditions:
    #   1. User exists (user is not None)
    #   2. Password matches stored hash (verify_pass returns True)
    # If either fails, deny login (don't reveal which one failed for security)
    if user is None or not verify_pass(userData.password, user.password):
        # Raise 403 Forbidden - credentials invalid
        # Note: NOT 401 Unauthorized (which means "provide credentials")
        # 403 means "credentials provided but rejected"
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Credentials"
        )
    
    # ========== STEP 3: CREATE JWT TOKEN ==========
    # Token payload contains only user_id (minimal for security)
    # oauth2.create_access_token:
    #   - Encodes user_id into JWT payload
    #   - Adds expiration timestamp (30 minutes from now)
    #   - Signs with SECRET_KEY (proves authenticity)
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    
    # ========== STEP 4: RETURN TOKEN ==========
    # Token schema requires access_token and token_type
    # token_type="bearer" indicates HTTP Bearer authentication scheme
    # Client must send: Authorization: Bearer <access_token>
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

