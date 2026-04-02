# FastAPI 101 - Technical Architecture & Component Integration Guide

**Purpose:** Deep-dive into the technical architecture of the FastAPI social media API project, focusing on how components interact and the reasoning behind design decisions.
 
**For beginners?** Start with README.md, then refer back here for detailed explanations.

---

## 🔗 Component Architecture Overview

This project demonstrates how different layers work together in a production-grade REST API:

```
┌─────────────────────────────────────────────────────────────┐
│                      HTTP CLIENT LAYER                       │
│  (Browser, Mobile App, curl, JavaScript fetch/axios)        │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Request
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI APPLICATION                        │
│  ├─ main.py: App initialization, CORS, router registration │
│  ├─ routers/: Endpoint handlers with business logic         │
│  ├─ config.py: Settings management from environment         │
│  └─ oauth2.py: JWT authentication & authorization           │
└────────────────────┬────────────────────────────────────────┘
                     │ Data validation & transformation
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             VALIDATION & SERIALIZATION LAYER                 │
│  ├─ schemas.py: Pydantic models for request/response        │
│  ├─ utils.py: Password hashing, helper functions            │
│  └─ oauth2.py: Token creation/verification                  │
└────────────────────┬────────────────────────────────────────┘
                     │ Database queries (ORM)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              DATA ACCESS LAYER (ORM)                         │
│  ├─ models.py: SQLAlchemy ORM model definitions             │
│  ├─ database.py: SQLAlchemy engine, session management      │
│  └─ alembic/: Schema version control & migrations           │
└────────────────────┬────────────────────────────────────────┘
                     │ SQL queries
                     ▼
┌─────────────────────────────────────────────────────────────┐
│               POSTGRESQL DATABASE                            │
│  ├─ users table: User accounts & authentication             │
│  ├─ posts table: Blog posts with owner relationships        │
│  └─ votes table: Like/vote junction table (many-to-many)    │
└─────────────────────────────────────────────────────────────┘
```

Each layer has a specific responsibility, making code maintainable and testable.

---

## � Component Integration Patterns

### 1. Models ↔ Schemas ↔ Database

**The Three-Layer Data Model:**

```
SQL Database Row    SQLAlchemy Model    Pydantic Schema    JSON Response
┌───────────────┐   ┌────────────────┐   ┌──────────────┐   ┌────────────┐
│ id: 1         │→→→│ Post(id=1,     │→→→│ PostResponse │→→→│ {          │
│ title: "..."  │   │   title="...",  │   │ - id: int    │   │   "id": 1, │
│ content:"..." │   │   content="...) │   │ - title: str │   │   "title"..│
│ owner_id: 5   │   │   owner_id=5)   │   │ - owner: User│   │ }          │
└───────────────┘   └────────────────┘   └──────────────┘   └────────────┘
    DATABASE          ORM LAYER          VALIDATION        API RESPONSE
                    (models.py)          (schemas.py)       (to client)
```

**Flow Example - Creating a Post:**

```python
# 1. CLIENT sends JSON
{
  "title": "My Post",
  "content": "Hello",
  "published": true
}

# 2. FASTAPI receives request, Pydantic VALIDATES using PostCreate schema
@router.post("/posts", response_model=PostResponse)
def create_post(post: PostCreate, ...)  # ← Pydantic validates JSON matches PostCreate

# 3. HANDLER converts to SQLAlchemy model for database
post_dict = post.model_dump()  # {"title": "My Post", ...}
new_post = models.Post(owner_id=current_user.id, **post_dict)

# 4. DATABASE stores the record
db.add(new_post)
db.commit()  # INSERT executed
db.refresh(new_post)  # Get database-generated values (id, created_at)

# 5. RESPONSE serialized using PostResponse schema
return new_post  # Pydantic converts SQLAlchemy model → JSON
{
  "id": 42,
  "title": "My Post",
  "content": "Hello",
  "published": true,
  "created_at": "2024-01-15T10:30:00",
  "owner_id": 1,
  "owner": {...}
}
```

**Why Three Layers?**
- **Schemas:** Validate input before database (prevent invalid data)
- **Models:** Define table structure and relationships
- **Database:** Persistent storage with constraints

