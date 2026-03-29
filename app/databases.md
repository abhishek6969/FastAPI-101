# SQL Database Fundamentals & Guide
## For FastAPI Projects & Basic SysAdmin Operations

---

## Table of Contents

1. [SQL Basics & Database Concepts](#1-sql-basics--database-concepts)
2. [Data Types & Table Design](#2-data-types--table-design)
3. [CRUD Operations](#3-crud-operations)
4. [Intermediate Topics](#4-intermediate-topics)
5. [Basic SysAdmin Operations](#5-basic-sysadmin-operations)
6. [FastAPI Database Integration](#6-fastapi-database-integration)
7. [Best Practices for Your Project](#7-best-practices-for-your-project)

---

## 1. SQL Basics & Database Concepts

### What is a Database?

- A structured collection of organized data
- SQL (Structured Query Language) is the standard language for relational DBs
- Common DBs: PostgreSQL, MySQL, SQLite, SQL Server, Oracle
- For your FastAPI project: SQLAlchemy ORM handles SQL operations

### Key Concepts

- **Table**: Collection of rows and columns (like a spreadsheet)
- **Row**: A single record
- **Column**: A field in the table
- **Primary Key (PK)**: Unique identifier for each row
- **Foreign Key (FK)**: Reference to a row in another table

### Example Table Structure

```
┌─────────────────────────────────────┐
│ users                               │
├─────────────────────────────────────┤
│ id (PK)  │ name      │ email        │
├─────────────────────────────────────┤
│ 1        │ John Doe  │ john@ex.com  │
│ 2        │ Jane Smith│ jane@ex.com  │
└─────────────────────────────────────┘
```

---

## 2. Data Types & Table Design

### Common SQL Data Types

| Data Type | Description |
|-----------|-------------|
| `INT` / `INTEGER` | Whole numbers (-2147483648 to 2147483647) |
| `BIGINT` | Large whole numbers (for large IDs, timestamps) |
| `VARCHAR(n)` | Variable-length text (n characters max) |
| `TEXT` | Long text without length limit |
| `BOOLEAN` | True/False values |
| `DATE` | Calendar dates (YYYY-MM-DD) |
| `DATETIME` / `TIMESTAMP` | Date and time (YYYY-MM-DD HH:MM:SS) |
| `DECIMAL(p, s)` | Fixed-point numbers (money, precise values) |
| `FLOAT` / `DOUBLE` | Floating-point numbers (approximate, scientific data) |

### Creating a Table Example
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### Key Constraints

- **PRIMARY KEY**: Uniquely identifies each row
- **NOT NULL**: Column must have a value
- **UNIQUE**: Values in column must be unique
- **DEFAULT**: Set default value if none provided
- **FOREIGN KEY**: Reference another table

### Multi-Table Example (with relationships)
```sql
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT DEFAULT 1,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

---

## 3. CRUD Operations

### CREATE (INSERT)

#### Insert single row
```sql
INSERT INTO users (username, email, password_hash)
VALUES ('john_doe', 'john@example.com', 'hashed_password_123');
```

#### Insert multiple rows
```sql
INSERT INTO users (username, email, password_hash)
VALUES 
    ('alice', 'alice@example.com', 'hash1'),
    ('bob', 'bob@example.com', 'hash2'),
    ('charlie', 'charlie@example.com', 'hash3');
```

### READ (SELECT)

#### Get all records
```sql
SELECT * FROM users;
```

#### Get specific columns
```sql
SELECT username, email FROM users;
```

#### With conditions (WHERE)
```sql
SELECT * FROM users WHERE is_active = TRUE;
SELECT * FROM users WHERE username = 'john_doe';
SELECT * FROM orders WHERE quantity > 5;
```

#### Filtering with comparison operators
```sql
WHERE price > 100          -- Greater than
WHERE price < 50           -- Less than
WHERE price >= 100         -- Greater than or equal
WHERE created_at <= '2024-01-01'  -- Date comparison
WHERE username LIKE 'john%'  -- Pattern matching (% = any chars)
```

#### Combining conditions
```sql
SELECT * FROM users 
WHERE is_active = TRUE AND email LIKE '%@gmail.com';

SELECT * FROM products 
WHERE price > 50 OR quantity < 10;
```

#### Ordering and Limiting
```sql
SELECT * FROM users ORDER BY created_at DESC;  -- DESC = descending
SELECT * FROM products ORDER BY price ASC LIMIT 10;  -- ASC = ascending
```

### UPDATE
```sql
UPDATE users SET is_active = FALSE WHERE id = 5;

UPDATE products 
SET price = price * 1.1, updated_at = CURRENT_TIMESTAMP 
WHERE category = 'electronics';
```

### DELETE
```sql
DELETE FROM orders WHERE order_date < '2020-01-01';
DELETE FROM users WHERE id = 100;
```

⚠️ **Warning**: Always use WHERE clause! DELETE without WHERE deletes everything!

---

## 4. Intermediate Topics

### JOINS

Combine data from multiple tables.

#### INNER JOIN

Only matching rows in both tables
```sql
SELECT u.username, o.id, o.quantity
FROM users u
INNER JOIN orders o ON u.id = o.user_id
WHERE u.is_active = TRUE;
```

#### LEFT JOIN

All rows from left table + matching from right
```sql
SELECT u.username, COUNT(o.id) as total_orders
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id
ORDER BY total_orders DESC;
```

#### Multiple Tables (3+ JOINs)
```sql
SELECT 
    u.username,
    p.name as product_name,
    o.quantity,
    o.order_date
FROM users u
INNER JOIN orders o ON u.id = o.user_id
INNER JOIN products p ON o.product_id = p.id
WHERE o.order_date >= '2024-01-01'
ORDER BY o.order_date DESC;
```

### AGGREGATION

Functions that combine multiple rows.

#### COUNT

Count rows
```sql
SELECT COUNT(*) as total_users FROM users;
SELECT COUNT(DISTINCT user_id) as unique_customers FROM orders;
```

#### SUM

Add values
```sql
SELECT SUM(quantity) as total_items_sold FROM orders;
SELECT SUM(price * quantity) as total_revenue FROM order_items;
```

#### AVG

Average value
```sql
SELECT AVG(price) as average_price FROM products;
```

#### MIN/MAX

Minimum/Maximum
```sql
SELECT MIN(price) as cheapest, MAX(price) as most_expensive FROM products;
```

#### GROUP BY

Group rows and apply aggregation
```sql
SELECT 
    user_id, 
    COUNT(*) as order_count,
    SUM(quantity) as total_items
FROM orders
GROUP BY user_id
HAVING COUNT(*) > 1  -- Only users with more than 1 order
ORDER BY order_count DESC;
```

### SUBQUERIES

Query within a query (useful but don't overuse).
```sql
-- Find users who made orders above average order value
SELECT username FROM users
WHERE id IN (
    SELECT user_id FROM orders 
    WHERE quantity > (SELECT AVG(quantity) FROM orders)
);
```

#### Common subquery pattern
```sql
SELECT * FROM products
WHERE price > (SELECT AVG(price) FROM products);
```

### DISTINCT

Remove duplicate values
```sql
SELECT DISTINCT user_id FROM orders;
SELECT DISTINCT category FROM products;
```

### CASE Statements

Conditional logic in SQL
```sql
SELECT 
    username,
    CASE 
        WHEN created_at > DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'New User'
        WHEN created_at > DATE_SUB(NOW(), INTERVAL 365 DAY) THEN 'Active User'
        ELSE 'Legacy User'
    END as user_type
FROM users;
```

---

## 5. Basic SysAdmin Operations

### Database Connection

#### PostgreSQL (most common for FastAPI)
```bash
psql -U username -d database_name -h localhost
psql -U postgres -d myapp_db -h 127.0.0.1 -p 5432
```

#### MySQL
```bash
mysql -u username -p database_name -h localhost
mysql -u root -p myapp_db
```

### Checking Database Status

#### PostgreSQL
```sql
-- List all databases
\l

-- Connect to database
\c database_name

-- List tables
\dt

-- Show table structure
\d table_name

-- Show table size
SELECT pg_size_pretty(pg_total_relation_size('table_name'));
```

### Creating & Dropping Databases
```sql
CREATE DATABASE myapp_db;
DROP DATABASE myapp_db;  -- Deletes everything!
```

### User Management

#### PostgreSQL
```sql
-- Create user
CREATE USER app_user WITH PASSWORD 'secure_password_123';

-- Grant permissions
GRANT CONNECT ON DATABASE myapp_db TO app_user;
GRANT USAGE ON SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_user;

-- Change password
ALTER USER app_user WITH PASSWORD 'new_password';

-- Drop user
DROP USER app_user;
```

### Backups

#### PostgreSQL backup (dump)
```bash
# Backup single database
pg_dump -U username -d database_name > backup.sql

# Backup all databases
pg_dumpall -U postgres > all_databases_backup.sql

# Restore from backup
psql -U username -d database_name < backup.sql
```

#### MySQL backup
```bash
mysqldump -u root -p database_name > backup.sql
mysql -u root -p database_name < backup.sql
```

### Performance Basics

#### Analyze query performance
```sql
-- PostgreSQL: Show query plan
EXPLAIN ANALYZE SELECT * FROM users WHERE id = 1;

-- See slow queries
\timing  -- Turn on timing
SELECT * FROM large_table WHERE condition;
```

#### Adding indexes for faster queries
```sql
-- Create index (faster lookups on this column)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- List indexes
\di  -- PostgreSQL
SHOW INDEXES FROM table_name;  -- MySQL
```

#### Monitoring disk space
```bash
# Check database size (PostgreSQL)
du -sh /var/lib/postgresql/data/

# Check table sizes
SELECT 
    table_name, 
    pg_size_pretty(pg_total_relation_size(table_name))
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY pg_total_relation_size(table_name) DESC;
```

#### Regular Maintenance
```sql
-- PostgreSQL: Analyze tables (for query optimizer)
ANALYZE users;
ANALYZE;  -- Analyze all tables

-- PostgreSQL: Vacuum (clean up deleted rows)
VACUUM;
```

---

## 6. FastAPI Database Integration

### Using SQLAlchemy ORM (Python)

#### Basic Model Definition
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

#### Database URL Connection
```python
# PostgreSQL
DATABASE_URL = "postgresql://username:password@localhost:5432/myapp_db"

# SQLite (development)
DATABASE_URL = "sqlite:///./test.db"

# MySQL
DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/myapp_db"
```

#### Query Examples in FastAPI
```python
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends

app = FastAPI()

# Get all users
def get_users(db: Session):
    return db.query(User).all()

# Get user by ID
def get_user_by_id(user_id: int, db: Session):
    return db.query(User).filter(User.id == user_id).first()

# Create user
def create_user(username: str, email: str, password_hash: str, db: Session):
    user = User(username=username, email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Update user
def update_user(user_id: int, is_active: bool, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    user.is_active = is_active
    db.commit()
    return user

# Delete user
def delete_user(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id).first()
    db.delete(user)
    db.commit()
```

---

## 7. Best Practices for Your Project

### Design Principles
✓ Normalize your database (avoid data duplication)
✓ Use appropriate data types (not everything as TEXT)
✓ Add indexes on columns you frequently search/filter by
✓ Always use foreign keys to maintain relationships
✓ Use NOT NULL constraints where values are required
✓ Set defaults for columns that usually have same values

### Connection Management
✓ Use connection pooling (SQLAlchemy handles this)
✓ Close connections properly (FastAPI dependency injection does this)
✓ Use transactions for multi-step operations
✓ Handle connection timeouts gracefully

### Security
✓ NEVER concatenate strings into SQL queries (SQL injection risk!)
✓ Always use parameterized queries/ORM
✓ Hash passwords, never store plain text
✓ Use strong passwords for DB users
✓ Restrict user permissions to minimum needed
✓ Backup regularly and test recovery procedures

### Performance
✓ Add indexes for frequently searched columns
✓ Use LIMIT for large result sets
✓ Avoid SELECT * in production code
✓ Monitor query performance with EXPLAIN
✓ Use pagination for large datasets
✓ Archive old data periodically (don't let tables grow infinitely)

### Development Workflow
✓ Start with SQLite for local development (no setup needed)
✓ Use PostgreSQL for production (more features, better scaling)
✓ Write migrations when schema changes (Alembic library)
✓ Keep backups before major schema changes
✓ Document your schema and relationships
✓ Use version control for SQL scripts

### Example Production Setup
```
Development: SQLite (local file)
Staging: PostgreSQL (separate instance)
Production: PostgreSQL (managed service or robust VM)
Backups: Daily automated backups to S3/cloud storage
Monitoring: Check disk space, query performance, connection counts
```

---

## Quick Reference Cheat Sheet

### Basic Commands

- `CREATE DATABASE db_name;`
- `CREATE TABLE table_name (...columns...);`
- `INSERT INTO table VALUES (...);`
- `SELECT * FROM table WHERE condition;`
- `UPDATE table SET column = value WHERE id = x;`
- `DELETE FROM table WHERE condition;`

### JOINs

- **INNER JOIN**: Matching rows only
- **LEFT JOIN**: All left rows + matching right
- **RIGHT JOIN**: All right rows + matching left
- **CROSS JOIN**: All combinations

### Aggregate Functions

- `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`
- **GROUP BY**: Group rows
- **HAVING**: Filter grouped results
- **ORDER BY**: Sort results

### Operators

- `=`, `!=`, `<`, `>`, `<=`, `>=`
- `AND`, `OR`, `NOT`
- `IN`, `BETWEEN`, `LIKE`
- `IS NULL`, `IS NOT NULL`

---

