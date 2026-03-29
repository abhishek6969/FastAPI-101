# ============ SQLALCHEMY ORM MODELS ============
# This module defines ORM (Object-Relational Mapping) model classes.
# ORM models bridge Python objects and database tables:
#   - Each class represents a database table
#   - Each class attribute represents a table column
#   - Instances of the class represent rows in the table
# 
# Benefits of ORM over Raw SQL:
#   1. Type-safe queries (Python compiler catches errors)
#   2. Automatic SQL generation (prevents SQL injection)
#   3. Relationship management (foreign keys, joins automatic)
#   4. Database-agnostic (same code works with PostgreSQL, MySQL, SQLite, etc.)
#   5. Better IDE support and autocomplete

from sqlalchemy import Column, Integer, String, Boolean , ForeignKey , text
from .database import Base
from sqlalchemy.sql.expression import func
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship



# ========== POST ORM MODEL CLASS ==========
# This class defines the structure of the 'posts' table in PostgreSQL.
# Inheritance from Base: Tells SQLAlchemy this class is a database model.
# When Base.metadata.create_all() is called, SQLAlchemy creates the 'posts' table based on this definition.
class Post(Base):
    # ========== TABLE NAME MAPPING ==========
    # __tablename__ tells SQLAlchemy which database table this class represents.
    # Value must match tha actual table name in PostgreSQL.
    # If not specified, SQLAlchemy defaults to lowercase class name ("post" → "posts" would require __tablename__)
    __tablename__ = "posts"

    # ========== COLUMN DEFINITIONS ==========
    # Each Column instance represents one database column.
    # Syntax: column_name = Column(type, optional_constraints...)
    
    # PRIMARY KEY COLUMN
    # Column(Integer, ...): Creates an integer column
    # primary_key=True: Marks this as PRIMARY KEY constraint
    #   - Ensures each row has unique id (database constraint)
    #   - Enables fast lookups by id
    #   - PostgreSQL auto-increments this by default (uses sequence)
    # index=True: Creates a database index on this column
    #   - Indexes speed up WHERE id = ? queries
    #   - Automatically created for primary keys, but explicit helps documentation
    # nullable=False: NOT NULL constraint - id must always have a value
    #   - Prevents NULL ids (which would violate PRIMARY KEY semantics)
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    
    # STRING COLUMN FOR POST TITLE
    # Column(String, ...): Creates a VARCHAR column (unlimited length by default in PostgreSQL)
    # index=True: Creates an index on title column
    #   - Speeds up WHERE title = ? or LIKE queries
    #   - Useful if you frequently filter posts by title
    # nullable=False: NOT NULL constraint - title must always be provided
    #   - Makes business sense: every post needs a title
    title = Column(String, index=True, nullable=False)
    
    # STRING COLUMN FOR POST CONTENT
    # Column(String, ...): Creates a VARCHAR column for storing post body/description
    # index=True: Creates an index on content column
    #   - Although content is often long, indexing supports LIKE searches
    #   - In production, might skip this if content is huge (indexes take storage)
    # nullable=False: NOT NULL constraint - content must be provided
    content = Column(String, index=True, nullable=False)
    
    # BOOLEAN COLUMN FOR PUBLISHED STATUS
    # Column(Boolean, ...): Creates a BOOLEAN column (TRUE or FALSE values only)
    # default=True: PostgreSQL DEFAULT constraint
    #   - When INSERT doesn't specify published value, defaults to TRUE
    #   - Example: If client only sends {title, content}, published automatically set to True
    # nullable=False: NOT NULL constraint
    #   - Ensures published column is always TRUE or FALSE, never NULL/missing
    published = Column(Boolean, server_default="TRUE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    owner = relationship("Users")
    

# ========== HOW SQLALCHEMY CREATES THE TABLE ==========
# In main.py, this code runs at app startup:
#   models.Base.metadata.create_all(bind=engine)
# 
# SQLAlchemy then executes SQL equivalent to:
#   CREATE TABLE IF NOT EXISTS posts (
#       id SERIAL PRIMARY KEY,
#       title VARCHAR NOT NULL,
#       content VARCHAR NOT NULL,
#       published BOOLEAN NOT NULL DEFAULT TRUE
#   );
#   CREATE INDEX idx_posts_title ON posts(title);
#   CREATE INDEX idx_posts_content ON posts(content);
#   CREATE INDEX idx_posts_id ON posts(id);  -- Primary key index
# 
# The CREATE TABLE IF NOT EXISTS clause means:
#   - If table already exists, do nothing
#   - If table doesn't exist, create it
#   - Safe to call multiple times (idempotent)


class Users(Base):
    """Users table - stores user account information
    
    This ORM model represents the 'users' table in PostgreSQL.
    Every user who registers gets a row in this table.
    """
    
    __tablename__ = "users"
    
    # PRIMARY KEY: Unique identifier for each user
    # SERIAL auto-increments: each new user gets next sequential ID (1, 2, 3, ...)
    # Constraints: NOT NULL, UNIQUE
    id = Column(Integer, primary_key=True, index=True, nullable=False)
    
    # EMAIL: Unique email address for login and communication
    # VARCHAR with UNIQUE constraint: only one account per email allowed
    # index=True: speeds up WHERE email = ? queries (login lookups)
    # nullable=False: every user MUST have an email
    email = Column(String, unique=True, index=True, nullable=False)
    
    # PASSWORD: Hashed password (NOT plaintext!)
    # Hashing algorithm: Argon2 (see utils.py for details)
    # Column(String, ...): stores the hash string (Argon2 hashes are ~90 characters)
    # nullable=False: every user MUST have a password
    # NOTE: This field is NEVER returned in responses (security best practice)
    password = Column(String, nullable=False)
    
    # CREATED_AT: Timestamp when user registered
    # TIMESTAMP(timezone=True): datetime with timezone support
    # server_default=func.now(): PostgreSQL NOW() function generates timestamp at INSERT time
    # Ensures consistent server-side timestamps (independent of client time)
    # nullable=False: always has a value
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    
    # PHONE_NUMBER: Optional user phone number
    # Column(String, nullable=True): allows NULL values (phone is optional)
    # server_default=text("NA"): if not provided, defaults to "NA" (Not Available)
    # Useful for future two-factor authentication or contact features
    phone_number = Column(String, nullable=True, server_default=text("NA"))
    

class Votes(Base):
    """Votes/Likes Junction Table - tracks which users like which posts
    
    This is a JUNCTION TABLE or ASSOCIATION TABLE:
    - Links many Users to many Posts (many-to-many relationship)
    - Records when a user votes/likes a post
    - Prevents duplicate votes (composite primary key constraint)
    
    Example data:
        post_id | user_id
        --------|--------
           1    |   5      # User 5 likes Post 1
           1    |   7      # User 7 likes Post 1
           3    |   5      # User 5 likes Post 3
    """
    
    __tablename__ = "votes"
    
    # FOREIGN KEY to posts table
    # post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    # 
    # Constraints:
    #   - ForeignKey("posts.id"): post_id MUST reference an existing post
    #   - ondelete="CASCADE": when post deleted, auto-delete all votes for that post
    #     (prevents orphaned votes pointing to non-existent posts)
    #   - primary_key=True: part of composite primary key (no duplicates allowed)
    #
    # Example: If a post is deleted, all votes for that post are automatically deleted.
    # This maintains referential integrity (no broken links).
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    
    # FOREIGN KEY to users table
    # user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    #
    # Constraints:
    #   - ForeignKey("users.id"): user_id MUST reference an existing user
    #   - ondelete="CASCADE": when user deleted, auto-delete all votes by that user
    #   - primary_key=True: part of composite primary key
    #
    # Example: If a user deletes their account, all their votes are automatically deleted.
    #
    # COMPOSITE PRIMARY KEY: (post_id, user_id)
    #   - Together guarantee uniqueness: One user can only vote once per post
    #   - Prevents duplicate vote records (database constraint)
    #   - Example: Inserting (post_id=1, user_id=5) twice would fail
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)