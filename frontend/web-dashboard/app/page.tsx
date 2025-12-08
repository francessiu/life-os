"use client";
import { useState } from 'react';

export default function Home() {
  const [goal, setGoal] = useState('');
  const [steps, setSteps] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  const handleDecompose = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/goals/decompose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: goal }),
      });
      
      // >>> Check for non-OK status (e.g., 404, 500)
      if (!res.ok) {
          const errorData = await res.json();
          throw new Error(`API Error (${res.status}): ${errorData.detail || 'Unknown server error'}`);
      }
      
      const data = await res.json();
      
      // >>> Update state based on the EXPECTED structure
      // Ensure we are getting the 'steps' property (which the backend sends)
      if (data && data.steps) {
        setSteps(data.steps);
      } else {
        throw new Error("Invalid response format from AI agent.");
      }

    } catch (error) {
      console.error("Fetch/Processing Error:", error);
      alert(`Could not process request. Check console for details. (Backend connection issue?)`);
      setSteps([]); // Clear steps on failure to prevent the "Cannot read properties..." error
    }
    setLoading(false);
  };

  return (
    <main className="flex min-h-screen flex-col items-center p-24 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-8">LifeOS MVP</h1>
      
      <div className="w-full max-w-md space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="Enter a new goal (e.g. Learn Python)"
            className="flex-1 p-3 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 outline-none"
          />
          <button
            onClick={handleDecompose}
            disabled={loading}
            className="bg-blue-600 px-6 py-3 rounded hover:bg-blue-700 transition disabled:opacity-50"
          >
            {loading ? 'Thinking...' : 'Plan'}
          </button>
        </div>

        {steps.length > 0 && (
          <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 mt-8">
            <h2 className="text-xl font-semibold mb-4 text-blue-400">AI Suggested Plan:</h2>
            <ul className="space-y-3">
              {steps.map((step, idx) => (
                <li key={idx} className="flex items-center gap-3">
                  <span className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-900 text-xs text-blue-200">
                    {idx + 1}
                  </span>
                  <span>{step}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </main>
  );
}
