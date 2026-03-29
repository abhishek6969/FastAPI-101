# ============ VOTE/LIKE ENDPOINTS ============
# This router handles user voting (liking/unliking) on posts.
# Endpoints:
#   - POST /vote          → Like or unlike a post

from fastapi import status, HTTPException, Depends, APIRouter
from ..schemas import Vote
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from .. import oauth2


router = APIRouter(
    prefix="/vote",                     # All routes prefixed with /vote
    tags=["Vote"]                       # Group under "Vote" tag in Swagger UI
)

@router.post("/", status_code=status.HTTP_201_CREATED)
def vote(vote_data: Vote, db: Session = Depends(get_db), current_user=Depends(oauth2.get_current_user)):
    """Like or unlike a post
    
    Endpoint: POST /vote
    
    Requires Authentication:
        - Authorization header with JWT Bearer token
        - Token must be valid and not expired
    
    Request Body (JSON):
        {
            "post_id": 5,           # Which post to vote on
            "dir": 1                # 1=like, 0=unlike
        }
    
    Response (201 Created):
        {"message": "Successfully added vote"}   # When liking
        {"message": "Successfully deleted vote"} # When unliking
    
    Error Codes:
        - 401: Unauthorized - invalid or missing token
        - 404: Post not found OR vote doesn't exist (when trying to unlike)
        - 409: Conflict - user already voted on this post (when trying to like again)
        - 422: Invalid form data (post_id not int, dir not 0 or 1)
    
    Business Logic:
        - One user can only like a post once
        - Duplicate likes are prevented by database composite key constraint
        - Unlike removes the like record
        - Cannot unlike a post that wasn't liked (vote doesn't exist)
    
    Authorization:
        - Authenticated user (from JWT token)
        - Any user can like/unlike any post
        - Vote record stores user_id, so we know who liked what
    """
    
    # ========== VALIDATION: DOES POST EXIST? ==========
    # Before allowing user to vote, ensure the post exists
    # Query for post with matching id
    post = db.query(models.Post).filter(models.Post.id == vote_data.post_id).first()
    
    if not post:
        # Post doesn't exist - return 404
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id: {vote_data.post_id} does not exist"
        )
    
    # ========== CHECK FOR EXISTING VOTE ==========
    # Query database to see if this user already voted on this post
    # Composite key (post_id, user_id) ensures max one vote per user per post
    vote_query = db.query(models.Votes).filter(
        models.Votes.post_id == vote_data.post_id,
        models.Votes.user_id == current_user.id
    )
    
    found_vote = vote_query.first()
    
    # ========== HANDLE VOTE DIRECTION (1 = LIKE, 0 = UNLIKE) ==========
    if vote_data.dir == 1:
        # ========== LIKE POST ==========
        if found_vote:
            # User already liked this post - prevent duplicate
            # Composite primary key (post_id, user_id) prevents duplicates at DB level
            # But we check first to give user-friendly error instead of database error
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"user {current_user.id} has already voted on post {vote_data.post_id}"
            )
        
        # Create new vote record
        new_vote = models.Votes(post_id=vote_data.post_id, user_id=current_user.id)
        
        # Add to session and commit to database
        db.add(new_vote)
        db.commit()
        
        return {"message": "Successfully added vote"}
    
    else:  # vote_data.dir == 0
        # ========== UNLIKE POST ==========
        if not found_vote:
            # User never voted on this post - cannot unlike
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote does not exist"
            )
        
        # Delete the vote record
        # vote_query.delete(): Mark record for deletion in session
        # synchronize_session=False: Skip checking in-memory objects (improves performance)
        #   - Only matters if this query result is still needed in memory (it's not)
        #   - Safe to use False here because we don't reference found_vote after deletion
        vote_query.delete(synchronize_session=False)
        
        # Commit transaction - DELETE executed in database
        db.commit()
        
        return {"message": "Successfully deleted vote"}