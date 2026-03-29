# SQLAlchemy ORM Models & Pydantic Schemas

## Overview

This project uses two types of data models:

1. **SQLAlchemy ORM Models** (`models.py`) - represent database tables
2. **Pydantic Schemas** (`schemas.py`) - validate and serialize API data

They work together but serve different purposes.

---

## Quick Comparison

| Aspect | SQLAlchemy Model | Pydantic Schema |
|--------|------------------|-----------------|
| **Purpose** | Database table representation | API request/response validation |
| **Location** | Database (PostgreSQL) | Memory (Python objects) |
| **Persistence** | Permanent (survives app restart) | Temporary (exists during request) |
| **When Created** | At app startup via `models.Base.metadata.create_all()` | When API request arrives |
| **Typical Use** | `db.query(models.Post).all()` | `PostResponse(id=1, title=...)` |

---

## SQLAlchemy ORM Models

### What is an ORM?

**ORM = Object-Relational Mapping**

Bridges Python objects and database tables:

```
Python Class          Database Table
┌───────────┐        ┌────────────────┐
│ Post      │   ←→   │ posts          │
├───────────┤        ├────────────────┤
│ id        │        │ id (INT PK)    │
│ title     │        │ title (VARCHAR)│
│ content   │        │ content (TEXT) │
│ published │        │ published (BOO)│
│ created_at│        │ created_at (TS)│
└───────────┘        └────────────────┘
```

### Benefits of ORM

**Without ORM (Raw SQL):**
```python
# Risk 1: SQL injection vulnerability
user_id = "1; DROP TABLE users;--"
query = f"SELECT * FROM posts WHERE user_id = {user_id}"
cursor.execute(query)  # ❌ Unsafe!

# Risk 2: Type mismatches
result = cursor.execute("SELECT * FROM posts")
posts = result.fetchall()  # Returns tuples or dicts
# No type checking - easy to access wrong fields

# Risk 3: Database-specific SQL
# Different SQL for PostgreSQL, MySQL, SQLite = maintenance nightmare
```

**With ORM (SQLAlchemy):**
```python
# ✅ Automatic escaping prevents SQL injection
user_id = 1234
posts = db.query(models.Post).filter(models.Post.user_id == user_id).all()

# ✅ Type-safe - IDE autocomplete
for post in posts:
    print(post.title)  # <-- IDE knows about 'title' attribute

# ✅ Database-agnostic - same code works with PostgreSQL, MySQL, SQLite
```

### The Post Model

Located in `models.py`:

```python
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    title = Column(String, index=True, nullable=False)
    content = Column(String, index=True, nullable=False)
    published = Column(Boolean, server_default="TRUE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
```

#### Field Breakdown

**id: Column(Integer, ...)**
- Type: `Integer` → SQL type: `INT`
- `primary_key=True` → Unique identifier, auto-increments
- `index=True` → Database index (speeds up lookups)
- `nullable=False` → NOT NULL constraint

**title: Column(String, ...)**
- Type: `String` → SQL type: `VARCHAR` (unlimited length in PostgreSQL)
- `index=True` → Searchable (useful for LIKE queries)
- `nullable=False` → Must always provide a title

**published: Column(Boolean, ...)**
- Type: `Boolean` → SQL type: `BOOLEAN`
- `server_default="TRUE"` → PostgreSQL default: if not provided, set to TRUE
- `nullable=False` → Always TRUE or FALSE, never NULL

**created_at: Column(TIMESTAMP, ...)**
- Type: `TIMESTAMP(timezone=True)` → SQL type: `TIMESTAMP WITH TIME ZONE`
- `server_default=func.now()` → PostgreSQL function: set to current time
- `nullable=False` → Always has a value

#### How It Creates Tables

When app starts:
```python
# In main.py
models.Base.metadata.create_all(bind=engine)
```

SQLAlchemy generates SQL:
```sql
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    published BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ON posts(id);
CREATE INDEX ON posts(title);
CREATE INDEX ON posts(content);
```

### The Users Model

```python
class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
```

**`unique=True`** on email:
- No two users can have the same email
- Database constraint prevents duplicates
- Attempting to insert duplicate email raises IntegrityError

---

## Pydantic Schemas

### What is Pydantic?

**Pydantic = Data validation and serialization library**

