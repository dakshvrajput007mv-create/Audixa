from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class SegmentBase(BaseModel):
    start_time: float
    end_time: float
    text: str
    order_index: int

class SegmentResponse(SegmentBase):
    id: int
    transcript_id: int

    class Config:
        from_attributes = True

class SegmentUpdate(BaseModel):
    text: str

class ChapterBase(BaseModel):
    title: str
    start_time: float
    end_time: float
    order_index: int

class ChapterResponse(ChapterBase):
    id: int
    transcript_id: int

    class Config:
        from_attributes = True

class ChapterUpdate(BaseModel):
    title: str
    start_time: float
    end_time: float

class TranscriptBase(BaseModel):
    filename: str

class TranscriptResponse(TranscriptBase):
    id: int
    status: str
    progress: int = 0
    duration: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class TranscriptDetailResponse(TranscriptResponse):
    segments: List[SegmentResponse] = []
    chapters: List[ChapterResponse] = []

    class Config:
        from_attributes = True
