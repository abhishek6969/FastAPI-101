# FastAPI 101: Social Media API

A complete, production-ready REST API built with **FastAPI** to demonstrate core concepts for building modern web applications. This project serves as an educational reference for learning FastAPI fundamentals including authentication, database design, ORM, and API best practices.

**Status:** ✅ Complete | 🎓 Educational Project | 🔐 Production-Ready Architecture

---

## 🎯 Project Purpose

Learn FastAPI fundamentals by building a real-world social media platform with:
- User registration and authentication
- JWT token-based authorization
- Blog post creation, updates, and deletion
- Social voting/like system
- Database migrations and version control
- Comprehensive documentation and code comments

**Perfect for:** FastAPI beginners, backend developers learning modern Python web development, students studying REST API design.

---

## ✨ Key Features

### 🔐 Security
- **Password Hashing:** Argon2 (memory-hard, GPU-resistant algorithm)
- **JWT Authentication:** Stateless token-based auth with 30-minute expiration
- **Authorization:** Role-based access control (users can only modify their own posts)
- **CORS Support:** Configurable cross-origin requests
- **Environment Variables:** Sensitive data stored in `.env` file (not in code)

### 📊 Database
- **PostgreSQL:** Relational database with ACID transactions
- **SQLAlchemy ORM:** Python object-oriented database queries
- **Alembic Migrations:** Version control for database schema
- **Cascade Deletes:** Automatic cleanup of related records
- **Indexes:** Optimized queries for common lookups

### 📡 REST API
- **Auto Documentation:** Interactive Swagger UI at `/docs`
- **Pydantic Validation:** Automatic request/response validation
- **Dependency Injection:** Clean, testable endpoint handlers
- **Error Handling:** Consistent HTTP status codes
- **Pagination:** Query parameters for limiting and offset

### 🏗️ Architecture
- **Modular Design:** Organized routers by resource type
- **Separation of Concerns:** Models, schemas, router logic separated
- **Reusable Dependencies:** Authentication, database session
- **Configuration Management:** External settings via Pydantic

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Framework** | FastAPI | 0.135.1 |
| **Server** | Uvicorn (ASGI) | 0.31.1 |
| **Database** | PostgreSQL | 12+ |
| **ORM** | SQLAlchemy | 2.0.25 |
| **Authentication** | Python-jose + Argon2 | 3.5.0 + 25.1.0 |
| **Validation** | Pydantic | 2.12.5 |
| **Migrations** | Alembic | 1.18.4 |

---

## 📋 Prerequisites

- **Python:** 3.10+
- **PostgreSQL:** 12+ (installed and running)
- **pip:** Python package manager
- **Virtual Environment:** (recommended) `venv` or `conda`

---

## 🚀 Quick Start

### 1. Clone/Download Project
```bash
cd KodekloudProject
```

### 2. Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Database Credentials
Create `app/.env` file with your database credentials:
```ini
database_hostname=localhost
database_port=5432
database_username=postgres
database_password=your_password_here
database_name=fastapi_db
database_driver=postgresql
secret_key=your-random-secret-key-32-chars-or-more
algorithm=HS256
access_token_expire_minutes=30
```

**Security Tip:** Use `openssl rand -hex 32` to generate a secure `secret_key`.

### 5. Create PostgreSQL Database
```bash
# Using psql
psql -U postgres
CREATE DATABASE fastapi_db;
\q

# Or using createdb command
createdb -U postgres fastapi_db
```

### 6. Run Database Migrations
```bash
alembic upgrade head
```

### 7. Start the Server
```bash
uvicorn app.main:app --reload
```

Server running at: **http://localhost:8000**

---

## 📚 API Documentation

### Interactive Documentation
Once server is running, visit:
- **Swagger UI:** http://localhost:8000/docs (recommended)
- **ReDoc:** http://localhost:8000/redoc (alternative format)

### Authentication
Most endpoints require JWT token in the `Authorization` header:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Get token by logging in:
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### Core Endpoints

#### 👤 Users
```
POST   /users                 # Register new user
GET    /users/{id}            # Get user profile
```

#### 🔑 Authentication
```
POST   /login                 # Login, get JWT token
```

#### 📝 Posts
```
GET    /posts                 # List all posts (with search, pagination, vote count)
POST   /posts                 # Create new post (authenticated)
GET    /posts/{id}            # Get post with vote count (authenticated)
PUT    /posts/{id}            # Update post (owner only)
DELETE /posts/{id}            # Delete post (owner only)
```

#### ❤️ Votes/Likes
```
POST   /vote                  # Like/unlike a post (authenticated)
```

---

## 📂 Project Structure

