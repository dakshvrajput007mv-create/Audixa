from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    transcripts = relationship("Transcript", back_populates="owner")

class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    disk_filename = Column(String)
    status = Column(String, default="pending")  # pending, processing, ready, failed
    progress = Column(Integer, default=0)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="transcripts")
    segments = relationship("Segment", back_populates="transcript", cascade="all, delete-orphan")
    chapters = relationship("Chapter", back_populates="transcript", cascade="all, delete-orphan")

class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    start_time = Column(Float)
    end_time = Column(Float)
    text = Column(String)
    order_index = Column(Integer)

    transcript = relationship("Transcript", back_populates="segments")

class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    transcript_id = Column(Integer, ForeignKey("transcripts.id"))
    title = Column(String)
    start_time = Column(Float)
    end_time = Column(Float)
    order_index = Column(Integer)

    transcript = relationship("Transcript", back_populates="chapters")
