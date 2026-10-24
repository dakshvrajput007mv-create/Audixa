================================================================================
AUDIXA - AI AUDIO TRANSCRIPT & CHAPTER MAKER
Full-Stack Speech-to-Text, Audio Synchronization, and Chapter Generation Engine
================================================================================

1. OVERVIEW & BROWSER LINKS
--------------------------------------------------------------------------------
Audixa is a lightweight, zero-build, full-stack web application designed for
high-accuracy speech transcription, interactive audio-text synchronized playback,
automated chapter creation, and multi-format subtitle exports (.txt, .srt, .vtt,
YouTube timestamps, .json).

* Local Web Browser Link : http://127.0.0.1:5000
* GitHub Repository URL  : https://github.com/dakshvrajput007mv-create/Audixa


2. KEY APPLICATION FEATURES
--------------------------------------------------------------------------------
PAGE 1: MULTI-SOURCE UPLOAD HUB (/)
- Segmented 3-Mode Ingestion Bar:
  1. [ File upload ]  : Drag-and-drop local audio/video file selector with format
                        badges (.mp3, .wav, .m4a, .mp4, .flac, .aac, .webm, .ogg)
                        and real-time file size calculation.
  2. [ Paste link ]   : Direct URL ingestion for YouTube videos, Vimeo, SoundCloud,
                        and streaming media files powered by yt-dlp.
  3. [ Record audio ] : In-browser live microphone recording via HTML5 MediaRecorder
                        with a pulsing animation ring, MM:SS live timer, pause/stop
                        controls, and instant playback preview.
- 25+ Speech Language Selector:
  * Multilingual / Hinglish Auto-detect with tailored prompt engineering.
  * 10 Indian Regional Languages: Hindi, Bengali, Marathi, Telugu, Tamil,
    Gujarati, Urdu, Kannada, Malayalam, Punjabi.
  * 14 Global Languages: English, Spanish, French, German, Japanese, Chinese,
    Russian, Portuguese, Italian, Arabic, Korean, Dutch, Turkish, Vietnamese.

PAGE 2: SIMULTANEOUS 3-PANEL SYNCHRONIZED EDITOR (/editor?id=...)
- Panel A (Waveform Player): Interactive WaveSurfer.js v7 audio waveform canvas,
  speed controls (0.75x to 2.0x), volume slider, and MM:SS playback timer.
- Panel B (Interactive Transcript): Synchronized dialogue segment cards with
  active playback highlight, automatic auto-scrolling (scrollIntoView), click-to-seek,
  keyword search filter, and inline editable transcript text.
- Panel C (Chapter Maker): Automatic pause-based chapter detection, "+ Add at
  Current Time" button to timestamp chapters at active playhead, inline editing,
  and reordering.
- Multi-Format Subtitle & Metadata Exports:
  * Plain Text (.txt)
  * SubRip Subtitles (.srt)
  * WebVTT Subtitles (.vtt)
  * YouTube Video Timestamps
  * Structured JSON Metadata (.json)


3. DESIGN SYSTEM (RADIANT PURPLE & ORCHID BLOSSOM)
--------------------------------------------------------------------------------
- Primary Royal Purple : #8F18A3
- Vibrant Orchid Accent: #C753C4
- Soft Blossom Progress: #EE97D8
- Pastel Pink Track    : #FFC1DF
- Midnight Plum Text   : #2B0733
Zero-404 Architecture: Styles are embedded directly into page templates so the
user interface renders with 100% fidelity across any hosting platform.


4. TECHNICAL STACK
--------------------------------------------------------------------------------
- Backend Server  : Python 3 + Flask 3.0+
- Speech AI Engine: faster-whisper (CTranslate2 CPU int8 quantized models)
- Media Extractor : yt-dlp (YouTube & web audio links)
- Audio Waveform  : WaveSurfer.js v7 (CDN)
- Database Store  : SQLite3 (stdlib relational schema with cascade deletes)
- Frontend Client : Semantic HTML5 + Vanilla CSS3 + ES6 JavaScript


5. QUICKSTART INSTALLATION (WINDOWS / MAC / LINUX)
--------------------------------------------------------------------------------
Step 1: Clone the repository
  git clone https://github.com/dakshvrajput007mv-create/Audixa.git
  cd Audixa

Step 2: Create and activate a Python virtual environment
  # Windows
  python -m venv venv
  venv\Scripts\activate

  # Linux / macOS
  python3 -m venv venv
  source venv/bin/activate

Step 3: Install dependencies
  pip install -r requirements.txt

Step 4: Launch the server
  python app.py

Step 5: Open your web browser
  Navigate to: http://127.0.0.1:5000


6. RUNNING TESTS
--------------------------------------------------------------------------------
Execute the automated test suite:
  python test_app.py
All 9 unit/integration tests verify upload routes, faster-whisper transcription,
chapter detection heuristics, and subtitle format serialization.


7. CLOUD DEPLOYMENT (VERCEL & RENDER)
--------------------------------------------------------------------------------
- Vercel: Preconfigured with vercel.json multi-service routing and .vercelignore
  bundle size exclusions (keeping functions safely under 500 MB).
- Render / Railway: Deploy as a standard Python Web Service running `python app.py`.


8. LICENSE
--------------------------------------------------------------------------------
Licensed under the MIT License. Open source and free for commercial or personal use.
================================================================================
