# ============ SQLALCHEMY DATABASE CONFIGURATION ============
# This module sets up SQLAlchemy ORM (Object-Relational Mapping) for PostgreSQL database connection.
# ORM allows Python objects to represent database tables, eliminating raw SQL in most cases.
# Benefits: Type safety, automatic query building, transaction management, and relationship handling.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from .config import settings


# ========== LEGACY APPROACH (NOT USED) ==========
# DATABASE_URL = "postgresql://postgres:postgreSunkale@1403@localhost/fastapi"
# This string-based URL approach has limitations. We use URL.create() for better security and flexibility.

# ========== CONNECTION URL CONFIGURATION ==========
# URL.create() constructs a database connection URL programmatically instead of as a hardcoded string.
# This approach is safer because:
#   1. Each parameter is explicitly named (more readable)
#   2. Avoids typos in connection strings (e.g., missing '@' or '://')
#   3. Easier to load credentials from environment variables for security
#   4. SQLAlchemy validates URL structure before attempting connection
# Result: "postgresql://postgres:postgreSunkale@1403@localhost/fastapi"
url_object = URL.create(
    drivername=settings.database_driver,      # Database driver: 'postgresql' tells SQLAlchemy to use psycopg2 adapter
    username=settings.database_username,          # PostgreSQL user account (should be moved to env variable in production)
    password=settings.database_password,  # User password (SECURITY: Never hardcode in production! Use environment variables)
    host=settings.database_hostname,              # Database server location (localhost = same machine, change for remote DB)
    database=settings.database_name ,            # Database name to connect to (schema for all tables)
    port=settings.database_port
)

# ========== DATABASE ENGINE CREATION ==========
# The engine is the core connection manager that:
#   1. Manages a connection pool (reuses DB connections instead of creating new ones each request)
#   2. Translates Python code into SQL queries specific to PostgreSQL
#   3. Handles type conversions (Python types ↔ SQL types)
#   4. Provides transaction management capabilities
# create_engine() does NOT immediately connect - it creates a lazy connection that connects when first used.
# Why lazy? Allows creating engine at app startup without failing if DB is temporarily down.
engine = create_engine(url_object)

# ========== SESSION FACTORY CONFIGURATION ==========
# sessionmaker() is a factory that creates new database sessions.
# A SESSION is a "conversation" with the database within a transaction context.
# Key Parameters:
#   - autocommit=False: Changes are NOT automatically saved. Must explicitly commit() for persistence.
#     (Safer because changes can be rolled back if an error occurs)
#   - autoflush=False: SQLAlchemy won't automatically push pending changes to DB before queries.
#     (Gives developer explicit control - must call session.flush() or commit())
#   - bind=engine: Connects this session factory to our PostgreSQL engine
# 
# How Sessions Work:
#   1. Each request creates a new session (separate database connection)
#   2. All queries and operations within that request use the same session
#   3. At request end, session is closed and connection returned to pool
#   4. This isolation prevents different requests from interfering with each session's data/transactions
sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ========== DECLARATIVE BASE FOR ORM MODELS ==========
# Base is the foundation class for all SQLAlchemy ORM models in this application.
# How Models Use Base:
#   1. Every model class (e.g., Post) inherits from Base
#   2. Base keeps a registry of all model classes defined
#   3. Base.metadata contains the table definitions for ALL models
#   4. Used later to auto-create tables: Base.metadata.create_all(bind=engine)
# 
# ORM Model Example (see models.py):
#   class Post(Base):
#       __tablename__ = "posts"
#       id = Column(Integer, primary_key=True)
#       title = Column(String)
#   This tells SQLAlchemy: Create a table 'posts' with columns 'id' and 'title'
Base = declarative_base()

# ========== DEPENDENCY INJECTION FUNCTION FOR FASTAPI ==========
# This function implements FastAPI's Depends() pattern for database session management.
# Purpose: Provide a fresh database session to each endpoint that needs one.
# 
# How FastAPI Dependency Injection Works:
#   1. When endpoint has parameter: db: Session = Depends(get_db)
#   2. FastAPI calls get_db() to get the session object
#   3. Endpoint function receives the session and can use it
#   4. After endpoint completes, FastAPI calls the finally block to clean up
# 
# Generator Pattern (yield vs return):
#   - Using 'yield' instead of 'return' creates a generator
#   - Code BEFORE yield: setup (create session)
#   - yield db: pause generator and provide session to endpoint
#   - Code AFTER yield: cleanup (close session)
#   - This ensures cleanup runs even if endpoint raises an exception
# 
# Example Usage in Endpoint:
#   @app.get("/posts")
#   def get_posts(db: Session = Depends(get_db)):
#       posts = db.query(Post).all()  # Use db session to query
#       return posts
def get_db():
    # ========== SESSION CREATION ==========
    # sessionlocal() creates a new database session for this request
    # Returns: Session object that can execute queries
    db = sessionlocal()
    try:
        # ========== YIELD PATTERN FOR DEPENDENCY INJECTION ==========
        # 'yield db' pauses this generator function and provides the session to the endpoint
        # FastAPI catches this yield value and passes it as the 'db' parameter
        # The function pauses here until the endpoint finishes executing
        yield db  # Provide this session to the endpoint function
    finally:
        # ========== CLEANUP GUARANTEE ==========
        # This 'finally' block ALWAYS runs, even if:
        #   - Endpoint raises an exception
        #   - Database query fails
        #   - Client closes connection mid-request
        # Purpose: Ensure session resources are released back to connection pool
        # db.close() closes the session but doesn't break the DB connection.
        # The connection is returned to the pool for reuse by next request.
        db.close()  # Ensure the database session is closed after the request completes (cleanup)