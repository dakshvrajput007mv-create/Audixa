import { useState, useEffect, useRef } from 'react';
import { useDebounce } from '../hooks/useDebounce';
import api from '../api';
import { Plus, Trash2, Loader2, Check } from 'lucide-react';

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

interface ChapterMakerProps {
  transcriptId: number;
  initialChapters: Chapter[];
  segments: Segment[];
  currentTime: number;
  duration: number;
  seekTo: (time: number) => void;
}

function ChapterItem({ 
  chapter, 
  isActive, 
  previewText, 
  duration, 
  updateChapter, 
  deleteChapter, 
  seekTo 
}: {
  chapter: Chapter;
  isActive: boolean;
  previewText: string;
  duration: number;
  updateChapter: (id: number, field: keyof Chapter, value: string | number) => void;
  deleteChapter: (id: number) => void;
  seekTo: (time: number) => void;
}) {
  const [localTitle, setLocalTitle] = useState(chapter.title);
  const [localStart, setLocalStart] = useState(chapter.start_time.toString());
  const [localEnd, setLocalEnd] = useState((chapter.end_time || duration).toString());

  // Sync with props if they change externally
  useEffect(() => { setLocalTitle(chapter.title); }, [chapter.title]);
  useEffect(() => { setLocalStart(chapter.start_time.toString()); }, [chapter.start_time]);
  useEffect(() => { setLocalEnd((chapter.end_time || duration).toString()); }, [chapter.end_time, duration]);

  const handleBlur = (field: keyof Chapter, valStr: string) => {
    if (field === 'title') {
      updateChapter(chapter.id, 'title', valStr);
    } else {
      const parsed = parseFloat(valStr) || 0;
      updateChapter(chapter.id, field, parsed);
    }
  };

  return (
    <div 
      className={`p-4 rounded-xl border transition-all duration-200 group
        ${isActive ? 'bg-indigo-50 border-indigo-200 shadow-sm transform scale-[1.02]' : 'bg-white border-zinc-200 hover:border-zinc-300 hover:shadow-sm'}`}
      onClick={(e) => {
        if ((e.target as HTMLElement).tagName !== 'INPUT' && (e.target as HTMLElement).tagName !== 'BUTTON' && !(e.target as HTMLElement).closest('button')) {
          seekTo(chapter.start_time);
        }
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <input
          type="text"
          value={localTitle}
          onChange={(e) => setLocalTitle(e.target.value)}
          onBlur={(e) => handleBlur('title', e.target.value)}
          className={`font-medium bg-transparent border-b border-transparent focus:border-zinc-300 focus:outline-none w-2/3
            ${isActive ? 'text-indigo-900' : 'text-zinc-900'}`}
          placeholder="Chapter Title"
        />
        <button 
          onClick={() => deleteChapter(chapter.id)}
          className="text-zinc-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
          title="Delete chapter"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>

      <div className="flex items-center space-x-2 text-xs mt-1">
        <input
          type="text"
          value={localStart}
          onChange={(e) => setLocalStart(e.target.value)}
          onBlur={(e) => handleBlur('start_time', e.target.value)}
          className="w-16 bg-transparent hover:bg-zinc-100 border border-transparent hover:border-zinc-200 rounded px-1.5 py-1 focus:outline-none focus:bg-white focus:border-zinc-300 focus:ring-1 focus:ring-indigo-400 text-zinc-700 font-mono transition-colors"
          title="Start Time (seconds)"
        />
        <span className="text-zinc-400 font-medium">to</span>
        <input
          type="text"
          value={localEnd}
          onChange={(e) => setLocalEnd(e.target.value)}
          onBlur={(e) => handleBlur('end_time', e.target.value)}
          className="w-16 bg-transparent hover:bg-zinc-100 border border-transparent hover:border-zinc-200 rounded px-1.5 py-1 focus:outline-none focus:bg-white focus:border-zinc-300 focus:ring-1 focus:ring-indigo-400 text-zinc-700 font-mono transition-colors"
          title="End Time (seconds)"
        />
      </div>

      <p className={`text-xs mt-3 italic truncate ${isActive ? 'text-indigo-600/80' : 'text-zinc-500'}`}>
        "{previewText}"
      </p>
    </div>
  );
}

export default function ChapterMaker({ transcriptId, initialChapters, segments, currentTime, duration, seekTo }: ChapterMakerProps) {
  const [chapters, setChapters] = useState<Chapter[]>(initialChapters);
  const debouncedChapters = useDebounce(chapters, 1500);
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved'>('idle');
  
  const isFirstRender = useRef(true);
  const lastSavedStr = useRef(JSON.stringify(initialChapters));

  // Sync to Backend
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }

    const currentStr = JSON.stringify(debouncedChapters);
    if (currentStr === lastSavedStr.current) return;

    const saveChapters = async () => {
      setSaveState('saving');
      try {
        await api.patch(`/files/${transcriptId}/chapters`, debouncedChapters);
        lastSavedStr.current = currentStr;
        setSaveState('saved');
        setTimeout(() => setSaveState('idle'), 2000);
      } catch (err) {
        console.error('Failed to save chapters:', err);
        setSaveState('idle'); // Or error state
      }
    };
    
    saveChapters();
  }, [debouncedChapters, transcriptId]);

  const addChapter = () => {
    const newChapters = [...chapters];
    
    // Find if we are currently inside an existing chapter
    const currentChapterIndex = newChapters.findIndex(
      c => currentTime >= c.start_time && (currentTime < (c.end_time || duration))
    );

    let nextStartTime = duration;
    
    if (currentChapterIndex !== -1) {
      // Split the current chapter
      const currentChapter = newChapters[currentChapterIndex];
      nextStartTime = currentChapter.end_time || duration;
      
      // Update the current chapter to end exactly at currentTime
      newChapters[currentChapterIndex] = {
        ...currentChapter,
        end_time: currentTime
      };
    } else {
      // If we aren't in a chapter, find the next chapter's start time
      for (const c of newChapters) {
        if (c.start_time > currentTime && c.start_time < nextStartTime) {
          nextStartTime = c.start_time;
        }
      }
    }

    const newChapter: Chapter = {
      id: Date.now(), // temporary ID
      title: 'New Chapter',
      start_time: currentTime,
      end_time: nextStartTime
    };

    newChapters.push(newChapter);
    newChapters.sort((a, b) => a.start_time - b.start_time);
    setChapters(newChapters);
  };

  const updateChapter = (id: number, field: keyof Chapter, value: string | number) => {
    setChapters(prev => {
      const updated = prev.map(c => c.id === id ? { ...c, [field]: value } : c);
      if (field === 'start_time') {
        return updated.sort((a, b) => a.start_time - b.start_time);
      }
      return updated;
    });
  };

  const deleteChapter = (id: number) => {
    if (window.confirm("Are you sure you want to delete this chapter?")) {
      setChapters(prev => prev.filter(c => c.id !== id));
    }
  };

  return (
    <div className="flex flex-col h-full bg-white border-r border-zinc-200">
      <div className="p-4 border-b border-zinc-200 flex justify-between items-center bg-zinc-50">
        <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Chapters</h3>
        <div className="flex items-center space-x-2">
          {saveState === 'saving' && <Loader2 className="h-3 w-3 text-zinc-400 animate-spin" />}
          {saveState === 'saved' && <Check className="h-3 w-3 text-green-500" />}
          <button 
            onClick={addChapter}
            className="flex items-center text-xs font-medium text-zinc-700 bg-white border border-zinc-300 px-2 py-1 rounded hover:bg-zinc-50 transition"
          >
            <Plus className="h-3 w-3 mr-1" /> Add
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chapters.map((c) => {
          const isActive = currentTime >= c.start_time && (currentTime < c.end_time || c.end_time === 0);
          
          // Find preview text (first segment that falls into this chapter)
          const previewSegment = segments.find(s => s.start_time >= c.start_time && s.start_time < (c.end_time || duration));
          const previewText = previewSegment ? previewSegment.text.substring(0, 40) + '...' : '...';

          return (
            <ChapterItem 
              key={c.id}
              chapter={c}
              isActive={isActive}
              previewText={previewText}
              duration={duration}
              updateChapter={updateChapter}
              deleteChapter={deleteChapter}
              seekTo={seekTo}
            />
          );
        })}

        {chapters.length === 0 && (
          <div className="text-center p-6 border-2 border-dashed border-zinc-200 rounded-lg">
            <p className="text-sm text-zinc-500 mb-2">No chapters yet.</p>
            <button 
              onClick={addChapter}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-700"
            >
              + Add first chapter
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