**Key Difference:**
```python
# schemas.py - VALIDATES input/output
class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True
    # NO id, created_at (client shouldn't provide these)

# models.py - DEFINES database table
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)  # Database generates
    title = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())  # DB timestamp
```

---

### 2. Alembic ↔ Models ↔ Database Schema

**How Migrations Maintain Schema Integrity:**

```
DEVELOPMENT PROCESS:

1. CHANGE MODEL (models.py)
   class Users(Base):
       phone_number = Column(String)  # ← new field added

2. GENERATE MIGRATION (Alembic)
   $ alembic revision --autogenerate -m "add phone_number"
   → Creates alembic/versions/xyz_add_phone_number.py

3. MIGRATION FILE CONTAINS:
   def upgrade():
       op.add_column('users', sa.Column('phone_number', ...))
   def downgrade():
       op.drop_column('users', 'phone_number')

4. APPLY MIGRATION (Alembic)
   $ alembic upgrade head
   → Executes upgrade() function
   → Database schema changes
   → Migration recorded in alembic_version table

5. UPDATE SCHEMA (Pydantic)
   class User(BaseModel):
       phone_number: Optional[str]  # ← schema updated
```

**Alembic maintains:**
- **Version history** - Who changed what and when
- **Rollback capability** - Downgrade() function for reversals
- **Deployment safety** - Apply migrations incrementally on production
- **Team collaboration** - Migration files committed to git, not raw SQL

**In code context:**

```python
# 1. Database structure defined in models.py
class Post(Base):
    __tablename__ = "posts"
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))

# 2. Alembic auto-generates SQL from model:
# ALTER TABLE posts ADD CONSTRAINT fk_owner_id 
#   FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE

# 3. SQLAlchemy ORM translates Python to SQL:
db.query(Post).filter(Post.owner_id == 5).all()
# ↓
# SELECT * FROM posts WHERE owner_id = 5
```

---

### 3. OAuth2 ↔ JWT Tokens ↔ Database Authentication

**Multi-Step Authentication Flow:**

```
STEP 1: USER REGISTRATION
  POST /users
  {"email": "john@example.com", "password": "plaintext"}
          ↓
  utils.hash_pass() → Argon2 hashing
          ↓
  DATABASE: users table
  {id: 1, email: "john@example.com", password: "$argon2id$v=19$..."}

STEP 2: USER LOGIN
  POST /login
  {"username": "john@example.com", "password": "plaintext"}
          ↓
  1. Query: SELECT * FROM users WHERE email = "john@example.com"
  2. Verify: utils.verify_pass(plaintext, stored_hash) → True/False
  3. Create: oauth2.create_access_token({"user_id": 1})
          ↓
  RESPONSE: 
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }

STEP 3: AUTHENTICATED REQUEST
  GET /posts
  Headers: Authorization: Bearer eyJ...
          ↓
  1. Extract token from header (oauth2_scheme)
  2. Verify signature with SECRET_KEY (oauth2.verify_token)
  3. Decode payload → extract user_id
  4. Query: SELECT * FROM users WHERE id = 1
  5. Return user object to endpoint
          ↓
  @app.get("/posts")
  def get_posts(current_user: User = Depends(oauth2.get_current_user)):
      # current_user is authenticated User object from database
      return posts
```

**Token Structure (JWT):**

```
Header.Payload.Signature

HEADER:
{"alg": "HS256", "typ": "JWT"}

PAYLOAD:
{"user_id": 1, "exp": 1705316445}

SIGNATURE (created by):
HMAC-SHA256(header + payload, SECRET_KEY)
```

**Why This Design?**
- **Stateless:** Server doesn't store sessions (scales to multiple servers)
- **Time-limited:** Token expires after 30 minutes
- **Verifiable:** Signature proves token wasn't tampered with
- **Mobile-friendly:** Can be sent in headers or cookies

---

### 4. Dependency Injection ↔ Session Management

**How Database Sessions Persist Across Request:**

