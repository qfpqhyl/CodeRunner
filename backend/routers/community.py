"""Community and social features routes."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_, desc

from models.database import (
    get_db, User, Post, PostLike, PostFavorite, Comment, CommentLike, 
    PostCodeShare, Follow, CodeLibrary, CodeExecution
)
from models.models import (
    PostCreate, PostUpdate, PostResponse, CommentCreate, CommentUpdate, 
    CommentResponse, PostQuery, CommentQuery, FollowCreate, FollowResponse
)
from services.auth import get_current_user
from utils.utils import log_system_event, get_client_info

router = APIRouter(prefix="/community", tags=["community"])


@router.post("/posts", response_model=PostResponse)
def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a new community post"""
    try:
        # Create the post
        post = Post(
            user_id=current_user.id,
            title=post_data.title,
            content=post_data.content,
            summary=post_data.summary,
            tags=post_data.tags,
            is_public=post_data.is_public
        )

        db.add(post)
        db.commit()
        db.refresh(post)

        # Handle code library sharing
        if post_data.shared_code_ids:
            for code_id in post_data.shared_code_ids:
                # Verify the code belongs to the user or is public
                code = db.query(CodeLibrary).filter(
                    CodeLibrary.id == code_id
                ).first()

                if code and (code.user_id == current_user.id or code.is_public):
                    post_code_share = PostCodeShare(
                        post_id=post.id,
                        code_library_id=code_id,
                        share_order=len(post.shared_codes) if hasattr(post, 'shared_codes') else 0
                    )
                    db.add(post_code_share)

                    # Mark code as shared via post and make it publicly accessible
                    if code.user_id == current_user.id:
                        code.is_shared_via_post = True
                        code.shared_post_id = post.id
                        # Make the code public if the post is public
                        if post_data.is_public:
                            code.is_public = True

        db.commit()

        # Log post creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_create",
            resource_type="post",
            resource_id=post.id,
            details={
                "title": post_data.title,
                "tags": post_data.tags,
                "is_public": post_data.is_public,
                "shared_code_count": len(post_data.shared_code_ids)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        # Prepare response with author info
        response_dict = {
            "id": post.id,
            "user_id": post.user_id,
            "title": post.title,
            "content": post.content,
            "summary": post.summary,
            "tags": post.tags,
            "view_count": post.view_count,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "favorite_count": post.favorite_count,
            "is_pinned": post.is_pinned,
            "is_public": post.is_public,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "author_username": current_user.username,
            "author_avatar": current_user.avatar_url,
            "author_full_name": current_user.full_name,
            "is_liked_by_current_user": False,
            "is_favorited_by_current_user": False,
            "shared_codes": []
        }

        return PostResponse(**response_dict)

    except Exception as e:
        # Log failed post creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_create",
            resource_type="post",
            details={
                "title": post_data.title,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"帖子创建失败: {str(e)}")


@router.get("/posts", response_model=dict)
def get_posts(
    query: PostQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get community posts with filtering and pagination"""
    try:
        # Build base query
        db_query = db.query(Post).filter(Post.is_public == True)

        # Apply filters
        if query.author_id:
            db_query = db_query.filter(Post.user_id == query.author_id)

        if query.tag:
            db_query = db_query.filter(Post.tags.like(f"%{query.tag}%"))

        if query.search:
            search_term = f"%{query.search}%"
            db_query = db_query.filter(
                (Post.title.like(search_term)) |
                (Post.content.like(search_term)) |
                (Post.summary.like(search_term))
            )

        if query.is_pinned is not None:
            db_query = db_query.filter(Post.is_pinned == query.is_pinned)

        # Apply sorting
        if query.sort_by == "latest":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.created_at.desc())
        elif query.sort_by == "popular":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.view_count.desc())
        elif query.sort_by == "most_liked":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.like_count.desc())
        elif query.sort_by == "most_commented":
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.comment_count.desc())
        else:
            db_query = db_query.order_by(Post.is_pinned.desc(), Post.created_at.desc())

        # Count total posts
        total_count = db_query.count()

        # Apply pagination
        page = max(1, query.page)
        page_size = min(50, max(1, query.page_size))
        offset = (page - 1) * page_size

        posts = db_query.offset(offset).limit(page_size).all()

        # Get user's interaction status for each post
        post_ids = [post.id for post in posts]
        user_likes = {}
        user_favorites = {}

        if post_ids:
            # Get user's likes
            user_like_records = db.query(PostLike).filter(
                PostLike.user_id == current_user.id,
                PostLike.post_id.in_(post_ids)
            ).all()
            user_likes = {like.post_id: True for like in user_like_records}

            # Get user's favorites
            user_favorite_records = db.query(PostFavorite).filter(
                PostFavorite.user_id == current_user.id,
                PostFavorite.post_id.in_(post_ids)
            ).all()
            user_favorites = {favorite.post_id: True for favorite in user_favorite_records}

        # Prepare response
        post_responses = []
        for post in posts:
            # Get author info
            author = db.query(User).filter(User.id == post.user_id).first()

            # Get shared codes
            shared_codes = []
            post_code_shares = db.query(PostCodeShare).filter(PostCodeShare.post_id == post.id).all()
            for share in post_code_shares:
                code = db.query(CodeLibrary).filter(CodeLibrary.id == share.code_library_id).first()
                if code:
                    shared_codes.append({
                        "id": code.id,
                        "title": code.title,
                        "description": code.description,
                        "language": code.language,
                        "tags": code.tags,
                        "author_id": code.user_id,
                        "author_username": author.username if author else "unknown",
                        "is_public": code.is_public
                    })

            response_dict = {
                "id": post.id,
                "user_id": post.user_id,
                "title": post.title,
                "content": post.content,
                "summary": post.summary,
                "tags": post.tags,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "comment_count": post.comment_count,
                "favorite_count": post.favorite_count,
                "is_pinned": post.is_pinned,
                "is_public": post.is_public,
                "created_at": post.created_at,
                "updated_at": post.updated_at,
                "author_username": author.username if author else "unknown",
                "author_avatar": author.avatar_url if author else None,
                "author_full_name": author.full_name if author else None,
                "is_liked_by_current_user": user_likes.get(post.id, False),
                "is_favorited_by_current_user": user_favorites.get(post.id, False),
                "shared_codes": shared_codes
            }
            post_responses.append(PostResponse(**response_dict))

        return {
            "posts": post_responses,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取帖子列表失败: {str(e)}")


@router.get("/posts/{post_id}", response_model=PostResponse)
def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific post by ID"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Increment view count
    post.view_count += 1
    db.commit()

    # Get author info
    author = db.query(User).filter(User.id == post.user_id).first()

    # Get user's interaction status
    is_liked = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first() is not None

    is_favorited = db.query(PostFavorite).filter(
        PostFavorite.user_id == current_user.id,
        PostFavorite.post_id == post_id
    ).first() is not None

    # Get shared codes
    shared_codes = []
    post_code_shares = db.query(PostCodeShare).filter(PostCodeShare.post_id == post_id).all()
    for share in post_code_shares:
        code = db.query(CodeLibrary).filter(CodeLibrary.id == share.code_library_id).first()
        if code and (code.user_id == current_user.id or code.is_public):
            shared_codes.append({
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "tags": code.tags,
                "author_id": code.user_id,
                "author_username": author.username if author else "unknown",
                "is_public": code.is_public
            })

    response_dict = {
        "id": post.id,
        "user_id": post.user_id,
        "title": post.title,
        "content": post.content,
        "summary": post.summary,
        "tags": post.tags,
        "view_count": post.view_count,
        "like_count": post.like_count,
        "comment_count": post.comment_count,
        "favorite_count": post.favorite_count,
        "is_pinned": post.is_pinned,
        "is_public": post.is_public,
        "created_at": post.created_at,
        "updated_at": post.updated_at,
        "author_username": author.username if author else "unknown",
        "author_avatar": author.avatar_url if author else None,
        "author_full_name": author.full_name if author else None,
        "is_liked_by_current_user": is_liked,
        "is_favorited_by_current_user": is_favorited,
        "shared_codes": shared_codes
    }

    return PostResponse(**response_dict)


@router.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Like or unlike a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Check if already liked
    existing_like = db.query(PostLike).filter(
        PostLike.user_id == current_user.id,
        PostLike.post_id == post_id
    ).first()

    if existing_like:
        # Unlike
        db.delete(existing_like)
        post.like_count = max(0, post.like_count - 1)
        message = "取消点赞"
        is_liked = False
    else:
        # Like
        like = PostLike(user_id=current_user.id, post_id=post_id)
        db.add(like)
        post.like_count += 1
        message = "点赞成功"
        is_liked = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="post_like" if is_liked else "post_unlike",
        resource_type="post",
        resource_id=post_id,
        details={"post_title": post.title},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_liked": is_liked, "like_count": post.like_count}


@router.post("/posts/{post_id}/favorite")
def favorite_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Favorite or unfavorite a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # Check if already favorited
    existing_favorite = db.query(PostFavorite).filter(
        PostFavorite.user_id == current_user.id,
        PostFavorite.post_id == post_id
    ).first()

    if existing_favorite:
        # Unfavorite
        db.delete(existing_favorite)
        post.favorite_count = max(0, post.favorite_count - 1)
        message = "取消收藏"
        is_favorited = False
    else:
        # Favorite
        favorite = PostFavorite(user_id=current_user.id, post_id=post_id)
        db.add(favorite)
        post.favorite_count += 1
        message = "收藏成功"
        is_favorited = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="post_favorite" if is_favorited else "post_unfavorite",
        resource_type="post",
        resource_id=post_id,
        details={"post_title": post.title},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_favorited": is_favorited, "favorite_count": post.favorite_count}


@router.post("/posts/{post_id}/comments", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a comment on a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    # If replying to a comment, check if parent comment exists
    if comment_data.parent_id:
        parent_comment = db.query(Comment).filter(Comment.id == comment_data.parent_id).first()
        if not parent_comment or parent_comment.post_id != post_id:
            raise HTTPException(status_code=404, detail="父评论未找到")

    # Create comment
    comment = Comment(
        user_id=current_user.id,
        post_id=post_id,
        parent_id=comment_data.parent_id,
        content=comment_data.content
    )

    db.add(comment)

    # Update post comment count
    post.comment_count += 1

    db.commit()
    db.refresh(comment)

    # Log comment creation
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="comment_create",
        resource_type="comment",
        resource_id=comment.id,
        details={
            "post_id": post_id,
            "parent_id": comment_data.parent_id,
            "content_length": len(comment_data.content)
        },
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    # Prepare response
    response_dict = {
        "id": comment.id,
        "user_id": comment.user_id,
        "post_id": comment.post_id,
        "parent_id": comment.parent_id,
        "content": comment.content,
        "like_count": comment.like_count,
        "is_deleted": comment.is_deleted,
        "created_at": comment.created_at,
        "updated_at": comment.updated_at,
        "author_username": current_user.username,
        "author_avatar": current_user.avatar_url,
        "author_full_name": current_user.full_name,
        "is_liked_by_current_user": False,
        "replies": []
    }

    return CommentResponse(**response_dict)


@router.get("/posts/{post_id}/comments", response_model=dict)
def get_comments(
    post_id: int,
    query: CommentQuery = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comments for a post"""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="帖子未找到")

    # Check if post is public or belongs to current user
    if not post.is_public and post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此帖子")

    try:
        # Get top-level comments (no parent)
        db_query = db.query(Comment).filter(
            Comment.post_id == post_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted == False
        )

        # Apply sorting
        if query.sort_by == "latest":
            db_query = db_query.order_by(Comment.created_at.desc())
        elif query.sort_by == "most_liked":
            db_query = db_query.order_by(Comment.like_count.desc())
        else:
            db_query = db_query.order_by(Comment.created_at.desc())

        # Apply pagination
        page = max(1, query.page)
        page_size = min(50, max(1, query.page_size))
        offset = (page - 1) * page_size

        comments = db_query.offset(offset).limit(page_size).all()

        # Get user's like status for each comment
        comment_ids = [comment.id for comment in comments]
        user_likes = {}

        if comment_ids:
            user_like_records = db.query(CommentLike).filter(
                CommentLike.user_id == current_user.id,
                CommentLike.comment_id.in_(comment_ids)
            ).all()
            user_likes = {like.comment_id: True for like in user_like_records}

        # Prepare response
        comment_responses = []
        for comment in comments:
            # Get author info
            author = db.query(User).filter(User.id == comment.user_id).first()

            # Get replies
            replies = []
            reply_records = db.query(Comment).filter(
                Comment.parent_id == comment.id,
                Comment.is_deleted == False
            ).order_by(Comment.created_at.asc()).all()

            for reply in reply_records:
                reply_author = db.query(User).filter(User.id == reply.user_id).first()
                reply_response_dict = {
                    "id": reply.id,
                    "user_id": reply.user_id,
                    "post_id": reply.post_id,
                    "parent_id": reply.parent_id,
                    "content": reply.content,
                    "like_count": reply.like_count,
                    "is_deleted": reply.is_deleted,
                    "created_at": reply.created_at,
                    "updated_at": reply.updated_at,
                    "author_username": reply_author.username if reply_author else "unknown",
                    "author_avatar": reply_author.avatar_url if reply_author else None,
                    "author_full_name": reply_author.full_name if reply_author else None,
                    "is_liked_by_current_user": False,
                    "replies": []
                }
                replies.append(CommentResponse(**reply_response_dict))

            response_dict = {
                "id": comment.id,
                "user_id": comment.user_id,
                "post_id": comment.post_id,
                "parent_id": comment.parent_id,
                "content": comment.content,
                "like_count": comment.like_count,
                "is_deleted": comment.is_deleted,
                "created_at": comment.created_at,
                "updated_at": comment.updated_at,
                "author_username": author.username if author else "unknown",
                "author_avatar": author.avatar_url if author else None,
                "author_full_name": author.full_name if author else None,
                "is_liked_by_current_user": user_likes.get(comment.id, False),
                "replies": replies
            }
            comment_responses.append(CommentResponse(**response_dict))

        return {
            "comments": comment_responses,
            "pagination": {
                "current_page": page,
                "page_size": page_size,
                "total_count": db_query.count(),
                "total_pages": (db_query.count() + page_size - 1) // page_size
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取评论失败: {str(e)}")


@router.post("/comments/{comment_id}/like")
def like_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Like or unlike a comment"""
    comment = db.query(Comment).filter(Comment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="评论未找到")

    # Check if user can access the post
    post = db.query(Post).filter(Post.id == comment.post_id).first()
    if not post or (not post.is_public and post.user_id != current_user.id):
        raise HTTPException(status_code=403, detail="无权访问此评论")

    # Check if already liked
    existing_like = db.query(CommentLike).filter(
        CommentLike.user_id == current_user.id,
        CommentLike.comment_id == comment_id
    ).first()

    if existing_like:
        # Unlike
        db.delete(existing_like)
        comment.like_count = max(0, comment.like_count - 1)
        message = "取消点赞"
        is_liked = False
    else:
        # Like
        like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.add(like)
        comment.like_count += 1
        message = "点赞成功"
        is_liked = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="comment_like" if is_liked else "comment_unlike",
        resource_type="comment",
        resource_id=comment_id,
        details={"post_id": comment.post_id},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    return {"message": message, "is_liked": is_liked, "like_count": comment.like_count}


@router.post("/follow/{user_id}")
def follow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Follow or unfollow a user"""
    # Cannot follow yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能关注自己")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Check if already following
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if existing_follow:
        # Unfollow
        db.delete(existing_follow)
        message = "取消关注"
        is_following = False
    else:
        # Follow
        follow = Follow(follower_id=current_user.id, following_id=user_id)
        db.add(follow)
        message = "关注成功"
        is_following = True

    db.commit()

    # Log the interaction
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="user_follow" if is_following else "user_unfollow",
        resource_type="user",
        resource_id=user_id,
        details={"target_username": target_user.username},
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    response_dict = {
        "message": message,
        "id": 0,  # Placeholder
        "follower_id": current_user.id,
        "following_id": user_id,
        "created_at": datetime.utcnow(),
        "following_username": target_user.username,
        "following_avatar": target_user.avatar_url,
        "following_full_name": target_user.full_name,
        "is_following": is_following
    }

    return response_dict

# Enhanced User Profile Stats

@router.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Delete a community post and hide related shared codes"""
    try:
        # Get the post
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            raise HTTPException(status_code=404, detail="帖子不存在")

        # Check if user is the author or admin
        if post.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="无权删除此帖子")

        # Get all shared codes for this post
        shared_codes = db.query(CodeLibrary).join(PostCodeShare).filter(
            PostCodeShare.post_id == post_id
        ).all()

        # Hide codes that were made public through this post
        for code in shared_codes:
            if code.is_shared_via_post and code.shared_post_id == post_id:
                code.is_public = False
                code.is_shared_via_post = False
                code.shared_post_id = None

        # Delete post code shares
        db.query(PostCodeShare).filter(PostCodeShare.post_id == post_id).delete()

        # Delete post comments
        db.query(Comment).filter(Comment.post_id == post_id).delete()

        # Delete post likes and favorites
        db.query(PostLike).filter(PostLike.post_id == post_id).delete()
        db.query(PostFavorite).filter(PostFavorite.post_id == post_id).delete()

        # Delete the post
        db.delete(post)
        db.commit()

        # Log post deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_delete",
            resource_type="post",
            resource_id=post_id,
            details={
                "title": post.title,
                "hidden_codes_count": len(shared_codes)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "帖子删除成功，相关代码已设为私密"}
    except HTTPException:
        raise
    except Exception as e:
        # Log failed post deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="post_delete",
            resource_type="post",
            resource_id=post_id,
            details={
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"帖子删除失败: {str(e)}")

# Follow/Followers List endpoints

@router.get("/users/{user_id}/followers", response_model=dict)
def get_user_followers(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's followers list"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Get followers with user info
    followers_query = db.query(
        User.id,
        User.username,
        User.full_name,
        User.avatar_url,
        Follow.created_at
    ).join(
        Follow, User.id == Follow.follower_id
    ).filter(
        Follow.following_id == user_id
    ).order_by(
        Follow.created_at.desc()
    )

    total_count = followers_query.count()
    followers = followers_query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "followers": [
            {
                "id": follower.id,
                "username": follower.username,
                "full_name": follower.full_name,
                "avatar_url": follower.avatar_url,
                "followed_at": follower.created_at
            }
            for follower in followers
        ],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }


@router.get("/users/{user_id}/following", response_model=dict)
def get_user_following(
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's following list"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Get following with user info
    following_query = db.query(
        User.id,
        User.username,
        User.full_name,
        User.avatar_url,
        Follow.created_at
    ).join(
        Follow, User.id == Follow.following_id
    ).filter(
        Follow.follower_id == user_id
    ).order_by(
        Follow.created_at.desc()
    )

    total_count = following_query.count()
    following = following_query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "following": [
            {
                "id": following_user.id,
                "username": following_user.username,
                "full_name": following_user.full_name,
                "avatar_url": following_user.avatar_url,
                "followed_at": following_user.created_at
            }
            for following_user in following
        ],
        "pagination": {
            "current_page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }


@router.get("/users/{user_id}/follow-status", response_model=dict)
def get_follow_status(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get follow status between current user and target user"""
    if user_id == current_user.id:
        return {"is_following": False, "is_self": True}

    is_following = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first() is not None

    return {"is_following": is_following, "is_self": False}


@router.get("/users/by-username/{username}")
def get_user_by_username(
    username: str,
    db: Session = Depends(get_db)
):
    """Get user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "avatar_url": user.avatar_url,
        "bio": user.bio,
        "location": user.location,
        "company": user.company,
        "github_username": user.github_username,
        "website": user.website,
        "created_at": user.created_at
    }


@router.get("/users/{user_id}/posts", response_model=dict)
def get_user_posts(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get public posts by a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count total posts
    total_count = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).count()

    # Get paginated posts
    posts = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).order_by(Post.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "posts": [
            {
                "id": post.id,
                "title": post.title,
                "content": post.content,
                "summary": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "code_snippet": post.code_snippet,
                "language": post.language,
                "tags": post.tags,
                "view_count": post.view_count,
                "like_count": post.like_count,
                "comment_count": len(db.query(Comment).filter(Comment.post_id == post.id).all()),
                "created_at": post.created_at,
                "updated_at": post.updated_at
            }
            for post in posts
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }


@router.get("/users/{user_id}/code-library", response_model=dict)
def get_user_code_library(
    user_id: int,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    """Get public code library entries by a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count total public code entries
    total_count = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).count()

    # Get paginated code library entries
    codes = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).order_by(CodeLibrary.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "codes": [
            {
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "tags": code.tags,
                "conda_env": code.conda_env,
                "created_at": code.created_at,
                "updated_at": code.updated_at
            }
            for code in codes
        ],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": (total_count + page_size - 1) // page_size
        }
    }


