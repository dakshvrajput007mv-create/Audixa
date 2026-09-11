/**
 * upload.js - Handles audio/video file selection, upload, and status updates.
 * Clean, standard Vanilla JavaScript for Milestone 1 (30% Project Review).
 */

document.addEventListener('DOMContentLoaded', () => {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const filePreview = document.getElementById('file-preview');
  const fileName = document.getElementById('file-name');
  const fileSize = document.getElementById('file-size');
  const removeFileBtn = document.getElementById('remove-file-btn');
  const uploadForm = document.getElementById('upload-form');
  const languageSelect = document.getElementById('language-select');
  const uploadProgressBox = document.getElementById('upload-progress-box');
  const uploadStatusLabel = document.getElementById('upload-status-label');
  const uploadPercentage = document.getElementById('upload-percentage');
  const progressBarFill = document.getElementById('progress-bar-fill');
  const transcribingBox = document.getElementById('transcribing-box');
  const processingStatusText = document.getElementById('processing-status-text');
  const elapsedTimeEl = document.getElementById('elapsed-time');
  const submitBtn = document.getElementById('submit-btn');
  const toastContainer = document.getElementById('toast-container');

  let selectedFile = null;
  let timerInterval = null;
  let startTime = null;

  // Simple Toast Helper
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.remove();
    }, 4000);
  }

  // Format file size helper
  function formatBytes(bytes) {
    if (!bytes) return '0 Bytes';
    const mb = (bytes / (1024 * 1024)).toFixed(2);
    return `${mb} MB`;
  }

  // Drag & Drop Handling
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

  function handleFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatBytes(file.size);
    dropzone.style.display = 'none';
    filePreview.style.display = 'flex';
  }

  removeFileBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    filePreview.style.display = 'none';
    dropzone.style.display = 'block';
  });

  // Upload and Transcribe submission
  uploadForm.addEventListener('submit', (e) => {
    e.preventDefault();

    if (!selectedFile) {
      showToast('Please choose an audio or video file first.', 'danger');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('language_mode', languageSelect ? languageSelect.value : 'auto');
    formData.append('model_size', 'base');

    // Show Progress State
    uploadForm.style.display = 'none';
    uploadProgressBox.style.display = 'block';
    submitBtn.disabled = true;

    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/upload', true);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        progressBarFill.style.width = percent + '%';
        uploadPercentage.textContent = percent + '%';
        uploadStatusLabel.textContent = `Uploading file (${formatBytes(event.loaded)} / ${formatBytes(event.total)})...`;
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
          showToast('Transcription complete! Redirecting...', 'success');
          setTimeout(() => {
            window.location.href = response.redirect_url;
          }, 300);
        } else {
          showToast(response.error || 'Transcription failed on server.', 'danger');
          resetForm();
        }
      } catch (err) {
        showToast('Server error while processing audio.', 'danger');
        resetForm();
      }
    };

    xhr.onerror = () => {
      stopTimer();
      showToast('Network error during upload. Please check connection.', 'danger');
      resetForm();
    };

    xhr.send(formData);
  });

  function startTimer() {
    startTime = Date.now();
    const messages = [
      "Transcribing speech with Whisper AI...",
      "Extracting timestamps and recognizing words...",
      "Analyzing pauses to create chapters...",
      "Saving results to database..."
    ];
    let idx = 0;

    timerInterval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - startTime) / 1000);
      const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
      const s = String(elapsed % 60).padStart(2, '0');
      elapsedTimeEl.textContent = `${m}:${s}`;

      if (elapsed > 0 && elapsed % 5 === 0 && idx < messages.length - 1) {
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
