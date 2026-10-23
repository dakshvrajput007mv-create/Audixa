/**
 * upload.js - Multi-source audio ingestion: File Upload, Paste Link, and Live Recording.
 * Radiant Purple & Orchid Blossom Design System.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mode Tabs
  const modeTabs = document.querySelectorAll('.upload-mode-tab');
  const paneFile = document.getElementById('pane-file');
  const paneLink = document.getElementById('pane-link');
  const paneRecord = document.getElementById('pane-record');

  // File Upload Elements
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const filePreview = document.getElementById('file-preview');
  const fileName = document.getElementById('file-name');
  const fileSize = document.getElementById('file-size');
  const previewIcon = document.getElementById('preview-icon');
  const removeFileBtn = document.getElementById('remove-file-btn');

  // Link Elements
  const linkUrlInput = document.getElementById('link-url-input');
  const clearLinkBtn = document.getElementById('clear-link-btn');

  // Record Audio Elements
  const recordRing = document.getElementById('record-pulsing-ring');
  const recordCounter = document.getElementById('record-time-counter');
  const recordLabel = document.getElementById('record-state-label');
  const recordToggleBtn = document.getElementById('record-toggle-btn');
  const recordStopBtn = document.getElementById('record-stop-btn');
  const recordedPreviewWrap = document.getElementById('recorded-preview-wrap');
  const recordedAudioPlayer = document.getElementById('recorded-audio-player');

  // Form & Status Elements
  const uploadForm = document.getElementById('upload-form');
  const languageSelect = document.getElementById('language-select');
  const uploadProgressBox = document.getElementById('upload-progress-box');
  const uploadStatusLabel = document.getElementById('upload-status-label');
  const uploadPercentage = document.getElementById('upload-percentage');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const transcribingBox = document.getElementById('transcribing-box');
  const processingStatusText = document.getElementById('processing-status-text');
  const submitBtn = document.getElementById('submit-btn');
  const toastContainer = document.getElementById('toast-container');

  // State
  let currentMode = 'file'; // 'file' | 'link' | 'record'
  let selectedFile = null;
  let timerInterval = null;
  let startTime = null;

  // Audio Recording State
  let mediaRecorder = null;
  let audioChunks = [];
  let recordTimer = null;
  let recordSeconds = 0;
  let mediaStream = null;

  // Simple Toast Helper
  function showToast(message, type = 'info') {
    if (!toastContainer) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 4500);
  }

  // Format file size helper
  function formatBytes(bytes) {
    if (!bytes) return '0 Bytes';
    const mb = (bytes / (1024 * 1024)).toFixed(2);
    return `${mb} MB`;
  }

  // Format seconds to MM:SS
  function formatSeconds(sec) {
    const m = String(Math.floor(sec / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${m}:${s}`;
  }

  // 1. Tab Switching (File Upload, Paste Link, Record Audio)
  modeTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const mode = tab.getAttribute('data-mode');
      if (mode === currentMode) return;

      currentMode = mode;
      modeTabs.forEach(t => t.classList.toggle('active', t === tab));

      // Show matching pane
      paneFile.style.display = (mode === 'file') ? 'block' : 'none';
      paneLink.style.display = (mode === 'link') ? 'block' : 'none';
      paneRecord.style.display = (mode === 'record') ? 'block' : 'none';

      // Update submit button text
      if (mode === 'link') {
        submitBtn.textContent = 'Fetch & Transcribe Link';
        filePreview.style.display = 'none';
      } else if (mode === 'record') {
        submitBtn.textContent = 'Transcribe Recording';
      } else {
        submitBtn.textContent = 'Upload & Transcribe Audio';
      }
    });
  });

  // 2. File Upload (Drag & Drop + File Selector)
  dropzone.addEventListener('click', () => fileInput.click());

  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  });

  function handleFile(file, isRecording = false) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    if (previewIcon) previewIcon.textContent = isRecording ? '🎙️' : '🎵';
    
    if (currentMode === 'file') dropzone.style.display = 'none';
    filePreview.style.display = 'flex';
  }

  removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    filePreview.style.display = 'none';
    if (currentMode === 'file') dropzone.style.display = 'block';
  });

  // 3. Paste Link Handling
  if (linkUrlInput) {
    linkUrlInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      if (clearLinkBtn) clearLinkBtn.style.display = val ? 'block' : 'none';
    });
  }

  if (clearLinkBtn) {
    clearLinkBtn.addEventListener('click', () => {
      linkUrlInput.value = '';
      clearLinkBtn.style.display = 'none';
      linkUrlInput.focus();
    });
  }

  // 4. Live Microphone Recording Handling
  if (recordToggleBtn) {
    recordToggleBtn.addEventListener('click', async () => {
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        // Stop recording
        stopRecording();
      } else {
        // Start recording
        startRecording();
      }
    });
  }

  if (recordStopBtn) {
    recordStopBtn.addEventListener('click', () => {
      stopRecording();
    });
  }

  async function startRecording() {
    try {
      audioChunks = [];
      recordSeconds = 0;
      recordCounter.textContent = '00:00';

      mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const options = { mimeType: 'audio/webm' };
      if (!MediaRecorder.isTypeSupported('audio/webm')) {
        delete options.mimeType; // Let browser pick default supported type
      }

      mediaRecorder = new MediaRecorder(mediaStream, options);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunks.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const mime = mediaRecorder.mimeType || 'audio/webm';
        const ext = mime.includes('mp4') ? 'm4a' : (mime.includes('ogg') ? 'ogg' : 'webm');
        const audioBlob = new Blob(audioChunks, { type: mime });
        const recordedFile = new File([audioBlob], `recorded_audio_${Date.now()}.${ext}`, { type: mime });

        handleFile(recordedFile, true);

        // Preview audio player
        if (recordedAudioPlayer) {
          recordedAudioPlayer.src = URL.createObjectURL(audioBlob);
          if (recordedPreviewWrap) recordedPreviewWrap.style.display = 'block';
        }

        recordLabel.textContent = `✅ Recording saved (${formatBytes(recordedFile.size)}). Ready to transcribe!`;
        recordToggleBtn.textContent = '🔄 Re-record Audio';
        showToast('Microphone recording finished!', 'success');

        // Stop all audio hardware tracks
        if (mediaStream) {
          mediaStream.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorder.start(250); // Record chunks every 250ms

      // Visual State
      recordRing.classList.add('recording');
      recordLabel.textContent = '🔴 Recording live voice... Speak into your microphone.';
      recordToggleBtn.textContent = '⏹️ Stop Recording';
      recordStopBtn.style.display = 'inline-flex';
      if (recordedPreviewWrap) recordedPreviewWrap.style.display = 'none';

      // Start duration counter
      recordTimer = setInterval(() => {
        recordSeconds++;
        recordCounter.textContent = formatSeconds(recordSeconds);
      }, 1000);

    } catch (err) {
      console.error('Microphone access error:', err);
      showToast('Could not access microphone. Please allow microphone permissions in browser.', 'danger');
    }
  }

  function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop();
    }
    if (recordTimer) clearInterval(recordTimer);
    recordRing.classList.remove('recording');
    recordStopBtn.style.display = 'none';
  }

  // 5. Form Submission (Upload & Transcribe)
  uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const selectedLang = languageSelect ? languageSelect.value : 'auto';
    const formData = new FormData();
    formData.append('language_mode', selectedLang);

    if (currentMode === 'link') {
      const linkVal = linkUrlInput ? linkUrlInput.value.trim() : '';
      if (!linkVal) {
        showToast('Please enter a YouTube video URL or audio link.', 'danger');
        linkUrlInput.focus();
        return;
      }
      formData.append('link_url', linkVal);
      uploadStatusLabel.textContent = 'Downloading media from link...';
    } else {
      if (!selectedFile) {
        const msg = (currentMode === 'record')
          ? 'Please record audio with your microphone first.'
          : 'Please choose or drop an audio file first.';
        showToast(msg, 'danger');
        return;
      }
      formData.append('file', selectedFile);
      uploadStatusLabel.textContent = 'Uploading audio file...';
    }

    // Show Progress State
    uploadForm.style.display = 'none';
    uploadProgressBox.style.display = 'block';
    submitBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);
    xhr.timeout = 600000; // 10 minutes timeout for larger files or videos

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        progressBarFill.style.width = percent + '%';
        uploadPercentage.textContent = percent + '%';
        uploadStatusLabel.textContent = `Uploading data (${formatBytes(event.loaded)} / ${formatBytes(event.total)})...`;
      }
    };

    xhr.upload.onload = () => {
      uploadProgressBox.style.display = 'none';
      transcribingBox.style.display = 'block';
      startTimer();
    };

    xhr.onload = () => {
      stopTimer();
      try {
        const response = JSON.parse(xhr.responseText);
        if (xhr.status === 200 && response.success) {
          showToast('Transcription complete! Redirecting to Editor...', 'success');
          setTimeout(() => {
            window.location.href = response.redirect_url;
          }, 300);
        } else {
          showToast(response.error || 'Transcription failed on server.', 'danger');
          resetForm();
        }
      } catch (err) {
        showToast('Server returned an unexpected response. Please try again.', 'danger');
        resetForm();
      }
    };

    xhr.ontimeout = () => {
      stopTimer();
      showToast('Process timed out. Please try with a shorter audio/video file.', 'danger');
      resetForm();
    };

    xhr.onerror = () => {
      stopTimer();
      showToast('Server connection error. Please ensure the server is running.', 'danger');
      resetForm();
    };

    xhr.send(formData);
  });

  function startTimer() {
    startTime = Date.now();
    const messages = [
      "Transcribing speech with Whisper AI...",
      "Extracting timestamps and recognizing words...",
      "Detecting pauses to build synchronized chapters...",
      "Saving results to database..."
    ];
    let idx = 0;

    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      if (elapsed > 0 && elapsed % 6 === 0 && idx < messages.length - 1) {
        idx++;
        processingStatusText.textContent = messages[idx];
      }
    }, 1000);
  }

  function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
  }

  function resetForm() {
    uploadProgressBox.style.display = 'none';
    transcribingBox.style.display = 'none';
    uploadForm.style.display = 'block';
    submitBtn.disabled = false;
  }
});
