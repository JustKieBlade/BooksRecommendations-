from pydantic import BaseModel
from typing import List, Optional

class UserCreate(BaseModel):
    chosen_tags: List[str]

class UserResponse(BaseModel):
    id: int
    chosen_tags: str

    class Config:
        from_attributes = True

class BookResponse(BaseModel):
    id: int
    title: str
    authors: Optional[str]
    description: Optional[str]
    image_url: Optional[str]
    genres: Optional[str]

    class Config:
        from_attributes = True

class ActionCreate(BaseModel):
    user_id: int
    book_id: int
    action: str  # 'like' или 'dislike'