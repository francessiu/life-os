import React, { useState } from 'react';
import { Loader2, Globe, Lock, Users, Plus } from 'lucide-react';
import axios from 'axios'; // Assume configured axios instance

export default function SourceManager() {
  const [url, setUrl] = useState('');
  const [isGlobal, setIsGlobal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  const handleAddSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      await axios.post('/api/v1/watcher/watch', {
        url: url,
        is_global: isGlobal,
        frequency_hours: 24
      });
      setMessage({ type: 'success', text: 'Source added! Crawling started in background.' });
      setUrl('');
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to add source.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <Globe className="w-5 h-5 text-purple-600" />
        Knowledge Sources
      </h3>

      <form onSubmit={handleAddSource} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target URL</label>
          <input
            type="url"
            required
            placeholder="https://example.com/docs"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-purple-500 outline-none"
          />
        </div>

        <div className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg border border-gray-100">
          <button
            type="button"
            onClick={() => setIsGlobal(!isGlobal)}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              isGlobal ? 'bg-purple-600' : 'bg-gray-200'
            }`}
          >
            <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
              isGlobal ? 'translate-x-6' : 'translate-x-1'
            }`} />
          </button>
          <div className="flex items-center gap-2 text-sm text-gray-700">
            {isGlobal ? <Users className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
            <span>{isGlobal ? 'Shared Database (Global)' : 'Private Knowledge (Only Me)'}</span>
          </div>
        </div>

        {message && (
          <div className={`text-sm p-2 rounded ${message.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            {message.text}
          </div>
        )}

        <button
          disabled={loading || !url}
          className="w-full bg-black text-white py-2.5 rounded-lg font-medium hover:bg-gray-800 disabled:opacity-50 flex justify-center items-center gap-2"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
          Start Watching
        </button>
      </form>
    </div>
  );
}