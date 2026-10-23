"""
app.py - Main Flask Application for Audixa (Audio Transcript & Chapter Maker).
Serves the 2-page web interface (Upload and Editor) and REST API endpoints.
"""

import os
import json
import uuid
import mimetypes
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, render_template, send_from_directory, abort

import db
import transcriber

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024  # 250 MB max upload
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

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


@app.route("/plan.pdf")
@app.route("/download/plan-pdf")
def download_plan_pdf():
    """Downloads the Post-30% Implementation Plan PDF document."""
    pdf_filename = "Audixa_Post_30_Percent_Implementation_Plan.pdf"
    pdf_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(pdf_dir, pdf_filename, as_attachment=True, download_name=pdf_filename)


@app.route("/plan-100.pdf")
@app.route("/download/plan-100-pdf")
def download_plan_100_pdf():
    """Downloads the 100% Final Milestone Implementation Plan PDF document."""
    pdf_filename = "Audixa_100_Percent_Implementation_Plan.pdf"
    pdf_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(pdf_dir, pdf_filename, as_attachment=True, download_name=pdf_filename)


@app.route("/download/project-zip")
def download_project_zip():
    """Downloads the clean 100% final project zip bundle."""
    zip_filename = "Audixa_v1.0_Final_100_Percent.zip"
    zip_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(zip_dir, zip_filename, as_attachment=True, download_name=zip_filename)


