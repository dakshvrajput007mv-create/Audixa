# 🎙️ Audixa — AI Audio Transcript & Chapter Maker

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Speech AI](https://img.shields.io/badge/Engine-faster--whisper%20(CTranslate2)-purple.svg)](https://github.com/SYSTRAN/faster-whisper)
[![Waveform](https://img.shields.io/badge/Waveform-wavesurfer.js%20v7-ff69b4.svg)](https://wavesurfer.xyz/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Vercel Deployment](https://img.shields.io/badge/Deploy-Vercel%20Multi--Service-000000.svg?logo=vercel&logoColor=white)](https://vercel.com/)

> **Audixa** is a modern, lightweight, full-stack web application designed for high-accuracy speech transcription, synchronized audio playback, automated chapter marker generation, and multi-format subtitle exports. 
> Built with **Flask**, **faster-whisper**, **wavesurfer.js**, and styled in a bespoke **Radiant Purple & Orchid Blossom** design system.

---

## 🌐 Quick Browser Links

* **Local Web Application:** [http://127.0.0.1:5000](http://127.0.0.1:5000)
* **GitHub Repository:** [https://github.com/dakshvrajput007mv-create/Audixa](https://github.com/dakshvrajput007mv-create/Audixa)

---

## 🌟 Key Features

### 1. Multi-Source Upload Hub (`/`)
* **Segmented 3-Mode Navigation Bar:**
  * 📄 **File upload:** Drag-and-drop local audio and video files (`.mp3`, `.wav`, `.m4a`, `.mp4`, `.flac`, `.aac`, `.webm`, `.ogg`) with real-time file size calculation and format badges.
  * 🔗 **Paste link:** Direct stream extraction for **YouTube videos**, Vimeo, SoundCloud, and direct web media URLs powered by server-side `yt-dlp`.
  * 🎙️ **Record audio:** In-browser live microphone recording using the HTML5 `MediaRecorder` API featuring a pulsing recording ring animation, live `MM:SS` timer, pause/stop controls, and an inline audio preview player to verify before submitting.
* **25+ Speech Language Selector:**
  * **Automatic & Mixed:** Auto-detect with specialized prompt engineering for **Code-switched Hinglish** (Hindi + English).
  * **10 Indian Regional Languages:** Hindi (हिन्दी), Bengali (বাংলা), Marathi (मराठी), Telugu (తెలుగు), Tamil (தமிழ்), Gujarati (ગુજરાતી), Urdu (اردو), Kannada (ಕನ್ನಡ), Malayalam (മലയാളം), Punjabi (ਪੰਜਾਬੀ).
  * **14 Global Languages:** English, Spanish, French, German, Japanese, Mandarin Chinese, Russian, Portuguese, Italian, Arabic, Korean, Dutch, Turkish, Vietnamese.
* **Live Progress Tracking:** Dynamic percentage progress bar and animated processing spinner during AI transcription.

---

### 2. Simultaneous 3-Panel Synchronized Editor (`/editor?id=...`)
* **Panel A: Audio Waveform Player**
  * Interactive canvas powered by **WaveSurfer.js v7**.
  * Precise playhead scrubbing, Play/Pause toggle, variable playback rate ($0.75\times$ to $2.0\times$), volume controls, and real-time timestamp display (`MM:SS / MM:SS`).
* **Panel B: Interactive Synchronized Transcript**
  * Timestamped dialogue segment cards with start and end times.
  * Active playback highlight with automatic auto-scrolling (`scrollIntoView`).
  * Click-to-seek: clicking any transcript segment jumps the audio player to that exact millisecond.
  * Live search keyword filter and inline editable transcript text.
* **Panel C: Intelligent Chapter Maker**
  * Automatic chapter segment detection based on speech pauses and topic shifts.
  * **"+ Add at Current Time"** button to drop chapters at the exact active playhead position.
  * Inline editable chapter titles, timeline reordering, and one-click deletion.
* **Multi-Format Subtitle & Metadata Export Engine:**
  * 📝 **Plain Text (`.txt`):** Formatted transcript dialogues.
  * 🎬 **SubRip Subtitles (`.srt`):** Standard subtitle file format for video editors (Premiere, Final Cut, DaVinci).
  * 🌐 **WebVTT (`.vtt`):** Modern HTML5 web video captioning format.
  * ▶️ **YouTube Timestamps:** One-click formatted timestamps ready to paste into video descriptions.
  * 📊 **Structured Metadata (`.json`):** Full export with segments, words, chapters, and audio duration.

---

## 🎨 Design System: Radiant Purple & Orchid Blossom

Audixa uses an exclusive, high-contrast, distraction-free color palette tailored for professional audio editors:

| Token Name | Hex Code | Visual Preview | Purpose |
| :--- | :--- | :--- | :--- |
| **Royal Purple** | `#8F18A3` | `rgb(143, 24, 163)` | Primary brand color, active pill backgrounds, primary buttons |
| **Vibrant Orchid** | `#C753C4` | `rgb(199, 83, 196)` | Accent highlights, active transcript borders, badges |
| **Soft Blossom** | `#EE97D8` | `rgb(238, 151, 216)` | Waveform progress, hover tints, secondary borders |
| **Pastel Pink** | `#FFC1DF` | `rgb(255, 193, 223)` | Subtle container backgrounds, progress track tints |
| **Deep Midnight Plum**| `#2B0733` | `rgb(43, 7, 51)` | Primary text, high contrast typography |

* **Zero 404 Resilience:** The complete design system is inlined into `<style id="audixa-inline-design-system">` inside page templates, guaranteeing instant, 100% styled rendering across any cloud provider or serverless platform.

---

## 🛠️ Architecture & Tech Stack

```
                               ┌────────────────────────┐
                               │   Audixa Client (Web)  │
                               │  HTML5 + CSS3 + JS ES6 │
                               └───────────┬────────────┘
                                           │ HTTP / JSON
                                           ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Flask Web Server (app.py)                             │
│                                                                                 │
│   ┌─────────────────────┐   ┌───────────────────────┐   ┌───────────────────┐   │
│   │   Upload Controller │   │ WaveSurfer Byte-Range │   │   Export Engine   │   │
│   │   (File/Link/Record)│   │ Audio Streaming (206) │   │ (.srt, .vtt, .txt)│   │
│   └──────────┬──────────┘   └───────────┬───────────┘   └─────────┬─────────┘   │
└──────────────┼──────────────────────────┼─────────────────────────┼─────────────┘
               │                          │                         │
               ▼                          ▼                         ▼
┌───────────────────────────────┐ ┌───────────────┐ ┌─────────────────────────────┐
│      Speech AI Engine         │ │ SQLite3 Store │ │    Remote Media Extractor   │
│  faster-whisper (CTranslate2) │ │  (audixa.db)  │ │            yt-dlp           │
│   CPU int8 Quantized Models   │ │ Transcripts & │ │   YouTube / Web Audio Links │
└───────────────────────────────┘ │   Chapters    │ └─────────────────────────────┘
                                  └───────────────┘
```

| Layer | Component | Description |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3 + Flask 3.0+ | REST API, static asset delivery, HTTP 206 byte-range audio streaming |
| **Speech Recognition** | `faster-whisper` (CTranslate2) | 4× faster than standard Whisper with CPU `int8` quantization |
| **Media Extraction** | `yt-dlp` | Remote audio extraction for YouTube and web media links |
| **Waveform Engine** | `wavesurfer.js v7` | Client-side canvas audio visualization and synchronization |
| **Database** | SQLite3 (`sqlite3` stdlib) | Zero-config relational database for transcripts, segments, chapters |
| **Frontend UI** | Semantic HTML5 & Vanilla CSS | Embedded Radiant Purple design system (zero external CSS dependencies) |

---

## 🚀 Quickstart & Local Installation

### Prerequisites
* **Python 3.10+** installed on your system.
* **Git** installed on your system.

### 1. Clone the Repository
```bash
git clone https://github.com/dakshvrajput007mv-create/Audixa.git
cd Audixa
```

### 2. Create and Activate a Virtual Environment
* **Windows (PowerShell):**
  ```powershell
  python -m venv venv
  venv\Scripts\Activate.ps1
  ```
* **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python app.py
```
Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🧪 Automated Testing

Audixa includes a comprehensive automated test suite verifying all upload modes, Whisper transcription, chapter generation, and export formats:

```bash
python test_app.py
```

Expected output:
```
Ran 9 tests in 4.00s

OK
[Audixa] Transcription complete: 3 segments, 1 chapters, duration=10.32s
[Test Result] Generated Transcript ID: audixa_test_ok
```

---

## ☁️ Deployment Configurations

### 1. Vercel (Multi-Service Architecture)
Audixa includes a verified [`vercel.json`](./vercel.json) supporting multi-service deployment:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "services": {
    "app": {
      "root": ".",
      "framework": "flask",
      "bindings": [
        {
          "type": "service",
          "service": "backend",
          "format": "url",
          "env": "BACKEND_URL"
        }
      ]
    },
    "backend": {
      "root": "backend",
      "framework": "fastapi"
    },
    "frontend": {
      "root": "frontend",
      "framework": "vite"
    }
  },
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": { "service": "backend" }
    },
    {
      "source": "/(.*)",
      "destination": { "service": "app" }
    }
  ]
}
```

* **Lambda Size Optimization:** Functions are kept within the 500 MB limit via `.vercelignore` and lightweight dependencies.
* **Zero 404 Guarantee:** Templates inline all essential CSS and JS controllers so pages never render unstyled.

### 2. Render / Railway / Docker
For persistent worker processes and unlimited audio file sizes, deploy as a standard web service:
* **Runtime:** Python 3
* **Build Command:** `pip install -r requirements.txt`
* **Start Command:** `python app.py`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Serves the main Upload Hub interface |
| `GET` | `/editor?id=<id>` | Serves the 3-panel synchronized editor interface |
| `POST` | `/upload` | Ingests a local file (`file`), link URL (`link_url`), or recorded audio |
| `GET` | `/transcript/<id>` | Retrieves transcript metadata and segmented word timestamps (JSON) |
| `GET` | `/audio/<id>` | Streams audio with HTTP 206 Partial Content byte-range support |
| `POST` | `/chapters/<id>` | Adds a new chapter marker at a specific timestamp |
| `PUT` | `/chapters/<id>/<ch_id>`| Renames or updates an existing chapter |
| `DELETE`| `/chapters/<id>/<ch_id>`| Deletes a chapter marker |
| `GET` | `/export/<id>/<format>` | Downloads formatted export (`txt`, `srt`, `vtt`, `youtube`, `json`) |
| `GET` | `/static/<path:filename>`| Serves static assets with guaranteed fallback |

---

## 📁 Repository Directory Structure

```
Audixa/
├── app.py                             # Main Flask application and REST routes
├── db.py                              # SQLite3 database schema & queries
├── transcriber.py                     # Whisper AI speech model & chapter generator
├── test_app.py                        # Automated test suite (9 unit/integration tests)
├── requirements.txt                   # Production Python dependencies
├── vercel.json                        # Vercel multi-service configuration
├── .vercelignore                      # Serverless bundle size exclusions
├── .gitignore                         # Git exclusion rules
├── README.md                          # Comprehensive GitHub documentation
├── README.txt                         # Plaintext project summary
├── static/
│   ├── css/
│   │   └── styles.css                 # Radiant Purple & Orchid Blossom stylesheet
│   └── js/
│       ├── upload.js                  # Ingestion modes, live recording, and dropzone
│       └── editor.js                  # WaveSurfer sync, chapter timeline, & exports
├── templates/
│   ├── index.html                     # Page 1: Upload Hub (with embedded fallback CSS)
│   └── editor.html                    # Page 2: 3-Panel Editor (with embedded fallback CSS)
├── backend/                           # Optional FastAPI microservice
└── frontend/                          # Optional React/Vite SPA client
```

---

## 📄 License
This project is licensed under the **MIT License** — feel free to use, modify, and distribute it for personal and commercial applications.
