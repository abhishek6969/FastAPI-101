# ============ ALEMBIC MIGRATION CONFIGURATION ============
# Alembic is a database migration tool for SQLAlchemy.
# 
# What are Migrations?
#   - Scripts that describe database schema changes
#   - Allow version control of database structure
#   - Track evolution of database (add columns, change types, etc.)
#   - Enable rollback to previous schema versions
#   - Better than models.Base.metadata.create_all() for production
#
# Migration Files:
#   - Located in alembic/versions/
#   - Auto-numbered: 012f5ccde382_bring_db_in_sync.py, 5ad2da6c8b04_update_posts.py, etc.
#   - Each includes: upgrade() (apply change) and downgrade() (undo change)
#
# Workflow:
#   1. Make changes to SQLAlchemy models (models.py)
#   2. Run: alembic revision --autogenerate -m "description"
#      → Auto-generates migration file by comparing models to database
#   3. Review generated migration file
#   4. Run: alembic upgrade head
#      → Applies migration to database (updates schema)
#   5. Commit to version control
#
# Benefits over create_all():
#   - Tracks incremental changes (not just current state)
#   - Allows team collaboration (no merge conflicts)
#   - Reversible (can downgrade if issue found)
#   - Production-safe (applies one migration at a time)

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from app.database import url_object
from app.models import Base


# ========== ALEMBIC CONFIGURATION OBJECT ==========
# context.config provides access to the .ini file settings
config = context.config

# ========== DATABASE URL SETUP ==========
# PROBLEM: Passwords with special characters (e.g., '@', '#', '%') can break the connection URL.
# 
# SOLUTION: Encode password using render_as_string(hide_password=False)
#   - '@' in password becomes '%40' (URL encoding)
#   - '#' becomes '%23'
#   - '%' becomes '%25'
#
# ADDITIONAL PROBLEM: Alembic's config parser (reads .ini file) treats '%' as special
# for variable interpolation, so '%40' would be interpreted as a variable reference.
#
# FINAL SOLUTION: Escape '%' by doubling it: '%40' → '%%40'
# This tells Alembic: "This '%%' is a literal % character, not interpolation syntax"
#
# Examples:
#   Password: user@db.com#123
#   Encoded: user%40db.com%2523123
#   Final: user%%40db.com%%2523123
config.set_main_option(
    "sqlalchemy.url",
    url_object.render_as_string(hide_password=False).replace('%', '%%')
)

# ========== LOGGING SETUP ==========
# Configures Python logging based on .ini file
# Logs SQL statements if configured
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ========== TARGET METADATA ==========
# All SQLAlchemy models inherit from Base
# Base.metadata contains definitions of all tables
# Alembic uses this to:
#   1. Detect changes (autogenerate migrations)
#   2. Validate migration success
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (without database connection)
    
    Used when:
    - Database is not available during setup
    - Generating SQL scripts for later execution
    - Generating migration code for review
    
    Process:
    1. Read database URL from config
    2. Execute migration scripts
    3. Output SQL to stdin/file
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with active database connection)
    
    Used when:
    - Database is available
    - Running in production
    - Need to apply migrations live
    
    Process:
    1. Create database engine
    2. Connect to database
    3. Execute migration scripts
    4. Automatic commit on success (rollback on error)
    """
    # ========== CREATE DATABASE ENGINE ==========
    # Gets connection parameters from config
    # NullPool: Don't cache connections (better for CLI usage)
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # ========== CONNECT AND MIGRATE ==========
    with connectable.connect() as connection:
        # Configure migration context (provide connection and table metadata)
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        # Run all pending migrations in transaction
        # Automatic commit if successful, rollback if migration fails
        with context.begin_transaction():
            context.run_migrations()


# ========== DETERMINE EXECUTION MODE ==========
# context.is_offline_mode() checks configuration
# Calls appropriate function based on mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
