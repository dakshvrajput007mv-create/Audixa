"""
app.py - Main Flask Application for Audixa (Audio Transcript & Chapter Maker).
Serves the 2-page web interface (Upload and Editor) and REST API endpoints.
"""

import os
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, abort

import db
import transcriber

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024  # 250 MB max upload

if os.environ.get("VERCEL"):
    app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
else:
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
db.init_db()

ALLOWED_EXTENSIONS = {"mp3", "wav", "m4a", "mp4", "ogg", "flac", "webm", "aac", "wma"}


def allowed_file(filename: str) -> bool:
    """Checks if the file extension is supported."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Page 1: Upload Page."""
    return render_template("index.html")


@app.route("/editor")
@app.route("/editor.html")
def editor():
    """Page 2: Editor Page."""
    transcript_id = request.args.get("id", "").strip()
    return render_template("editor.html", transcript_id=transcript_id)


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handles audio/video file upload, executes Whisper transcription,
    generates automatic chapters, saves to SQLite, and returns transcript ID.
    """
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({
            "success": False, 
            "error": f"Unsupported file type. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        }), 400

    # Extract options
    language_mode = request.form.get("language_mode", "auto").strip().lower()
    if language_mode not in ["en", "hi", "auto"]:
        language_mode = "auto"

    model_size = request.form.get("model_size", "base").strip().lower()
    if model_size not in ["tiny", "base", "small", "medium"]:
        model_size = "base"

    # Generate unique ID and save file
    original_filename = secure_filename(file.filename) or "audio_file.mp3"
    ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "mp3"
    transcript_id = f"audixa_{uuid.uuid4().hex[:10]}"
    storage_filename = f"{transcript_id}.{ext}"
    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], storage_filename)

    try:
        file.save(saved_path)

        # Run Whisper AI transcription and Chapter Generation
        segments, chapters, metadata = transcriber.transcribe_audio(
            file_path=saved_path,
            language_mode=language_mode,
            model_size=model_size,
        )

        # Save to SQLite Database
        db.save_full_transcript(
            transcript_id=transcript_id,
            filename=storage_filename,
            original_name=original_filename,
            language_mode=language_mode,
            detected_language=metadata.get("detected_language"),
            duration=metadata.get("duration", 0.0),
            model_size=model_size,
            segments=segments,
            chapters=chapters,
        )

        return jsonify({
            "success": True,
            "id": transcript_id,
            "filename": original_filename,
            "redirect_url": f"/editor?id={transcript_id}",
            "metadata": metadata,
            "segments_count": len(segments),
            "chapters_count": len(chapters),
        })

    except Exception as e:
        print(f"[Audixa Error] Upload / Transcription failed: {e}")
        # Clean up partially saved file if needed
        if os.path.exists(saved_path) and not db.get_transcript_by_id(transcript_id):
            try:
                os.remove(saved_path)
            except Exception:
                pass
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/transcript/<transcript_id>", methods=["GET"])
def get_transcript(transcript_id):
    """Returns stored transcript metadata, segments, and chapters from SQLite."""
    data = db.get_transcript_by_id(transcript_id)
    if not data:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    # Include audio stream URL
    data["audio_url"] = f"/audio/{transcript_id}"
    return jsonify({"success": True, "data": data})


@app.route("/save_transcript/<transcript_id>", methods=["POST"])
def save_transcript(transcript_id):
    """Updates transcript segments in SQLite."""
    payload = request.get_json(silent=True)
    if not payload or "segments" not in payload:
        return jsonify({"success": False, "error": "Missing segments in request body"}), 400

    existing = db.get_transcript_by_id(transcript_id)
    if not existing:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    try:
        db.save_transcript_segments(transcript_id, payload["segments"])
        return jsonify({"success": True, "message": "Transcript saved successfully"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/save_chapters/<transcript_id>", methods=["POST"])
def save_chapters(transcript_id):
    """Updates and re-orders chapters in SQLite."""
    payload = request.get_json(silent=True)
    if not payload or "chapters" not in payload:
        return jsonify({"success": False, "error": "Missing chapters in request body"}), 400

    existing = db.get_transcript_by_id(transcript_id)
    if not existing:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    try:
        saved_chapters = db.save_chapters(transcript_id, payload["chapters"])
        return jsonify({
            "success": True, 
            "message": "Chapters saved successfully",
            "chapters": saved_chapters
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/audio/<transcript_id>")
def serve_audio(transcript_id):
    """Serves the stored media file for playback with HTTP range support."""
    data = db.get_transcript_by_id(transcript_id)
    if not data:
        abort(404, description="Transcript not found")

    filename = data["filename"]
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        abort(404, description="Media file not found on disk")

    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "audio/mpeg"

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        mimetype=mime_type,
        as_attachment=False,
        conditional=True  # Enables 206 Partial Content byte range requests
    )


@app.route("/api/history")
def history():
    """Returns recently transcribed files for quick access."""
    recent = db.get_recent_transcripts(limit=12)
    return jsonify({"success": True, "history": recent})


@app.route("/api/delete/<transcript_id>", methods=["DELETE", "POST"])
def delete_transcript(transcript_id):
    """Deletes transcript from DB and removes its audio file."""
    filename = db.delete_transcript_record(transcript_id)
    if filename:
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return jsonify({"success": True, "message": "Transcript deleted"})
    return jsonify({"success": False, "error": "Not found"}), 404


@app.route("/api/health")
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "app": "Audixa", "whisper_ready": True})


if __name__ == "__main__":
    print("[Audixa] Starting server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)

