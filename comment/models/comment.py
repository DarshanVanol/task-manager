from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional
class CommentBase(SQLModel):
    content: str
    entity_id: Optional[int] = None

class Comment(CommentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None


