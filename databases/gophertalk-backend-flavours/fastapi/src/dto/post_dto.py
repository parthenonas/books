from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PostCreateDTO(BaseModel):
    text: str = Field(..., min_length=1, max_length=280)
    reply_to_id: Optional[int] = Field(default=None)
    user_id: int

    @field_validator("reply_to_id")
    @classmethod
    def reply_to_id_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError("ReplyToID must be greater than 0")
        return v


class PostFilterDTO(BaseModel):
    search: Optional[str] = None
    owner_id: Optional[int] = Field(default=None, ge=1)
    user_id: Optional[int] = Field(default=None, ge=1)
    reply_to_id: Optional[int] = Field(default=None, ge=1)
    limit: Optional[int] = Field(default=None, ge=1)
    offset: Optional[int] = Field(default=None, ge=0)


class PostReadDTO(BaseModel):
    id: int
    text: str
    user_id: int
    reply_to_id: Optional[int]
    created_at: str  
    likes_count: int
    views_count: int

    class Config:
        from_attributes = True
