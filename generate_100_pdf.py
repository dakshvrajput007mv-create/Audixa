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
        self.setFillColor(colors.HexColor("#6A3373"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 11 * inch - 36, "Audixa — Final 100% Milestone Implementation Plan & Technical Blueprint")
            self.setStrokeColor(colors.HexColor("#ECCDE4"))
            self.setLineWidth(0.5)
            self.line(45, 11 * inch - 42, 8.5 * inch - 45, 11 * inch - 42)
        
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 45, 30, page_str)
        self.drawString(45, 30, "Audixa Engineering & Academic Evaluation Report — 100% Production Milestone")
        self.setStrokeColor(colors.HexColor("#ECCDE4"))
        self.setLineWidth(0.5)
        self.line(45, 42, 8.5 * inch - 45, 42)
        
        self.restoreState()

def build_pdf(filename="Audixa_100_Percent_Implementation_Plan.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Color Palette: Radiant Purple & Orchid Blossom Design System
    C_PRIMARY = colors.HexColor("#8F18A3")
    C_PRIMARY_DARK = colors.HexColor("#50155B")
    C_TEXT = colors.HexColor("#2B0733")
    C_MUTED = colors.HexColor("#6A3373")
    C_BG_CARD = colors.HexColor("#FAF0F7")
    C_ACCENT_SAGE = colors.HexColor("#FFC1DF")
    C_BORDER = colors.HexColor("#ECCDE4")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=23,
        textColor=C_PRIMARY_DARK,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=C_MUTED,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=C_PRIMARY_DARK,
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=C_PRIMARY,
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=C_TEXT,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2.5
    )

    table_header_style = ParagraphStyle(
        'DocTableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=colors.white,
        alignment=0
    )

    table_cell_style = ParagraphStyle(
        'DocTableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=10,
        textColor=C_TEXT
    )

    table_cell_bold = ParagraphStyle(
        'DocTableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Title Block
    story.append(Paragraph("🎙️ Audixa — Final 100% Milestone Implementation Plan", title_style))
    story.append(Paragraph("<b>Target:</b> Production-Grade Speech Studio & Final Evaluation &nbsp;|&nbsp; <b>Stack:</b> Faster-Whisper, WaveSurfer.js, Flask, SQLite, ReportLab", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_PRIMARY, spaceBefore=0, spaceAfter=10))

    # 1. Executive Summary & Full Milestone Evolution
    story.append(Paragraph("1. Executive Summary & Complete Milestone Evolution", h1_style))
    story.append(Paragraph(
        "Audixa has evolved from an initial concept into a full-featured speech-to-text intelligence studio. Below is the multi-phase milestone progression from initial scaffolding to complete 100% production readiness:",
        body_style
    ))

    roadmap_data = [
        [Paragraph("Milestone Phase", table_header_style), Paragraph("Status", table_header_style), Paragraph("Key Features & Deliverables", table_header_style)],
        [
            Paragraph("<b>Phase 1 (30% Milestone)</b>", table_cell_style),
            Paragraph("✅ COMPLETED", table_cell_bold),
            Paragraph("Custom flat UI tokens, initial 2-page layout grids, basic SQLite schema, WaveSurfer.js audio player foundation.", table_cell_style)
        ],
        [
            Paragraph("<b>Phase 2 (60% Milestone)</b>", table_cell_style),
            Paragraph("✅ COMPLETED", table_cell_bold),
            Paragraph("Live local Faster-Whisper AI engine, multi-core CPU threading, synchronized 3-panel playback, active highlight, auto-scroll, in-line editing, pause-gap auto-chapters, 6 export formats, and decluttered UI.", table_cell_style)
        ],
        [
            Paragraph("<b>Phase 3 (100% Final)</b>", table_cell_style),
            Paragraph("🚀 ACTIVE BUILD", table_cell_bold),
            Paragraph("<b>25+ Multilingual Engine</b> (Indian regional + global), <b>Speech-to-English translation</b>, <b>Dark/Light theme switcher</b> (Warm Sage & Midnight Moss), <b>Waveform Chapter Pins</b>, <b>Speaker Diarization Tagging</b>, <b>Speech Metrics (WPM)</b>, <b>Session History Drawer</b>, and <b>PDF Export</b>.", table_cell_style)
        ]
    ]

    t_roadmap = Table(roadmap_data, colWidths=[1.8*inch, 1.2*inch, 4.0*inch])
    t_roadmap.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_roadmap)
    story.append(Spacer(1, 8))

    # 2. Key Suggestions & Upgrades for 100%
    story.append(Paragraph("2. Key Suggestions & Feature Enhancements for 100% Completion", h1_style))
    story.append(Paragraph(
        "To elevate Audixa to a commercial-grade, award-winning application, the following strategic enhancements form the core of the 100% implementation:",
        body_style
    ))

    story.append(Paragraph("• <b>25+ Language Multilingual Expansion:</b> Native support for Indian regional languages (Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Malayalam, Punjabi) and international languages with auto-detection confidence scoring.", bullet_style))
    story.append(Paragraph("• <b>AI Speech-to-English Translation (task='translate'):</b> Transcribes foreign speech directly into fluent English subtitles, unlocking cross-lingual podcasts and international lectures.", bullet_style))
    story.append(Paragraph("• <b>Best UI/UX Design System (Day/Night Modes):</b> Smooth transition between Warm Sage Light Mode and Midnight Moss Dark Mode with CSS custom properties.", bullet_style))
    story.append(Paragraph("• <b>Waveform Chapter Visual Pins:</b> Proportional chapter divider lines rendered right over the WaveSurfer audio timeline for visual scrubbing.", bullet_style))
    story.append(Paragraph("• <b>Speaker Diarization & Attribution:</b> Segment labeling with customizable speaker tags (e.g., Speaker A, Speaker B, Host, Guest) and distinctive pastel badges.", bullet_style))
    story.append(Paragraph("• <b>Live Speech Metrics:</b> Real-time analytics bar displaying Total Word Count, Speaking Rate in Words Per Minute (WPM), and Estimated Reading Time.", bullet_style))
    story.append(Paragraph("• <b>History Session Drawer:</b> Sliding sidebar allowing users to browse, search, and reload previous audio sessions stored in SQLite.", bullet_style))
    story.append(Paragraph("• <b>Interactive Keyboard Shortcuts Modal:</b> Power-user hotkeys for playback, seeking, and quick-saving with on-screen modal help.", bullet_style))
    story.append(Paragraph("• <b>Publication-Quality PDF Export:</b> Beautifully typeset PDF documents containing timestamps, speaker tags, and chapter summaries.", bullet_style))
    story.append(Spacer(1, 8))

    # 3. Multilingual Engine Architecture
    story.append(Paragraph("3. Multilingual Speech Engine Architecture (25+ Languages)", h1_style))
    story.append(Paragraph(
        "The multilingual engine categorizes supported languages into organized dropdown groups for intuitive selection, coupled with Whisper's direct translation pipeline:",
        body_style
    ))

    lang_data = [
        [Paragraph("Category", table_header_style), Paragraph("Languages Supported", table_header_style), Paragraph("Engine Implementation & Script", table_header_style)],
        [
            Paragraph("<b>Auto-Detect & Mixed</b>", table_cell_bold),
            Paragraph("Auto-detect (Hinglish, Multilingual Code-switching)", table_cell_style),
            Paragraph("Whisper language=None mode with phonetic token language identification.", table_cell_style)
        ],
        [
            Paragraph("<b>Indian Regional</b>", table_cell_bold),
            Paragraph("Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Malayalam, Punjabi", table_cell_style),
            Paragraph("Native Devanagari, Bengali, Dravidian, and Perso-Arabic script vocabularies.", table_cell_style)
        ],
        [
            Paragraph("<b>Global International</b>", table_cell_bold),
            Paragraph("English, Spanish, French, German, Japanese, Chinese (Mandarin), Russian, Portuguese, Italian, Arabic, Korean, Dutch, Turkish, Vietnamese", table_cell_style),
            Paragraph("High-accuracy multilingual vocabulary with native character tokenization.", table_cell_style)
        ],
        [
            Paragraph("<b>Translation Mode</b>", table_cell_bold),
            Paragraph("Any foreign language &rarr; English", table_cell_style),
            Paragraph("Whisper task='translate' pipeline generates English subtitles directly from audio.", table_cell_style)
        ]
    ]

    t_lang = Table(lang_data, colWidths=[1.5*inch, 2.5*inch, 3.0*inch])
    t_lang.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_lang)
    story.append(Spacer(1, 8))

    # 4. Best UI/UX Design System & 3-Panel Studio
    story.append(Paragraph("4. Best-in-Class UI/UX & Synchronized Studio Specifications", h1_style))
    story.append(Paragraph(
        "Audixa 100% adopts a refined, distraction-free design architecture with dual themes and rich micro-interactions:",
        body_style
    ))

    ux_data = [
        [Paragraph("UI Component", table_header_style), Paragraph("100% Final Enhancements & Technical Design", table_header_style)],
        [
            Paragraph("<b>Theme Engine<br/>(Day & Night)</b>", table_cell_bold),
            Paragraph("• <b>Warm Sage Light Mode:</b> #F8F6EB (Linen background), #758359 (Olive actions), #242D1C (Forest text).<br/>• <b>Midnight Moss Dark Mode:</b> #131710 (Deep dark canvas), #1E2519 (Panel cards), #C6D99E (Mint highlights).<br/>• Instant theme switching with zero layout shift via CSS custom property overrides.", table_cell_style)
        ],
        [
            Paragraph("<b>Waveform & Chapter Visual Pins</b>", table_cell_bold),
            Paragraph("• WaveSurfer v7 high-resolution audio waveform with responsive canvas resizing.<br/>• <b>Chapter Timeline Pins:</b> Proportional markers placed along the waveform bar matching chapter start times.<br/>• Clicking any marker seeks audio to that exact moment and triggers smooth auto-scroll.", table_cell_style)
        ],
        [
            Paragraph("<b>Interactive Transcript & Speaker Tags</b>", table_cell_bold),
            Paragraph("• <b>Active Segment Highlight:</b> Real-time CSS transition on the active dialogue card.<br/>• <b>Speaker Attribution:</b> Customizable dropdown/badge on each segment (Speaker 1, Speaker 2, Host, Guest).<br/>• <b>In-Line Editing:</b> Editable contenteditable text fields with manual or debounced background save.<br/>• <b>Speech Analytics:</b> Real-time display of WPM, total word count, and reading time.", table_cell_style)
        ],
        [
            Paragraph("<b>Session History & Keyboard Shortcuts</b>", table_cell_bold),
            Paragraph("• <b>History Drawer:</b> Sliding side-panel allowing users to inspect past audio transcripts without leaving the page.<br/>• <b>Hotkeys Sheet Modal:</b> Space (Play/Pause), J/L (Seek +/-5s), Ctrl+S (Save), / (Search), ? (Shortcuts sheet).", table_cell_style)
        ]
    ]

    t_ux = Table(ux_data, colWidths=[2.0*inch, 5.0*inch])
    t_ux.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_ux)
    story.append(Spacer(1, 8))

    # 5. Multi-Format Export Engine (7 Formats)
    story.append(Paragraph("5. Complete Multi-Format Export Engine (7 Formats)", h1_style))
    story.append(Paragraph(
        "Audixa supports direct one-click exports covering media editing, publishing, video descriptions, and academic reporting:",
        body_style
    ))

    export_data = [
        [Paragraph("Export Format", table_header_style), Paragraph("Ext", table_header_style), Paragraph("Structure & Standard", table_header_style), Paragraph("Primary Workflow", table_header_style)],
        [Paragraph("Plain Text", table_cell_bold), Paragraph(".txt", table_cell_style), Paragraph("Clean transcript with speaker names and timestamps.", table_cell_style), Paragraph("Notes, study guides, articles.", table_cell_style)],
        [Paragraph("SubRip Subtitles", table_cell_bold), Paragraph(".srt", table_cell_style), Paragraph("Numbered subtitle intervals with comma ms timestamps.", table_cell_style), Paragraph("Premiere, DaVinci, Final Cut.", table_cell_style)],
        [Paragraph("WebVTT Subtitles", table_cell_bold), Paragraph(".vtt", table_cell_style), Paragraph("HTML5 video caption standard with dot ms timestamps.", table_cell_style), Paragraph("Web players, YouTube, Vimeo.", table_cell_style)],
        [Paragraph("YouTube Chapters", table_cell_bold), Paragraph(".txt", table_cell_style), Paragraph("Description-ready timestamp list (00:00 Intro\\n01:15 Topic).", table_cell_style), Paragraph("YouTube video descriptions.", table_cell_style)],
        [Paragraph("Markdown Summary", table_cell_bold), Paragraph(".md", table_cell_style), Paragraph("Formatted markdown with metadata, chapters, and quotes.", table_cell_style), Paragraph("GitHub, Notion, Obsidian.", table_cell_style)],
        [Paragraph("Structured JSON", table_cell_bold), Paragraph(".json", table_cell_style), Paragraph("Full data schema with segment boundaries and speakers.", table_cell_style), Paragraph("Downstream APIs and search indexes.", table_cell_style)],
        [Paragraph("Typeset PDF Report", table_cell_bold), Paragraph(".pdf", table_cell_style), Paragraph("Formal multi-page document with headers, chapters, and text.", table_cell_style), Paragraph("Academic submissions, executive briefs.", table_cell_style)],
    ]

    t_export = Table(export_data, colWidths=[1.4*inch, 0.6*inch, 2.7*inch, 2.3*inch])
    t_export.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_export)
    story.append(Spacer(1, 8))

    # 6. Database & REST API Architecture
    story.append(Paragraph("6. Database Architecture & REST Endpoints", h1_style))
    story.append(Paragraph(
        "Audixa utilizes SQLite (<code>audixa.db</code>) with scoped unique IDs (<code>f'{transcript_id}_{raw_id}'</code>) and cascading foreign keys across <code>transcripts</code>, <code>segments</code>, and <code>chapters</code> tables. The REST API covers upload, streaming, editing, history, and exports.",
        body_style
    ))

    api_data = [
        [Paragraph("Method", table_header_style), Paragraph("Endpoint", table_header_style), Paragraph("Description & Output Schema", table_header_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/upload", table_cell_style), Paragraph("Multipart upload supporting language_mode, model_size, and translate_mode.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/transcript/&lt;id&gt;", table_cell_style), Paragraph("Returns metadata, segments list with speaker tags, chapters, and audio URL.", table_cell_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/save_transcript/&lt;id&gt;", table_cell_style), Paragraph("Saves edited segment text, timestamps, and speaker labels.", table_cell_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/save_chapters/&lt;id&gt;", table_cell_style), Paragraph("Saves updated chapter titles and boundaries.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/api/export/&lt;id&gt;/&lt;fmt&gt;", table_cell_style), Paragraph("Direct download for txt, srt, vtt, youtube, md, json, or pdf formats.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/api/history", table_cell_style), Paragraph("Fetches historical transcript records for session drawer.", table_cell_style)],
        [Paragraph("POST", table_cell_bold), Paragraph("/api/delete/&lt;id&gt;", table_cell_style), Paragraph("Deletes transcript record and purges audio file from disk.", table_cell_style)],
        [Paragraph("GET", table_cell_bold), Paragraph("/plan-100.pdf", table_cell_style), Paragraph("Direct download of this 100% Milestone Implementation Plan PDF.", table_cell_style)]
    ]

    t_api = Table(api_data, colWidths=[0.8*inch, 2.0*inch, 4.2*inch])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, C_BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, C_BG_CARD]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_api)
    story.append(Spacer(1, 8))

    # 7. Step-by-Step Execution Plan
    story.append(Paragraph("7. Step-by-Step Execution Plan for 100% Completion", h1_style))
    story.append(Paragraph("• <b>Step 1 (Speech Engine):</b> Update <code>transcriber.py</code> to support 25+ language codes, <code>task='translate'</code> for English translation, and model precision toggle.", bullet_style))
    story.append(Paragraph("• <b>Step 2 (Database Updates):</b> Update <code>db.py</code> to store speaker attribution and language detection metadata.", bullet_style))
    story.append(Paragraph("• <b>Step 3 (Theme Engine & Styles):</b> Update <code>styles.css</code> with Midnight Moss Dark Mode variables, smooth toggle transitions, and chapter pin styling.", bullet_style))
    story.append(Paragraph("• <b>Step 4 (Upload Hub UX):</b> Update <code>index.html</code> with organized language optgroups, translation switch, and model precision dropdown.", bullet_style))
    story.append(Paragraph("• <b>Step 5 (Studio Editor Features):</b> Implement waveform chapter visual pins, speaker attribution badges, WPM analytics bar, history drawer, and keyboard shortcuts modal in <code>editor.html</code> and <code>editor.js</code>.", bullet_style))
    story.append(Paragraph("• <b>Step 6 (Export & PDF Engine):</b> Add PDF export handler in <code>app.py</code> and expose in export dropdown.", bullet_style))
    story.append(Paragraph("• <b>Step 7 (QA & Packaging):</b> Run automated test suite, rebuild clean zip distribution, and verify live server.", bullet_style))
    story.append(Spacer(1, 8))

    # 8. Viva Review Presentation Guide
    story.append(Paragraph("8. Viva & Faculty Review Q&A Guide (100% Final Review)", h1_style))
    story.append(Paragraph("<b>Q1: What sets Audixa apart from standard transcription software?</b><br/><b>A:</b> Audixa provides a simultaneous 3-panel synchronized studio combining WaveSurfer waveform audio scrubbing, live dialogue highlighting, in-line editing, automatic pause-gap chapter detection, speaker attribution tagging, and multi-format exports including subtitles and PDF reports.", body_style))
    story.append(Paragraph("<b>Q2: How is the multilingual and translation pipeline achieved?</b><br/><b>A:</b> Using faster-whisper with CTranslate2 and int8 quantization. The model supports 99 languages. When task='translate' is enabled, the neural acoustic model transcribes non-English speech directly into English text, eliminating the need for an external translation API.", body_style))
    story.append(Paragraph("<b>Q3: How does the application maintain fast performance on local hardware?</b><br/><b>A:</b> By leveraging multi-threaded CPU parallelization across all 12 hardware threads, greedy 1-beam decoding, int8 quantization, Silero VAD silence filtering, and background model pre-warming.", body_style))

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[Audixa] 100% Plan PDF generated successfully at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Audixa_100_Percent_Implementation_Plan.pdf"
    build_pdf(out_file)
