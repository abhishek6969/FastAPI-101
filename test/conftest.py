#Any fixture defined in conftest.py is automatically available to all test files in the same directory and subdirectories. This allows you to share common setup code, such as database connections or test clients, across multiple test files without needing to import them explicitly. In this case, the db_session and client fixtures defined in conftest.py can be used in any test file within the test directory, including test_users.py, without needing to import them.

# TestClient simulates HTTP requests directly to FastAPI app
# without a running server - all requests handled in-memory
# Ideal for unit/integration tests of route handlers and business logic

from fastapi.testclient import TestClient
from app.main import app
import pytest
from app import models
# SQLAlchemy ORM setup for PostgreSQL connection
# Maps Python objects to database tables, provides type safety & auto query building

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.engine.url import URL
from app.config import settings
from app.database import  get_db , Base
from app.oauth2 import create_access_token

# URL.create() is safer than string-based approach
# Explicitly names each parameter, prevents typos, loads env vars securely
url_object = URL.create(
    drivername=settings.database_driver,      # PostgreSQL driver
    username=settings.database_username,      # DB user
    password=settings.database_password,      # DB password
    host=settings.database_hostname,          # DB host
    database=f"{settings.database_name}_test",          # DB name
    port=5433              # DB port
)

# Engine manages connection pool, translates Python to SQL, handles transactions
# Uses lazy connection (doesn't connect until first use)
engine = create_engine(url_object)

# Creates database sessions for each request
# autocommit=False (explicit control), autoflush=False, bound to engine
test_sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all ORM models
# All models inherit from Base to be registered in metadata



@pytest.fixture()
def db_session():
  # Recreate test database tables before each test to ensure clean state
  # Yields session to test, then closes connection after test completes
  Base.metadata.drop_all(bind=engine)
  Base.metadata.create_all(bind=engine)
  db = test_sessionlocal()
  try:
      # Provide session to endpoint, pause until endpoint finishes
      yield db
  finally:
      # Always runs: close session and return connection to pool
      db.close()



@pytest.fixture()
def client(db_session):
  # Override FastAPI dependency to inject test database session
  # Returns TestClient that routes requests through our mocked database
  def override_get_db():
    try:
        yield db_session
    finally:
        pass
  app.dependency_overrides[get_db] = override_get_db # Override get_db dependency with our test session
  yield TestClient(app) # Provide TestClient instance to tests
  

@pytest.fixture
def create_test_user(client):
    # Creates test user via API endpoint and returns user data including password
    # Required by tests that need authenticated requests or user-owned resources
    user_data = {
    "email": "test_user@gmail.com",
    "password": "Abhishek@14"
    }
    response = client.post("/users/", json=user_data)
    new_user = response.json()
    print("Create test User Response status code:", response.status_code)
    print("Create test User Response JSON:", response.json())
    assert response.status_code == 200
    assert new_user["email"] == user_data["email"]
    new_user["password"] = user_data["password"]
    return new_user
  
@pytest.fixture
def create_test_user2(client):
    # Creates second test user for testing multi-user scenarios
    # Allows tests to verify user isolation and permission boundaries
    user_data = {
    "email": "test_user2@gmail.com",
    "password": "Abhishek@14"
    }
    response = client.post("/users/", json=user_data)
    new_user = response.json()
    print("Create test User Response status code:", response.status_code)
    print("Create test User Response JSON:", response.json())
    assert response.status_code == 200
    assert new_user["email"] == user_data["email"]
    new_user["password"] = user_data["password"]
    return new_user
  
  
@pytest.fixture
def token(create_test_user):
  # Generates JWT token for authenticated requests
  # Token contains user_id claim used by authorization middleware
  return create_access_token({"user_id": create_test_user["id"]})

@pytest.fixture
def authorized_client(client, token):
    # Extends client with Authorization header containing valid JWT token
    # Used to test protected endpoints that require authentication
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client
  
  
@pytest.fixture
def test_create_posts(db_session, create_test_user , create_test_user2):
    # Populates database with sample posts owned by different users
    # Enables testing of filtering, authorization, and multi-user scenarios
    post_data = [
      {
        "title": "Test Post 1 ",
        "content": "This is a test post number 1.",
        "owner_id": create_test_user["id"]
      },
      {
        "title": "Test Post 2",
        "content": "This is a test post number 2.",
        "owner_id": create_test_user["id"]
      },
      {
        "title": "Test Post 3",
        "content": "This is a test post number 3.",
        "owner_id": create_test_user["id"]
      },
      {
        "title": "Test Post 4",
        "content": "This is a test post number 4.",
        "owner_id": create_test_user2["id"]
      }
    ]

    db_session.add_all([models.Post(**post) for post in post_data])
    db_session.commit()
    
    posts = db_session.query(models.Post).all()
    assert db_session.query(models.Post).count() == len(post_data)
    return posts
