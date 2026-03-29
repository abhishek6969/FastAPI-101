# FastAPI Post Management API

A modern REST API built with FastAPI for managing blog posts with user authentication using JWT tokens. Features include user registration, login with OAuth2 password flow, and authenticated post CRUD operations.

---

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL server running
- Virtual environment (`kodekloudFastAPI/`)

### Installation

```bash
# Activate virtual environment
.\kodekloudFastAPI\Scripts\activate

# Install dependencies (already done, but if needed)
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-jose passlib argon2-cffi

# Start the server
uvicorn app.main:app --reload
```

### Access API

- **API Docs**: http://localhost:8000/docs (interactive Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Health Check**: http://localhost:8000/ (root endpoint)

---

## Project Structure

```
app/
│
├── main.py                    # FastAPI app initialization, route registration, startup logic
├── database.py                # PostgreSQL connection, SQLAlchemy engine, session factory
├── models.py                  # ORM models for database tables (Post, Users)
├── schemas.py                 # Pydantic schemas for request/response validation
├── oauth2.py                  # JWT token creation and verification logic
├── utils.py                   # Password hashing (Argon2) and verification
│
├── routers/
│   ├── auth.py                # POST /login endpoint (OAuth2 password flow)
│   ├── post.py                # POST CRUD endpoints (GET, POST, create, delete)
│   └── user.py                # User registration and retrieval endpoints
│
├── databases.md               # SQL basics and database fundamentals
├── OAuth2_JWT_Flow.md         # Detailed JWT authentication flow explanation
├── Models_Schemas.md          # ORM models vs Pydantic schemas documentation
│
├── __pycache__/               # Python bytecode cache
└── routers/__pycache__/       # Bytecode cache for routers
```

---

## API Overview

### Authentication Flow

The API uses **JWT (JSON Web Token)** with **OAuth2 password flow**:

```
1. Register/Login → Get JWT Token
2. Include Token in API Requests → Authenticate
3. Server Verifies Token → Execute Endpoint
```

**Detailed explanation**: See [OAuth2_JWT_Flow.md](OAuth2_JWT_Flow.md)

### Endpoints

#### 1. User Management

**Register New User**
```http
POST /users
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "secure123"
}

Response: 201 Created
{
  "id": 1,
  "email": "john@example.com",
  "created_at": "2024-03-24T10:30:00Z"
}
```

**Get User Details**
```http
GET /users/{id}

Response: 200 OK
{
  "id": 1,
  "email": "john@example.com",
  "created_at": "2024-03-24T10:30:00Z"
}
```

#### 2. Authentication

**Login (Get JWT Token)**
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=john@example.com&password=secure123

Response: 200 OK
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Token Details**
- **Type**: Bearer token (JWT)
- **Expiration**: 30 minutes after creation
- **Usage**: Include in Authorization header of authenticated requests

#### 3. Post Management

**Get All Posts** (authenticated)
```http
GET /posts
Authorization: Bearer <token>

Response: 200 OK
[
  {
    "id": 1,
    "title": "My First Post",
    "content": "Hello World",
    "published": true,
    "created_at": "2024-03-24T10:30:00Z"
  }
]
```

**Get Single Post** (authenticated)
```http
GET /posts/{id}
Authorization: Bearer <token>

Response: 200 OK
{
  "id": 1,
  "title": "My First Post",
  "content": "Hello World",
  "published": true,
  "created_at": "2024-03-24T10:30:00Z"
}
```

**Create New Post** (authenticated)
```http
POST /posts
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My First Post",
  "content": "Hello World",
  "published": true
}

Response: 201 Created
{
  "id": 1,
  "title": "My First Post",
  "content": "Hello World",
  "published": true,
  "created_at": "2024-03-24T10:30:00Z"
}
```

---

## Key Technologies

### FastAPI
- Modern, fast web framework for building APIs with automatic validation and documentation
- Automatic OpenAPI/Swagger docs at `/docs`
- Type hints for request/response validation

### SQLAlchemy ORM
- Object-Relational Mapping for database operations
- Type-safe database queries (prevents SQL injection)
- Works with PostgreSQL, MySQL, SQLite, etc.
- See [Models_Schemas.md](Models_Schemas.md) for detailed ORM explanation

### PostgreSQL
- Relational database for persistent data storage
- Tables: `posts`, `users`
- Auto-create tables at app startup via ORM

