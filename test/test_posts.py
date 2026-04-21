from app.schemas import PostOut , PostResponse
import pytest

def test_get_all_posts(authorized_client, test_create_posts):
    # Verifies GET /posts/ returns all posts in correct PostOut schema format
    response = authorized_client.get("/posts/")
    print("Get All Posts Response status code:", response.status_code)
    print("Get All Posts Response JSON:", response.json())
    post_list = [PostOut(**post) for post in response.json()]
    assert response.status_code == 200
    assert len(post_list) == len(test_create_posts)
    for index, post in enumerate(post_list):
        assert post.Post.id in [p.id for p in test_create_posts]
        
        
def test_unauthorized_get_all_posts(client , test_create_posts):
    # Confirms unauthenticated users can still view all posts (public endpoint)
    response = client.get("/posts/")
    print("Unauthorized Get All Posts Response status code:", response.status_code)
    print("Unauthorized Get All Posts Response JSON:", response.json())
    assert response.status_code == 200
    
def test_get_one_post(authorized_client, test_create_posts):
    # Verifies GET /posts/{id} returns single post with matching ID
    post_id = test_create_posts[0].id
    response = authorized_client.get(f"/posts/{post_id}")
    print("Get One Post Response status code:", response.status_code)
    print("Get One Post Response JSON:", response.json())
    post = PostOut(**response.json())
    assert response.status_code == 200
    assert post.Post.id == post_id
    
def test_unauthorized_get_one_post(client, test_create_posts):
    # Ensures unauthenticated requests to protected endpoints return 401 Unauthorized
    post_id = test_create_posts[0].id
    response = client.get(f"/posts/{post_id}")
    print("Unauthorized Get One Post Response status code:", response.status_code)
    print("Unauthorized Get One Post Response JSON:", response.json())
    assert response.status_code == 401
    
def test_get_nonexistent_post(authorized_client):
    # Verifies endpoint returns 404 when post ID doesn't exist in database
    response = authorized_client.get("/posts/9999")
    print("Get Non-existent Post Response status code:", response.status_code)
    print("Get Non-existent Post Response JSON:", response.json())
    assert response.status_code == 404
    
def test_bad_url_string_get_one_post(authorized_client):
    # Validates endpoint returns 422 Unprocessable Entity for invalid ID type
    response = authorized_client.get("/posts/12lk")
    print("Bad URL String Get One Post Response status code:", response.status_code)
    print("Bad URL String Get One Post Response JSON:", response.json())
    assert response.status_code == 422
    
    
@pytest.mark.parametrize("title, content", [
    ("Post no 1", "This is a test post 1."),
    ("Post no 2", "This is a test post 2.")
])
def test_create_post_with_default_published_value(title, content, authorized_client, create_test_user , test_create_posts):
    # Parametrize runs this test twice with different title/content values
    post_data = {
        "title": title,
        "content": content,
        "owner_id": create_test_user["id"]
    }
    response = authorized_client.post("/posts/", json=post_data)
    post_response = PostResponse(**response.json())
    print("Create Post Response status code:", response.status_code)
    print("Create Post Response JSON:", response.json())
    assert response.status_code == 201
    assert post_response.title == post_data["title"]
    assert post_response.content == post_data["content"]
    assert post_response.owner_id == post_data["owner_id"]
    assert post_response.published == True
    
    
@pytest.mark.parametrize("title, content, published", [
    ("Post no 1", "This is a test post 1.", False),
    ("Post no 2", "This is a test post 2.", True)
])
def test_create_post_with_non_default_published_value(title, content, published, authorized_client, create_test_user , test_create_posts):
    # Parametrize runs test twice with different published values (True/False)
    post_data = {
        "title": title,
        "content": content,
        "owner_id": create_test_user["id"],
        "published": published
    }
    response = authorized_client.post("/posts/", json=post_data)
    post_response = PostResponse(**response.json())
    print("Create Post Response status code:", response.status_code)
    print("Create Post Response JSON:", response.json())
    assert response.status_code == 201
    assert post_response.title == post_data["title"]
    assert post_response.content == post_data["content"]
    assert post_response.owner_id == post_data["owner_id"]
    assert post_response.published == post_data["published"]
    
    