@router.get("/users/{user_id}/stats", response_model=dict)
def get_user_public_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get public statistics for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户未找到")

    # Count posts
    posts_count = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).count()

    # Count public code library entries
    code_library_count = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).count()

    # Count followers and following
    followers_count = db.query(Follow).filter(Follow.following_id == user_id).count()
    following_count = db.query(Follow).filter(Follow.follower_id == user_id).count()

    # Get recent posts
    recent_posts = db.query(Post).filter(
        Post.user_id == user_id,
        Post.is_public == True
    ).order_by(Post.created_at.desc()).limit(5).all()

    # Get recent code library entries
    recent_codes = db.query(CodeLibrary).filter(
        CodeLibrary.user_id == user_id,
        CodeLibrary.is_public == True
    ).order_by(CodeLibrary.created_at.desc()).limit(5).all()

    return {
        "posts_count": posts_count,
        "code_library_count": code_library_count,
        "followers_count": followers_count,
        "following_count": following_count,
        "recent_posts": [
            {
                "id": post.id,
                "title": post.title,
                "summary": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                "like_count": post.like_count,
                "comment_count": len(db.query(Comment).filter(Comment.post_id == post.id).all()),
                "view_count": post.view_count,
                "created_at": post.created_at
            }
            for post in recent_posts
        ],
        "recent_codes": [
            {
                "id": code.id,
                "title": code.title,
                "description": code.description,
                "language": code.language,
                "conda_env": code.conda_env,
                "created_at": code.created_at
            }
            for code in recent_codes
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