Converts and validates data:
```
Raw JSON Input               Pydantic Schema           Validated Python Object
{"title": "My Post",    →    class PostCreate(...)    →  PostCreate(
 "content": "Hello"}                                         title="My Post",
                                                           content="Hello",
                                                           published=True
                                                       )
```

### Schema Pattern: Create, Response, and Base

The project follows this pattern:

```python
# 1. Base Schema (common fields for creation and response)
class Post(BaseModel):
    title: str
    content: str
    published: bool = True

# 2. Create Schema (used for POST requests)
class PostCreate(Post):
    pass  # Inherits all fields from Post

# 3. Response Schema (returned from API)
class PostResponse(Post):
    id: int  # Added field (not expected in request)
    created_at: datetime  # Added field (auto-generated by DB)
    
    class Config:
        from_attributes = True  # Convert SQLAlchemy models to dicts
```

### Why Separate Schemas?

```python
# ❌ Bad: Same schema for request and response
class Post(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime

# User should NOT provide id and created_at in request
# But we force them to because they're in the same schema

# ✅ Good: Separate schemas
class PostCreate(BaseModel):
    title: str
    content: str

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
```

### How Response Serialization Works

```
SQLAlchemy ORM Object          Pydantic Response          JSON Response
┌────────────────────────┐    ┌──────────────────────┐   ┌─────────────┐
│ Post(                  │    │ PostResponse(        │   │ {           │
│   id=42,               │ → │   id=42,             │ → │   id: 42,   │
│   title="Hello",       │    │   title="Hello",     │   │   title: ..│
│   content="...",       │    │   content="...",     │   │   content:.│
│   published=True,      │    │   published=True,    │   │   published│
│   created_at=2024-...) │    │   created_at=...)    │   │ }           │
│                        │    │                      │   │             │
│ from_attributes=True   │    │ (from ORM object)    │   │ (JSON str)  │
└────────────────────────┘    └──────────────────────┘   └─────────────┘
```

**The Config class:**
```python
class PostResponse(BaseModel):
    id: int
    # ...other fields...
    
    class Config:
        from_attributes = True
```

`from_attributes = True` allows Pydantic to read data from SQLAlchemy ORM objects:
```python
# Without Config.from_attributes:
post = db.query(models.Post).first()  # Returns ORM object
response = PostResponse(**post)  # ❌ Error: can't convert ORM to dict

# With Config.from_attributes:
post = db.query(models.Post).first()
response = PostResponse.from_orm(post)  # ✅ Works!
# OR just pass ORM object - FastAPI auto-converts
return post  # FastAPI uses PostResponse to serialize
```

---

## All Schemas in This Project

```
schemas.py

POST-RELATED:
├─ Post
│  ├─ PostCreate (inherits Post)
│  └─ PostResponse (inherits Post + adds id, created_at)

USER-RELATED:
├─ User (response only - no password!)
├─ UserCreate (request - for registration)
└─ UserLogin (request - for authentication)

AUTH-RELATED:
├─ Token (login response - contains JWT)
└─ TokenData (internal - extracted from JWT)
```

### Detailed Schema Documentation

**Post Base**
```python
class Post(BaseModel):
    title: str                      # Required: must be non-empty string
    content: str                    # Required: must be non-empty string
    published: bool = True          # Optional: defaults to True
```

**PostCreate**
```python
class PostCreate(Post):
    pass  # Same as Post
# Usage: POST /posts with {"title": "...", "content": "..."}
# Client should NOT provide id or created_at
```

**PostResponse**
```python
class PostResponse(Post):
    id: int                         # From database
    created_at: datetime            # From database
    
    class Config:
        from_attributes = True      # Allows SQLAlchemy → Pydantic
# Usage: GET /posts returns [...{id, title, content, published, created_at}...]
# Includes auto-generated fields
```

**User**
```python
class User(BaseModel):
    id: int                         # User ID
    email: EmailStr                 # Email (validated format)
    created_at: datetime            # Registration timestamp
    # NOTE: password NOT included in response
    
    class Config:
        from_attributes = True
```

**UserCreate**
```python
class UserCreate(BaseModel):
    email: EmailStr                 # Validated email format
    password: str                   # Plaintext (will be hashed server-side)
# Usage: POST /users to register new user
```

**UserLogin**
```python
class UserLogin(BaseModel):
    email: EmailStr
    password: str
# Usage: POST /login to authenticate
# Note: OAuth2PasswordRequestForm used internally, not this schema
```

