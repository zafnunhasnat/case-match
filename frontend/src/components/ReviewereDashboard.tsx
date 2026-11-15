// frontend/src/components/ReviewerDashboard.tsx

import React, { useState, useEffect } from 'react';

interface PendingNote {
  id: number;
  note_identifier: string;
  raw_text: string;
  redacted_text: string;
}

export function ReviewerDashboard() {
  const [notes, setNotes] = useState<PendingNote[]>([]);
  const [selectedNote, setSelectedNote] = useState<PendingNote | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('/api/notes/pending', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
      .then(res => res.json())
      .then(data => {
        setNotes(data);
        if (data.length > 0) setSelectedNote(data[0]);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleReview = async (approve: boolean) => {
    if (!selectedNote) return;
    try {
      const response = await fetch(`/api/notes/${selectedNote.id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ approved: approve })
      });

      if (response.ok) {
        const remaining = notes.filter(n => n.id !== selectedNote.id);
        setNotes(remaining);
        setSelectedNote(remaining.length > 0 ? remaining[0] : null);
      }
    } catch (error) {
      console.error("Failed to submit review", error);
    }
  };

  if (loading) {
    return <div className="p-8 text-slate-400 bg-slate-950 min-h-screen">Loading pending review queue...</div>;
  }

  return (
    <div className="grid grid-cols-12 gap-6 p-6 bg-slate-950 text-slate-100 min-h-screen">
      <div className="col-span-4 border-r border-slate-800 pr-4">
        <h2 className="text-xl font-semibold mb-4 text-slate-200">Pending Review Queue ({notes.length})</h2>
        {notes.length === 0 ? (
          <p className="text-slate-500 text-sm">No notes currently pending review.</p>
        ) : (
          <div className="space-y-2">
            {notes.map(note => (
              <div
                key={note.id}
                onClick={() => setSelectedNote(note)}
                className={`p-3 rounded-lg cursor-pointer transition ${
                  selectedNote?.id === note.id 
                    ? 'bg-blue-600/30 border border-blue-500 text-blue-200' 
                    : 'bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800/60'
                }`}
              >
                <p className="font-mono text-sm font-medium">{note.note_identifier}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="col-span-8 flex flex-col">
        {selectedNote ? (
          <>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-slate-200">De-Identification Verification: <span className="font-mono text-blue-400">{selectedNote.note_identifier}</span></h2>
            </div>
            
            <div className="grid grid-cols-2 gap-4 flex-1 mb-6">
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 overflow-y-auto max-h-[60vh]">
                <h3 className="text-xs font-bold text-rose-400 mb-2 uppercase tracking-wider">Raw Clinical Text</h3>
                <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300 leading-relaxed">{selectedNote.raw_text}</pre>
              </div>
              <div className="bg-slate-900 p-4 rounded-xl border border-slate-800 overflow-y-auto max-h-[60vh]">
                <h3 className="text-xs font-bold text-emerald-400 mb-2 uppercase tracking-wider">Screened & Redacted (Safe Harbor)</h3>
                <pre className="whitespace-pre-wrap font-mono text-xs text-slate-300 leading-relaxed">{selectedNote.redacted_text}</pre>
              </div>
            </div>

            <div className="flex gap-4 justify-end pt-2 border-t border-slate-800">
              <button
                onClick={() => handleReview(false)}
                className="px-5 py-2.5 bg-rose-600 hover:bg-rose-700 font-medium rounded-lg text-white transition text-sm shadow-sm"
              >
                Reject Note
              </button>
              <button
                onClick={() => handleReview(true)}
                className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 font-medium rounded-lg text-white transition text-sm shadow-sm"
              >
                Approve & Release to Search
              </button>
            </div>
          </>
        ) : (
          <div className="flex items-center justify-center h-full text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800">
            Select a note from the queue to begin review
          </div>
        )}
      </div>
    </div>
  );
}