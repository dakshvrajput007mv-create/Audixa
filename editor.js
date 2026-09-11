/**
 * editor.js - Audio Player, Interactive Transcript, and Chapter Synchronization.
 * Clean, standard Vanilla JavaScript for Milestone 1 (30% Project Review).
 */

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const transcriptId = urlParams.get('id');

  if (!transcriptId) {
    window.location.href = '/';
    return;
  }

  // DOM Elements
  const mediaFilenameEl = document.getElementById('media-filename');
  const langBadge = document.getElementById('lang-badge');
  const durationBadge = document.getElementById('duration-badge');
  const exportBtn = document.getElementById('export-btn');
  const exportDropdown = document.getElementById('export-dropdown');

  // Player Elements
  const playPauseBtn = document.getElementById('play-pause-btn');
  const playIcon = document.getElementById('play-icon');
  const pauseIcon = document.getElementById('pause-icon');
  const skipBackBtn = document.getElementById('skip-back-btn');
  const skipFwdBtn = document.getElementById('skip-fwd-btn');
  const playbackSpeed = document.getElementById('playback-speed');
  const volumeSlider = document.getElementById('volume-slider');
  const currentTimeDisplay = document.getElementById('current-time-display');
  const totalDurationDisplay = document.getElementById('total-duration-display');
  const activeTimeLabel = document.getElementById('active-time-label');

  // Chapters Elements
  const chapterCountBadge = document.getElementById('chapter-count-badge');
  const addChapterBtn = document.getElementById('add-chapter-btn');
  const addChapterTimeHint = document.getElementById('add-chapter-time-hint');
  const chaptersList = document.getElementById('chapters-list');
  const manualSaveChaptersBtn = document.getElementById('manual-save-chapters-btn');

  // Transcript Elements
  const segmentCountBadge = document.getElementById('segment-count-badge');
  const manualSaveTranscriptBtn = document.getElementById('manual-save-transcript-btn');
  const transcriptSearchInput = document.getElementById('transcript-search-input');
  const searchMatchCount = document.getElementById('search-match-count');
  const transcriptList = document.getElementById('transcript-list');
  const toastContainer = document.getElementById('toast-container');

  // App State
  let transcriptData = null;
  let segments = [];
  let chapters = [];
  let wavesurfer = null;
  let isPlaying = false;
  let currentActiveSegmentId = null;

  // Simple Toast Helper
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }

  // Format Seconds to MM:SS
  function formatTime(seconds) {
    if (isNaN(seconds) || seconds === null) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  // 1. Fetch Transcript and Audio Metadata from SQLite Backend
  try {
    const res = await fetch(`/transcript/${transcriptId}`);
    const data = await res.json();
    if (!data.success) {
      showToast('Error loading transcript.', 'danger');
      return;
    }

    transcriptData = data;
    segments = data.segments || [];
    chapters = data.chapters || [];

    // Populate Header
    mediaFilenameEl.textContent = data.filename || 'Audio Recording';
    langBadge.textContent = data.language_mode === 'hi' ? 'Hindi' : (data.language_mode === 'en' ? 'English' : 'Hinglish / Auto');
    if (durationBadge) durationBadge.textContent = `⏱️ ${formatTime(data.duration || 0)}`;

    initWaveSurfer(data.audio_url);
    renderTranscript();
    renderChapters();
  } catch (err) {
    showToast('Failed to connect to backend server.', 'danger');
  }

  // 2. Initialize WaveSurfer Audio Player
  function initWaveSurfer(audioUrl) {
    wavesurfer = WaveSurfer.create({
      container: '#waveform',
      waveColor: '#C6D99E',
      progressColor: '#758359',
      cursorColor: '#242D1C',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 60,
      url: audioUrl
    });

    wavesurfer.on('ready', () => {
      const dur = wavesurfer.getDuration();
      totalDurationDisplay.textContent = formatTime(dur);
      activeTimeLabel.textContent = `00:00 / ${formatTime(dur)}`;
    });

    wavesurfer.on('timeupdate', (currentTime) => {
      currentTimeDisplay.textContent = formatTime(currentTime);
      const dur = wavesurfer.getDuration();
      activeTimeLabel.textContent = `${formatTime(currentTime)} / ${formatTime(dur)}`;
      addChapterTimeHint.textContent = formatTime(currentTime);
      highlightActiveSegment(currentTime);
      highlightActiveChapter(currentTime);
    });

    wavesurfer.on('play', () => {
      isPlaying = true;
      playIcon.style.display = 'none';
      pauseIcon.style.display = 'inline';
    });

    wavesurfer.on('pause', () => {
      isPlaying = false;
      playIcon.style.display = 'inline';
      pauseIcon.style.display = 'none';
    });

    wavesurfer.on('finish', () => {
      isPlaying = false;
      playIcon.style.display = 'inline';
      pauseIcon.style.display = 'none';
    });
  }

  // Play / Pause Controls
  playPauseBtn.addEventListener('click', () => {
    if (wavesurfer) wavesurfer.playPause();
  });

  if (skipBackBtn) {
    skipBackBtn.addEventListener('click', () => {
      if (wavesurfer) wavesurfer.setTime(Math.max(0, wavesurfer.getCurrentTime() - 5));
    });
  }

  if (skipFwdBtn) {
    skipFwdBtn.addEventListener('click', () => {
      if (wavesurfer) wavesurfer.setTime(Math.min(wavesurfer.getDuration(), wavesurfer.getCurrentTime() + 5));
    });
  }

  playbackSpeed.addEventListener('change', (e) => {
    if (wavesurfer) wavesurfer.setPlaybackRate(parseFloat(e.target.value));
  });

  volumeSlider.addEventListener('input', (e) => {
    if (wavesurfer) wavesurfer.setVolume(parseFloat(e.target.value));
  });

  // 3. Render Interactive Transcript
  function renderTranscript() {
    transcriptList.innerHTML = '';
    segmentCountBadge.textContent = `${segments.length} segments`;

    if (segments.length === 0) {
      transcriptList.innerHTML = '<div style="color:var(--text-dim); text-align:center; padding:30px;">No speech detected in audio.</div>';
      return;
    }

    segments.forEach((seg, idx) => {
      const card = document.createElement('div');
      card.className = 'segment-card';
      card.id = `segment-card-${seg.id}`;

      card.innerHTML = `
        <div class="segment-header">
          <span class="segment-timestamp">⏱️ ${formatTime(seg.start_time)} - ${formatTime(seg.end_time)}</span>
          <span style="font-size:0.75rem; color:var(--text-dim);">#${idx + 1}</span>
        </div>
        <div class="segment-text" contenteditable="true" spellcheck="false" data-id="${seg.id}">
          ${escapeHtml(seg.text)}
        </div>
      `;

      // Click card header to seek audio
      card.querySelector('.segment-header').addEventListener('click', () => {
        if (wavesurfer) wavesurfer.setTime(seg.start_time);
      });

      // Update segment text in memory on edit
      const textDiv = card.querySelector('.segment-text');
      textDiv.addEventListener('input', (e) => {
        seg.text = e.target.innerText;
      });

      transcriptList.appendChild(card);
    });
  }

  // Highlight Segment during Playback & Auto-scroll
  function highlightActiveSegment(currentTime) {
    const activeSeg = segments.find(s => currentTime >= s.start_time && currentTime <= s.end_time);
    if (!activeSeg) return;

    if (activeSeg.id !== currentActiveSegmentId) {
      if (currentActiveSegmentId) {
        const prev = document.getElementById(`segment-card-${currentActiveSegmentId}`);
        if (prev) prev.classList.remove('active');
      }

      currentActiveSegmentId = activeSeg.id;
      const curr = document.getElementById(`segment-card-${activeSeg.id}`);
      if (curr) {
        curr.classList.add('active');
        curr.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  // 4. Render Chapters
  function renderChapters() {
    chaptersList.innerHTML = '';
    chapterCountBadge.textContent = chapters.length;

    if (chapters.length === 0) {
      chaptersList.innerHTML = '<div style="color:var(--text-dim); text-align:center; padding:20px;">No chapters generated. Click "+ Add" to create one.</div>';
      return;
    }

    // Sort chapters by start time
    chapters.sort((a, b) => a.start_time - b.start_time);

    chapters.forEach((ch, idx) => {
      const card = document.createElement('div');
      card.className = 'chapter-card';
      card.id = `chapter-card-${ch.id || idx}`;

      card.innerHTML = `
        <button class="chapter-time-btn" type="button">${formatTime(ch.start_time)}</button>
        <input type="text" class="chapter-title-input" value="${escapeHtml(ch.title)}" data-idx="${idx}">
        <button class="chapter-delete-btn" title="Delete chapter" type="button">✕</button>
      `;

      // Seek audio to chapter
      card.querySelector('.chapter-time-btn').addEventListener('click', () => {
        if (wavesurfer) wavesurfer.setTime(ch.start_time);
      });

      // Edit title
      const titleInput = card.querySelector('.chapter-title-input');
      titleInput.addEventListener('input', (e) => {
        ch.title = e.target.value;
      });

      // Delete chapter
      card.querySelector('.chapter-delete-btn').addEventListener('click', () => {
        chapters = chapters.filter((_, i) => i !== idx);
        renderChapters();
      });

      chaptersList.appendChild(card);
    });
  }

  function highlightActiveChapter(currentTime) {
    if (chapters.length === 0) return;
    let activeIdx = -1;
    for (let i = 0; i < chapters.length; i++) {
      if (currentTime >= chapters[i].start_time) {
        activeIdx = i;
      } else {
        break;
      }
    }

    document.querySelectorAll('.chapter-card').forEach((card, idx) => {
      if (idx === activeIdx) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });
  }

  // Add Chapter at Current Playhead
  addChapterBtn.addEventListener('click', () => {
    const curTime = wavesurfer ? wavesurfer.getCurrentTime() : 0;
    const newChapter = {
      id: 'temp_' + Date.now(),
      title: `Chapter ${chapters.length + 1}`,
      start_time: Math.round(curTime * 10) / 10,
      end_time: Math.round(curTime * 10) / 10 + 30
    };
    chapters.push(newChapter);
    renderChapters();
    showToast(`Added chapter at ${formatTime(curTime)}`, 'info');
  });

  // 5. Save Transcript to SQLite Backend
  manualSaveTranscriptBtn.addEventListener('click', async () => {
    manualSaveTranscriptBtn.textContent = 'Saving...';
    try {
      const res = await fetch(`/save_transcript/${transcriptId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segments: segments })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Transcript saved to database!', 'success');
      } else {
        showToast('Failed to save transcript.', 'danger');
      }
    } catch (e) {
      showToast('Error saving transcript.', 'danger');
    } finally {
      manualSaveTranscriptBtn.textContent = 'Save Transcript';
    }
  });

  // 6. Save Chapters to SQLite Backend
  manualSaveChaptersBtn.addEventListener('click', async () => {
    manualSaveChaptersBtn.textContent = 'Saving...';
    try {
      const res = await fetch(`/save_chapters/${transcriptId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapters: chapters })
      });
      const data = await res.json();
      if (data.success) {
        showToast('Chapters saved to database!', 'success');
      } else {
        showToast('Failed to save chapters.', 'danger');
      }
    } catch (e) {
      showToast('Error saving chapters.', 'danger');
    } finally {
      manualSaveChaptersBtn.textContent = 'Save Chapters';
    }
  });

  // 7. Search Filter in Transcript
  transcriptSearchInput.addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase().trim();
    let matches = 0;

    document.querySelectorAll('.segment-card').forEach(card => {
      const text = card.querySelector('.segment-text').innerText.toLowerCase();
      if (!query || text.includes(query)) {
        card.style.display = 'block';
        if (query && text.includes(query)) matches++;
      } else {
        card.style.display = 'none';
      }
    });

    searchMatchCount.textContent = query ? `${matches} matches` : '';
  });

  // 8. Multi-format Export Handlers
  exportBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    exportDropdown.classList.toggle('show');
  });

  document.addEventListener('click', () => {
    exportDropdown.classList.remove('show');
  });

  document.querySelectorAll('.dropdown-item').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const type = e.target.getAttribute('data-export');
      exportFile(type);
    });
  });

  function exportFile(type) {
    const baseName = (transcriptData.filename || 'transcript').replace(/\.[^/.]+$/, '');
    let content = '';
    let ext = 'txt';
    let mime = 'text/plain';

    if (type === 'txt') {
      content = segments.map(s => `[${formatTime(s.start_time)} - ${formatTime(s.end_time)}] ${s.text}`).join('\n\n');
      ext = 'txt';
    } else if (type === 'srt') {
      content = segments.map((s, idx) => {
        return `${idx + 1}\n${formatSrt(s.start_time)} --> ${formatSrt(s.end_time)}\n${s.text}\n`;
      }).join('\n');
      ext = 'srt';
    } else if (type === 'vtt') {
      content = 'WEBVTT\n\n' + segments.map((s, idx) => {
        return `${idx + 1}\n${formatVtt(s.start_time)} --> ${formatVtt(s.end_time)}\n${s.text}\n`;
      }).join('\n');
      ext = 'vtt';
    } else if (type === 'youtube') {
      content = chapters.map(ch => `${formatTime(ch.start_time)} ${ch.title}`).join('\n');
      ext = 'txt';
    } else if (type === 'json') {
      content = JSON.stringify({ metadata: transcriptData, segments: segments, chapters: chapters }, null, 2);
      ext = 'json';
      mime = 'application/json';
    }

    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${baseName}_export.${ext}`;
    a.click();
    URL.revokeObjectURL(url);
    showToast(`Exported .${ext} file!`, 'success');
  }

  function formatSrt(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')},${String(ms).padStart(3,'0')}`;
  }

  function formatVtt(sec) {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    const s = Math.floor(sec % 60);
    const ms = Math.floor((sec % 1) * 1000);
    return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}.${String(ms).padStart(3,'0')}`;
  }

  function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