```python
# database.py defines the dependency
def get_db():
    db = sessionlocal()      # ← Create fresh session for THIS request
    try:
        yield db             # ← Pause here, provide db to endpoint
    finally:
        db.close()           # ← Clean up after endpoint completes

# routers/post.py uses the dependency
@router.post("/posts")
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),           # ← FastAPI calls get_db()
    current_user = Depends(oauth2.get_current_user)  # ← Nested dependency
):
    # db is same session throughout this request
    new_post = models.Post(owner_id=current_user.id, **post_dict)
    db.add(new_post)      # ← Same database session
    db.commit()           # ← Same database session
    db.refresh(new_post)  # ← Same database session
    return new_post
```

**Request Lifecycle with Session:**

```
HTTP Request arrives
    ↓
FastAPI resolves dependencies:
    1. oauth2.get_current_user()
       ├─ Depends(oauth2_scheme) → extract JWT from headers
       ├─ Depends(get_db) → create session (Session #1)
       └─ Uses Session #1 to query users table
    2. Depends(get_db) → SAME session (Session #1, reused)
    ↓
Endpoint handler executes:
    all() queries use Session #1
    ↓
Endpoint returns
    ↓
finally: db.close() in get_db()
    → Session #1 closed
    → Connection returned to pool
    ↓
HTTP Response sent
```

This ensures isolation: each request gets its own session, preventing data corruption from concurrent requests.

---

### 5. Validation Pipeline

**Pydantic Validation Prevents Bad Data:**

```
REQUEST BODY (JSON from client):
{
  "title": "Post",
  "content": "Content",
  "published": "yes"  # ← Wrong type (string instead of bool)
}
    ↓
PYDANTIC SCHEMA:
class PostCreate(BaseModel):
    title: str          # Expects string
    content: str
    published: bool     # Expects boolean
    ↓
VALIDATION RESULT:
422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "published"],
      "msg": "value could not be parsed as a boolean",
      "type": "type_error.boolean"
    }
  ]
}
```

**Validation Happens Automatically:**

```python
@router.post("/posts")
def create_post(post: PostCreate, ...):  # ← Type hint triggers validation
    # If we reach here, 'post' is guaranteed to be valid PostCreate
    # - title is string
    # - content is string  
    # - published is boolean
    # This prevents SQL injection, type errors, invalid data
```

---

### 6. Constraint Enforcement (Database + ORM)

**Foreign Keys & Cascade Deletes:**

```python
# models.py defines relationships
class Post(Base):
    owner_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE")
    )

class Votes(Base):
    post_id = Column(
        Integer,
        ForeignKey("posts.id", ondelete="CASCADE"),
        primary_key=True
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )
```

**When User is Deleted:**

```
DELETE FROM users WHERE id = 5
    ↓
PostgreSQL CASCADE rules trigger:
    ↓
Step 1: Delete all posts owned by user 5
    DELETE FROM posts WHERE owner_id = 5
    ↓
Step 2: Delete all votes on those posts
    DELETE FROM votes WHERE post_id IN (posts we just deleted)
    ↓
Step 3: Delete all votes by user 5
    DELETE FROM votes WHERE user_id = 5
    ↓
Result: Database remains consistent
        No orphaned records
        No referential integrity violations
```

This enforces at the DATABASE level (most secure):

```python
# REST endpoint
@router.delete("/users/{id}")
def delete_user(id: int, db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == id).first()
    if user:
        db.delete(user)  # Calls SQLAlchemy
        db.commit()      # Executes CASCADE deletes in PostgreSQL
    # All related posts and votes auto-deleted by database
```

---

## 🔐 Security Through Component Design

### Password Hashing Pipeline

```
User Registration:
  plaintext password
       ↓
  utils.hash_pass()
       ↓
  Argon2 algorithm:
    - Generate random salt
    - Hash with salt (slow, memory-hard)
  ↓
  Store ONLY HASH in database
  (plaintext never stored)

User Login:
  plaintext password from request
       ↓
  Retrieve stored HASH from database
       ↓
  utils.verify_pass(plaintext, hash)
       ↓
  Argon2.verify() → True/False
  (compares plaintext against hash)
```

