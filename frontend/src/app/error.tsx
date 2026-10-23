'use client';

import React, { useEffect } from 'react';
import { AlertCircle, RotateCcw } from 'lucide-react';

export default function ErrorBoundary({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Application boundary error:', error);
  }, [error]);

  return (
    <div className="min-h-[80vh] flex items-center justify-center bg-[#080808] px-4">
      <div className="text-center max-w-md border border-brand-red/30 p-10 bg-[#111111] shadow-2xl">
        <div className="inline-flex p-3 bg-brand-red/10 border border-brand-red/30 rounded-full mb-4 text-brand-red">
          <AlertCircle className="w-6 h-6 animate-pulse" />
        </div>
        <div className="text-xs font-mono uppercase text-brand-red tracking-widest mb-2">
          SYSTEM NOTICE
        </div>
        <h1 className="text-2xl font-display font-black text-white uppercase tracking-tight mb-3">
          ANOMALY DETECTED
        </h1>
        <p className="text-xs text-brand-muted leading-relaxed mb-6">
          A client-side state irregularity occurred during execution. You can attempt to reinitialize the session.
        </p>
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center space-x-2 px-6 py-3 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-mono uppercase tracking-widest transition-all"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reinitialize Experience</span>
        </button>
      </div>
    </div>
  );
}