```
KodekloudProject/
├── app/
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Settings & environment variables
│   ├── database.py             # SQLAlchemy setup & session management
│   ├── models.py               # ORM models (Post, Users, Votes)
│   ├── schemas.py              # Pydantic validation schemas
│   ├── oauth2.py               # JWT token generation & verification
│   ├── utils.py                # Helper functions (password hashing)
│   ├── .env                    # Environment variables (⚠️ don't commit)
│   └── routers/                # API endpoint handlers organized by resource
│       ├── auth.py             # Login endpoint
│       ├── user.py             # User registration & profile
│       ├── post.py             # Post CRUD operations
│       └── vote.py             # Vote/like endpoints
├── alembic/                    # Database migrations
│   ├── env.py                  # Migration configuration
│   ├── alembic.ini             # Alembic settings
│   └── versions/               # Migration history
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── FASTAPI_101_GUIDE.md        # Comprehensive learning guide
├── Models_Schemas.md           # ORM vs Pydantic explanation
├── OAuth2_JWT_Flow.md          # Authentication flow details
└── CORS.md                     # CORS configuration reference

```

---

## 🔐 Security Features Explained

### Password Security
Passwords are hashed using **Argon2** (OWASP recommended):
- Never stored in plaintext
- Salt added automatically
- Memory-hard algorithm resistant to GPU attacks
- See `app/utils.py` for implementation

### JWT Token Flow
1. User logs in with email + password
2. Server verifies credentials against hashed password
3. Server creates JWT token signed with `SECRET_KEY`
4. Client sends token in `Authorization: Bearer <token>` header
5. On protected endpoints, server verifies token signature
6. Token expires after 30 minutes (configurable)

### Database Constraints
- Primary keys ensure unique row identification
- Foreign keys maintain relationship integrity
- Composite keys prevent duplicate votes
- `ON DELETE CASCADE` automatically cleans up related records

---

## 🗄️ Database Schema

### Users Table
Stores user account information:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password VARCHAR NOT NULL,          -- Argon2 hashed password
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    phone_number VARCHAR DEFAULT 'NA'
);
```

### Posts Table
Stores blog posts/content:
```sql
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content VARCHAR NOT NULL,
    published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
);
```

### Votes Table
Junction table for likes/votes (many-to-many relationship):
```sql
CREATE TABLE votes (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, user_id)     -- One vote per user per post
);
```

---

## 💻 Example Usage

### 1. Register a User
```bash
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "securePassword123"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john@example.com&password=securePassword123"

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

### 3. Create a Post
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X POST http://localhost:8000/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello FastAPI world!",
    "published": true
  }'
```

### 4. Get All Posts
```bash
curl -X GET http://localhost:8000/posts?limit=10&skip=0&search=fastapi \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Like a Post
```bash
curl -X POST http://localhost:8000/vote \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "dir": 1
  }'
```

---

## 🔧 Database Migrations

Alembic manages database schema changes:

### Check Migration Status
```bash
alembic current
```

### Create New Migration
After modifying `models.py`:
```bash
alembic revision --autogenerate -m "add phone_number to users"
```

### Apply Migrations
```bash
alembic upgrade head
```

### Rollback One Migration
```bash
alembic downgrade -1
```

See `alembic/versions/` for migration history.

---

## � Learning Resources

### Documentation Files
- **[FASTAPI_101_GUIDE.md](FASTAPI_101_GUIDE.md)** ⭐ **START HERE FOR DEEP LEARNING**
  - Component integration patterns (Models ↔ Schemas ↔ Database)
  - How Alembic migrations maintain schema integrity
  - JWT authentication flow through multiple layers
  - Request-response examples with data transformations
  - Performance considerations and optimization
  - Advanced topics (async, relationships, transactions)

- **[Models_Schemas.md](Models_Schemas.md)** - Difference between ORM models and Pydantic schemas
- **[OAuth2_JWT_Flow.md](OAuth2_JWT_Flow.md)** - Detailed authentication flow
- **[CORS.md](CORS.md)** - Cross-origin configuration

