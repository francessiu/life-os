import React, { useState, useRef, useEffect } from 'react';
import { pkmApi } from '@/lib/api';
import { Send, Bot, User as UserIcon, Settings2, X } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  mode_used?: string;
}

export default function ChatInterface() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hello. I am your LifeOS Brain. How can I help you today?" }
  ]);
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Manual Overrides
  const [selectedMode, setSelectedMode] = useState('auto');
  const [selectedProvider, setSelectedProvider] = useState<string | null>(null); // null = use mode default
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Auto-scroll to bottom
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    const userMsg = query;
    setQuery('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const { data } = await pkmApi.chat(
        userMsg, 
        selectedMode, 
        selectedProvider || undefined, // Only send if set
        selectedModel || undefined
      );
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.answer,
        mode_used: data.mode_used 
      }]);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: "Error connecting to Agent." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden relative">
      
      {/* Header with Settings Toggle */}
      <div className="bg-gray-50 px-4 py-3 border-b flex justify-between items-center">
        <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-gray-700">Neural Chat</span>
        </div>
        <button onClick={() => setShowSettings(!showSettings)} className="p-1 hover:bg-gray-200 rounded">
            {showSettings ? <X className="w-4 h-4"/> : <Settings2 className="w-4 h-4 text-gray-500"/>}
        </button>
      </div>

      {/* Settings Panel Overlay */}
      {showSettings && (
        <div className="absolute top-14 left-0 right-0 bg-gray-50 border-b p-4 z-10 grid grid-cols-2 gap-4 text-sm animate-in slide-in-from-top-2">
            <div>
                <label className="block text-gray-500 mb-1">Agent Persona</label>
                <select 
                    value={selectedMode} 
                    onChange={(e) => setSelectedMode(e.target.value)}
                    className="w-full p-2 border rounded-lg bg-white"
                >
                    <option value="auto">🤖 Auto-Route (AI Decides)</option>
                    <option value="productivity">⚡ Productivity</option>
                    <option value="academic">🎓 Academic</option>
                    <option value="coder">💻 Coder</option>
                    <option value="analyst">📊 Analyst</option>
                    <option value="creative">🎨 Creative</option>
                    <option value="casual">😊 Casual</option>
                </select>
            </div>
            <div>
                 <label className="block text-gray-500 mb-1">Brain Override (Optional)</label>
                 <select 
                    value={selectedProvider || ''} 
                    onChange={(e) => {
                        const val = e.target.value;
                        setSelectedProvider(val || null);
                        // Reset model when provider changes
                        setSelectedModel(val === 'openai' ? 'gpt-4o' : val === 'google' ? 'gemini-1.5-pro' : val === 'anthropic' ? 'claude-3-opus-20240229' : null);
                    }}
                    className="w-full p-2 border rounded-lg bg-white"
                >
                    <option value="">Default (Use Persona)</option>
                    <option value="openai">OpenAI (GPT-4o)</option>
                    <option value="anthropic">Anthropic (Claude 3.5)</option>
                    <option value="google">Google (Gemini 1.5)</option>
                </select>
            </div>
        </div>
      )}

      {/* Chat Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
             <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-black text-white' : 'bg-purple-100 text-purple-700'}`}>
              {msg.role === 'user' ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>
            <div className={`max-w-[80%] space-y-1`}>
                <div className={`p-3 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user' 
                    ? 'bg-black text-white rounded-tr-none' 
                    : 'bg-gray-100 text-gray-800 rounded-tl-none'
                }`}>
                    {msg.content}
                </div>
                {msg.role === 'assistant' && msg.mode_used && (
                    <div className="text-[10px] text-gray-400 pl-2">
                        via {msg.mode_used}
                    </div>
                )}
            </div>
          </div>
        ))}
        {loading && (
             <div className="flex gap-3 items-center text-xs text-gray-400 italic pl-12">
                Thinking...
             </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSend} className="p-4 border-t bg-white flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 px-4 py-2 border rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <button disabled={loading || !query} className="w-10 h-10 bg-black text-white rounded-full flex items-center justify-center hover:bg-gray-800 disabled:opacity-50">
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
}