# 🎙️ Audixa — AI Audio Transcript & Chapter Maker

> **Lightweight, Zero-Build 2-Page Web Application for Audio Transcription and Synchronized Chapter Generation**  
> Supports English, Hindi, and Code-switched Hinglish Speech.

---

## 🌟 Key Features

1. **Page 1: Multi-Source Upload Hub (`/`)**
   - **Segmented Upload Modes:**
     - 📄 **File upload:** Drag-and-drop local audio/video file ingestion (`.mp3`, `.wav`, `.m4a`, `.mp4`, `.flac`, `.aac`, `.webm`, `.ogg`).
     - 🔗 **Paste link:** Online media streaming support for **YouTube videos**, SoundCloud, Vimeo, and direct media streams (`.mp3`, `.wav`, `.m4a`, `.mp4`) powered by `yt-dlp`.
     - 🎙️ **Record audio:** In-browser live microphone recording using HTML5 `MediaRecorder` with an animated pulsing visual, live timer (`MM:SS`), and instant audio playback preview.
   - **25+ Speech Languages:** Auto-detect / Hinglish code-switching, 10 Indian Regional languages (Hindi, Bengali, Marathi, Telugu, Tamil, Gujarati, Urdu, Kannada, Malayalam, Punjabi), and 14 Global languages.
   - **Modern Aesthetic:** Radiant Purple & Orchid Blossom color system with smooth micro-interactions.

2. **Page 2: Simultaneous 3-Panel Synchronized Editor (`/editor?id=...`)**
   - **Section A (Audio Waveform Player):** Interactive waveform canvas powered by `wavesurfer.js`, Play/Pause, speed adjustment ($0.75\times - 2.0\times$), volume slider, and real-time playback timer.
   - **Section B (Interactive Transcript):** Spoken dialogue cards with precise timestamps, active playback highlight, auto-scrolling (`scrollIntoView`), click-to-seek, search filter, and inline content-editable text.
   - **Section C (Chapter Maker):** Chapter markers, "+ Add at Current Time" button to create chapters at the active playhead, inline editable titles, and delete actions.
   - **Multi-Format Export Engine:** One-click downloads for **Plain Text (`.txt`)**, **SubRip Subtitles (`.srt`)**, **WebVTT (`.vtt`)**, **YouTube Timestamps**, and **Structured Metadata (`.json`)**.

---

## 🛠️ Tech Stack & Architecture

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Backend** | Python 3 + Flask | REST API routing, file storage, and HTTP 206 byte-range audio streaming. |
| **Frontend** | Semantic HTML5 & Vanilla CSS3 | Radiant Purple & Orchid Blossom Design System (flat, high contrast, responsive). |
| **Client Scripting** | Vanilla JavaScript (ES6+) | WaveSurfer synchronization, in-browser MediaRecorder, inline transcript editing, and export triggers. |
| **Media Extraction** | `yt-dlp` | Remote audio extraction for YouTube and web media links. |
| **Database** | SQLite3 (`sqlite3` stdlib) | Relational store for `transcripts`, `segments`, and `chapters` with cascading deletes. |
| **Speech AI** | `faster-whisper` (CTranslate2) | 4× faster than OpenAI Whisper with `int8` CPU quantization. |
| **Audio Visualization** | `wavesurfer.js v7` (CDN) | Interactive audio waveform rendering. |

---

## 🚀 Quickstart & Local Installation

### Prerequisites
- Python 3.10+ installed
- Git (optional)

### 1. Clone or Extract the Repository
```bash
git clone https://github.com/your-username/Audixa.git
cd Audixa
```

### 2. Create Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## ☁️ Deployment Instructions

### Deploy to Render (Recommended Free Web Service)
1. Push this repository to your GitHub account.
2. Log into [Render.com](https://render.com) and click **New + > Web Service**.
3. Connect your GitHub repository.
4. Set the following build and start commands:
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Click **Create Web Service**.

---

## 📁 Repository Structure

```
Audixa/
├── app.py                             # Flask web server & REST endpoints
├── db.py                              # SQLite database manager & schema
├── transcriber.py                     # Whisper AI speech-to-text & chapter generator
├── test_app.py                        # Automated backend test suite
├── requirements.txt                   # Production Python dependencies
├── Procfile                           # Cloud deployment configuration
├── .gitignore                         # Git ignore rules
├── static/
│   ├── css/
│   │   └── styles.css                 # Sage & Cream light theme stylesheet
│   └── js/
│       ├── upload.js                  # File upload & progress bar handler
│       └── editor.js                  # WaveSurfer sync & chapter editor logic
└── templates/
    ├── index.html                     # Page 1: Upload interface
    └── editor.html                    # Page 2: 3-Panel editor interface
```

---

## 📄 License
This project is licensed under the MIT License.
