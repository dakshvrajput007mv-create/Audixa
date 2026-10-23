import os
from faster_whisper import WhisperModel
import models
from sqlalchemy.orm import Session
from database import SessionLocal

MODEL_SIZE = os.environ.get("WHISPER_MODEL_SIZE", "small") # small is required for accurate Hindi/Marathi, base hallucinates on songs

def transcribe_and_generate_chapters(transcript_id: int, file_path: str, language: str = None):
    db = SessionLocal()
    transcript = db.query(models.Transcript).filter(models.Transcript.id == transcript_id).first()
    if not transcript:
        db.close()
        return

    try:
        transcript.status = "processing"
        db.commit()

        # 1. Transcribe with faster-whisper
        actual_model_size = f"{MODEL_SIZE}.en" if language == "en" else MODEL_SIZE
        import os as _os
        cpu_threads = _os.cpu_count() or 4
        model = WhisperModel(actual_model_size, device="cpu", compute_type="int8", cpu_threads=cpu_threads)
        
        # Handle Hinglish explicitly
        actual_language = "hi" if language == "hinglish" else language
        
        # Provide a specialized prompt for Hinglish to encourage code-mixing (English + Hindi)
        if language == "hinglish":
            prompt = "Um, uh, well, you know, bhai, main theek hoon... [pause] [autotune]"
        else:
            prompt = "Um, uh, well, you know... [pause] [autotune]"
        
        segments_gen, info = model.transcribe(
            file_path, 
            beam_size=1,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
            language=actual_language,
            initial_prompt=prompt
        )

        transcript.duration = info.duration
        
        segments_data = []
        last_progress_update = 0
        
        for i, segment in enumerate(segments_gen):
            seg = models.Segment(
                transcript_id=transcript.id,
                start_time=segment.start,
                end_time=segment.end,
                text=segment.text.strip(),
                order_index=i
            )
            db.add(seg)
            segments_data.append(seg)
            
            # Calculate and update progress
            if info.duration > 0:
                current_pct = int((segment.end / info.duration) * 100)
                # Only update DB if progress increased by at least 2% to avoid overwhelming SQLite
                if current_pct - last_progress_update >= 2:
                    transcript.progress = min(current_pct, 99) # Keep at 99 until fully done
                    db.commit()
                    last_progress_update = current_pct
        
        db.commit()

        # 2. Generate chapters (heuristic: pause/gap detection + max duration)
        # We'll split if there's a gap of > 3 seconds, OR if the chapter is longer than 3 minutes.
        chapters = []
        current_chapter_start = 0.0
        current_chapter_segments = []
        chapter_index = 0

        for i, seg in enumerate(segments_data):
            if not current_chapter_segments:
                current_chapter_start = seg.start_time
            
            current_chapter_segments.append(seg)
            
            # Check for split conditions
            split_now = False
            
            # Condition A: Gap detection
            if i < len(segments_data) - 1:
                next_seg = segments_data[i + 1]
                gap = next_seg.start_time - seg.end_time
                if gap > 3.0: # 3 seconds pause
                    split_now = True
            
            # Condition B: Max duration (e.g. 3 minutes)
            chapter_duration = seg.end_time - current_chapter_start
            if chapter_duration > 180.0:
                split_now = True
            
            # Last segment always ends the chapter
            if i == len(segments_data) - 1:
                split_now = True
                
            if split_now:
                # Create chapter
                title = f"Chapter {chapter_index + 1}"
                
                # Try to make a smarter title from the first few words
                words = " ".join([s.text for s in current_chapter_segments]).split()
                if len(words) > 0:
                    title = " ".join(words[:5]) + "..."
                    
                ch = models.Chapter(
                    transcript_id=transcript.id,
                    title=title,
                    start_time=current_chapter_start,
                    end_time=seg.end_time,
                    order_index=chapter_index
                )
                db.add(ch)
                chapters.append(ch)
                
                # Reset for next chapter
                current_chapter_segments = []
                chapter_index += 1

        db.commit()

        transcript.progress = 100
        transcript.status = "ready"
        db.commit()

    except Exception as e:
        print(f"Transcription error: {e}")
        transcript.status = "failed"
        db.commit()
    finally:
        db.close()