**Why Argon2?**
- Memory-hard (requires large RAM to compute)
- GPU/ASIC resistant (can't parallelize attacks)
- OWASP recommended (industry standard)
- Slow by design (makes brute force expensive)

### JWT Security Through Secrets

```
SECRET_KEY = "random-32-character-string"  (in app/.env)
    ↓
    Only server knows this
    ↓
During token creation:
  HMAC-SHA256(header + payload, SECRET_KEY) = signature
    ↓
Token sent to client: header.payload.signature
    ↓
Client sends token in header:
  Authorization: Bearer header.payload.signature

Server receives token:
    ↓
Verify: HMAC-SHA256(header + payload, SECRET_KEY) == signature?
    ↓
If attacker modifies payload or signature:
  HMAC-SHA256(modified_header + payload, SECRET_KEY) != signature
  → Token rejected, 401 Unauthorized
```

Only server has SECRET_KEY, so tokens can't be forged.

---

## 📊 Request-Response Examples with Component Flow

### Example 1: Creating a Post

```
REQUEST:
POST /posts HTTP/1.1
Authorization: Bearer eyJ...
Content-Type: application/json

{
  "title": "Learning FastAPI",
  "content": "Today I learned about models",
  "published": true
}

PROCESSING:

1. FastAPI receives request
   └─ Extract Authorization header → JWT token

2. Dependency: oauth2.get_current_user()
   ├─ oauth2.verify_token(token)  [oauth2.py]
   │  ├─ jwt.decode(token, SECRET_KEY, algorithm="HS256")
   │  ├─ Verify signature matches
   │  ├─ Check expiration (exp claim)
   │  └─ Extract user_id from payload
   │
   └─ db.query(Users).filter(Users.id == user_id).first()  [database.py]
      └─ returns: Users(id=1, email="john@example.com", ...)

3. Dependency: get_db()
   └─ Returns SQLAlchemy session for this request [database.py]

4. Pydantic Validation: PostCreate schema
   ├─ title: "Learning FastAPI" ✓ (string)
   ├─ content: "Today I learned..." ✓ (string)
   └─ published: true ✓ (boolean)

5. Handler: create_post()
   ├─ Convert to dict: {"title": "...", "content": "...", "published": true}
   ├─ Create SQLAlchemy model: models.Post(owner_id=1, **post_dict)
   ├─ db.add(new_post)
   ├─ db.commit()  ← INSERT executed: INSERT INTO posts (title, content, published, owner_id) VALUES (...)
   └─ db.refresh(new_post)  ← Get database values: id=42, created_at="2024-01-15T10:30:00"

6. Response Serialization: PostResponse schema
   ├─ Convert SQLAlchemy model → Pydantic model
   ├─ Serialize to JSON
   └─ Exclude password field (not in schema)

RESPONSE:
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 42,
  "title": "Learning FastAPI",
  "content": "Today I learned about models",
  "published": true,
  "created_at": "2024-01-15T10:30:00.000000",
  "owner_id": 1,
  "owner": {
    "id": 1,
    "email": "john@example.com",
    "created_at": "2024-01-15T10:00:00.000000"
  }
}
```

### Example 2: Deleting a Post (Authorization Check)

```
REQUEST:
DELETE /posts/42 HTTP/1.1
Authorization: Bearer eyJ...

PROCESSING:

1. Verify authentication: oauth2.get_current_user()
   └─ Returns User(id=1, email="john@example.com", ...)

2. Query post: db.query(Post).filter(Post.id == 42).first()
   └─ Returns Post(id=42, owner_id=1, ...)

3. Authorization check:
   if query_post.owner_id != current_user.id:
       raise HTTPException(403, "Not authorized")
   
   1 == 1  ✓  Allowed

4. Delete cascade:
   db.delete(post)
   db.commit()
   ↓
   PostgreSQL executes with CASCADE:
   - DELETE FROM votes WHERE post_id = 42
   - DELETE FROM posts WHERE id = 42

5. Return 204 No Content

RESPONSE:
HTTP/1.1 204 No Content
(empty body)
```

---

## 🚀 Performance Considerations

### Connection Pooling

```python
# database.py
engine = create_engine(url_object)
# Creates connection pool (default 5-20 connections)

sessionlocal = sessionmaker(bind=engine)
# Factory for creating sessions from pool

# Each request:
db = sessionlocal()      # Get connection from pool
# ... use db ...
db.close()               # Return connection to pool (not destroyed)
```

**Without pooling:** New TCP connection per request = slow + resource-intensive
**With pooling:** Connections reused = fast, efficient

### Query Optimization

```python
# INEFFICIENT - N+1 query problem
posts = db.query(Post).all()  # Query 1: Get all posts
for post in posts:
    # Query 2, 3, 4, 5... executed per post
    print(post.owner.email)   # Each access: SELECT * FROM users WHERE id = ?

# EFFICIENT - Eager loading
posts = db.query(Post).options(joinedload(Post.owner)).all()  # Single query with JOIN
for post in posts:
    # No additional queries - owner already loaded
    print(post.owner.email)
```

### Index Strategy

```python
# models.py - Indexes speed up WHERE clauses
class Users(Base):
    id = Column(Integer, primary_key=True)  # Indexed by default
    email = Column(String, unique=True, index=True)  # Indexed: SELECT * FROM users WHERE email = ?

class Posts(Base):
    id = Column(Integer, primary_key=True)  # Indexed
    owner_id = Column(..., ForeignKey(...))  # Indexed by default (foreign key)
    title = Column(String, index=True)      # Indexed: SELECT * FROM posts WHERE title LIKE ?
```

Without indexes, every query scans entire table (slow).
With indexes, database uses B-tree structure (fast).

---

## 🧪 Testing Integration Points

**Test each component layer:**

```python
# 1. Test Schemas (Pydantic validation)
def test_post_create_schema_valid():
    data = {"title": "Test", "content": "Content", "published": True}
    post = PostCreate(**data)
    assert post.title == "Test"

def test_post_create_schema_invalid():
    data = {"title": "Test"}  # Missing content
    with pytest.raises(ValidationError):
        PostCreate(**data)

# 2. Test Models (Database operations)
def test_create_post_in_db():
    post = Post(title="Test", content="Content", published=True, owner_id=1)
    db.add(post)
    db.commit()
    assert post.id is not None  # Auto-generated by database

# 3. Test OAuth2 (Token generation/verification)
def test_create_access_token():
    token = create_access_token({"user_id": 1})
    token_data = verify_token(token, exception)
    assert token_data.id == "1"

# 4. Test Endpoints (Full integration)
def test_create_post_endpoint():
    response = client.post(
        "/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test", "content": "Content"}
    )
    assert response.status_code == 201
    assert response.json()["id"] is not None
```

---

## 📈 Scaling Considerations

### Vertical Scaling (More Powerful Server)
- Increase CPU cores → SQLAlchemy asyncio support
- Increase RAM → Larger connection pool
- Faster disk → Better database query performance

### Horizontal Scaling (Multiple Servers)
- **Web servers:** Run multiple FastAPI instances behind load balancer
- **Database:** Use connection pooling to handle multiple servers
- **Sessions:** JWT is stateless, works across multiple servers
- **Cache:** Redis for session/post caching

### Database Scaling
- **Read replicas:** Distribute queries across read-only databases
- **Connection pooling:** PgBouncer / pgpool middleware
- **Sharding:** Partition data by user_id or date
- **Indexes:** Strategic indexing on frequently queried columns

---

**This technical guide explains the "why" behind each component's design. Reference specific sections when implementing similar patterns in your projects.**


---

## 🎓 Learning Path for This Guide

**Read in this order:**

1. **Architecture Overview** - Understand component layers (above)
2. **Component Integration Patterns** - See how each component connects
3. **Security Through Component Design** - Understand why each layer exists
4. **Request-Response Examples** - See the full flow with real data
5. **Performance Considerations** - Learn optimization techniques

**For setup and running:** See [README.md](README.md)
**For API reference:** See [README.md](README.md)
**For migration details:** See inline comments in `alembic/env.py`

---

## 📚 File-by-File Technical Details

### app/models.py
Defines SQLAlchemy ORM models that map to database tables. Key design:
- **Inheritance from Base:** SQLAlchemy tracks all models and their metadata
- **Column types match PostgreSQL:** Integer→SERIAL, String→VARCHAR
- **Foreign keys create relationships:** `ForeignKey("users.id")` ensures referential integrity
- **ondelete="CASCADE":** PostgreSQL auto-deletes dependent records

### app/schemas.py
Pydantic models for validation. Key design:
- **NEVER include auto-generated fields in request schemas:** No id, created_at in PostCreate
- **ALWAYS include them in response schemas:** PostResponse has id and created_at
- **Separate create/update/response schemas:** Allows different validation rules for each
- **from_attributes = True:** Converts SQLAlchemy models to Pydantic models

### app/database.py
SQLAlchemy engine and session setup. Key design:
- **create_engine(url_object):** Creates connection pool, not individual connections
- **sessionmaker(autocommit=False, autoflush=False):** Explicit control over transactions
- **get_db() generator with yield:** Ensures cleanup via finally block
- **Session closed but connection reused:** Connection pooling for efficiency

### app/oauth2.py
JWT token generation and verification. Key design:
- **create_access_token:** HMAC-SHA256 signature only (not encrypted, payload readable)
- **Token expiration:** 30 minutes balances security vs UX
- **get_current_user:** Two-stage verification (JWT signature + database lookup)
- **Database lookup step:** Ensures user still exists, enables account deletion

### app/routers/post.py
Post CRUD endpoints. Key design:
- **Response model serialization:** PostResponse includes nested owner User object
- **Vote aggregation:** LEFT JOIN to include posts with 0 votes
- **Ownership check:** `query_post.owner_id != current_user.id` prevents unauthorized updates
- **Cascade behavior:** Deleting post auto-deletes votes due to FK constraint

### alembic/env.py
Database migration configuration. Key design:
- **url_object.render_as_string():** Handles special characters in passwords
- **replace('%', '%%'):** Escapes % for Alembic's interpolation parser
- **target_metadata = Base.metadata:** Auto-detects schema changes in models
- **upgrade()/downgrade():** Makes migrations reversible and debuggable

---

## Advanced Topics

### Async/Await in FastAPI

FastAPI handles only async I/O automatically. Database queries in SQLAlchemy are blocking:

```python
# This LOOKS async but database query is blocking
@app.get("/posts")
async def get_posts(db: Session = Depends(get_db)):
    return db.query(Post).all()  # ← Blocks entire thread!
```

For true async database queries, use:
- **AsyncSession** from SQLAlchemy 2.0
- **asyncpg** driver for PostgreSQL
- Requires refactoring to async context

In this project, we use standard SQLAlchemy because:
- Simpler for learning
- Uvicorn handles concurrency with multiple workers
- Connection pooling prevents bottlenecks

### Relationship Loading Strategies

```python
# 1. Lazy loading (N+1 query problem)
posts = db.query(Post).all()  # Query 1
for post in posts:
    print(post.owner.email)    # Queries 2, 3, 4...

# 2. Eager loading (single query)
from sqlalchemy.orm import joinedload
posts = db.query(Post).options(joinedload(Post.owner)).all()  # Single query with JOIN

# 3. Explicit join
posts = db.query(Post).join(User).all()  # Explicit control over join
```

Our project uses Option 1 (lazy loading) for simplicity. Production systems use Options 2-3.

### Transaction Isolation Levels

PostgreSQL isolation levels (set in engine):

```python
# SERIALIZABLE: Highest isolation, slowest (conflicts if concurrent transactions)
# REPEATABLE READ: Medium isolation and speed (default for PostgreSQL)
# READ COMMITTED: Lower isolation, faster (default for most databases)
# READ UNCOMMITTED: Lowest isolation, fastest

# This project uses default REPEATABLE READ
# For financial transactions, use SERIALIZABLE
```

### Batch Operations

```python
# Inefficient: One INSERT per post
for title in titles:
    post = Post(title=title, owner_id=1)
    db.add(post)
    db.commit()

# Efficient: Batch INSERT
posts = [Post(title=t, owner_id=1) for t in titles]
db.bulk_insert_mappings(Post, posts)
db.commit()
```

---
