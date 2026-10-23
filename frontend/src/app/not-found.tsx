import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Sparkles } from 'lucide-react';

export default function NotFound() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center bg-[#080808] px-4">
      <div className="text-center max-w-md border border-white/10 p-10 bg-[#111111] shadow-2xl">
        <div className="inline-flex p-3 bg-brand-red/10 border border-brand-red/30 rounded-full mb-4 text-brand-red">
          <Sparkles className="w-6 h-6 animate-pulse" />
        </div>
        <div className="text-xs font-mono uppercase text-brand-red tracking-widest mb-2">
          ERROR 404 • SIGNAL LOST
        </div>
        <h1 className="text-4xl font-display font-black text-white uppercase tracking-tight mb-3">
          PAGE NOT FOUND
        </h1>
        <p className="text-xs text-brand-muted leading-relaxed mb-6">
          The experience or document you are seeking does not exist or has been relocated to another dimension.
        </p>
        <Link
          href="/"
          className="inline-flex items-center space-x-2 px-6 py-3 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-mono uppercase tracking-widest transition-all"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Sanctum</span>
        </Link>
      </div>
    </div>
  );
}
