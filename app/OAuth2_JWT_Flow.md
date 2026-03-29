# OAuth2 & JWT Authentication Flow

## Quick Overview

This FastAPI application uses **JWT (JSON Web Tokens)** with **OAuth2** for stateless authentication.

- **JWT**: A cryptographically signed token that proves a user's identity
- **OAuth2**: A standard authorization framework (we implement the "password flow")
- **Stateless**: No server-side session storage needed - each token contains everything needed

---

## What is JWT?

### Structure

A JWT has three parts separated by dots:

```
header.payload.signature
```

Example JWT:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJ1c2VyX2lkIjo1LCJleHAiOjE4Njc0MzIwMDB9.
5Cy5eIZ8_5F6pK9lX2mU3qA8nB1_dC6eZ5vN2qL0sW8
```

### Parts Explained

**1. Header** (first part)
```json
{
  "alg": "HS256",    // Algorithm: HMAC with SHA-256
  "typ": "JWT"       // Token type
}
```

**2. Payload** (second part)
```json
{
  "user_id": 5,                      // Custom claim: user's database ID
  "exp": 1867432000,                 // Standard claim: expiration time (Unix timestamp)
  "iat": 1867430000                  // Standard claim: issued at time
}
```

**3. Signature** (third part)
```
HMAC-SHA256(
  header + payload,
  SECRET_KEY
)
```

The signature proves the token hasn't been tampered with. Only someone with the SECRET_KEY can create a valid signature.

---

## How Authentication Works

### 1. User Registration (`POST /users`)

```
Client                                Server
  |
  |--- POST /users ------------------>|
  |    {email, password}              |
  |                                   |--- Hash password (Argon2)
  |                                   |--- Store in database
  |                                   |
  |<---- 200 OK ----------------------|
       {id, email, created_at}
```

**Code in `routers/user.py`:**
```python
def create_user(user: UserCreate, db: Session):
    hashed_password = hash_pass(user.password)  # Argon2 hashing
    new_user = models.Users(**user.model_dump())
    db.add(new_user)
    db.commit()
    return new_user
```

---

### 2. User Login (`POST /login`)

```
Client                                Server
  |
  |--- POST /login ------------------>|
  |    {username, password}           |
  |    (OAuth2PasswordRequestForm)     |
  |                                   |--- Query user by email
  |                                   |--- Verify password hash
  |                                   |--- Create JWT token
  |                                   |
  |<---- 200 OK ----------------------|
       {access_token, token_type}
