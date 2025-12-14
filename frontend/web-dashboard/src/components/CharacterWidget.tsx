import React, { useEffect, useState } from 'react';
import { gameApi } from '@/lib/api';
import { CharacterState } from '@/types';
import { Heart, ShieldAlert, Coins } from 'lucide-react';

export default function CharacterWidget() {
  const [state, setState] = useState<CharacterState | null>(null);

  const fetchState = async () => {
    try {
      const { data } = await gameApi.getCharacterState();
      setState(data);
    } catch (e) {
      console.error("Failed to load character", e);
    }
  };

  useEffect(() => {
    fetchState();
    // Poll every 30 seconds to keep tokens in sync
    const interval = setInterval(fetchState, 30000);
    return () => clearInterval(interval);
  }, []);

  if (!state) return <div className="animate-pulse h-20 bg-gray-100 rounded-xl" />;

  const getEmotionEmoji = () => {
    switch (state.emotion) {
      case 'happy': return '😺'; // Or custom asset
      case 'worried': return '🙀';
      case 'panicked': return '😿';
      default: return '🤖';
    }
  };

  const getColor = () => {
    if (state.tokens === 0) return 'bg-red-100 border-red-300';
    if (state.tokens === 1) return 'bg-yellow-100 border-yellow-300';
    return 'bg-blue-50 border-blue-200';
  };

  return (
    <div className={`p-4 rounded-xl border-2 flex items-center justify-between shadow-sm ${getColor()}`}>
      <div className="flex items-center gap-4">
        <div className="text-4xl bg-white p-2 rounded-full shadow-sm">
          {getEmotionEmoji()}
        </div>
        <div>
          <h3 className="font-bold text-gray-700">Butler Status</h3>
          <p className="text-sm text-gray-500 capitalize">{state.emotion}</p>
        </div>
      </div>
      
      <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-gray-200">
        <Coins className="text-yellow-500 w-5 h-5" />
        <span className="font-bold text-gray-800">{state.tokens} / 3</span>
      </div>
    </div>
  );
}