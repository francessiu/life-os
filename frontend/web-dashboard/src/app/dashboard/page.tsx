'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { goalApi } from '@/lib/api';
import { Goal } from '@/types';
import CharacterWidget from '@/components/CharacterWidget';
import GoalList from '@/components/GoalList';
import GoalCreator from '@/components/GoalCreator';
import ChatInterface from '@/components/ChatInterface';

export default function Dashboard() {
  const { user, logout } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);

  const fetchGoals = async () => {
    try {
      const { data } = await goalApi.getGoals();
      setGoals(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchGoals();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <header className="max-w-7xl mx-auto flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">LifeOS Command</h1>
          <p className="text-gray-500">Welcome back, {user?.full_name || 'Pilot'}</p>
        </div>
        <div className="flex items-center gap-4">
            <button onClick={logout} className="text-sm text-red-600 hover:underline">Sign Out</button>
            <div className="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                {user?.email?.[0].toUpperCase()}
            </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Game & Chat (Sticky) */}
        <div className="space-y-6">
          <CharacterWidget />
          <ChatInterface />
        </div>

        {/* Right Column: Goals */}
        <div className="lg:col-span-2 space-y-8">
          <GoalCreator onGoalCreated={fetchGoals} />
          
          <div>
            <h2 className="text-lg font-semibold mb-4 text-gray-700">Active Directives</h2>
            {goals.length === 0 ? (
                <div className="text-center py-12 text-gray-400 bg-white rounded-xl border border-dashed">
                    No active goals. Initialize one above.
                </div>
            ) : (
                <GoalList goals={goals} refreshData={fetchGoals} />
            )}
          </div>
        </div>
      </main>
    </div>
  );
}