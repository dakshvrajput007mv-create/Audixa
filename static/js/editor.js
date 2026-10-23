/**
 * editor.js - Audio Player, Interactive Transcript, and Chapter Synchronization.
 * Audixa - Radiant Purple & Orchid Blossom Clean Edition.
 */

document.addEventListener('DOMContentLoaded', async () => {
  const urlParams = new URLSearchParams(window.location.search);
  const transcriptId = urlParams.get('id');

  if (!transcriptId) {
    window.location.href = '/';
    return;
  }

  // DOM Elements - Header
  const mediaFilenameEl = document.getElementById('media-filename');
  const exportBtn = document.getElementById('export-btn');
  const exportDropdown = document.getElementById('export-dropdown');

  // Player Elements
  const playPauseBtn = document.getElementById('play-pause-btn');
  const playIcon = document.getElementById('play-icon');
  const pauseIcon = document.getElementById('pause-icon');
  const playbackSpeed = document.getElementById('playback-speed');
  const volumeSlider = document.getElementById('volume-slider');
  const muteBtn = document.getElementById('mute-btn');
  const currentTimeDisplay = document.getElementById('current-time-display');
  const totalDurationDisplay = document.getElementById('total-duration-display');
  const activeTimeLabel = document.getElementById('active-time-label');

  // Chapters Elements
  const addChapterBtn = document.getElementById('add-chapter-btn');
  const chaptersList = document.getElementById('chapters-list');
  const manualSaveChaptersBtn = document.getElementById('manual-save-chapters-btn');
  const chapterCountBadge = document.getElementById('chapter-count-badge');
  const chaptersSummaryText = document.getElementById('chapters-summary-text');

  // Transcript Elements
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
  let isMuted = false;
  let currentActiveSegmentId = null;

  // Toast Notification Helper
  function showToast(message, type = 'info') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }

  // Format Seconds to MM:SS
  function formatTime(seconds) {
    if (isNaN(seconds) || seconds === null || seconds === undefined) return '00:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  // 1. Fetch Transcript and Audio Metadata from SQLite Backend
  try {
    const res = await fetch(`/transcript/${transcriptId}`);
    const resJson = await res.json();

    if (!resJson.success || !resJson.data) {
      showToast('Error loading transcript from server.', 'danger');
      return;
    }

    transcriptData = resJson.data;
    segments = transcriptData.segments || [];
    chapters = transcriptData.chapters || [];

    // Populate Header
    if (mediaFilenameEl) {
      mediaFilenameEl.textContent = transcriptData.original_name || transcriptData.filename || 'Audio Recording';
    }

    initWaveSurfer(transcriptData.audio_url || `/audio/${transcriptId}`);
    renderTranscript();
    renderChapters();
  } catch (err) {
    showToast('Failed to connect to backend server.', 'danger');
  }

  // 2. Initialize WaveSurfer Audio Player
  function initWaveSurfer(audioUrl) {
    try {
      wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: '#EE97D8',
        progressColor: '#8F18A3',
        cursorColor: '#751286',
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

      wavesurfer.on('error', (e) => {
        console.warn('WaveSurfer notice:', e);
      });
    } catch (e) {
      console.warn('WaveSurfer initialization fallback:', e);
    }
  }

  // Play / Pause Controls
  playPauseBtn.addEventListener('click', () => {
    if (wavesurfer) wavesurfer.playPause();
  });

  playbackSpeed.addEventListener('change', (e) => {
    if (wavesurfer) wavesurfer.setPlaybackRate(parseFloat(e.target.value));
  });

  volumeSlider.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value);
    if (wavesurfer) wavesurfer.setVolume(val);
    isMuted = (val === 0);
    muteBtn.textContent = isMuted ? '🔇' : '🔊';
  });

  if (muteBtn) {
    muteBtn.addEventListener('click', () => {
      if (!wavesurfer) return;
      if (isMuted) {
        wavesurfer.setVolume(1.0);
        volumeSlider.value = 1.0;
        muteBtn.textContent = '🔊';
        isMuted = false;
      } else {
        wavesurfer.setVolume(0.0);
        volumeSlider.value = 0.0;
        muteBtn.textContent = '🔇';
        isMuted = true;
      }
    });
  }

  // 3. Render Interactive Transcript
  function renderTranscript() {
    transcriptList.innerHTML = '';

    if (segments.length === 0) {
      transcriptList.innerHTML = '<div style="color:var(--text-dim); text-align:center; padding:30px;">No speech detected in audio.</div>';
      return;
    }

    segments.forEach((seg) => {
      const card = document.createElement('div');
      card.className = 'segment-card';
      card.id = `segment-card-${seg.id}`;

      card.innerHTML = `
        <div class="segment-header">
          <span class="segment-timestamp" title="Click to seek audio">⏱️ ${formatTime(seg.start_time)} - ${formatTime(seg.end_time)}</span>
          <div class="segment-header-actions">
            <button type="button" class="segment-action-btn delete-btn" title="Delete segment" data-id="${seg.id}">🗑️</button>
          </div>
        </div>
        <div class="segment-text" contenteditable="true" spellcheck="false" data-id="${seg.id}">
          ${escapeHtml(seg.text)}
        </div>
      `;

      // Click timestamp to seek audio
      const timeStampEl = card.querySelector('.segment-timestamp');
      if (timeStampEl) {
        timeStampEl.addEventListener('click', () => {
          if (wavesurfer) wavesurfer.setTime(seg.start_time);
        });
      }

      // Inline text editing
      const textDiv = card.querySelector('.segment-text');
      if (textDiv) {
        textDiv.addEventListener('input', (e) => {
          seg.text = e.target.innerText;
        });
      }

      // Delete action
      const deleteBtn = card.querySelector('.delete-btn');
      if (deleteBtn) {
        deleteBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          handleDeleteSegment(seg.id);
        });
      }

      transcriptList.appendChild(card);
    });
  }

  // Segment Delete Handler
  function handleDeleteSegment(segId) {
    segments = segments.filter(s => s.id !== segId);
    renderTranscript();
    showToast('Segment deleted.', 'info');
  }

  // Highlight Segment during Playback & Auto-scroll
  function highlightActiveSegment(currentTime) {
    const activeSeg = segments.find(s => currentTime >= s.start_time && currentTime <= s.end_time);

    if (activeSeg && activeSeg.id !== currentActiveSegmentId) {
      if (currentActiveSegmentId) {
        const prevCard = document.getElementById(`segment-card-${currentActiveSegmentId}`);
        if (prevCard) prevCard.classList.remove('active');
      }

      currentActiveSegmentId = activeSeg.id;
      const curCard = document.getElementById(`segment-card-${currentActiveSegmentId}`);
      if (curCard) {
        curCard.classList.add('active');
        curCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    }
  }

  // 4. Render Chapters Panel
  function renderChapters() {
    chaptersList.innerHTML = '';

    if (chapterCountBadge) {
      chapterCountBadge.textContent = `${chapters.length} chapter${chapters.length === 1 ? '' : 's'}`;
    }
    if (chaptersSummaryText) {
      chaptersSummaryText.textContent = `${chapters.length} timestamp marker${chapters.length === 1 ? '' : 's'}`;
    }

    if (chapters.length === 0) {
      chaptersList.innerHTML = `
        <div class="chapters-empty-state">
          <span class="empty-icon">📑</span>
          <p>No chapters yet.<br>Click <strong>+ Add Chapter</strong> to create timestamped markers.</p>
        </div>
      `;
      return;
    }

    // Sort chapters by start_time
    chapters.sort((a, b) => a.start_time - b.start_time);

    chapters.forEach((ch, idx) => {
      const chCard = document.createElement('div');
      chCard.className = 'chapter-card';
      chCard.id = `chapter-card-${idx}`;

      chCard.innerHTML = `
        <span class="chapter-idx-badge">${String(idx + 1).padStart(2, '0')}</span>
        <input type="text" class="chapter-time-input" value="${formatTime(ch.start_time)}" title="Click to seek audio, or edit time (MM:SS)" data-idx="${idx}">
        <input type="text" class="chapter-title-input" value="${escapeHtml(ch.title)}" placeholder="Enter chapter title..." title="Edit chapter title" data-idx="${idx}">
        <div class="chapter-actions">
          <button type="button" class="chapter-action-btn play-ch-btn" title="Play from this chapter" data-time="${ch.start_time}">▶</button>
          <button type="button" class="chapter-action-btn delete-ch-btn" title="Delete chapter" data-idx="${idx}">✕</button>
        </div>
      `;

      // Click time input to seek & play
      const timeInput = chCard.querySelector('.chapter-time-input');
      timeInput.addEventListener('click', (e) => {
        e.stopPropagation();
        if (wavesurfer) {
          wavesurfer.setTime(ch.start_time);
          if (!isPlaying) wavesurfer.play();
        }
      });

      timeInput.addEventListener('change', (e) => {
        const parts = e.target.value.split(':');
        if (parts.length === 2) {
          const m = parseInt(parts[0], 10) || 0;
          const s = parseInt(parts[1], 10) || 0;
          ch.start_time = Math.max(0, m * 60 + s);
          renderChapters();
          showToast(`Updated timestamp to ${formatTime(ch.start_time)}`, 'info');
        } else {
          e.target.value = formatTime(ch.start_time);
        }
      });

      // Edit title
      const titleInput = chCard.querySelector('.chapter-title-input');
      titleInput.addEventListener('input', (e) => {
        ch.title = e.target.value;
      });

      // Play button
      const playBtn = chCard.querySelector('.play-ch-btn');
      playBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        if (wavesurfer) {
          wavesurfer.setTime(ch.start_time);
          wavesurfer.play();
          showToast(`Playing: ${ch.title}`, 'info');
        }
      });

      // Delete chapter
      const deleteChBtn = chCard.querySelector('.delete-ch-btn');
      deleteChBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        chapters.splice(idx, 1);
        renderChapters();
        showToast('Chapter removed.', 'info');
      });

      chaptersList.appendChild(chCard);
    });
  }

  // Highlight active chapter
  function highlightActiveChapter(currentTime) {
    if (chapters.length === 0) return;
    let activeIdx = -1;
    for (let i = 0; i < chapters.length; i++) {
      if (currentTime >= chapters[i].start_time) {
        activeIdx = i;
      }
    }
    document.querySelectorAll('.chapter-card').forEach((el, idx) => {
      el.classList.toggle('active', idx === activeIdx);
    });
  }

  // Add Chapter Button
  addChapterBtn.addEventListener('click', () => {
    const curTime = wavesurfer ? Math.floor(wavesurfer.getCurrentTime()) : 0;
    const newCh = {
      title: `Chapter ${chapters.length + 1}`,
      start_time: curTime,
      end_time: curTime + 60
    };
    chapters.push(newCh);
    renderChapters();
    showToast(`Added chapter at ${formatTime(curTime)}`, 'success');
  });

  // 5. Save Actions (Backend API Persistence)
  async function performSaveTranscript() {
    try {
      const payload = {
        segments: segments.map(s => ({
          id: s.id,
          start_time: s.start_time,
          end_time: s.end_time,
          text: s.text
        }))
      };

      const res = await fetch(`/save_transcript/${transcriptId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast('Transcript saved successfully!', 'success');
      } else {
        showToast(data.error || 'Failed to save transcript.', 'danger');
      }
    } catch (e) {
      showToast('Error connecting to backend server.', 'danger');
    }
  }

  async function performSaveChapters() {
    try {
      const payload = {
        chapters: chapters.map(ch => ({
          title: ch.title,
          start_time: ch.start_time,
          end_time: ch.end_time
        }))
      };

      const res = await fetch(`/save_chapters/${transcriptId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        showToast('Chapters saved successfully!', 'success');
      } else {
        showToast(data.error || 'Failed to save chapters.', 'danger');
      }
    } catch (e) {
      showToast('Error connecting to backend server.', 'danger');
    }
  }

  manualSaveTranscriptBtn.addEventListener('click', performSaveTranscript);
  manualSaveChaptersBtn.addEventListener('click', performSaveChapters);

  // 6. Search Filter in Transcript
  if (transcriptSearchInput) {
    transcriptSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase().trim();
      let matches = 0;

      document.querySelectorAll('.segment-card').forEach(card => {
        const textEl = card.querySelector('.segment-text');
        const text = textEl ? textEl.innerText.toLowerCase() : '';

        if (!query || text.includes(query)) {
          card.style.display = 'block';
          if (query && text.includes(query)) matches++;
        } else {
          card.style.display = 'none';
        }
      });

      if (searchMatchCount) searchMatchCount.textContent = query ? `${matches} matches` : '';
    });
  }

  // 7. Multi-format Export Handlers (Direct API Downloads including PDF)
  if (exportBtn) {
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
        window.location.href = `/api/export/${transcriptId}/${type}`;
        showToast(`Generating .${type} download...`, 'success');
      });
    });
  }

  // 8. Shortcuts: Space to Play/Pause, Ctrl+S to Save
  document.addEventListener('keydown', (e) => {
    const isEditing = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      performSaveTranscript();
      performSaveChapters();
      return;
    }

    if (!isEditing && e.code === 'Space') {
      e.preventDefault();
      if (wavesurfer) wavesurfer.playPause();
    }
  });

  // Utility Helpers
  function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
