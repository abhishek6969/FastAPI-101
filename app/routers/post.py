# ============ POST CRUD ENDPOINTS ============
# This router handles all post (blog post, social media post) operations.
# Endpoints:
#   - GET /posts              → List all posts with search and pagination
#   - GET /posts/{id}         → Get single post by ID with vote count
#   - POST /posts             → Create new post (requires authentication)
#   - PUT /posts/{id}         → Update existing post (owner only)
#   - DELETE /posts/{id}      → Delete post (owner only)

from fastapi import Response, status, HTTPException, Depends, APIRouter
from ..schemas import PostCreate, PostResponse, PostOut
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, oauth2
from ..database import get_db
from typing import Optional

router = APIRouter(
    prefix="/posts",                    # All routes in this file prefixed with /posts
    tags=["Posts"]                      # Group all post endpoints under "Posts" tag in Swagger UI
)


@router.get("/", response_model=List[PostOut])
def get_my_posts(
    db: Session = Depends(get_db),
    limit: int = 10,
    skip: int = 0,
    search: Optional[str] = ""
):
    """List all posts with optional search, pagination, and vote counts
    
    Endpoint: GET /posts
    
    Query Parameters:
        - limit (int): Max posts to return per page (default 10, max typically 100)
        - skip (int): Number of posts to skip (for pagination)
                      skip=0 → first 10 posts
                      skip=10 → posts 11-20
        - search (str): Filter posts by title substring (optional, empty string = no filter)
    
    Response (200 OK):
        [
            {
                "Post": {
                    "id": 1,
                    "title": "My First Post",
                    "content": "Content here...",
                    "published": true,
                    "created_at": "2024-01-15T10:00:00",
                    "owner_id": 5,
                    "owner": {"id": 5, "email": "user@example.com", "created_at": "..."}
                },
                "votes": 3
            },
            ...
        ]
    
    SQL Generated (approximately):
        SELECT posts.id, posts.title, ... COUNT(votes.post_id) as votes
        FROM posts
        LEFT JOIN votes ON posts.id = votes.post_id
        WHERE posts.title LIKE %search%
        GROUP BY posts.id
        LIMIT 10 OFFSET 0
    
    Authorization:
        - No authentication required (public endpoint)
        - Anyone can view all posts
    
    Performance:
        - Uses OUTER JOIN (LEFT JOIN) to include posts with 0 votes
        - func.count() counts votes without loading vote rows in memory
        - Pagination with LIMIT/OFFSET for large datasets
    
    Note:
        - No authentication required
        - Public data - anyone can search and browse
        - Vote count is aggregated using SQL COUNT function (efficient)
    """
    # ========== BUILD QUERY WITH AGGREGATION ==========
    # Query posts with vote count using LEFT JOIN and GROUP BY
    # LEFT JOIN: Include posts with 0 votes (INNER JOIN would exclude them)
    results = db.query(
        models.Post,
        func.count(models.Votes.post_id).label("votes")  # Count votes per post
    ).outerjoin(
        models.Votes,                                     # Join with votes table
        models.Post.id == models.Votes.post_id           # ON clause
    ).group_by(
        models.Post.id                                    # Aggregate by post ID
    ).filter(
        models.Post.title.contains(search)               # Optional search filter
    ).limit(limit).offset(skip)                          # Pagination
    
    # Execute query and fetch all results
    results = results.all()
    
    # Transform results into response format
    # Each result is a tuple: (Post object, vote_count integer)
    posts = [{"Post": post, "votes": votes} for post, votes in results]
    
    return posts