@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handles audio/video file upload, executes Whisper transcription,
    generates automatic chapters, saves to SQLite, and returns transcript ID.
    """
    has_file = "file" in request.files and request.files["file"].filename != ""
    link_url = request.form.get("link_url", "").strip()

    if not has_file and not link_url:
        return jsonify({"success": False, "error": "Please select a file, record audio, or provide a media link."}), 400

    # Extract options
    language_mode = request.form.get("language_mode", "auto").strip().lower()
    if language_mode != "auto" and language_mode not in transcriber.SUPPORTED_LANGUAGES:
        language_mode = "auto"

    model_size = request.form.get("model_size", "tiny").strip().lower()
    if model_size not in ["tiny", "base", "small", "medium"]:
        model_size = "tiny"

    task_mode = request.form.get("task_mode", "transcribe").strip().lower()
    if task_mode not in ["transcribe", "translate"]:
        task_mode = "transcribe"

    transcript_id = f"audixa_{uuid.uuid4().hex[:10]}"

    try:
        if link_url:
            storage_filename_base = transcript_id
            outtmpl = os.path.join(app.config["UPLOAD_FOLDER"], f"{storage_filename_base}.%(ext)s")
            saved_path = None
            storage_filename = None
            original_filename = "web_media.mp3"

            # Download audio using yt-dlp
            try:
                import yt_dlp
                ydl_opts = {
                    'format': 'bestaudio/best',
                    'outtmpl': outtmpl,
                    'quiet': True,
                    'no_warnings': True,
                    'noplaylist': True,
                    'max_filesize': 150 * 1024 * 1024,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(link_url, download=True)
                    downloaded_file = ydl.prepare_filename(info)
                    if not os.path.exists(downloaded_file):
                        for f in os.listdir(app.config["UPLOAD_FOLDER"]):
                            if f.startswith(storage_filename_base):
                                downloaded_file = os.path.join(app.config["UPLOAD_FOLDER"], f)
                                break
                    saved_path = downloaded_file
                    storage_filename = os.path.basename(downloaded_file)
                    title = info.get("title") or "web_media"
                    ext = storage_filename.rsplit(".", 1)[-1].lower() if "." in storage_filename else "mp3"
                    original_filename = f"{title}.{ext}"
            except Exception as e:
                # Direct HTTP audio URL fallback
                try:
                    import urllib.request
                    parsed_ext = link_url.split("?")[0].rsplit(".", 1)[-1].lower()
                    if parsed_ext not in ALLOWED_EXTENSIONS:
                        parsed_ext = "mp3"
                    storage_filename = f"{transcript_id}.{parsed_ext}"
                    saved_path = os.path.join(app.config["UPLOAD_FOLDER"], storage_filename)
                    req = urllib.request.Request(
                        link_url, 
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                    )
                    with urllib.request.urlopen(req, timeout=30) as resp, open(saved_path, 'wb') as out_f:
                        out_f.write(resp.read())
                    original_filename = link_url.split("?")[0].split("/")[-1] or f"web_audio.{parsed_ext}"
                except Exception as e2:
                    return jsonify({"success": False, "error": f"Could not fetch audio from link: {str(e)}"}), 400
        else:
            file = request.files["file"]
            if not allowed_file(file.filename):
                return jsonify({
                    "success": False, 
                    "error": f"Unsupported file type. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
                }), 400

            original_filename = secure_filename(file.filename) or "audio_file.mp3"
            ext = original_filename.rsplit(".", 1)[1].lower() if "." in original_filename else "mp3"
            storage_filename = f"{transcript_id}.{ext}"
            saved_path = os.path.join(app.config["UPLOAD_FOLDER"], storage_filename)
            file.save(saved_path)

        # Run Whisper AI transcription and Chapter Generation
        segments, chapters, metadata = transcriber.transcribe_audio(
            file_path=saved_path,
            language_mode=language_mode,
            model_size=model_size,
            task_mode=task_mode,
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
            task_mode=task_mode,
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
    """Saves edited segment text and timestamps."""
    payload = request.get_json(silent=True) or {}
    segments = payload.get("segments", [])
    if not segments:
        return jsonify({"success": False, "error": "No segments provided"}), 400

    db.save_transcript_segments(transcript_id, segments)
    return jsonify({"success": True, "message": "Transcript saved successfully"})


@app.route("/save_chapters/<transcript_id>", methods=["POST"])
def save_chapters(transcript_id):
    """Saves edited chapters list."""
    payload = request.get_json(silent=True) or {}
    chapters = payload.get("chapters", [])
    updated = db.save_chapters(transcript_id, chapters)
    return jsonify({"success": True, "chapters": updated, "message": "Chapters saved successfully"})


@app.route("/api/regenerate_chapters/<transcript_id>", methods=["POST"])
def regenerate_chapters(transcript_id):
    """Regenerates automatic chapters based on pause detection heuristics."""
    record = db.get_transcript_by_id(transcript_id)
    if not record:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    segments = record.get("segments", [])
    duration = record.get("duration", 0.0)
    new_chapters = transcriber.generate_auto_chapters(segments, duration)
    saved_chapters = db.save_chapters(transcript_id, new_chapters)

    return jsonify({
        "success": True,
        "chapters": saved_chapters,
        "message": f"Generated {len(saved_chapters)} automatic chapters"
    })


@app.route("/api/split_segment/<transcript_id>", methods=["POST"])
def split_segment(transcript_id):
    """Splits a single segment into two segments at the given split timestamp."""
    payload = request.get_json(silent=True) or {}
    segment_id = payload.get("segment_id")
    split_time = float(payload.get("split_time", 0.0))

    record = db.get_transcript_by_id(transcript_id)
    if not record:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    segments = record.get("segments", [])
    target_idx = None
    target_seg = None

    for i, seg in enumerate(segments):
        if str(seg.get("id")) == str(segment_id) or str(seg.get("id")).endswith(f"_{segment_id}") or str(seg.get("id")).endswith(str(segment_id)):
            target_idx = i
            target_seg = seg
            break

    if target_seg is None or split_time <= target_seg["start_time"] or split_time >= target_seg["end_time"]:
        return jsonify({"success": False, "error": "Invalid split time or segment"}), 400

    # Split text roughly proportionally or by word boundary
    words = target_seg["text"].split()
    total_dur = max(target_seg["end_time"] - target_seg["start_time"], 0.1)
    split_ratio = (split_time - target_seg["start_time"]) / total_dur
    word_split_idx = max(1, min(len(words) - 1, int(len(words) * split_ratio)))

    seg1 = {
        "id": f"seg_{uuid.uuid4().hex[:8]}",
        "start_time": target_seg["start_time"],
        "end_time": round(split_time, 2),
        "text": " ".join(words[:word_split_idx]),
        "order_index": target_idx
    }
    seg2 = {
        "id": f"seg_{uuid.uuid4().hex[:8]}",
        "start_time": round(split_time, 2),
        "end_time": target_seg["end_time"],
        "text": " ".join(words[word_split_idx:]),
        "order_index": target_idx + 1
    }

    new_segments = segments[:target_idx] + [seg1, seg2] + segments[target_idx + 1:]
    db.save_transcript_segments(transcript_id, new_segments)

    return jsonify({
        "success": True,
        "segments": new_segments,
        "message": "Segment split successfully"
    })


@app.route("/api/merge_segments/<transcript_id>", methods=["POST"])
def merge_segments(transcript_id):
    """Merges two adjacent segments together."""
    payload = request.get_json(silent=True) or {}
    first_segment_id = payload.get("segment_id")

    record = db.get_transcript_by_id(transcript_id)
    if not record:
        return jsonify({"success": False, "error": "Transcript not found"}), 404

    segments = record.get("segments", [])
    target_idx = None

    for i, seg in enumerate(segments):
        if str(seg.get("id")) == str(first_segment_id) or str(seg.get("id")).endswith(f"_{first_segment_id}") or str(seg.get("id")).endswith(str(first_segment_id)):
            target_idx = i
            break

    if target_idx is None or target_idx >= len(segments) - 1:
        return jsonify({"success": False, "error": "Cannot merge last or non-existent segment"}), 400

    seg1 = segments[target_idx]
    seg2 = segments[target_idx + 1]

    merged_seg = {
        "id": seg1["id"],
        "start_time": seg1["start_time"],
        "end_time": seg2["end_time"],
        "text": f"{seg1['text']} {seg2['text']}".strip(),
        "order_index": target_idx
    }

    new_segments = segments[:target_idx] + [merged_seg] + segments[target_idx + 2:]
    db.save_transcript_segments(transcript_id, new_segments)

    return jsonify({
        "success": True,
        "segments": new_segments,
        "message": "Segments merged successfully"
    })


def _format_time_hhmmss(sec: float) -> str:
    m = int(sec // 60)
    s = int(sec % 60)
    return f"{m:02d}:{s:02d}"


def _format_srt_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _format_vtt_time(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


@app.route("/api/export/<transcript_id>/<export_format>")
def export_transcript(transcript_id, export_format):
    """
    Exports transcript in TXT, SRT, VTT, JSON, YouTube Chapters, or Markdown format.
    """
    record = db.get_transcript_by_id(transcript_id)
    if not record:
        abort(404)

    segments = record.get("segments", [])
    chapters = record.get("chapters", [])
    orig_name = record.get("original_name", "transcript")
    base_name = os.path.splitext(orig_name)[0]
    fmt = export_format.lower()

    if fmt == "txt":
        content = "\n\n".join(
            f"[{_format_time_hhmmss(s['start_time'])} - {_format_time_hhmmss(s['end_time'])}] {s.get('speaker', 'Speaker 1')}: {s['text']}"
            for s in segments
        )
        mimetype = "text/plain; charset=utf-8"
        filename = f"{base_name}_transcript.txt"

    elif fmt == "srt":
        lines = []
        for idx, s in enumerate(segments, 1):
            lines.append(f"{idx}")
            lines.append(f"{_format_srt_time(s['start_time'])} --> {_format_srt_time(s['end_time'])}")
            spk_prefix = f"[{s.get('speaker', 'Speaker 1')}] " if s.get('speaker') else ""
            lines.append(f"{spk_prefix}{s['text']}\n")
        content = "\n".join(lines)
        mimetype = "text/plain; charset=utf-8"
        filename = f"{base_name}_subtitles.srt"

    elif fmt == "vtt":
        lines = ["WEBVTT\n"]
        for idx, s in enumerate(segments, 1):
            lines.append(f"{idx}")
            lines.append(f"{_format_vtt_time(s['start_time'])} --> {_format_vtt_time(s['end_time'])}")
            spk_prefix = f"<v {s.get('speaker', 'Speaker 1')}>" if s.get('speaker') else ""
            lines.append(f"{spk_prefix}{s['text']}\n")
        content = "\n".join(lines)
        mimetype = "text/vtt; charset=utf-8"
        filename = f"{base_name}_subtitles.vtt"

    elif fmt == "youtube":
        content = "\n".join(
            f"{_format_time_hhmmss(ch['start_time'])} {ch['title']}"
            for ch in chapters
        )
        mimetype = "text/plain; charset=utf-8"
        filename = f"{base_name}_youtube_chapters.txt"

    elif fmt == "md":
        lines = [
            f"# 🎙️ {orig_name} — Transcript & Chapters",
            f"- **Detected Language:** `{record.get('detected_language', 'Auto')}`",
            f"- **Duration:** `{_format_time_hhmmss(record.get('duration', 0.0))}`",
            f"- **Total Segments:** `{len(segments)}`",
            f"- **Total Chapters:** `{len(chapters)}`\n",
            "## 📑 Chapters"
        ]
        for ch in chapters:
            lines.append(f"- **{_format_time_hhmmss(ch['start_time'])}** — {ch['title']}")

        lines.append("\n## 📝 Full Transcript")
        for s in segments:
            spk = s.get('speaker', 'Speaker 1')
            lines.append(f"> **[{_format_time_hhmmss(s['start_time'])}] {spk}:** {s['text']}\n")

        content = "\n".join(lines)
        mimetype = "text/markdown; charset=utf-8"
        filename = f"{base_name}_summary.md"

    elif fmt == "json":
        content = json.dumps(record, indent=2)
        mimetype = "application/json; charset=utf-8"
        filename = f"{base_name}_data.json"

    elif fmt == "pdf":
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.units import inch

        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, leftMargin=45, rightMargin=45, topMargin=45, bottomMargin=45)
        styles = getSampleStyleSheet()

        C_PRIMARY = colors.HexColor("#8F18A3")
        C_DARK = colors.HexColor("#2B0733")
        C_MUTED = colors.HexColor("#6A3373")
        C_CARD = colors.HexColor("#FAF0F7")
        C_BORDER = colors.HexColor("#ECCDE4")

        title_style = ParagraphStyle('T1', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, leading=20, textColor=C_DARK)
        meta_style = ParagraphStyle('M1', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=C_MUTED)
        h2_style = ParagraphStyle('H2', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=C_PRIMARY, spaceBefore=10, spaceAfter=5)
        text_style = ParagraphStyle('TX', parent=styles['Normal'], fontName='Helvetica', fontSize=8.5, leading=12, textColor=C_DARK, spaceAfter=3)
        ts_style = ParagraphStyle('TS', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=C_PRIMARY)

        story = []
        story.append(Paragraph(f"🎙️ {orig_name}", title_style))
        lang_label = str(record.get('detected_language') or 'Auto').upper()
        dur_label = _format_time_hhmmss(record.get('duration', 0.0))
        story.append(Paragraph(f"<b>Duration:</b> {dur_label} &nbsp;|&nbsp; <b>Language:</b> {lang_label} &nbsp;|&nbsp; <b>Model:</b> {record.get('model_size', 'tiny')} &nbsp;|&nbsp; <b>Segments:</b> {len(segments)}", meta_style))
        story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceBefore=4, spaceAfter=8))

        if chapters:
            story.append(Paragraph("📑 Chapters Overview", h2_style))
            ch_data = [[Paragraph("Timestamp", ts_style), Paragraph("Chapter Title", ts_style)]]
            for ch in chapters:
                ch_data.append([
                    Paragraph(f"<b>{_format_time_hhmmss(ch['start_time'])}</b>", text_style),
                    Paragraph(ch.get('title', 'Chapter'), text_style)
                ])
            t_ch = Table(ch_data, colWidths=[1.2*inch, 5.8*inch])
            t_ch.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), C_CARD),
                ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
                ('TOPPADDING', (0, 0), (-1, -1), 2.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
            ]))
            story.append(t_ch)
            story.append(Spacer(1, 8))

        story.append(Paragraph("📝 Full Synchronized Transcript", h2_style))
        for s in segments:
            spk = s.get('speaker', 'Speaker 1')
            time_str = f"{_format_time_hhmmss(s['start_time'])} - {_format_time_hhmmss(s['end_time'])}"
            story.append(Paragraph(f"<b>[{time_str}]</b> <font color='#758359'><b>{spk}:</b></font> {s['text']}", text_style))

        doc.build(story)
        from flask import Response
        return Response(
            pdf_buffer.getvalue(),
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={base_name}_transcript.pdf"}
        )

    else:
        return jsonify({"success": False, "error": f"Unsupported format: {fmt}"}), 400

    from flask import Response
    return Response(
        content,
        mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/audio/<transcript_id>")
def serve_audio(transcript_id):
    """
    Streams audio/video file with HTTP 206 Partial Content support
    for smooth WaveSurfer.js rendering and seeking.
    """
    record = db.get_transcript_by_id(transcript_id)
    if not record:
        abort(404)

    filename = record["filename"]
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        abort(404)

    # Determine mime type
    mtype, _ = mimetypes.guess_type(filename)
    if not mtype:
        mtype = "audio/mpeg"

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        mimetype=mtype,
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


def _preload_whisper_in_background():
    """Pre-warms the default Whisper model in the background so uploads are instant."""
    import threading
    def _loader():
        try:
            transcriber.get_whisper_model("tiny")
        except Exception as e:
            print(f"[Audixa] Background model warm-up notice: {e}")
    threading.Thread(target=_loader, daemon=True).start()


if __name__ == "__main__":
    _preload_whisper_in_background()
    print("[Audixa] Starting server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

