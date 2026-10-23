'use client';

import React, { useState } from 'react';
import { Lock, Mail, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { AdminUser } from '@/types';

interface AdminLoginProps {
  onSuccess: (user: AdminUser) => void;
}

export default function AdminLogin({ onSuccess }: AdminLoginProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Authentication failed');
      } else {
        onSuccess(data.user);
      }
    } catch {
      setError('Connection error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fillCredentials = (userType: 'owner' | 'admin' | 'dev') => {
    if (userType === 'owner') {
      setEmail('owner@urben.entt');
      setPassword('UrbenOwner2026!');
    } else if (userType === 'admin') {
      setEmail('admin@urben.entt');
      setPassword('UrbenAdmin2026!');
    } else {
      setEmail('dev@urben.entt');
      setPassword('UrbenDev2026!');
    }
    setError(null);
  };

  return (
    <div className="min-h-screen bg-[#080808] flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-[#111111] border border-white/10 p-8 shadow-2xl relative">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 bg-brand-red/10 border border-brand-red/30 rounded-full mb-3 text-brand-red">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-display font-black text-white uppercase tracking-tight">
            URBEN<span className="text-brand-red">.</span>ENTT
          </h1>
          <p className="text-xs font-mono uppercase tracking-widest text-zinc-400 mt-1">
            PROTECTED OPERATIONS GATEWAY
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-red-950/70 border border-brand-red text-xs text-white flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-brand-red flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase text-zinc-400 mb-1.5">
              Authorized Email
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@urben.entt"
                className="w-full pl-9 pr-4 py-2.5 bg-[#080808] border border-white/15 focus:border-brand-red text-white text-xs font-mono focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-mono uppercase text-zinc-400 mb-1.5">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-zinc-500 absolute left-3 top-3.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-4 py-2.5 bg-[#080808] border border-white/15 focus:border-brand-red text-white text-xs font-mono focus:outline-none"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-3 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold font-mono uppercase tracking-widest transition-all flex items-center justify-center space-x-2 disabled:opacity-60"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>AUTHENTICATING...</span>
              </>
            ) : (
              <span>SIGN IN TO DASHBOARD</span>
            )}
          </button>
        </form>

        {/* Demo Fast-Login Assist */}
        <div className="mt-8 pt-6 border-t border-white/10">
          <p className="text-[11px] font-mono text-zinc-500 uppercase tracking-wider mb-2 text-center">
            Role Testing Quick-Switch:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => fillCredentials('owner')}
              className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 text-[10px] font-mono text-zinc-300 uppercase hover:border-brand-red transition-colors text-left"
            >
              <span className="font-bold text-white block">OWNER ROLE</span>
              <span className="text-[9px] text-zinc-500 block truncate">Full Publishing Power</span>
            </button>

            <button
              type="button"
              onClick={() => fillCredentials('admin')}
              className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 text-[10px] font-mono text-zinc-300 uppercase hover:border-brand-red transition-colors text-left"
            >
              <span className="font-bold text-white block">EVENT ADMIN ROLE</span>
              <span className="text-[9px] text-zinc-500 block truncate">Draft & Review Only</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