**Token**
```python
class Token(BaseModel):
    access_token: str               # The JWT token string
    token_type: str                 # Usually "bearer"
# Usage: POST /login response
# Example: {"access_token": "eyJ...", "token_type": "bearer"}
```

---

## Data Flow Examples

### Example 1: Creating a Post

```
1. Client Request:
   POST /posts
   {"title": "My First Post", "content": "Hello World"}

2. FastAPI receives raw JSON string

3. Pydantic validates using PostCreate schema:
   - Check title is string ✓
   - Check content is string ✓
   - Set published = True (default) ✓
   - Create Python object: PostCreate(title=..., content=...)

4. Route handler receives validated object:
   def create_post(post: PostCreate, db: Session):
       # 'post' is a validated PostCreate object
       post_dict = post.model_dump()  # Convert to dict
       new_post = models.Post(**post_dict)  # Create ORM object
       db.add(new_post)  # Stage in session
       db.commit()  # Execute INSERT
       db.refresh(new_post)  # Reload from DB (get id, created_at)

5. Return ORM object:
   return new_post

6. FastAPI serializes using PostResponse schema:
   - Get response_model=PostResponse
   - Convert ORM object to Pydantic object
   - Serialize to JSON:
   {"id": 123, "title": "My First Post", "content": "Hello World", 
    "published": true, "created_at": "2024-03-24T10:30:00Z"}

7. Client receives JSON response
```

### Example 2: Getting a Post

```
1. Client Request:
   GET /posts/123
   Authorization: Bearer <token>

2. FastAPI dependency injection:
   - Verify JWT token (oauth2_scheme)
   - Get current user from token (get_current_user)
   - Get database session (get_db)

3. Route handler executes:
   def get_post(id: int, db: Session, current_user: models.Users):
       my_post = db.query(models.Post).filter(models.Post.id == id).first()
       return my_post  # Returns ORM object

4. FastAPI serializes using response_model=PostResponse:
   - Convert ORM Post object to PostResponse
   - ORM object: Post(id=123, title=..., content=..., created_at=...)
   - Pydantic object: PostResponse(id=123, ...)

5. JSON Response:
   {"id": 123, "title": "...", "content": "...", "published": true, 
    "created_at": "2024-03-24T10:30:00Z"}
```

---

## Field Validation

### EmailStr Validation

```python
from pydantic import EmailStr

class UserCreate(BaseModel):
    email: EmailStr

# ✅ Valid
UserCreate(email="john@example.com")

# ❌ Invalid
UserCreate(email="not-an-email")  # Missing @
# Raises: ValidationError: invalid email format

UserCreate(email="john@.com")  # Invalid
# Raises: ValidationError: invalid email format
```

### Type Checking

```python
class Post(BaseModel):
    title: str
    content: str

# ✅ Valid
Post(title="Hello", content="World")

# ❌ Invalid - title is int instead of str
Post(title=123, content="World")
# Raises: ValidationError: str expected

# ⚠️ Coercion - Pydantic tries to convert
Post(title="123", content="World")  # ✅ Works (string coercion)

# Strict validation (disable coercion)
class Post(BaseModel):
    title: str
    
    class Config:
        strict = True  # Raises error if type doesn't match exactly
```

---

## ORM Relationships (Future Enhancement)

Currently, the Post and Users models are independent. To add relationships:

```python
# Add foreign key to Post model
class Post(Base):
    __tablename__ = "posts"
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationship: access post.user to get User object
    owner = relationship("Users", back_populates="posts")

class Users(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    
    # Relationship: access user.posts to get all posts by this user
    posts = relationship("Post", back_populates="owner")

# Usage:
post = db.query(models.Post).first()
author_email = post.owner.email  # Access related user!

user = db.query(models.Users).first()
post_count = len(user.posts)  # All posts by this user
```

---

## Summary

| Concept | SQLAlchemy | Pydantic |
|---------|------------|----------|
| **Represents** | Database tables | API data format |
| **Type Hints** | Column() declarations | Python type hints |
| **Validation** | Database constraints | Pydantic validators |
| **Storage** | PostgreSQL (permanent) | Memory (temporary) |
| **Primary Use** | `db.query().filter()` | Request/response models |
| **Example** | `models.Post` | `schemas.PostResponse` |
