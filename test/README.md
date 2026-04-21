# Testing Guide: Pytest Fundamentals & Fixtures

## Overview

This test suite uses **pytest** to verify the FastAPI application's endpoints, authentication, database operations, and business logic. Tests are organized by feature (users, posts, votes) and use fixtures for reusable setup code.

---

## Pytest Fundamentals

### What is Pytest?

Pytest is a Python testing framework that:
- **Discovers tests** automatically from files matching `test_*.py` or `*_test.py`
- **Runs tests** in functions starting with `test_`
- **Provides assertions** with clear failure messages
- **Supports fixtures** for setup/teardown and dependency injection
- **Allows parametrization** to run tests with multiple input values

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_users.py

# Run with verbose output
pytest -v

# Run and show print statements (debugging)
pytest -s

# Run single test function
pytest test/test_users.py::test_create_user

# Run tests matching a pattern
pytest -k "login"
```

### Test Discovery

Pytest automatically finds and runs:
- **Files**: `test_*.py` or `*_test.py`
- **Functions**: `test_*` prefix (e.g., `test_create_user()`)
- **Classes**: `Test*` prefix with `test_*` methods (not used in this suite)

---

## Fixtures Explained

### What is a Fixture?

A **fixture** is a reusable piece of setup code that:
1. **Runs before** each test (or once per session)
2. **Provides data** to tests via parameters
3. **Handles cleanup** automatically via teardown code
4. **Eliminates duplication** across test files

### Fixture Declaration

```python
@pytest.fixture
def my_fixture():
    # Setup
    data = prepare_data()
    
    # Yield value to test
    yield data
    
    # Cleanup (optional)
    cleanup()
```

The `@pytest.fixture` decorator registers the function as a fixture. Tests receive the fixture by including its name as a parameter.

### Fixture Scope

Fixtures can run at different scopes:

| Scope | Behavior | Use Case |
|-------|----------|----------|
| `function` | New instance per test (default) | Most tests; fresh state needed |
| `class` | One instance per test class | Class-based tests |
| `module` | One instance per file | Expensive setup (DB connection) |
| `session` | One instance for entire test run | Global config |

Example with scope:
```python
@pytest.fixture(scope="session")
def expensive_resource():
    return ExpensiveSetup()  # Runs once for all tests
```

---

## Fixtures in This Project

### Database & Client Fixtures (conftest.py)

#### `db_session` - Clean Database

```python
@pytest.fixture()
def db_session():
    Base.metadata.drop_all(bind=engine)  # Delete all tables
    Base.metadata.create_all(bind=engine) # Recreate tables
    db = test_sessionlocal()
    try:
        yield db  # Provide to test
    finally:
        db.close()  # Cleanup
```

**Purpose**: Each test gets a fresh, empty database to ensure tests don't interfere with each other.

**Used by**: Almost all tests (indirectly through other fixtures)

---

#### `client` - Test Client with Database Override

```python
@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session  # Inject test database into endpoints
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
```

**Purpose**: 
- Creates `TestClient` that simulates HTTP requests without running server
- Overrides FastAPI's `get_db` dependency to use test database
- Allows tests to make API calls and verify responses

**Why `TestClient`?**
- No network overhead
- No running server needed
- Full control over database state
- Cleaner test execution

**Used by**: All endpoint tests

---

#### `create_test_user` - Test User Creation

```python
@pytest.fixture
def create_test_user(client):
    user_data = {
        "email": "test_user@gmail.com",
        "password": "Abhishek@14"
    }
    response = client.post("/users/", json=user_data)
    new_user = response.json()
    new_user["password"] = user_data["password"]  # Add password for login tests
    return new_user
```

**Purpose**: 
- Creates a user via POST /users/ endpoint
- Returns user dict with password for authentication tests
- Demonstrates fixture chaining (`client` → `create_test_user`)

**Used by**: Login tests, post creation tests, vote tests

---

#### `create_test_user2` - Second Test User

Same as `create_test_user` but different email. Allows testing multi-user scenarios like:
- User isolation
- Permission boundaries
- Filtering by owner

**Used by**: Post filtering tests, vote tests

---

#### `token` - JWT Token Generation

```python
@pytest.fixture
def token(create_test_user):
    return create_access_token({"user_id": create_test_user["id"]})