@router.get("/{id}", response_model=PostOut)
def get_post(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user)
):
    """Get single post by ID with vote count
    
    Endpoint: GET /posts/{id}
    
    Path Parameters:
        - id (int): Post ID (auto-validated as integer by Pydantic)
    
    Response (200 OK):
        {
            "Post": {
                "id": 5,
                "title": "Post Title",
                "content": "Post content...",
                "published": true,
                "created_at": "2024-01-15T10:00:00",
                "owner_id": 3,
                "owner": {"id": 3, "email": "author@example.com", "created_at": "..."}
            },
            "votes": 7
        }
    
    Error Codes:
        - 404: Not Found - post doesn't exist
        - 422: Invalid ID format (non-integer)
        - 401: Unauthorized - invalid or missing JWT token
    
    Authorization:
        - Requires valid JWT token in Authorization header
        - Any authenticated user can view any post
    
    Path Parameter Validation:
        FastAPI automatically:
        1. Extracts "id" from URL: GET /posts/5 → "5" (string)
        2. Validates and converts: "5" → 5 (integer)
        3. If conversion fails (e.g., "abc"): Returns 422 immediately
        4. Passes validated integer to function
    """
    # ========== QUERY POST WITH VOTE COUNT ==========
    # Use same JOIN + aggregation pattern as list endpoint
    my_post = db.query(
        models.Post,
        func.count(models.Votes.post_id).label("votes")
    ).outerjoin(
        models.Votes,
        models.Post.id == models.Votes.post_id
    ).group_by(
        models.Post.id
    ).filter(
        models.Post.id == id
    ).first()
    
    # ========== HANDLE NOT FOUND ==========
    if not my_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} was not found"
        )
    
    # Transform tuple result into response format
    # Query returns tuple: (Post model, vote_count)
    my_post = {"Post": my_post[0], "votes": my_post[1]}
    
    return my_post


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=PostResponse)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user)
):
    """Create a new post
    
    Endpoint: POST /posts
    
    Requires Authentication:
        - Authorization header with valid JWT Bearer token
    
    Request Body (JSON):
        {
            "title": "My Post Title",
            "content": "Post content here...",
            "published": true          # Optional, defaults to true
        }
    
    Response (201 Created):
        {
            "id": 42,
            "title": "My Post Title",
            "content": "Post content here...",
            "published": true,
            "created_at": "2024-01-15T10:30:00",
            "owner_id": 5,
            "owner": {"id": 5, "email": "user@example.com", "created_at": "..."}
        }
    
    Error Codes:
        - 201: Created - success
        - 401: Unauthorized - missing or invalid JWT token
        - 422: Unprocessable Entity - invalid request format
    
    Authorization:
        - Requires authenticated user
        - Post is automatically assigned current_user as owner
        - User cannot create posts for other users
    
    Flow:
        1. Pydantic validates request body matches PostCreate schema
        2. FastAPI calls oauth2.get_current_user to verify JWT token
        3. Convert Pydantic model to dict
        4. Create SQLAlchemy Post model with owner_id=current_user.id
        5. Add to session and commit (INSERT)
        6. Refresh object to get auto-generated id and created_at
        7. Return created post (serialized as JSON by Pydantic schema)
    """
    # Convert Pydantic model to dict
    # Extracts: title, content, published
    post_dict = post.model_dump()
    
    # Create SQLAlchemy model with owner_id from authenticated user
    # **post_dict unpacks all fields (title, content, published)
    new_post = models.Post(owner_id=current_user.id, **post_dict)
    
    # Add to session (staging area for transaction)
    db.add(new_post)
    
    # Commit transaction - INSERT statement executed
    db.commit()
    
    # Refresh from database to populate auto-generated values
    # This ensures id and created_at are populated from database defaults
    db.refresh(new_post)
    
    # Return the new post (Pydantic schema serializes to JSON)
    return new_post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user)
):
    """Delete a post (owner only)
    
    Endpoint: DELETE /posts/{id}
    
    Requires Authentication:
        - Authorization header with valid JWT Bearer token
        - User must be the post owner
    
    Path Parameters:
        - id (int): Post ID to delete
    
    Response (204 No Content):
        - Empty body (no content to return)
    
    Error Codes:
        - 204: No Content - deleted successfully
        - 401: Unauthorized - missing or invalid JWT token
        - 403: Forbidden - user doesn't own this post
        - 404: Not Found - post doesn't exist
        - 422: Invalid ID format
    
    Authorization:
        - Requires authenticated user
        - User must be the post owner (owner_id == current_user.id)
        - Other users cannot delete posts they don't own
    
    Cascade Behavior:
        - When post deleted, all votes on this post auto-deleted
        - This is enforced by database constraint in Votes model:
          ForeignKey("posts.id", ondelete="CASCADE")
    
    Why 204 No Content?
        - DELETE succeeded but has no response body
        - Standard REST practice for successful deletion
        - Differ from 200 OK which typically has content
    """
    # ========== QUERY POST ==========
    post = db.query(models.Post).filter(models.Post.id == id)
    query_post = post.first()
    
    # ========== CHECK IF POST EXISTS ==========
    if query_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} was not found"
        )
    
    # ========== VERIFY AUTHORIZATION ==========
    if query_post.owner_id != current_user.id:
        # Post exists but user doesn't own it
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )
    
    # ========== DELETE POST ==========
    # Mark for deletion in session
    post.delete(synchronize_session=False)
    
    # Commit transaction - DELETE statement executed
    db.commit()
    
    # Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{id}", status_code=status.HTTP_200_OK, response_model=PostResponse)
def update_post(
    id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user=Depends(oauth2.get_current_user)
):
    """Update an existing post (owner only)
    
    Endpoint: PUT /posts/{id}
    
    Requires Authentication:
        - Authorization header with valid JWT Bearer token
        - User must be the post owner
    
    Path Parameters:
        - id (int): Post ID to update
    
    Request Body (JSON):
        {
            "title": "Updated Title",
            "content": "Updated content...",
            "published": false
        }
    
    Response (200 OK):
        {
            "id": 5,
            "title": "Updated Title",
            "content": "Updated content...",
            "published": false,
            "created_at": "2024-01-15T10:00:00",    # Original creation time (not changed)
            "owner_id": 3,
            "owner": {...}
        }
    
    Error Codes:
        - 200: OK - updated successfully
        - 401: Unauthorized - missing or invalid JWT
        - 403: Forbidden - user doesn't own this post
        - 404: Not Found - post doesn't exist
        - 422: Invalid request body or ID format
    
    Authorization:
        - Requires authenticated user
        - User must own the post
        - Can update any fields (title, content, published)
        - Cannot change owner_id or created_at (system fields)
    
    Immutable Fields:
        - created_at: Original creation timestamp preserved
        - owner_id: Cannot reassign post to different user
        - id: Post ID never changes
    """
    # Convert request Pydantic model to dict
    post_dict = post.model_dump()
    
    # Query for post to update
    post_query = db.query(models.Post).filter(models.Post.id == id)
    query_post = post_query.first()
    
    # ========== CHECK IF POST EXISTS ==========
    if query_post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {id} was not found"
        )
    
    # ========== VERIFY AUTHORIZATION ==========
    if query_post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action"
        )
    
    # ========== PERFORM UPDATE ==========
    # Update all fields in post_dict (title, content, published)
    post_query.update(post_dict, synchronize_session=False)
    
    # Commit transaction - UPDATE statement executed
    db.commit()
    
    # Query updated post from database to return latest values
    updated_post = db.query(models.Post).filter(models.Post.id == id).first()
    
    # Return updated post
    return updated_post
