
from fastapi import APIRouter, Depends, HTTPException
from ..models.comment import Comment, CommentBase
from sqlmodel import Session, select
from ..database import get_session
from ..dependencies import get_current_user, User
from datetime import datetime, timezone


router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=Comment)
def create_comment(comment: CommentBase, session: Session = Depends(get_session), current_user: User= Depends(get_current_user)):
    db_comment = Comment(**comment.model_dump(), user_id=current_user.user_id)
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment


@router.put("/{id}", response_model=Comment)
def update_comment(id: int,comment: CommentBase, session: Session = Depends(get_session), _: User= Depends(get_current_user)):
    db_comment = session.exec(select(Comment).where((Comment.id == id) & (Comment.deleted_at.is_(None)) )).first()
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db_comment.content = comment.content
    db_comment.updated_at = datetime.now(timezone.utc)
    session.add(db_comment)
    session.commit()
    session.refresh(db_comment)
    return db_comment
    

# delete
@router.delete("/{id}")
def delete_comment(id: int,  session: Session = Depends(get_session), current_user: User= Depends(get_current_user)):
    db_comment = session.get(Comment, id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    db_comment.deleted_at = datetime.now(timezone.utc)
    session.commit()
    return {
        "message": "Successfully deleted!"
    }


# List all comment based on entity Id
@router.get("/")
def list_comments(entity_id: int,session: Session = Depends(get_session), current_user: User= Depends(get_current_user) ):
    comments = session.exec(
        select(Comment).where(
            (Comment.entity_id == entity_id) & (Comment.deleted_at.is_(None))
        )
    ).all()
    return comments
    