```

**Purpose**: 
- Generates valid JWT token for authenticated requests
- Contains `user_id` claim required by authorization middleware
- Depends on `create_test_user` to have a user

**Used by**: `authorized_client` fixture

---

#### `authorized_client` - Authenticated Client

```python
@pytest.fixture
def authorized_client(client, token):
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {token}"
    }
    return client
```

**Purpose**:
- Extends `client` with Authorization header containing valid JWT token
- Simulates authenticated user making requests
- Tests protected endpoints that require authentication

**Example usage**:
```python
def test_create_post(authorized_client, create_test_user):
    response = authorized_client.post("/posts/", json=post_data)
    # Request includes: Authorization: Bearer <valid_token>
```

---

#### `test_create_posts` - Sample Data Population

```python
@pytest.fixture
def test_create_posts(db_session, create_test_user, create_test_user2):
    post_data = [
        {"title": "Post 1", "content": "...", "owner_id": create_test_user["id"]},
        {"title": "Post 2", "content": "...", "owner_id": create_test_user["id"]},
        {"title": "Post 3", "content": "...", "owner_id": create_test_user["id"]},
        {"title": "Post 4", "content": "...", "owner_id": create_test_user2["id"]},
    ]
    
    db_session.add_all([models.Post(**post) for post in post_data])
    db_session.commit()
    return db_session.query(models.Post).all()
```

**Purpose**:
- Populates database with test posts
- Creates posts owned by different users
- Enables testing filtering, authorization, list endpoints

**Dependencies**: Requires `create_test_user` and `create_test_user2` to exist first

**Used by**: Post retrieval tests, vote tests

---

#### `create_test_post_with_vote` - Vote Test Data

```python
@pytest.fixture
def create_test_post_with_vote(db_session, create_test_user, test_create_posts):
    post_id = test_create_posts[3].id
    db_session.add(models.Votes(post_id=post_id, user_id=create_test_user["id"]))
    db_session.commit()
    return {"post_id": post_id, "dir": 1}
