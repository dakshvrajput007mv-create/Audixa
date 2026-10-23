from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, BackgroundTasks, Form
from starlette.background import BackgroundTask
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse, PlainTextResponse
import os
import uuid
import tempfile
import shutil

import models, schemas, database
from database import engine
from transcription import transcribe_and_generate_chapters
from fpdf import FPDF

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Audixa API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup Event to ensure a guest user exists
@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    guest = db.query(models.User).filter(models.User.email == "guest@audixa.local").first()
    if not guest:
        guest = models.User(email="guest@audixa.local", hashed_password="")
        db.add(guest)
        db.commit()
    db.close()

def get_guest_user(db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == "guest@audixa.local").first()
    if not user:
        raise HTTPException(status_code=500, detail="Guest user not initialized")
    return user

# --- File Management & Transcription ---

@app.post("/files/upload", response_model=schemas.TranscriptResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    language: str = Form(None),
    guest_user: models.User = Depends(get_guest_user),
    db: Session = Depends(get_db)
):
    # Save file
    file_ext = os.path.splitext(file.filename)[1]
    disk_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, disk_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Create DB record
    new_transcript = models.Transcript(
        user_id=guest_user.id,
        filename=file.filename,
        disk_filename=disk_filename,
        status="pending"
    )
    db.add(new_transcript)
    db.commit()
    db.refresh(new_transcript)
    
    # Queue background task
    background_tasks.add_task(transcribe_and_generate_chapters, new_transcript.id, file_path, language)
    
    return new_transcript

@app.get("/files", response_model=list[schemas.TranscriptResponse])
def get_files(guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    return db.query(models.Transcript).filter(models.Transcript.user_id == guest_user.id).order_by(models.Transcript.created_at.desc()).all()

@app.get("/files/{transcript_id}", response_model=schemas.TranscriptDetailResponse)
def get_file(transcript_id: int, guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id, 
        models.Transcript.user_id == guest_user.id
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return transcript

@app.get("/files/{transcript_id}/media")
def get_file_media(transcript_id: int, guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id, 
        models.Transcript.user_id == guest_user.id
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    file_path = os.path.join(UPLOAD_DIR, transcript.disk_filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media file not found on disk")
        
    return FileResponse(file_path)

@app.delete("/files/{transcript_id}")
def delete_file(transcript_id: int, guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    transcript = db.query(models.Transcript).filter(
        models.Transcript.id == transcript_id, 
        models.Transcript.user_id == guest_user.id
    ).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    db.delete(transcript)
    db.commit()
    return {"detail": "Deleted successfully"}

# --- Editing & Export ---

@app.patch("/files/{transcript_id}/transcript")
def update_transcript_segments(transcript_id: int, updates: dict, guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    """ Updates is a dict of segment_id: new_text """
    transcript = db.query(models.Transcript).filter(models.Transcript.id == transcript_id, models.Transcript.user_id == guest_user.id).first()
    if not transcript:
         raise HTTPException(status_code=404, detail="Transcript not found")
         
    for seg_id, new_text in updates.items():
        db.query(models.Segment).filter(
            models.Segment.id == int(seg_id),
            models.Segment.transcript_id == transcript_id
        ).update({"text": new_text})
        
    db.commit()
    return {"detail": "Updated"}

@app.patch("/files/{transcript_id}/chapters")
def update_chapters(transcript_id: int, chapters: list[dict], guest_user: models.User = Depends(get_guest_user), db: Session = Depends(get_db)):
    """ Replace all chapters with the provided list """
    transcript = db.query(models.Transcript).filter(models.Transcript.id == transcript_id, models.Transcript.user_id == guest_user.id).first()
    if not transcript:
         raise HTTPException(status_code=404, detail="Transcript not found")
         
    # Delete existing chapters
    db.query(models.Chapter).filter(models.Chapter.transcript_id == transcript_id).delete()
    
    # Insert new ones
    for idx, chap in enumerate(chapters):
        new_chapter = models.Chapter(
            transcript_id=transcript_id,
            title=chap.get("title", "Chapter"),
            start_time=chap.get("start_time", 0),
            end_time=chap.get("end_time", 0),
            order_index=idx
        )
        db.add(new_chapter)
        
    db.commit()
    return {"detail": "Chapters updated"}

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"

@app.get("/files/{transcript_id}/export")
def export_file(
    transcript_id: int, 
    background_tasks: BackgroundTasks,
    format: str = "txt", 
    guest_user: models.User = Depends(get_guest_user), 
    db: Session = Depends(get_db)
):
    transcript = db.query(models.Transcript).filter(models.Transcript.id == transcript_id, models.Transcript.user_id == guest_user.id).first()
    if not transcript:
        raise HTTPException(status_code=404, detail="Transcript not found")
        
    segments = db.query(models.Segment).filter(models.Segment.transcript_id == transcript_id).order_by(models.Segment.order_index).all()
    
    if format == "txt":
        text = "\n".join([s.text for s in segments])
        return PlainTextResponse(text, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={transcript.filename}.txt"})
    
    elif format == "srt":
        srt_content = ""
        for i, s in enumerate(segments):
            start = format_timestamp(s.start_time)
            end = format_timestamp(s.end_time)
            srt_content += f"{i+1}\n{start} --> {end}\n{s.text}\n\n"
        return PlainTextResponse(srt_content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={transcript.filename}.srt"})
        
    elif format == "pdf":
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, text=f"Transcript: {transcript.filename}", ln=True, align='C')
        pdf.ln(10)
        
        for s in segments:
            pdf.multi_cell(0, 10, text=s.text)
            
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.close() # Must close so FPDF can open it on Windows
        pdf.output(temp_file.name)
        
        return FileResponse(temp_file.name, filename=f"{transcript.filename}.pdf", background=BackgroundTask(os.remove, temp_file.name))
    
    else:
        raise HTTPException(status_code=400, detail="Invalid format")
