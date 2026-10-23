import os
import sys
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#5C684E"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 11 * inch - 36, "Audixa — Post-30% Implementation Plan & Technical Architecture")
            self.setStrokeColor(colors.HexColor("#D5DEC3"))
            self.setLineWidth(0.5)
            self.line(45, 11 * inch - 42, 8.5 * inch - 45, 11 * inch - 42)
        
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 45, 30, page_str)
        self.drawString(45, 30, "Confidential — Audixa Engineering & Academic Evaluation Report")
        self.setStrokeColor(colors.HexColor("#D5DEC3"))
        self.setLineWidth(0.5)
        self.line(45, 42, 8.5 * inch - 45, 42)
        
        self.restoreState()

def build_pdf(filename="Audixa_Implementation_Plan.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Color Palette: Radiant Purple & Orchid Rose Theme
    C_PRIMARY = colors.HexColor("#8F18A3")
    C_PRIMARY_DARK = colors.HexColor("#630D72")
    C_TEXT = colors.HexColor("#2B0733")
    C_MUTED = colors.HexColor("#6A3373")
    C_BG_CARD = colors.HexColor("#FAF0F7")
    C_ACCENT_SAGE = colors.HexColor("#EE97D8")
    C_BORDER = colors.HexColor("#ECCDE4")

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=C_PRIMARY_DARK,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=C_MUTED,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=17,
        textColor=C_PRIMARY_DARK,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=C_PRIMARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=C_TEXT,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    table_header_style = ParagraphStyle(
        'DocTableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=0
    )

    table_cell_style = ParagraphStyle(
        'DocTableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=C_TEXT
    )

    table_cell_bold = ParagraphStyle(
        'DocTableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8,
        leading=10.5,
        textColor=C_TEXT
    )

    story = []

    # Title Block
    story.append(Paragraph("🎙️ Audixa — Project Implementation Plan & Technical Report", title_style))
    story.append(Paragraph("<b>Stage:</b> Post-30% Implementation & 60% Milestone Review &nbsp;|&nbsp; <b>Tech:</b> Python, Flask, Faster-Whisper, WaveSurfer.js, SQLite", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceBefore=0, spaceAfter=12))

    # 1. Executive Summary
    story.append(Paragraph("1. Executive Summary & Milestone Progress", h1_style))
    story.append(Paragraph(
        "Audixa is a dedicated, web-based speech synchronization and content structuring platform designed to convert lengthy audio and video recordings into interactive transcripts, time-synchronized waveforms, and auto-generated video chapters. Following the initial 30% UI scaffolding milestone, the platform has reached a fully functional <b>60% working state</b> with an active local AI speech recognition pipeline, 3-panel synchronized editor, multi-format exports, and database persistence.",
        body_style
    ))

    # Matrix Table
    matrix_data = [
        [Paragraph("Feature / Subsystem", table_header_style), Paragraph("Initial 30% Baseline", table_header_style), Paragraph("Post-30% Implementation (Current)", table_header_style)],
        [
            Paragraph("<b>Speech-to-Text</b>", table_cell_style),
            Paragraph("Static JSON mockup fixtures", table_cell_style),
            Paragraph("<b>Live local Faster-Whisper AI</b> (int8 quantization, CTranslate2 engine).", table_cell_style)
        ],
        [
            Paragraph("<b>Inference Speed</b>", table_cell_style),
            Paragraph("N/A (no model execution)", table_cell_style),
            Paragraph("<b>3x–5x acceleration</b> via multi-threading, greedy 1-beam search, VAD filtering.", table_cell_style)
        ],
        [
            Paragraph("<b>Audio Player</b>", table_cell_style),
            Paragraph("Basic static canvas container", table_cell_style),
            Paragraph("<b>Bi-directional WaveSurfer sync</b>, speed pitching (0.5x–2x), volume slider, mute.", table_cell_style)
        ],
        [
            Paragraph("<b>Transcript Editor</b>", table_cell_style),
            Paragraph("Read-only placeholder text", table_cell_style),
            Paragraph("<b>Live active segment highlight</b>, smooth auto-scroll, in-line editing, click-to-seek.", table_cell_style)
        ],
        [
            Paragraph("<b>Chapter Maker</b>", table_cell_style),
            Paragraph("Wireframe cards only", table_cell_style),
            Paragraph("<b>Pause-gap (>=1.5s) auto-detection</b>, manual '+ Add Chapter', inline rename.", table_cell_style)
        ],
        [
            Paragraph("<b>Export Engine</b>", table_cell_style),
            Paragraph("Disabled UI dropdown menu", table_cell_style),
            Paragraph("<b>6 Live Formats</b>: TXT, SubRip (.srt), WebVTT (.vtt), YouTube Chapters, Markdown, JSON.", table_cell_style)
        ],
        [
            Paragraph("<b>Database Storage</b>", table_cell_style),
            Paragraph("Basic schema prone to collisions", table_cell_style),
            Paragraph("<b>Scoped IDs</b>, INSERT OR REPLACE transactions, foreign key cascades, manual saves.", table_cell_style)
        ],
        [
            Paragraph("<b>UI/UX Design</b>", table_cell_style),
            Paragraph("Cluttered with debug badges", table_cell_style),
            Paragraph("<b>Streamlined Organic Warm Sage layout</b> with eliminated button clutter.", table_cell_style)
        ]
    ]

    t_matrix = Table(matrix_data, colWidths=[1.3*inch, 2.0*inch, 3.7*inch])
    t_matrix.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_matrix)
    story.append(Spacer(1, 10))

    # 2. AI Speech Recognition Pipeline
    story.append(Paragraph("2. AI Speech Recognition & Speed Architecture", h1_style))
    story.append(Paragraph(
        "To replace the static fixtures from Phase 1, Audixa integrates <b>Faster-Whisper</b>—a high-efficiency CTranslate2 reimplementation of OpenAI's Whisper model optimized for fast CPU execution.",
        body_style
    ))

    story.append(Paragraph("• <b>Multi-Threaded CPU Scaling:</b> Automatically detects all available CPU cores using <code>os.cpu_count()</code> (utilizing 12 hardware threads) for parallelized tensor operations.", bullet_style))
    story.append(Paragraph("• <b>int8 Quantization:</b> Compresses neural weights from float32 to 8-bit integers, halving memory bandwidth and accelerating execution on standard CPU hardware.", bullet_style))
    story.append(Paragraph("• <b>Greedy 1-Beam Search:</b> Sets <code>beam_size=1</code> and <code>best_of=1</code>, reducing decoding latency by ~70% over beam-5 search while preserving word accuracy.", bullet_style))
    story.append(Paragraph("• <b>Voice Activity Detection (VAD):</b> Integrates Silero VAD (<code>vad_filter=True</code>) to discard non-speech silence and prevent repetitive looping.", bullet_style))
    story.append(Paragraph("• <b>Background Model Pre-Warming:</b> Spawns a background thread on server startup to load weights into memory, ensuring zero cold-start delay for the first user upload.", bullet_style))
    story.append(Paragraph("• <b>Language Support:</b> Provides dedicated modes for English (<code>en</code>), Hindi (<code>hi</code>), and mixed bilingual Hinglish (<code>auto</code>).", bullet_style))
    story.append(Spacer(1, 10))

    # 3. Synchronized 3-Panel Editor
    story.append(Paragraph("3. Synchronized 3-Panel Editor Architecture", h1_style))
    story.append(Paragraph(
        "The core studio interface (<code>editor.html</code> & <code>editor.js</code>) delivers a multi-panel workspace where audio playback, transcription text, and chapter markers are kept in real-time synchronization.",
        body_style
    ))

    editor_data = [
        [Paragraph("Panel", table_header_style), Paragraph("Core Features & Technical Implementation", table_header_style)],
        [
            Paragraph("<b>Panel A:<br/>Audio Waveform & Player</b>", table_cell_style),
            Paragraph("• Interactive canvas waveform generated via <b>WaveSurfer.js v7</b>.<br/>• Real-time timeupdate event dispatching.<br/>• Play/Pause with spacebar shortcut.<br/>• Speed selector: 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 2.0x.<br/>• Real-time volume slider and one-click mute toggle.", table_cell_style)
        ],
        [
            Paragraph("<b>Panel B:<br/>Interactive Transcript</b>", table_cell_style),
            Paragraph("• <b>Live Active Segment Highlighting:</b> Compares audio playhead to segment intervals and applies high-contrast active styling.<br/>• <b>Auto-Scroll:</b> Smoothly scrolls dialogue into view as speaker advances.<br/>• <b>In-Line Editing:</b> Editable segment text via <code>contenteditable=\"true\"</code>.<br/>• <b>Click-to-Seek:</b> Clicking timestamp badges seeks audio instantly.<br/>• <b>Instant Filter:</b> Live client-side phrase search with match counter.<br/>• <b>Segment Deletion:</b> Single-click segment deletion.", table_cell_style)
        ],
        [
            Paragraph("<b>Panel C:<br/>Auto-Chapter Maker</b>", table_cell_style),
            Paragraph("• <b>Pause-Gap Detection:</b> Heuristic scans speech pauses (&ge; 1.5s) to propose logical topic transitions.<br/>• <b>Manual Creation:</b> <code>+ Add Chapter</code> creates a chapter at the exact playhead position.<br/>• <b>In-Line Title Renaming:</b> Direct text input for custom chapter names.<br/>• <b>Click-to-Seek:</b> Clicking a chapter jumps audio directly to that topic.", table_cell_style)
        ]
    ]

    t_editor = Table(editor_data, colWidths=[2.0*inch, 5.0*inch])
    t_editor.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_editor)
    story.append(Spacer(1, 10))

    # 4. UI/UX Decluttering
    story.append(Paragraph("4. UI/UX Streamlining & Decluttering (Post-30% Refinements)", h1_style))
    story.append(Paragraph(
        "To provide a clean, distraction-free editing environment, several redundant buttons, auxiliary badges, and repetitive indicators were removed per interface evaluation:",
        body_style
    ))
    story.append(Paragraph("• <b>Removed Skip Buttons:</b> Removed <code>-5s</code> and <code>+5s</code> buttons from the audio player controls.", bullet_style))
    story.append(Paragraph("• <b>Removed Auto-saved Text:</b> Cleaned duplicate status text underneath the chapters panel.", bullet_style))
    story.append(Paragraph("• <b>Cleaned Chapter Actions:</b> Replaced the auxiliary <code>Auto-Detect</code> button and dynamic <code>+ Add at 01:27</code> label with a single clean <b><code>+ Add Chapter</code></b> button.", bullet_style))
    story.append(Paragraph("• <b>Removed Header Badges:</b> Removed <code>Auto / Hinglish</code>, <code>⏱️ duration</code>, <code>✓ Saved</code>, and <code>📁 History</code> pills from the top navigation bar.", bullet_style))
    story.append(Paragraph("• <b>Cleaned Segment Cards:</b> Removed <code>#index</code> labels and <code>✂️ Split</code> / <code>🔗 Merge</code> buttons from segment card headers.", bullet_style))
    story.append(Paragraph("• <b>Cleaned Transcript Toolbar:</b> Removed <code>123 words</code> counter, <code>+ Add Segment</code>, and find-replace popups, retaining direct in-line editing and search.", bullet_style))
    story.append(Spacer(1, 10))

    # 5. Multi-Format Export Engine
    story.append(Paragraph("5. Multi-Format Export Engine", h1_style))
    story.append(Paragraph(
        "Audixa provides direct file downloads via <code>/api/export/&lt;id&gt;/&lt;format&gt;</code> supporting 6 standard media workflows:",
        body_style
    ))

    export_data = [
        [Paragraph("Format", table_header_style), Paragraph("Extension", table_header_style), Paragraph("Output Specification", table_header_style), Paragraph("Primary Use Case", table_header_style)],
        [Paragraph("Plain Text", table_cell_bold), Paragraph(".txt", table_cell_style), Paragraph("Clean transcript text with timestamps.", table_cell_style), Paragraph("Documentation, study notes.", table_cell_style)],
        [Paragraph("SubRip Subtitles", table_cell_bold), Paragraph(".srt", table_cell_style), Paragraph("Numbered subtitle blocks with comma ms timestamps.", table_cell_style), Paragraph("Premiere, DaVinci, Final Cut.", table_cell_style)],
        [Paragraph("WebVTT", table_cell_bold), Paragraph(".vtt", table_cell_style), Paragraph("HTML5 subtitle track format with dot ms timestamps.", table_cell_style), Paragraph("Web video players & LMS.", table_cell_style)],
        [Paragraph("YouTube Chapters", table_cell_bold), Paragraph(".txt", table_cell_style), Paragraph("Standard timestamp list (00:00 Intro\\n01:15 Topic 1).", table_cell_style), Paragraph("YouTube video descriptions.", table_cell_style)],
        [Paragraph("Markdown Summary", table_cell_bold), Paragraph(".md", table_cell_style), Paragraph("Formatted doc with headings, metadata, and blockquotes.", table_cell_style), Paragraph("Notion, GitHub, Obsidian.", table_cell_style)],
        [Paragraph("Full JSON", table_cell_bold), Paragraph(".json", table_cell_style), Paragraph("Complete structured schema with segment arrays.", table_cell_style), Paragraph("API integrations & pipelines.", table_cell_style)],
    ]

    t_export = Table(export_data, colWidths=[1.3*inch, 0.8*inch, 2.7*inch, 2.2*inch])
    t_export.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_export)
    story.append(Spacer(1, 10))

    # 6. Database & REST API Architecture
    story.append(Paragraph("6. Database & REST API Architecture", h1_style))
    story.append(Paragraph(
        "Audixa utilizes SQLite (<code>audixa.db</code>) with 3 relational tables (<code>transcripts</code>, <code>segments</code>, <code>chapters</code>) featuring foreign key cascade deletions and scoped ID keys (<code>transcript_id_raw_id</code>) using <code>INSERT OR REPLACE</code> to prevent primary key collision errors.",
        body_style
    ))

    api_data = [
        [Paragraph("Method", table_header_style), Paragraph("Route", table_header_style), Paragraph("Description & Output", table_header_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/upload", table_cell_style), Paragraph("Uploads media, runs Whisper AI & pause chaptering, returns transcript ID.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/transcript/&lt;id&gt;", table_cell_style), Paragraph("Returns metadata, segments list, chapters list, and audio URL.", table_cell_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/save_transcript/&lt;id&gt;", table_cell_style), Paragraph("Persists updated segment text and timestamps into SQLite.", table_cell_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/save_chapters/&lt;id&gt;", table_cell_style), Paragraph("Persists updated chapter titles and timestamps into SQLite.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/api/export/&lt;id&gt;/&lt;fmt&gt;", table_cell_style), Paragraph("Streams exported file (txt, srt, vtt, youtube, md, json).", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/audio/&lt;id&gt;", table_cell_style), Paragraph("Streams raw audio with HTTP 206 Partial Content byte ranges.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/api/health", table_cell_style), Paragraph("Health check returning backend and engine readiness.", table_cell_style)]
    ]

    t_api = Table(api_data, colWidths=[0.8*inch, 1.9*inch, 4.3*inch])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 10))

    # 7. Automated Testing & Verification
    story.append(Paragraph("7. Automated Testing & Verification", h1_style))
    story.append(Paragraph(
        "All 8 automated backend and integration test suites pass with 100% success rate (<code>Ran 8 tests in ~3.5s: OK</code>):",
        body_style
    ))
    story.append(Paragraph("• <b>test_01_db_crud:</b> Verified SQLite insertion, queries, and foreign key cascades.", bullet_style))
    story.append(Paragraph("• <b>test_02_routes_get:</b> Verified HTTP 200 responses on <code>/</code> and <code>/editor</code>.", bullet_style))
    story.append(Paragraph("• <b>test_03_api_endpoints:</b> Verified JSON API health and metadata endpoints.", bullet_style))
    story.append(Paragraph("• <b>test_04_upload_flow:</b> End-to-end Whisper speech recognition test (10.3s audio in 2.8s).", bullet_style))
    story.append(Paragraph("• <b>test_05_segment_split_and_merge:</b> Verified split/merge data consistency.", bullet_style))
    story.append(Paragraph("• <b>test_06_regenerate_chapters:</b> Verified pause-gap chaptering heuristic.", bullet_style))
    story.append(Paragraph("• <b>test_07_export_endpoints:</b> Verified byte streaming for all 6 export formats.", bullet_style))
    story.append(Paragraph("• <b>test_08_history_and_health:</b> Verified history fetching and deletion cascades.", bullet_style))
    story.append(Spacer(1, 10))

    # 8. Viva Review Presentation Guide
    story.append(Paragraph("8. Viva & Faculty Review Q&A Guide", h1_style))
    story.append(Paragraph("<b>Q1: What major progress has been made since the 30% milestone?</b><br/><b>A:</b> We transitioned from static mockups to a live local AI speech recognition pipeline (Faster-Whisper), built the synchronized 3-panel editor with active highlight and auto-scroll, implemented the pause-gap chaptering heuristic, built 6 export formats, and hardened the SQLite database.", body_style))
    story.append(Paragraph("<b>Q2: How is transcription made fast on local CPUs?</b><br/><b>A:</b> Using CTranslate2 with int8 quantization, multi-threading across all 12 CPU hardware threads, greedy 1-beam search, Silero VAD silence filtering, and background model pre-warming.", body_style))
    story.append(Paragraph("<b>Q3: How does the editor synchronize playback with transcript?</b><br/><b>A:</b> WaveSurfer dispatches <code>timeupdate</code> events; the editor compares the playhead against segment boundaries <code>[start_time, end_time]</code>, applies the active CSS class, and auto-scrolls smoothly.", body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[Audixa] PDF generated successfully at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Audixa_Post_30_Percent_Implementation_Plan.pdf"
    build_pdf(out_file)