@pytest.mark.parametrize("title, content, published", [
    ("Post no 1", "This is a test post 1.", False),
    ("Post no 2", "This is a test post 2.", True)
])
def test_unauthorised_create_post_with_non_default_published_value(title, content, published, client, create_test_user , test_create_posts):
    # Verifies unauthenticated users cannot create posts (requires valid token)
    post_data = {
        "title": title,
        "content": content,
        "owner_id": create_test_user["id"],
        "published": published
    }
    response = client.post("/posts/", json=post_data)
    print("Unauthorized Create Post Response status code:", response.status_code)
    print("Unauthorized Create Post Response JSON:", response.json())
    assert response.status_code == 401
    
def test_unauthorized_delete_post(client, test_create_posts):
    # Ensures unauthenticated users cannot delete posts
    post_id = test_create_posts[0].id
    response = client.delete(f"/posts/{post_id}")
    print("Unauthorized Delete Post Response status code:", response.status_code)
    print("Unauthorized Delete Post Response JSON:", response.json())
    assert response.status_code == 401
    
def test_delete_nonexistent_post(authorized_client):
    # Validates endpoint returns 404 when attempting to delete non-existent post
    response = authorized_client.delete("/posts/9999")
    print("Delete Non-existent Post Response status code:", response.status_code)
    print("Delete Non-existent Post Response JSON:", response.json())
    assert response.status_code == 404
    
def test_delete_post(authorized_client, test_create_posts):
    # Verifies authenticated user can delete their own post (204 No Content response)
    post_id = test_create_posts[0].id
    response = authorized_client.delete(f"/posts/{post_id}")
    print("Delete Post Response status code:", response.status_code)
    assert response.status_code == 204
    
def test_delete_post_by_non_owner(authorized_client, test_create_posts):
    # Validates users cannot delete posts owned by other users (403 Forbidden)
    post_id = test_create_posts[3].id
    response = authorized_client.delete(f"/posts/{post_id}")
    print("Delete Post by Non-owner Response status code:", response.status_code)
    print("Delete Post by Non-owner Response JSON:", response.json())
    assert response.status_code == 403
    
def test_update_post(authorized_client, test_create_posts):
    # Verifies authenticated user can update their own post with new title/content
    post_id = test_create_posts[0].id
    updated_post_data = {
        "title": "Updated Title 1",
        "content": "Updated content 1 .",
        "published": True
    }
    response = authorized_client.put(f"/posts/{post_id}", json=updated_post_data)
    post_response = PostResponse(**response.json())
    print("Update Post Response status code:", response.status_code)
    print("Update Post Response JSON:", response.json())
    assert response.status_code == 200
    assert post_response.title == updated_post_data["title"]
    assert post_response.content == updated_post_data["content"]
    assert post_response.published == updated_post_data["published"]
    
def test_update_post_by_non_owner(authorized_client, test_create_posts):
    # Validates users cannot update posts owned by other users (403 Forbidden)
    post_id = test_create_posts[3].id
    updated_post_data = {
        "title": "Updated Title 4",
        "content": "Updated content 4 .",
        "published": False
    }
    response = authorized_client.put(f"/posts/{post_id}", json=updated_post_data)
    print("Update Post by Non-owner Response status code:", response.status_code)
    print("Update Post by Non-owner Response JSON:", response.json())
    assert response.status_code == 403
    
def test_update_nonexistent_post(authorized_client):
    # Verifies endpoint returns 404 when attempting to update non-existent post
    updated_post_data = {
        "title": "Updated Title Non-existent",
        "content": "Updated content for non-existent post.",
        "published": True
    }
    response = authorized_client.put("/posts/9999", json=updated_post_data)
    print("Update Non-existent Post Response status code:", response.status_code)
    print("Update Non-existent Post Response JSON:", response.json())
    assert response.status_code == 404
    
def test_unauthorized_update_post(client, test_create_posts):
    # Ensures unauthenticated users cannot update posts
    post_id = test_create_posts[0].id
    updated_post_data = {
        "title": "Updated Title 1",
        "content": "Updated content 1 .",
        "published": True
    }
    response = client.put(f"/posts/{post_id}", json=updated_post_data)
    print("Unauthorized Update Post Response status code:", response.status_code)
    print("Unauthorized Update Post Response JSON:", response.json())
    assert response.status_code == 401
    
