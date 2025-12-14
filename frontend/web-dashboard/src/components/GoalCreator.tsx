import React, { useState } from 'react';
import { goalApi } from '@/lib/api';
import { Loader2, Sparkles, Calendar } from 'lucide-react';

interface Props {
  onGoalCreated: () => void;
}

export default function GoalCreator({ onGoalCreated }: Props) {
  const [title, setTitle] = useState('');
  const [deadline, setDeadline] = useState('');
  const [decompose, setDecompose] = useState(true); // Default to AI on
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title) return;

    setLoading(true);
    try {
      await goalApi.createGoal({ 
        title, 
        deadline: deadline || null,
        days_per_week: 5 
      }, decompose);
      
      setTitle('');
      setDeadline('');
      onGoalCreated();
    } catch (err) {
      alert("Failed to create goal");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4">
      <h3 className="font-semibold text-lg flex items-center gap-2">
        <Sparkles className="w-5 h-5 text-purple-600" />
        New Objective
      </h3>

      <div className="space-y-2">
        <input
          type="text"
          placeholder="What do you want to achieve?"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
        />
        
        <div className="flex gap-4">
            <div className="relative flex-1">
                <Calendar className="absolute left-3 top-2.5 w-4 h-4 text-gray-400"/>
                <input 
                    type="date" 
                    value={deadline}
                    onChange={(e) => setDeadline(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border rounded-lg text-sm"
                />
            </div>
            
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
                type="checkbox"
                checked={decompose}
                onChange={(e) => setDecompose(e.target.checked)}
                className="w-4 h-4 text-purple-600 rounded"
            />
            AI Breakdown
            </label>
        </div>
      </div>

      <button
        disabled={loading || !title}
        className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed flex justify-center items-center gap-2"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Planning...
          </>
        ) : (
          "Initialize Goal"
        )}
      </button>
    </form>
  );
}