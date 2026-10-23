import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';
import WaveSurfer from 'wavesurfer.js';
import { ArrowLeft, Play, Pause, Download, Loader2, Check } from 'lucide-react';
import ChapterMaker from '../components/ChapterMaker';
import { useDebounce } from '../hooks/useDebounce';

interface Segment {
  id: number;
  start_time: number;
  end_time: number;
  text: string;
}

interface Chapter {
  id: number;
  title: string;
  start_time: number;
  end_time: number;
}

interface Transcript {
  id: number;
  filename: string;
  status: string;
  duration: number | null;
  segments: Segment[];
  chapters: Chapter[];
}

export default function Editor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  
  // Transcript edits local state & autosave
  const [segmentsState, setSegmentsState] = useState<Segment[]>([]);
  const debouncedSegments = useDebounce(segmentsState, 1500);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  const isFirstRender = useRef(true);
  
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurfer = useRef<WaveSurfer | null>(null);
  const activeSegmentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchTranscript = async () => {
      try {
        const res = await api.get(`/files/${id}`);
        setTranscript(res.data);
        setSegmentsState(res.data.segments);
      } catch (err) {
        console.error(err);
      }
    };
    fetchTranscript();
  }, [id]);

  useEffect(() => {
    if (!transcript || transcript.status !== 'ready' || !waveformRef.current) return;

    if (wavesurfer.current) {
      wavesurfer.current.destroy();
    }

    wavesurfer.current = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#d4d4d8',
      progressColor: '#18181b',
      cursorColor: '#ef4444',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 80,
    });

    const loadAudio = async () => {
      try {
        const res = await api.get(`/files/${id}/media`, { responseType: 'blob' });
        const blobUrl = URL.createObjectURL(res.data);
        wavesurfer.current?.load(blobUrl);
      } catch (err) {
        console.error('Failed to load audio', err);
      }
    };
    loadAudio();

    wavesurfer.current.on('ready', () => setDuration(wavesurfer.current?.getDuration() || 0));
    wavesurfer.current.on('play', () => setIsPlaying(true));
    wavesurfer.current.on('pause', () => setIsPlaying(false));
    wavesurfer.current.on('timeupdate', (time) => setCurrentTime(time));

    return () => {
      wavesurfer.current?.destroy();
    };
  }, [transcript?.status, id]);

  // Transcript Autosave Logic
  useEffect(() => {
    if (isFirstRender.current || debouncedSegments.length === 0) {
      isFirstRender.current = false;
      return;
    }

    // Only save if it's different from the originally fetched transcript
    // To be efficient, we check if any segment text changed.
    const hasChanges = debouncedSegments.some((seg, idx) => seg.text !== transcript?.segments[idx]?.text);
    if (!hasChanges) return;

    const saveEdits = async () => {
      setSaveState('saving');
      
      // Build updates dict for backend { id: text }
      const updates: Record<number, string> = {};
      debouncedSegments.forEach(s => {
        updates[s.id] = s.text;
      });
      
      try {
        await api.patch(`/files/${id}/transcript`, updates);
        setSaveState('saved');
        // Update the transcript reference to reflect saved changes
        setTranscript(prev => prev ? { ...prev, segments: debouncedSegments } : null);
        setTimeout(() => setSaveState('idle'), 2000);
      } catch (err) {
        console.error(err);
        setSaveState('idle');
      }
    };

    saveEdits();
  }, [debouncedSegments, id]);

  useEffect(() => {
    // Auto-scroll to active segment
    if (activeSegmentRef.current) {
      activeSegmentRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [currentTime]);

  const togglePlay = () => wavesurfer.current?.playPause();
  const seekTo = (time: number) => {
    wavesurfer.current?.setTime(time);
    if (!isPlaying) wavesurfer.current?.play();
  };

  const handleEditChange = (segId: number, newText: string) => {
    setSegmentsState(prev => prev.map(s => s.id === segId ? { ...s, text: newText } : s));
  };

  const handleExport = async (format: string) => {
    try {
      const res = await api.get(`/files/${id}/export?format=${format}`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${transcript?.filename}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
    } catch (err) {
      console.error(err);
      alert('Export failed');
    }
  };

  if (!transcript) {
    return <div className="min-h-screen flex items-center justify-center bg-zinc-50"><Loader2 className="animate-spin text-zinc-500 h-8 w-8" /></div>;
  }

  return (
    <div className="h-screen flex flex-col bg-zinc-50 overflow-hidden">
      {/* Header */}
      <header className="bg-zinc-900 border-b border-zinc-800 px-6 py-3 flex justify-between items-center flex-shrink-0 shadow-sm z-10">
        <div className="flex items-center space-x-4">
          <button onClick={() => navigate('/')} className="text-zinc-400 hover:text-white transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-lg font-semibold text-white truncate max-w-md tracking-tight">{transcript.filename}</h1>
        </div>
        <div className="flex items-center space-x-4">
          
          <div className="flex items-center text-xs font-medium text-zinc-300">
            {saveState === 'saving' && <><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Saving transcript...</>}
            {saveState === 'saved' && <><Check className="h-3 w-3 mr-1 text-green-400" /> Saved</>}
          </div>
          
          <div className="relative group">
            <button className="flex items-center px-4 py-1.5 bg-zinc-800 border border-zinc-700 text-white text-sm font-medium rounded-lg hover:bg-zinc-700 transition-colors shadow-sm">
              <Download className="h-4 w-4 mr-2" /> Export
            </button>
            <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg border border-zinc-200 hidden group-hover:block z-10">
              <button onClick={() => handleExport('txt')} className="block w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">.TXT</button>
              <button onClick={() => handleExport('srt')} className="block w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">.SRT</button>
              <button onClick={() => handleExport('pdf')} className="block w-full text-left px-4 py-2 text-sm text-zinc-700 hover:bg-zinc-50">.PDF</button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content: Studio Layout */}
      <div className="flex-1 flex flex-col overflow-hidden">
        
        {/* Top Pane: Full-Width Waveform Player */}
        <div className="w-full bg-white border-b border-zinc-200 p-4 flex-shrink-0 flex items-center shadow-sm z-0">
          <button onClick={togglePlay} className="p-3 bg-zinc-900 text-white rounded-full hover:bg-zinc-800 transition mr-6 flex-shrink-0">
            {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5 ml-1" />}
          </button>
          
          <div className="flex-1 flex flex-col justify-center">
            <div ref={waveformRef} className="w-full"></div>
            <div className="mt-2 text-xs font-mono text-zinc-500 text-right">
              {Math.floor(currentTime / 60)}:{(Math.floor(currentTime % 60)).toString().padStart(2, '0')} 
              <span className="text-zinc-300 mx-1">/</span>
              {Math.floor(duration / 60)}:{(Math.floor(duration % 60)).toString().padStart(2, '0')}
            </div>
          </div>
        </div>

        {/* Bottom Pane: Split View (Chapters & Transcript) */}
        <div className="flex-1 flex overflow-hidden bg-zinc-50">
          
          {/* Left Pane: Chapter Maker (25%) */}
          <div className="w-full md:w-1/4 bg-white border-r border-zinc-200 flex flex-col z-0">
            <ChapterMaker 
              transcriptId={transcript.id}
              initialChapters={transcript.chapters}
              segments={segmentsState}
              currentTime={currentTime}
              duration={duration || (transcript.segments[transcript.segments.length - 1]?.end_time) || 0}
              seekTo={seekTo}
            />
          </div>

          {/* Right Pane: Transcript Editor (75%) */}
          <div className="w-full md:w-3/4 flex flex-col relative">
            <div className="flex-1 overflow-y-auto p-8 scroll-smooth">
              <div className="max-w-3xl mx-auto pb-48">
                {segmentsState.map(s => {
                  const isActive = currentTime >= s.start_time && currentTime <= s.end_time;
                  return (
                    <div 
                      key={s.id}
                      ref={isActive ? activeSegmentRef : null}
                      className={`flex mb-6 group rounded-2xl transition-all duration-300 border ${
                        isActive 
                          ? 'border-indigo-200 bg-white shadow-md transform scale-[1.01]' 
                          : 'border-transparent bg-transparent hover:bg-white/60 hover:shadow-sm'
                      }`}
                    >
                      {/* Timestamp Badge */}
                      <div 
                        className={`w-20 pt-5 pl-4 flex-shrink-0 cursor-pointer rounded-l-2xl flex justify-center items-start border-l-4 transition-colors ${
                          isActive ? 'border-indigo-500 bg-indigo-50/30' : 'border-transparent'
                        }`}
                        onClick={() => seekTo(s.start_time)}
                      >
                        <span className={`text-xs font-mono px-2 py-1 rounded-md transition-colors ${
                          isActive ? 'bg-indigo-100 text-indigo-700 font-bold' : 'text-zinc-400 group-hover:text-zinc-600'
                        }`}>
                          {Math.floor(s.start_time / 60)}:{(Math.floor(s.start_time % 60)).toString().padStart(2, '0')}
                        </span>
                      </div>
                      
                      {/* Text Editor */}
                      <div className="flex-1 p-4 pl-2">
                        <textarea
                          value={s.text}
                          onChange={(e) => handleEditChange(s.id, e.target.value)}
                          className={`w-full bg-transparent resize-none overflow-hidden focus:outline-none focus:ring-2 focus:ring-indigo-100 focus:bg-white rounded-lg p-2 text-lg leading-relaxed transition-all
                            ${isActive ? 'text-zinc-900 font-medium' : 'text-zinc-600'}`}
                          style={{ minHeight: '3rem' }}
                          onInput={(e) => {
                            const target = e.target as HTMLTextAreaElement;
                            target.style.height = 'auto';
                            target.style.height = target.scrollHeight + 'px';
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
          
        </div>
      </div>
    </div>
  );
}