```

**Flow in `routers/auth.py`:**

```python
@router.post("/login", response_model=schemas.Token)
def login(userData: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Step 1: Find user by email
    user = db.query(models.Users).filter(models.Users.email == userData.username).first()
    
    # Step 2: Verify password
    if user is None or not verify_pass(userData.password, user.password):
        raise HTTPException(status_code=403, detail="Invalid Credentials")
    
    # Step 3: Create JWT token
    access_token = oauth2.create_access_token(data={"user_id": user.id})
    
    return {"access_token": access_token, "token_type": "bearer"}
```

**JWT Created by `oauth2.create_access_token()`:**

```python
def create_access_token(data: dict):
    to_encode = data.copy()  # {"user_id": 5}
    
    # Add expiration time (30 minutes from now)
    expire = datetime.now().astimezone(pytz.utc) + timedelta(minutes=30)
    to_encode.update({"exp": expire})  # {"user_id": 5, "exp": <timestamp>}
    
    # Sign and encode: Creates header.payload.signature
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    
    return encoded_jwt  # "eyJhbGc...payload...signature"
```

---

### 3. Authenticated Request

Once the user has a token, they use it in subsequent requests:

```
Client                                Server
  |
  |--- GET /posts ------------------>|
  |    Authorization: Bearer <token>  |
  |                                   |--- Extract token from header
  |                                   |--- Verify signature
  |                                   |--- Check expiration
  |                                   |--- Extract user_id
  |                                   |--- Fetch user from DB
  |                                   |--- Run endpoint logic
  |                                   |
  |<---- 200 OK ----------------------|
       [{posts...}]
```

**Code in `oauth2.get_current_user()`:**

```python
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    # Step 1: Verify token signature and expiration
    token_data = verify_token(token, credentials_exception)
    
    # Step 2: Extract user_id from token
    user_id = token_data.id  # "5" from payload
    
    # Step 3: Fetch full user from database
    user = db.query(models.Users).filter(models.Users.id == user_id).first()
    
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

**Using in Protected Endpoints:**

```python
@app.get("/posts")
def get_posts(current_user: models.Users = Depends(get_current_user)):
    # If we reach here, token is valid and current_user is loaded from DB
    print(f"Authenticated user: {current_user.email}")
    # ... rest of logic
```

---

### 4. Token Verification

When the server receives a token in the Authorization header:

```python
def verify_token(token: str, credentials_exception):
    try:
        # Decode and verify signature
        # jwt.decode() checks:
        #   1. Signature is valid (hasn't been tampered with)
        #   2. Token hasn't expired (checks "exp" claim)
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        # Extract user_id from payload
        user_id = payload.get("user_id")
        
        if user_id is None:
            raise credentials_exception
        
        return schemas.TokenData(id=str(user_id))
        
    except JWTError:  # Signature invalid or token expired
        raise credentials_exception  # 401 Unauthorized
```

---

## Security Aspects

### Token Lifetime

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

- **Pro:** Reduces exposure window if token is stolen
- **Con:** User must re-authenticate every 30 minutes
- **Solution:** Implement refresh tokens (not in this project, but recommended for production)

**In Production, use refresh tokens:**
```
Short-lived access token (5-15 min) + Long-lived refresh token (7 days)
When access token expires, use refresh token to get new access token
Refresh token stored in HTTP-only cookie (safe from XSS)
```

### Password Security

```python
from utils import hash_pass, verify_pass

# Never store plaintext passwords
hashed = hash_pass("MyPassword123")  # Returns hashed version

# Verify login
if verify_pass("MyPassword123", hashed):  # True - password matches
    # Grant access
```

Uses **Argon2** hashing:
- ✅ Resistant to GPU attacks (high memory requirements)
- ✅ Resistant to timing attacks (constant-time comparison)
- ✅ Industry standard (OWASP recommended)

### Secret Key

```python
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
```

⚠️ **NEVER hardcode in production!**

Use environment variables instead:
```python
import os
SECRET_KEY = os.getenv("SECRET_KEY")
```

If SECRET_KEY is compromised:
- Attacker can forge any JWT token
- Can impersonate any user
- All current tokens become insecure

---

## Complete Request Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REGISTRATION (New User)                         │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Client: POST /users                                                  │
│    Payload: {email: "john@example.com", password: "secure123"}          │
│                                                                         │
│ 2. Server: Hash password and store in database                         │
│    stored_hash = argon2(password)                                       │
│    INSERT INTO users (email, password) VALUES (...)                     │
│                                                                         │
│ 3. Server: Return 200 OK                                               │
│    {id: 42, email: "john@example.com", created_at: "2024-03-24"}      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                            LOGIN (Get Token)                             │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Client: POST /login (OAuth2PasswordRequestForm)                      │
│    Body: username=john@example.com, password=secure123                  │
│                                                                         │
│ 2. Server: Verify credentials                                          │
│    - Query user by email: SELECT * FROM users WHERE email = '...'      │
│    - Verify password: argon2.verify(plain, stored_hash)                │
│    - If credentials valid: proceed to step 3                           │
│    - If invalid: raise HTTPException(401)                              │
│                                                                         │
│ 3. Server: Create JWT token                                            │
│    payload = {"user_id": 42, "exp": now + 30 minutes}                 │
│    signature = HMAC-SHA256(header + payload, SECRET_KEY)              │
│    token = header.payload.signature                                    │
│                                                                         │
│ 4. Server: Return token to client                                      │
│    {access_token: "eyJ...", token_type: "bearer"}                     │
│                                                                         │
│ 5. Client: Store token (localStorage, cookie, or memory)              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATED REQUEST (Use Token)                     │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Client: GET /posts                                                   │
│    Header: Authorization: Bearer eyJ...                                 │
│                                                                         │
│ 2. Server: Extract and verify token (oauth2_scheme extracts from header)│
│    - Extract "eyJ..." from "Bearer eyJ..."                             │
│    - Call jwt.decode("eyJ...", SECRET_KEY, "HS256")                   │
│    - Verify signature (ensures not tampered with)                      │
│    - Check expiration time                                             │
│    - If valid: extract {"user_id": 42}                                 │
│    - If invalid/expired: raise HTTPException(401)                      │
│                                                                         │
│ 3. Server: Fetch user from database                                    │
│    user = SELECT * FROM users WHERE id = 42                           │
│                                                                         │
│ 4. Server: Execute endpoint logic                                      │
│    posts = SELECT * FROM posts WHERE user_id = 42                     │
│                                                                         │
│ 5. Server: Return response                                             │
│    [{post1}, {post2}, ...]                                             │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      INVALID/EXPIRED TOKEN SCENARIO                      │
├─────────────────────────────────────────────────────────────────────────┤
│ 1. Client: GET /posts                                                   │
│    Header: Authorization: Bearer <old_token_30_days_old>               │
│                                                                         │
│ 2. Server: Verify token                                                │
│    - Extract token from header ✓                                       │
│    - Check signature ✓                                                 │
│    - Check expiration: exp = 30 min ago ✗                             │
│    - Raise HTTPException(401, "Could not validate credentials")        │
│                                                                         │
│ 3. Server: Return 401 Unauthorized                                     │
│    Header: WWW-Authenticate: Bearer                                    │
│    Body: {"detail": "Could not validate credentials"}                  │
│                                                                         │
│ 4. Client: Handle 401 error                                            │
│    - Clear stored token                                                │
│    - Redirect to login page                                            │
│    - Prompt user to login again                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Testing JWT Flow

### Using cURL

```bash
# 1. Register user
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"secure123"}'

# Response: {"id":1,"email":"john@example.com","created_at":"2024-03-24T..."}

# 2. Login and get token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=secure123"

# Response: {"access_token":"eyJ...","token_type":"bearer"}

# 3. Use token in authenticated request
curl -X GET "http://localhost:8000/posts" \
  -H "Authorization: Bearer eyJ..."

# Response: [{...posts...}]
```

### Using Swagger UI

1. Go to `http://localhost:8000/docs`
2. Click "Try it out" on any endpoint to test
3. For protected endpoints, click "Authorize" button
4. Paste token in format: `Bearer <token_here>`
5. Click "Authorize" to set token for all requests

---

## Files Involved

- **`oauth2.py`**: Token creation and verification logic
- **`routers/auth.py`**: Login endpoint (OAuth2PasswordRequestForm)
- **`routers/user.py`**: User registration endpoint
- **`utils.py`**: Password hashing (Argon2)
- **`schemas.py`**: Token and authentication data models
- **`models.py`**: User database model

---

## Common Issues

### 401 Unauthorized Errors

**Problem:** Token invalid or expired
```
HTTPException: Could not validate credentials
```

**Solutions:**
1. Check token expiration: tokens expire after 30 minutes
2. Re-login to get fresh token
3. Verify token is in "Bearer <token>" format in Authorization header
4. Check SECRET_KEY hasn't changed (impossible in same server process)

### 422 Login Fails

**Problem:** OAuth2PasswordRequestForm validation failed
```
Expected form data: username, password
```

**Solution:** Use correct form format:
```
Content-Type: application/x-www-form-urlencoded
username=email@example.com&password=mypassword
```

Not JSON:
```json
{"username": "...", "password": "..."}
```

---

## Production Improvements

1. **Use refresh tokens** for longer-term access without re-login
2. **Store SECRET_KEY in environment variables** (never hardcode)
3. **Use HTTPS** (JWT sent in requests, needs encryption in transit)
4. **HTTP-only cookies** for token storage (prevents XSS attacks)
5. **Token blacklist/revocation** (when user logs out)
6. **Rate limiting** on login endpoint (brute force protection)
7. **Shorter token lifetime** (5-15 min instead of 30 min)