```

**Purpose**:
- Creates a pre-existing vote in database
- Used to test duplicate vote detection
- Used to test vote removal

---

## Fixture Dependency Chain

Fixtures can depend on other fixtures, creating a dependency chain:

```
conftest.py
├── db_session (database setup)
├── client (depends on: db_session)
├── create_test_user (depends on: client)
├── create_test_user2 (depends on: client)
├── token (depends on: create_test_user)
├── authorized_client (depends on: client, token)
├── test_create_posts (depends on: db_session, create_test_user, create_test_user2)
└── create_test_post_with_vote (depends on: db_session, create_test_user, test_create_posts)
```

When a test requests `authorized_client`:
1. pytest sees it depends on `client` and `token`
2. `token` depends on `create_test_user`
3. `create_test_user` depends on `client`
4. `client` depends on `db_session`
5. pytest resolves entire chain and runs fixtures in order:
   - `db_session()` → clean database
   - `client(db_session)` → create client
   - `create_test_user(client)` → create user
   - `token(create_test_user)` → generate token
   - `authorized_client(client, token)` → add auth header

---

## Parametrization

### What is Parametrization?

**Parametrization** runs the same test multiple times with different input values:

```python
@pytest.mark.parametrize("input_value, expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_multiply(input_value, expected):
    assert input_value * 2 == expected
```

This runs 3 tests:
- `test_multiply[1-2]`: 1 × 2 = 2 ✓
- `test_multiply[2-4]`: 2 × 2 = 4 ✓
- `test_multiply[3-6]`: 3 × 2 = 6 ✓

### Usage in This Suite

**test_users.py**:
```python
@pytest.mark.parametrize("email,password,expected_status", [
    ("test1_user@gmail.com", "Abhishek@14", 403),  # Non-existent user
    ("test_user@gmail.com", "wrongpassword", 403), # Wrong password
    (None, "Abhishek@14", 422),                     # Missing email
    ("test_user@gmail.com", None, 422),             # Missing password
])
def test_incorrect_login(client, email, password, expected_status):
    # Test runs 4 times with different credentials
```

**Benefits**:
- Reduce code duplication
- Test multiple scenarios with same logic
- Clear test IDs showing what failed: `test_incorrect_login[test1_user@gmail.com-Abhishek@14-403]`

---

## Test Organization

### By Feature

Tests are organized in separate files:
- **test_users.py**: User creation, login, authentication
- **test_posts.py**: Post CRUD, filtering, authorization
- **test_votes.py**: Vote creation, removal, constraints

### Naming Convention

Test function names describe what they test:
- `test_create_user` - Test user creation
- `test_unauthorized_get_all_posts` - Test unauthenticated post listing
- `test_vote_again_on_same_post` - Test duplicate vote rejection

Pattern: `test_<action>_<scenario>`

---

## Common Testing Patterns

### 1. Happy Path (Success Case)

```python
def test_create_user(client):
    response = client.post("/users/", json={
        "email": "new@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
```

**What to verify**:
- Correct HTTP status code (200, 201, etc.)
- Response contains expected fields
- Field values match input or business logic

### 2. Unhappy Path (Error Cases)

```python
def test_unauthorized_access(client):
    response = client.get("/posts/1")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
```

**What to verify**:
- Correct error status code (401, 403, 404, 422, etc.)
- Error message is informative

### 3. Authorization Tests

```python
def test_user_cannot_delete_other_posts(authorized_client, create_test_user2):
    # authorized_client is logged in as create_test_user
    post_owned_by_user2 = ...
    response = authorized_client.delete(f"/posts/{post_owned_by_user2.id}")
    assert response.status_code == 403  # Forbidden
```

**What to verify**:
- Users can't access other users' data
- Proper permission checks exist

### 4. Schema Validation

```python
def test_response_schema(authorized_client):
    response = authorized_client.get("/posts/1")
    post = PostOut(**response.json())  # Validate schema
    assert post.Post.id == 1
```

**What to verify**:
- Response matches expected schema
- All required fields present
- Field types correct

---

## Assertion Best Practices

### Use Specific Assertions

```python
# ✗ Avoid vague assertions
assert response

# ✓ Be specific
assert response.status_code == 200
assert "email" in response.json()
assert response.json()["email"] == "test@example.com"
```

### Test One Thing Per Test

```python
# ✗ Multiple things in one test
def test_user():
    user_response = client.post(...)
    assert user_response.status_code == 200
    login_response = client.post(...)
    assert login_response.status_code == 200
    post_response = client.post(...)
    assert post_response.status_code == 201

# ✓ Separate concerns
def test_create_user(client):
    response = client.post("/users/", ...)
    assert response.status_code == 200

def test_login(client, create_test_user):
    response = client.post("/login/", ...)
    assert response.status_code == 200

def test_create_post(authorized_client):
    response = authorized_client.post("/posts/", ...)
    assert response.status_code == 201
```

---

## Debugging Failed Tests

### Use `-s` Flag to See Print Statements

```bash
pytest test/test_users.py -s
```

Tests include `print()` statements. Use `-s` to view them.

### Use `-v` for Verbose Output

```bash
pytest -v
```

Shows test names and individual pass/fail for each parametrized variant.

### Use `-x` to Stop at First Failure

```bash
pytest -x
```

Stops running tests after first failure (good for debugging).

### Inspect Response Objects

Tests print response status codes and JSON. Use this to understand what endpoints returned.

---

## Key Concepts Summary

| Concept | Purpose |
|---------|---------|
| **Fixture** | Reusable setup code (database, client, users, etc.) |
| **Scope** | When fixture runs (function, session, etc.) |
| **Dependency Chain** | Fixtures depending on other fixtures |
| **Parametrization** | Run test multiple times with different inputs |
| **TestClient** | Simulate HTTP requests without running server |
| **Assertion** | Verify expected behavior |
| **Status Code** | Verify endpoint returned correct HTTP code |
| **Schema Validation** | Verify response matches Pydantic schema |

---

## File Structure

```
test/
├── conftest.py          # Fixtures used by all tests
├── test_users.py        # User creation, login, authentication
├── test_posts.py        # Post CRUD operations, filtering
├── test_votes.py        # Vote creation, removal, constraints
├── __init__.py          # Package marker
└── README.md            # This file
```

All tests run against a fresh test database, ensuring clean state and no interference between tests.