### JWT (JSON Web Tokens)
- Stateless authentication (no server-side session storage)
- Token contains user ID and expiration time
- Digitally signed to prevent tampering
- See [OAuth2_JWT_Flow.md](OAuth2_JWT_Flow.md) for JWT flow

### Pydantic
- Data validation library for Python
- Automatic request/response serialization
- Type checking for API contracts

### Argon2
- Password hashing algorithm (industry standard)
- Resistant to GPU/ASIC attacks
- Timing-safe comparison

---

## Database Schema

### posts Table
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

### users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

---

## Security Features

### Password Security
✅ **Argon2 Hashing**
- Industry-standard password hashing algorithm
- Never store plaintext passwords
- Hash verified on login, plaintext discarded

### JWT Security
✅ **Token Verification**
- Signature verification prevents tampering
- Expiration checking (30 min default)
- Secret key signing

✅ **Authorization Headers**
- Token sent in `Authorization: Bearer <token>` format
- OAuth2 compliance

### Input Validation
✅ **Pydantic Schemas**
- Email format validation (EmailStr)
- Type checking for all fields
- Automatic error messages (422 for invalid input)

⚠️ **Improvements Needed**
1. Move `SECRET_KEY` to environment variables (don't hardcode)
2. Use HTTPS in production (token transmitted in requests)
3. Implement token blacklist for logout functionality
4. Add refresh tokens for longer session duration

---

## Development

### Key Files to Understand

1. **[main.py](main.py)** - Express API initialization
   - FastAPI app setup
   - Router registration
   - Database table auto-creation

2. **[oauth2.py](oauth2.py)** - JWT authentication
   - Token creation
   - Token verification
   - Dependency injection for protected routes

3. **[routers/auth.py](routers/auth.py)** - Login endpoint
   - OAuth2PasswordRequestForm handling
   - Credential verification
   - Token generation

4. **[database.py](database.py)** - Database connection
   - SQLAlchemy engine configuration
   - Session management
   - Connection pooling

5. **[models.py](models.py)** - ORM models
   - Post model (table definition)
   - Users model (table definition)

### Protected Endpoints Pattern

```python
@router.get("/posts")
def get_posts(
    db: Session = Depends(get_db),                      # Database session
    current_user: models.Users = Depends(get_current_user)  # Authentication check
):
    # If we reach here, user is authenticated
    # current_user contains full user object from database
    posts = db.query(models.Post).all()
    return posts
```

**How it works:**
1. `Depends(get_current_user)` - Run authentication check
2. `get_current_user()` - Extracts and verifies JWT token
3. If valid - loads user from database and passes to endpoint
4. If invalid - raises 401 Unauthorized before endpoint runs

### Testing the API

#### Using Swagger UI (Easiest)

1. Go to http://localhost:8000/docs
2. Try each endpoint with "Try it out" button
3. For protected endpoints, click "Authorize" and paste your JWT token

#### Using cURL

```bash
# 1. Register
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# 2. Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=pass123"

# 3. Create post (replace TOKEN with actual token from step 2)
curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"First Post","content":"Hello"}'

# 4. Get posts
curl -X GET http://localhost:8000/posts \
  -H "Authorization: Bearer TOKEN"
```

---

## Documentation

### Conceptual Docs

- **[OAuth2_JWT_Flow.md](OAuth2_JWT_Flow.md)** - Complete explanation of JWT authentication
  - How tokens are created
  - How tokens are verified
  - Request flow diagrams
  - Security considerations
  - Testing examples

- **[Models_Schemas.md](Models_Schemas.md)** - ORM vs Pydantic schemas
  - SQLAlchemy ORM basics
  - Pydantic data validation
  - Schema patterns (Create, Response)
  - Data flow examples

- **[databases.md](databases.md)** - SQL and database fundamentals
  - SQL basics
  - Table design
  - CRUD operations
  - FastAPI-specific patterns

### Auto-Generated Docs

- **Swagger UI** (OpenAPI): http://localhost:8000/docs
  - Interactive endpoint testing
  - Request/response schema visualization
  - Authorization UI

- **ReDoc**: http://localhost:8000/redoc
  - Clean, searchable API documentation

---

## Common Tasks

### Add a New Endpoint

1. Create function in `routers/` file
2. Add `@router.get()`, `@router.post()`, etc. decorator
3. Include dependencies:
   ```python
   db: Session = Depends(get_db)
   current_user: models.Users = Depends(get_current_user)  # if protected
   ```
4. Access database: `db.query(models.Post).filter(...).first()`
5. Return data matching `response_model` schema

### Handle Authentication Errors

```python
# 401 Unauthorized (token invalid/expired/missing)
HTTPException(
    status_code=401,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"}
)

# 403 Forbidden (credentials wrong)
HTTPException(status_code=403, detail="Invalid Credentials")

# 422 Unprocessable Entity (validation error)
# Raised automatically by Pydantic for schema mismatches
```

### Query Database

```python
# SELECT * FROM posts
all_posts = db.query(models.Post).all()

# SELECT * FROM posts WHERE id = 1
one_post = db.query(models.Post).filter(models.Post.id == 1).first()

# SELECT * FROM posts WHERE user_id = 5 AND published = TRUE
published_posts = db.query(models.Post)\
    .filter(models.Post.user_id == 5)\
    .filter(models.Post.published == True)\
    .all()

# INSERT
new_post = models.Post(title="...", content="...")
db.add(new_post)
db.commit()
db.refresh(new_post)  # Get auto-generated ID

# UPDATE
post = db.query(models.Post).filter(models.Post.id == 1).first()
post.title = "New Title"
db.commit()

# DELETE
db.delete(post)
db.commit()
```

---

## Troubleshooting

### 401 Unauthorized on Protected Endpoints

**Problem**: Token invalid or expired
```json
{"detail": "Could not validate credentials"}
```

**Solution**:
1. Check token expiration (30 min lifetime)
2. Re-login with `/login` endpoint to get fresh token
3. Verify token is in Authorization header (format: `Bearer <token>`)
4. Check SECRET_KEY hasn't changed

### 422 Validation Error

**Problem**: Request body format incorrect
```json
{"detail": [{"loc": ["body", "email"], "msg": "invalid email format"}]}
```

**Solution**:
1. Check Content-Type header (should be `application/json`)
2. Verify required fields are provided
3. Check field types match schema (email must be string, not number)

### Database Connection Error

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
1. Verify PostgreSQL is running
2. Check connection string in `database.py`
3. Verify credentials (username, password, database name)
4. Check server location (localhost:5432 is default)

### Password Verification Fails

**Problem**: Correct password rejected on login
```json
{"detail": "Invalid Credentials"}
```

**Explanation**: Each hash is unique due to random salt
- If you see this with known-good password, check:
  1. User exists in database
  2. Password actually hashed (not stored plaintext)
  3. HashFunction wasn't changed mid-project

---

## Next Steps / Production Improvements

1. **Environment Variables**
   - Move SECRET_KEY to `.env` file
   - Use `python-dotenv` to load variables

2. **Refresh Tokens**
   - Implement longer-lived refresh tokens
   - Allow token refresh without re-login
   - Separate access token (5 min) and refresh token (7 days)

3. **Token Revocation**
   - Implement logout endpoint
   - Blacklist tokens or destroy user sessions
   - Add token invalidation on password change

4. **HTTPS**
   - Required for production (tokens sent in requests)
   - Use reverse proxy (nginx, Caddy) or ASGI server (Gunicorn + SSL)

5. **Logging & Monitoring**
   - Log authentication attempts
   - Monitor failed login attempts (brute force detection)
   - Alert on suspicious activity

6. **Database Migrations**
   - Replace `create_all()` with Alembic migrations
   - Version control for schema changes
   - Safe rollback and team collaboration

7. **Rate Limiting**
   - Limit login attempts  
   - Prevent brute force attacks
   - Use Python-Slowapi middleware

8. **Testing**
   - Unit tests for endpoints
   - Integration tests for auth flow
   - Test database separately (test database vs prod)

---

## References

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/
- **JWT Handbook**: https://auth0.com/resources/ebooks/jwt-handbook
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **Argon2 Reference**: https://github.com/p-h-c/phc-winner-argon2

---

## Project Files Quick Reference

| File | Purpose |
|------|---------|
| `main.py` | App initialization, startup logic |
| `database.py` | Database connection configuration |
| `models.py` | SQLAlchemy ORM models |
| `schemas.py` | Pydantic validation schemas |
| `oauth2.py` | JWT token handling (create, verify) |
| `utils.py` | Password hashing functions |
| `routers/auth.py` | Login endpoint |
| `routers/user.py` | User CRUD endpoints |
| `routers/post.py` | Post CRUD endpoints |
| `OAuth2_JWT_Flow.md` | JWT flow deep dive |
| `Models_Schemas.md` | ORM vs Pydantic explanation |
| `databases.md` | SQL fundamentals |
