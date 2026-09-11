"""
db.py - SQLite database management for Audixa.
Handles schema initialization, persistence, and CRUD operations for
transcripts, segments, and chapters using Python's built-in sqlite3.
"""

import sqlite3
import os
import json
import uuid
from typing import Dict, List, Optional, Any

if os.environ.get("VERCEL"):
    DB_PATH = "/tmp/audixa.db"
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audixa.db")


def get_db_connection() -> sqlite3.Connection:
    """Creates a connection to the SQLite database with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    """Initializes the database tables if they do not already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS transcripts (
        id TEXT PRIMARY KEY,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        language_mode TEXT NOT NULL,
        detected_language TEXT,
        duration REAL DEFAULT 0.0,
        model_size TEXT DEFAULT 'base',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS segments (
        id TEXT PRIMARY KEY,
        transcript_id TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        text TEXT NOT NULL,
        order_index INTEGER NOT NULL,
        FOREIGN KEY (transcript_id) REFERENCES transcripts (id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS chapters (
        id TEXT PRIMARY KEY,
        transcript_id TEXT NOT NULL,
        title TEXT NOT NULL,
        start_time REAL NOT NULL,
        end_time REAL NOT NULL,
        order_index INTEGER NOT NULL,
        FOREIGN KEY (transcript_id) REFERENCES transcripts (id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_segments_transcript ON segments (transcript_id, order_index);
    CREATE INDEX IF NOT EXISTS idx_chapters_transcript ON chapters (transcript_id, start_time);
    """)

    conn.commit()
    conn.close()


def save_full_transcript(
    transcript_id: str,
    filename: str,
    original_name: str,
    language_mode: str,
    detected_language: Optional[str],
    duration: float,
    model_size: str,
    segments: List[Dict[str, Any]],
    chapters: List[Dict[str, Any]],
) -> None:
    """Saves a newly generated transcript with its segments and chapters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Insert transcript metadata
        cursor.execute(
            """
            INSERT OR REPLACE INTO transcripts 
            (id, filename, original_name, language_mode, detected_language, duration, model_size)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transcript_id,
                filename,
                original_name,
                language_mode,
                detected_language,
                duration,
                model_size,
            ),
        )

        # Clear any existing segments/chapters for this transcript_id
        cursor.execute("DELETE FROM segments WHERE transcript_id = ?", (transcript_id,))
        cursor.execute("DELETE FROM chapters WHERE transcript_id = ?", (transcript_id,))

        # Insert segments
        for idx, seg in enumerate(segments):
            seg_id = seg.get("id") or str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO segments (id, transcript_id, start_time, end_time, text, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    seg_id,
                    transcript_id,
                    float(seg.get("start_time", 0.0)),
                    float(seg.get("end_time", 0.0)),
                    str(seg.get("text", "")).strip(),
                    idx,
                ),
            )

        # Insert chapters
        for idx, ch in enumerate(chapters):
            ch_id = ch.get("id") or str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO chapters (id, transcript_id, title, start_time, end_time, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    ch_id,
                    transcript_id,
                    str(ch.get("title", f"Chapter {idx + 1}")).strip(),
                    float(ch.get("start_time", 0.0)),
                    float(ch.get("end_time", 0.0)),
                    idx,
                ),
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_transcript_by_id(transcript_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves full transcript data including ordered segments and chapters."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM transcripts WHERE id = ?", (transcript_id,))
    tx_row = cursor.fetchone()

    if not tx_row:
        conn.close()
        return None

    transcript = dict(tx_row)

    # Fetch segments
    cursor.execute(
        "SELECT * FROM segments WHERE transcript_id = ? ORDER BY order_index ASC, start_time ASC",
        (transcript_id,),
    )
    transcript["segments"] = [dict(row) for row in cursor.fetchall()]

    # Fetch chapters
    cursor.execute(
        "SELECT * FROM chapters WHERE transcript_id = ? ORDER BY start_time ASC",
        (transcript_id,),
    )
    transcript["chapters"] = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return transcript


def save_transcript_segments(transcript_id: str, segments: List[Dict[str, Any]]) -> None:
    """Updates segments for an existing transcript."""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM segments WHERE transcript_id = ?", (transcript_id,))
        for idx, seg in enumerate(segments):
            seg_id = seg.get("id") or str(uuid.uuid4())
            cursor.execute(
                """
                INSERT INTO segments (id, transcript_id, start_time, end_time, text, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    seg_id,
                    transcript_id,
                    float(seg.get("start_time", 0.0)),
                    float(seg.get("end_time", 0.0)),
                    str(seg.get("text", "")).strip(),
                    idx,
                ),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def save_chapters(transcript_id: str, chapters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Updates and re-orders chapters for an existing transcript."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Sort chapters by start_time
    sorted_chapters = sorted(chapters, key=lambda c: float(c.get("start_time", 0.0)))

    try:
        cursor.execute("DELETE FROM chapters WHERE transcript_id = ?", (transcript_id,))
        saved_list = []
        for idx, ch in enumerate(sorted_chapters):
            ch_id = ch.get("id") or str(uuid.uuid4())
            start_t = float(ch.get("start_time", 0.0))
            end_t = float(ch.get("end_time", 0.0))
            title = str(ch.get("title", f"Chapter {idx + 1}")).strip()

            cursor.execute(
                """
                INSERT INTO chapters (id, transcript_id, title, start_time, end_time, order_index)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (ch_id, transcript_id, title, start_t, end_t, idx),
            )
            saved_list.append({
                "id": ch_id,
                "transcript_id": transcript_id,
                "title": title,
                "start_time": start_t,
                "end_time": end_t,
                "order_index": idx,
            })

        conn.commit()
        return saved_list
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_recent_transcripts(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetches recently created transcripts for dashboard/history drawer."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT t.*, 
               (SELECT COUNT(*) FROM segments WHERE transcript_id = t.id) AS segment_count,
               (SELECT COUNT(*) FROM chapters WHERE transcript_id = t.id) AS chapter_count
        FROM transcripts t
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_transcript_record(transcript_id: str) -> Optional[str]:
    """Deletes transcript and associated records from DB. Returns filename for file deletion."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT filename FROM transcripts WHERE id = ?", (transcript_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    filename = row["filename"]
    cursor.execute("DELETE FROM transcripts WHERE id = ?", (transcript_id,))
    conn.commit()
    conn.close()
    return filename


# Automatically initialize the database tables on import
init_db()
