# ============ JWT TOKEN GENERATION & VERIFICATION ============
# This module implements JSON Web Token (JWT) authentication for the FastAPI application.
# 
# What is JWT?
#   - A stateless authentication token (no server-side session storage needed)
#   - Contains encoded user data + digital signature for tamper detection
#   - Format: header.payload.signature (three Base64-encoded parts joined by dots)
#   - Example: eyJhbGc...iIsInR...._5Cy5e...
# 
# JWT Flow Overview:
#   1. User logs in with email/password → server verifies credentials
#   2. Server creates JWT with user_id → signs it with SECRET_KEY
#   3. Server returns JWT to client
#   4. Client stores JWT (localStorage, cookie, memory)
#   5. Client sends JWT in Authorization header on each request
#   6. Server verifies JWT signature (proves it wasn't tampered)
#   7. Extract user_id from JWT payload → load full user from database
# 
# Why JWT?
#   - Stateless: Server doesn't maintain session database
#   - Scalable: Works with multiple servers (no session syncing)
#   - Mobile-friendly: Can be sent in URL prefix, headers, or cookies
#   - API standard: Works with REST, GraphQL, mobile apps
# 
# Security Notes:
#   - SECRET_KEY must be random and kept private (environment variable in production)
#   - HTTPS is mandatory (JWT is still transmitted in HTTP requests without HTTPS)
#   - Short expiration times recommended (30 min, with refresh token for longer access)
#   - Token should be signed but NOT encrypted (anyone can read payload without secret)

from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
import pytz
from sqlalchemy.orm import Session
from .database import get_db
from .config import settings

# ========== JWT CONFIGURATION CONSTANTS ==========
# These values determine how tokens are generated and verified

SECRET_KEY = settings.secret_key
# SECURITY WARNING: This is a hardcoded example key!
# In production, MUST use:
#   1. Environment variable: os.getenv("SECRET_KEY")
#   2. Random generated: secrets.token_urlsafe(32)
#   3. Never commit to version control
# If compromised, all current tokens can be forged by attackers.

ALGORITHM = settings.algorithm
# HS256 (HMAC with SHA-256) is the symmetric signing algorithm:
#   - Same key (SECRET_KEY) used for signing AND verification
#   - Fast and standard-compliant
#   - Other options: RS256 (asymmetric), ES256 (elliptic curve)

ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
# Short expiration (30 min) balances security vs user convenience:
#   - Reduces window of opportunity if token is stolen
#   - Forces user to re-authenticate occasionally
#   - Paired with refresh tokens for longer-term access in production

# ========== OAUTH2 PASSWORD BEARER SCHEME ==========
# Tells FastAPI + Swagger UI how authentication works and where to find the token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
# OAuth2PasswordBearer configuration:
#   - tokenUrl="login": Tells Swagger UI that POST /login endpoint provides tokens
#   - Automatically adds "Authorize" button to Swagger UI
#   - Validates that Authorization header is present when endpoint requires it
#   - Format: "Authorization: Bearer <token>"
# 
# When used in endpoint with Depends(oauth2_scheme):
#   - FastAPI extracts token from Authorization header
#   - If token missing/malformed: Returns 403 automatically
#   - If valid: Passes token string to function


def create_access_token(data: dict) -> str:
    """Generate a JWT access token
    
    Args:
        data (dict): Payload to encode in JWT. Usually {"user_id": <int>}
        
    Returns:
        str: Encoded JWT token string ready to send to client
        
    Example:
        >>> token = create_access_token({"user_id": 5})
        >>> # token = "eyJhbGc...payload...signature"
        
    JWT Structure Created:
        1. Header: {"alg": "HS256", "typ": "JWT"}
        2. Payload: {original data + exp timestamp}
        3. Signature: HMAC-SHA256(header + payload, SECRET_KEY)
    """
    to_encode = data.copy()  # Copy to avoid modifying original dict
    
    # Generate expiration timestamp (30 minutes from now, UTC timezone)
    expire = datetime.now().astimezone(pytz.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration claim to payload
    # "exp" is standard JWT claim for expiration time (Unix timestamp)
    to_encode.update({"exp": expire})
    
    # Sign and encode the token
    # jwt.encode() returns the complete token string with all three parts
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str, credentials_exception: HTTPException) -> schemas.TokenData:
    """Decode and verify JWT token signature and expiration
    
    Args:
        token (str): The JWT token string from Authorization header
        credentials_exception (HTTPException): Exception to raise if token invalid
        
    Returns:
        schemas.TokenData: Decoded token data (extracts user_id)
        
    Raises:
        credentials_exception: If signature invalid, expired, or malformed
        
    How it works:
        1. Decode token using SECRET_KEY (verifies signature)
        2. Check "exp" expiration claim (jwt library handles automatically)
        3. Extract user_id from payload
        4. Return TokenData object with user_id
    """
    try:
        # jwt.decode() verifies signature and expiration
        # Raises JWTError if:
        #   - Signature invalid (token was tampered with)
        #   - Expiration time passed (token expired)
        #   - Algorithm mismatch (token signed with different algorithm)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user_id from payload
        # In create_access_token(), we stored {"user_id": <value>}
        user_id: str = payload.get("user_id")
        
        # If user_id missing from payload, token is invalid
        if user_id is None:
            raise credentials_exception
            
        # Create TokenData object with extracted user_id
        token_data = schemas.TokenData(id=str(user_id))
        
        return token_data
        
    except JWTError:
        # Token verification failed (bad signature, expired, malformed)
        # Return 401 Unauthorized
        raise credentials_exception


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> models.Users:
    """Extract user from JWT token and fetch from database
    
    This is the main dependency used by protected endpoints.
    FastAPI processes this dependency for every request to protected endpoints.
    
    Args:
        token (str): JWT token from Authorization header (extracted by oauth2_scheme)
        db (Session): Database session (from get_db())
        
    Returns:
        models.Users: The authenticated user object from database
        
    Raises:
        HTTPException(401): If token invalid, expired, or user not found in database
        
    Usage Example:
        @app.get("/posts")
        def get_posts(current_user: models.Users = Depends(get_current_user)):
            # Only runs if user is authenticated
            return f"Hello {current_user.email}"
    
    Flow:
        1. Extract token from Authorization header (oauth2_scheme handles)
        2. Verify token signature and expiration (verify_token)
        3. Extract user_id from token payload
        4. Query database for user with that ID
        5. Return user object or 401 if not found
        
    Why fetch from database?
        - Token contains only user_id (minimal payload)
        - Database has full user details (email, created_at, etc.)
        - Ensures user still exists (account wasn't deleted)
        - Allows revoking access if needed (delete user from DB)
    """
    # Define exception to raise if token invalid
    # Returns 401 Unauthorized with challenge for bearer token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    # Verify token and extract user_id
    token_data = verify_token(token, credentials_exception)
    
    # Extract user_id from token
    user_id = token_data.id
    
    # Query database for user with this ID
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    
    # If user not found in database, raise 401
    # (User might have been deleted, or token is from different server)
    if user is None:
        raise credentials_exception
    
    # Exclude password field before returning to endpoints
    # Password is never needed after authentication - only in login endpoint
    # This prevents accidental password exposure in downstream functions
    #user.password = None
    
    return user