import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import { FileAudio, UploadCloud, Loader2, Music, XCircle, FileVideo, AlertCircle } from 'lucide-react';

export default function Home() {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [isUploading, setIsUploading] = useState(false);
  
  const [transcriptId, setTranscriptId] = useState<number | null>(null);
  const [processingStatus, setProcessingStatus] = useState<'pending' | 'processing' | 'ready' | 'failed' | null>(null);
  const [transcriptionProgress, setTranscriptionProgress] = useState<number>(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('');
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleFile = (file: File) => {
    setErrorMsg(null);
    const validExtensions = ['.mp3', '.wav', '.m4a', '.mp4'];
    const isValidExt = validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
    const isValidMime = file.type.startsWith('audio/') || file.type.startsWith('video/');

    if (!isValidExt && !isValidMime) {
      setErrorMsg('Invalid file type. Please upload .mp3, .wav, .m4a, or .mp4');
      return;
    }
    
    setSelectedFile(file);
    startUpload(file);
  };

  const startUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    if (selectedLanguage) {
      formData.append('language', selectedLanguage);
    }

    setIsUploading(true);
    setUploadProgress(0);
    
    try {
      const res = await api.post('/files/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percentCompleted);
          }
        }
      });
      
      setTranscriptId(res.data.id);
      setProcessingStatus('pending');
    } catch (err) {
      console.error(err);
      setErrorMsg('Upload failed. Please try again.');
      setIsUploading(false);
      setSelectedFile(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };
  
  const handleReset = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setIsUploading(false);
    setTranscriptId(null);
    setProcessingStatus(null);
    setErrorMsg(null);
  };

  // Polling effect
  useEffect(() => {
    if (!transcriptId || (processingStatus !== 'pending' && processingStatus !== 'processing')) return;

    const pollInterval = setInterval(async () => {
      try {
        const res = await api.get(`/files/${transcriptId}`);
        const status = res.data.status;
        setProcessingStatus(status);
        if (res.data.progress !== undefined) {
          setTranscriptionProgress(res.data.progress);
        }
        
        if (status === 'ready') {
          clearInterval(pollInterval);
          navigate(`/editor/${transcriptId}`);
        } else if (status === 'failed') {
          clearInterval(pollInterval);
          setErrorMsg('Transcription failed on the server.');
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 2500);

    return () => clearInterval(pollInterval);
  }, [transcriptId, processingStatus, navigate]);

  return (
    <div className="min-h-screen bg-zinc-50 flex flex-col">
      {/* Header */}
      <nav className="bg-white px-8 py-4 flex items-center shadow-sm">
        <FileAudio className="h-8 w-8 text-zinc-900 mr-2" />
        <span className="text-2xl font-bold tracking-tight text-zinc-900">Audixa</span>
      </nav>

      {/* Main Hero / Upload Area */}
      <main className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-extrabold text-zinc-900 tracking-tight mb-4">
            Turn audio into text, instantly.
          </h1>
          <p className="text-lg text-zinc-600 max-w-2xl mx-auto">
            Upload your audio or video file. Our AI will automatically transcribe the speech and intelligently split it into chapters for you to review and edit.
          </p>
        </div>

        {/* Upload Container */}
        <div className="w-full max-w-2xl">
          {errorMsg && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
              <AlertCircle className="h-5 w-5 mr-3 flex-shrink-0" />
              <p>{errorMsg}</p>
            </div>
          )}

          {!selectedFile ? (
            /* Drag & Drop Zone */
            <div 
              className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer
                ${dragActive ? 'border-zinc-900 bg-zinc-100' : 'border-zinc-300 bg-white hover:border-zinc-400'}
              `}
              onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); setDragActive(true); }}
              onDragEnter={(e) => { e.preventDefault(); e.stopPropagation(); setDragActive(true); }}
              onDragLeave={(e) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); }}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                type="file"
                accept=".mp3, .wav, .m4a, .mp4, audio/*, video/*"
                ref={fileInputRef}
                className="hidden"
                onChange={(e) => e.target.files && handleFile(e.target.files[0])}
              />
              <div className="flex flex-col items-center justify-center space-y-4">
                <div className="p-4 bg-zinc-100 rounded-full text-zinc-900">
                  <UploadCloud className="h-10 w-10" />
                </div>
                <div>
                  <p className="text-xl font-semibold text-zinc-900">
                    Click or drag your file here
                  </p>
                  <p className="text-zinc-500 mt-2">
                    Supports .mp3, .wav, .m4a, .mp4
                  </p>
                </div>
                
                <div className="mt-4 pt-4 border-t border-zinc-200 w-full flex flex-col items-center">
                  <label className="text-sm font-medium text-zinc-700 mb-2">Spoken Language (Optional)</label>
                  <select 
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    onClick={(e) => e.stopPropagation()}
                    className="mb-4 bg-white border border-zinc-300 text-zinc-900 text-sm rounded-lg focus:ring-indigo-500 focus:border-indigo-500 block w-48 p-2"
                  >
                    <option value="">Auto-detect</option>
                    <option value="hi">Hindi</option>
                    <option value="hinglish">Hinglish</option>
                    <option value="mr">Marathi</option>
                    <option value="en">English</option>
                  </select>
                  <button className="px-6 py-3 bg-zinc-900 text-white font-medium rounded-lg shadow hover:bg-zinc-800 transition">
                    Browse files
                  </button>
                </div>
              </div>
            </div>
          ) : (
            /* Processing State */
            <div className="bg-white border border-zinc-200 rounded-2xl p-8 shadow-sm">
              <div className="flex items-center space-x-4 mb-6">
                <div className="p-3 bg-indigo-50 rounded-lg text-indigo-600">
                  {selectedFile.type.startsWith('video') ? <FileVideo className="h-8 w-8" /> : <FileAudio className="h-8 w-8" />}
                </div>
                <div className="flex-1 truncate">
                  <h3 className="font-semibold text-zinc-900 truncate" title={selectedFile.name}>{selectedFile.name}</h3>
                  <p className="text-sm text-zinc-500">{(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
                {processingStatus === 'failed' && (
                  <button onClick={handleReset} className="text-zinc-400 hover:text-zinc-700">
                    <XCircle className="h-6 w-6" />
                  </button>
                )}
              </div>

              {/* Progress/Status area */}
              {(!transcriptId || processingStatus === 'pending' || processingStatus === 'processing' || processingStatus === null) && processingStatus !== 'failed' && (
                <div className="space-y-3">
                  <div className="flex justify-between text-sm font-medium">
                    <span className="text-zinc-700">
                      {!transcriptId ? 'Uploading...' : 'Transcribing...'}
                    </span>
                    <span className="text-zinc-900">
                      {!transcriptId ? `${uploadProgress}%` : `${transcriptionProgress}%`}
                    </span>
                  </div>
                  
                  <div className="w-full bg-zinc-100 rounded-full h-3 overflow-hidden">
                    {!transcriptId ? (
                      <div 
                        className="bg-zinc-900 h-3 rounded-full transition-all duration-300" 
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    ) : (
                      <div 
                        className="bg-zinc-900 h-3 rounded-full transition-all duration-300" 
                        style={{ width: `${transcriptionProgress}%` }}
                      ></div>
                    )}
                  </div>
                  
                  {transcriptId && (
                    <p className="text-xs text-zinc-500 text-center mt-4">
                      This might take a few minutes depending on the file length.
                    </p>
                  )}
                </div>
              )}

              {processingStatus === 'failed' && (
                <div className="mt-6 text-center">
                  <button 
                    onClick={handleReset}
                    className="px-6 py-2 bg-zinc-900 text-white font-medium rounded-lg shadow hover:bg-zinc-800 transition"
                  >
                    Try again
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Feature Highlights */}
        <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl w-full">
          <div className="text-center">
            <div className="bg-white p-4 rounded-full shadow-sm inline-block mb-3 text-zinc-900 border border-zinc-100">
              <Music className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-zinc-900 mb-1">High Accuracy</h3>
            <p className="text-sm text-zinc-500">Powered by advanced AI transcription.</p>
          </div>
          <div className="text-center">
            <div className="bg-white p-4 rounded-full shadow-sm inline-block mb-3 text-zinc-900 border border-zinc-100">
              <FileAudio className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-zinc-900 mb-1">Smart Chapters</h3>
            <p className="text-sm text-zinc-500">Automatically segments based on silences.</p>
          </div>
          <div className="text-center">
            <div className="bg-white p-4 rounded-full shadow-sm inline-block mb-3 text-zinc-900 border border-zinc-100">
              <UploadCloud className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-zinc-900 mb-1">Easy Export</h3>
            <p className="text-sm text-zinc-500">Download as TXT, SRT, or PDF instantly.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
