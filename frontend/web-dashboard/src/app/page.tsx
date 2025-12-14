'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
      <h1 className="text-4xl font-bold mb-4">Welcome to LifeOS</h1>
      <p className="text-gray-600 mb-8">Your personal AI-powered Second Brain.</p>

      <div className="flex gap-4">
        <Link 
          href="/dashboard" 
          className="px-6 py-3 bg-black text-white rounded-lg hover:bg-gray-800 transition"
        >
          Enter Dashboard
        </Link>
        {/* Add a Login Link if you have a separate login page */}
      </div>
    </div>
  );
}
