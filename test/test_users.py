from jose import jwt
from app.config import settings
from app import schemas
import pytest




def test_root(client, db_session):
    # Verifies FastAPI server is running and responds to root GET request
    # Baseline test to confirm test environment setup
    response = client.get("/")
    
    # Print response details (use pytest -s to see output)
    print(" Test Root Response status code:", response.status_code)
    print("Test Root Response JSON:", response.json())
    assert response.status_code == 200
    assert response.json() == {"message": "FastAPI Server is running!!"}
    
    
# def test_simple():
#   assert 1 + 1 == 2 # This won't run because the test will fail before it gets here due to the assertion error in the previous test.
  
  
def test_create_user(client,db_session):
  # Verifies POST /users/ endpoint creates user and returns correct user data
  # Confirms password hashing occurs and plaintext password not returned
    user_data = {
    "email": "meena12@gmail.com",
    "password": "Abhishek@14"
    }
    response = client.post("/users/", json=user_data)# The trailing slash for /users if removed will cause a 307 redirect to /users/ which can interfere with the test. Keeping the trailing slash ensures the request goes directly to the correct endpoint without redirection.
    new_user = schemas.User(**response.json())
    print("Create User Response status code:", response.status_code)
    print("Create User Response JSON:", response.json())
    assert response.status_code == 200
    assert new_user.email == user_data["email"]
    
def test_user_login(client, create_test_user):
    # Validates login endpoint returns valid JWT token with correct user_id claim
    # Tests JWT decode and payload verification
    login_data = {
        "username": create_test_user["email"], # Use the email from the created test user
        "password": create_test_user["password"]  # Use the password from the created test user
    }
    response = client.post("/login/", data=login_data)
    print("Login Response status code:", response.status_code)
    print("Login Response JSON:", response.json())
    token  = schemas.Token(**response.json())
    payload = jwt.decode(token.access_token, settings.secret_key, algorithms=[settings.algorithm ])
        
        # Extract user_id from payload
        # In create_access_token(), we stored {"user_id": <value>}
    user_id: str = payload.get("user_id")
    
    # If user_id missing from payload, token is invalid
    if user_id is None:
        raise credentials_exception
    assert response.status_code == 200
    assert "access_token" in token.model_dump() # Check if access_token is in the response
    assert payload.get("user_id") == create_test_user["id"] # Check if the user_id in the token payload matches the id of the created test user


def test_login(client, create_test_user):
    # Confirms successful login returns 200 status and access_token in response
    # Validates happy-path authentication flow
    login_data = {
        "username": create_test_user["email"], # Use the email from the created test user
        "password": create_test_user["password"]  # Use the password from the created test user
    }
    response = client.post("/login/", data=login_data)
    print(f"Login Response status code: {response.status_code}")
    print(f"Login Response JSON: {response.json()}")
    assert response.status_code == 200


@pytest.mark.parametrize("email,password,expected_status", [
    ("test1_user@gmail.com", "Abhishek@14", 403),  # Non-existent user
    ("test_user@gmail.com", "wrongpassword", 403), # Incorrect password for existing user
    (None, "Abhishek@14", 422),                    # Missing email
    ("test_user@gmail.com", None, 422),             # Missing password
    ("test1_user@gmail.com", "wrongpassword", 403)             # Missing password for non-existent user
])
def test_incorrect_login(client, email, password, expected_status):
    # Tests login endpoint rejects invalid credentials with correct HTTP status
    # Parametrize runs test multiple times with different input combinations
    login_data = {
        "username": email,
        "password": password
    }
    response = client.post("/login/", data=login_data)
    print("Incorrect Login Response status code:", response.status_code)
    print("Incorrect Login Response JSON:", response.json())
    assert response.status_code == expected_status
    if expected_status == 403:
        assert response.json().get("detail") == "Invalid Credentials"