### Official Documentation
- [FastAPI Official Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM Guide](https://docs.sqlalchemy.org/)
- [Pydantic Validation](https://docs.pydantic.dev/)
- [JWT Explained](https://jwt.io/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)

---

## � How Components Work Together

This project demonstrates how different architectural layers integrate. Here's what you'll learn:

### Models ↔ Schemas ↔ Database
- SQLAlchemy ORM models define table structure
- Pydantic schemas validate input/output
- Database stores persistent data
- **See:** [FASTAPI_101_GUIDE.md - Component Integration Patterns](FASTAPI_101_GUIDE.md#-component-integration-patterns)

### Alembic ↔ Models ↔ Database
- Modify models → Auto-generate migrations → Apply to database
- Maintains schema version history for team collaboration
- **See:** [FASTAPI_101_GUIDE.md - Alembic Models Database](FASTAPI_101_GUIDE.md#2-alembic--models--database-schema)

### OAuth2 ↔ JWT ↔ Database
- Login creates JWT token
- Client sends token in headers
- Server verifies token and loads user from database
- **See:** [FASTAPI_101_GUIDE.md - OAuth2 JWT Tokens Database Authentication](FASTAPI_101_GUIDE.md#3-oauth2--jwt-tokens--database-authentication)

### Dependency Injection ↔ Session Management
- Each request gets its own database session
- Dependencies automatically resolved and injected
- Session cleaned up after request completes
- **See:** [FASTAPI_101_GUIDE.md - Dependency Injection Session Management](FASTAPI_101_GUIDE.md#4-dependency-injection--session-management)

---

### **Issue: "database fastapi_db does not exist"**
**Solution:** Create the database first
```bash
createdb -U postgres fastapi_db
```

### **Issue: "can't connect to PostgreSQL"**
**Solution:** Check `.env` file has correct credentials and PostgreSQL is running
```bash
# Test connection
psql -U postgres -h localhost -d fastapi_db
```

### **Issue: "ModuleNotFoundError: No module named 'fastapi'"**
**Solution:** Install dependencies and activate virtual environment
```bash
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### **Issue: "JWT token expired"**
**Solution:** Login again to get a new token. Tokens expire after 30 minutes (configurable in `.env`)

### **Issue: "403 Forbidden - Not authorized"**
**Solution:** Make sure you own the post you're trying to update/delete. Users can only modify their own posts.

---

## 📝 Development Tips

### Run Tests
```bash
# Install pytest
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run with verbose output
pytest -v
```

### Format Code
```bash
# Install black
pip install black

# Format all Python files
black app/
```

### Check Code Quality
```bash
# Install pylint
pip install pylint

# Check file
pylint app/main.py
```

### View Database Directly
```bash
psql -U postgres -d fastapi_db

# Common queries
\dt                    # List tables
SELECT * FROM users;   # View users
\q                     # Quit
```

---

## 🎓 Learning Path

**New to FastAPI?** Follow this path:

1. **Start Here:** This README for project overview and setup
2. **Run the Project:** Follow Quick Start to get everything working
3. **Explore the API:** Visit `/docs` and test endpoints
4. **Deep Dive:** Read [FASTAPI_101_GUIDE.md](FASTAPI_101_GUIDE.md) for technical architecture
5. **Component Interactions:** Understand how Models, Schemas, Alembic, and OAuth2 work together
6. **Code Review:** Read individual files starting with `app/main.py`
7. **Practice:** Modify code and add new features
8. **Deployment:** Review production checklist

---

## 📊 API Response Examples

### Successful Post Creation (201 Created)
```json
{
  "id": 1,
  "title": "My First Post",
  "content": "Hello world!",
  "published": true,
  "created_at": "2024-01-15T10:30:45.123456",
  "owner_id": 1,
  "owner": {
    "id": 1,
    "email": "user@example.com",
    "created_at": "2024-01-15T10:00:00.000000"
  }
}
```

### List Posts with Vote Count (200 OK)
```json
[
  {
    "Post": {
      "id": 1,
      "title": "First Post",
      "content": "Content here...",
      "published": true,
      "created_at": "2024-01-15T10:30:45.123456",
      "owner_id": 1,
      "owner": {...}
    },
    "votes": 5
  }
]
```

### Authentication Error (401 Unauthorized)
```json
{
  "detail": "Could not validate credentials"
}
```

### Not Found Error (404)
```json
{
  "detail": "Post with id: 999 was not found"
}
```

---

## 🌐 Deployment Considerations

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `database_password` in environment variables (not `.env`)
- [ ] Enable HTTPS (SSL/TLS certificates)
- [ ] Update CORS origins to specific domain (not "*")
- [ ] Add rate limiting to prevent abuse
- [ ] Implement logging for monitoring
- [ ] Add API key authentication for additional security
- [ ] Setup database backups
- [ ] Consider read replicas for scaling
- [ ] Use environment-specific configurations (dev/staging/prod)

See `FASTAPI_101_GUIDE.md` production checklist for more details.

---

## 📄 License

This educational project is provided as-is for learning purposes.

---

## 🤝 Contributing

This is an educational project. Feel free to:
- Fork and modify for learning
- Add more features (comments, followers, notifications)
- Improve code organization
- Enhance documentation
- Add test cases

---

## ❓ FAQ

**Q: Can I use this in production?**
A: The architecture is production-ready, but you should add logging, monitoring, rate limiting, and comprehensive testing before deploying.

**Q: How do I add more features?**
A: Add new models in `models.py`, create migrations with Alembic, add validation schemas in `schemas.py`, and create route handlers in `routers/`.

**Q: How do I change password hashing algorithm?**
A: Edit `app/utils.py`. New passwords will use the new algorithm; old ones still work due to `deprecated="auto"` setting.

**Q: Can I use SQLite instead of PostgreSQL?**
A: Yes, change database driver in `.env` to `sqlite` and update connection string. However, PostgreSQL is recommended for production.

**Q: How do I add refresh tokens?**
A: Implement a separate refresh token endpoint that issues long-lived tokens to get new short-lived access tokens.

---

## 📞 Support

For questions or issues:
1. Check the documentation files (`FASTAPI_101_GUIDE.md`, etc.)
2. Review code comments for detailed explanations
3. Check FastAPI official documentation
4. Consult SQLAlchemy and Pydantic docs for specific topics

---

**Happy Learning! 🚀**

Start with `/docs` endpoint after running the server to explore the API interactively.
