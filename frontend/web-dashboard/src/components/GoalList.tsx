import React, { useState } from 'react';
import { goalApi, gameApi } from '@/lib/api';
import { Goal, Step } from '@/types';
import { CheckCircle2, Circle, AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  goals: Goal[];
  refreshData: () => void;
}

export default function GoalList({ goals, refreshData }: Props) {
  
  const handleToggleStep = async (goalId: number, stepId: number, currentStatus: boolean) => {
    try {
      await goalApi.updateStep(goalId, stepId, !currentStatus);
      refreshData();
    } catch (e) {
      console.error(e);
    }
  };

  const handleSmartRestart = async () => {
    if(!confirm("The AI will analyze your failed tasks and break them down. Proceed?")) return;
    try {
        await goalApi.restartSmart();
        refreshData();
    } catch (e) {
        alert("Restart failed");
    }
  }

  return (
    <div className="space-y-6">
        {/* Failed State Header (F-3.7) */}
        {goals.some(g => g.status === 'failed') && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-lg flex items-center justify-between">
                <div>
                    <h4 className="font-bold text-red-700 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5"/> Plan Failed
                    </h4>
                    <p className="text-sm text-red-600">You ran out of tokens. Restart required.</p>
                </div>
                <button 
                    onClick={handleSmartRestart}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-red-700 flex items-center gap-2"
                >
                    <RefreshCw className="w-4 h-4"/> Smart Restart
                </button>
            </div>
        )}

      {goals.map((goal) => (
        <div key={goal.id} className={`bg-white rounded-xl shadow-sm border p-6 ${goal.status === 'failed' ? 'opacity-50 pointer-events-none' : ''}`}>
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-xl font-bold text-gray-900">{goal.title}</h3>
              {goal.description && <p className="text-gray-500 text-sm mt-1">{goal.description}</p>}
            </div>
            <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${goal.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
              {goal.status}
            </span>
          </div>

          <div className="space-y-3">
            {goal.steps.map((step) => (
              <div
                key={step.id}
                onClick={() => handleToggleStep(goal.id, step.id, step.is_completed)}
                className="flex items-center gap-3 p-3 hover:bg-gray-50 rounded-lg cursor-pointer group transition-colors"
              >
                {step.is_completed ? (
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                ) : (
                  <Circle className="w-5 h-5 text-gray-300 group-hover:text-purple-500" />
                )}
                <span className={`flex-1 ${step.is_completed ? 'text-gray-400 line-through' : 'text-gray-700'}`}>
                  {step.description}
                </span>
                <span className="text-xs text-gray-400 font-mono">#{step.step_order}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}