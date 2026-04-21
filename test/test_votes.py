import pytest

from app import models


@pytest.fixture
def create_test_post_with_vote(db_session, create_test_user, test_create_posts):
    # Creates a vote in the database for testing vote removal/duplicate scenarios
    post_id = test_create_posts[3].id
    # Create a vote for the post
    vote_data = {
        "post_id": post_id,
        "dir": 1
    }
    db_session.add(models.Votes(post_id=vote_data["post_id"], user_id=create_test_user["id"]))
    db_session.commit()
    return vote_data

def test_vote_on_post(authorized_client, create_test_user, test_create_posts):
    # Verifies POST /vote/ endpoint creates vote with 201 Created status
    post_id = test_create_posts[0].id
    
    # Create a vote for the post
    vote_data = {
        "post_id": post_id,
        "dir": 1  
    }
    
    response = authorized_client.post("/vote/", json=vote_data)
    print("Upvote Post Response status code:", response.status_code)
    print("Upvote Post Response JSON:", response.json())
    assert response.status_code == 201
    assert response.json() == {"message": "Successfully added vote"}
    
    
def test_vote_again_on_same_post(authorized_client, create_test_user, test_create_posts , create_test_post_with_vote):
    # Validates duplicate votes return 409 Conflict with specific error message
    post_id = create_test_post_with_vote["post_id"]
    
    # Create a vote for the post
    vote_data = {
        "post_id": create_test_post_with_vote["post_id"],
        "dir": create_test_post_with_vote["dir"]
    }
    
    response = authorized_client.post("/vote/", json=vote_data)
    print("Duplicate Upvote Post Response status code:", response.status_code)
    print("Duplicate Upvote Post Response JSON:", response.json())
    assert response.status_code == 409
    assert response.json() == {"detail": f"user {create_test_user['id']} has already voted on post {post_id}"}
    
def test_delete_vote_on_post(authorized_client, create_test_user, test_create_posts , create_test_post_with_vote):
    # Verifies POST /vote/ with dir=0 removes existing vote (soft delete)
    post_id = create_test_post_with_vote["post_id"]
    vote_data = {
        "post_id": post_id,
        "dir": 0
    }
    response = authorized_client.post("/vote/", json=vote_data)
    print("Delete Vote on Post Response status code:", response.status_code)
    print("Delete Vote on Post Response JSON:", response.json())
    assert response.status_code == 201
    
def test_delete_nonexistent_vote_on_post(authorized_client, create_test_user, test_create_posts):
    # Verifies attempt to delete non-existent vote returns 404 Not Found
    post_id = test_create_posts[0].id
    vote_data = {
        "post_id": post_id,
        "dir": 0
    }
    response = authorized_client.post("/vote/", json=vote_data)
    print("Delete Non-existent Vote on Post Response status code:", response.status_code)
    print("Delete Non-existent Vote on Post Response JSON:", response.json())
    assert response.status_code == 404
    
def test_vote_on_nonexistent_post(authorized_client, create_test_user):
    # Validates voting on non-existent post returns 404 Not Found
    vote_data = {
        "post_id": 9999,
        "dir": 1
    }
    response = authorized_client.post("/vote/", json=vote_data)
    print("Vote on Non-existent Post Response status code:", response.status_code)
    print("Vote on Non-existent Post Response JSON:", response.json())
    assert response.status_code == 404
    
    
def test_unauthorized_vote_on_post(client, create_test_user, test_create_posts):
    # Ensures unauthenticated users cannot vote (requires valid JWT token)
    post_id = test_create_posts[0].id
    vote_data = {
        "post_id": post_id,
        "dir": 1
    }
    response = client.post("/vote/", json=vote_data)
    print("Unauthorized Vote on Post Response status code:", response.status_code)
    print("Unauthorized Vote on Post Response JSON:", response.json())
    assert response.status_code == 401