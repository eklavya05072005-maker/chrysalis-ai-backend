'use client';

import React, { useState, useEffect } from 'react';
import AdminLogin from '@/components/admin/AdminLogin';
import AdminDashboard from '@/components/admin/AdminDashboard';
import { AdminUser } from '@/types';
import { Loader2 } from 'lucide-react';

export default function EventAdminPage() {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);

  useEffect(() => {
    // Check if existing session cookie is valid
    const checkSession = async () => {
      try {
        const res = await fetch('/api/auth/me');
        if (res.ok) {
          const data = await res.json();
          if (data.authenticated && data.user) {
            setUser(data.user);
          }
        }
      } catch (err) {
        console.error('Session check failed:', err);
      } finally {
        setIsCheckingAuth(false);
      }
    };

    checkSession();
  }, []);

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } finally {
      setUser(null);
    }
  };

  if (isCheckingAuth) {
    return (
      <div className="min-h-screen bg-[#080808] flex items-center justify-center">
        <div className="flex items-center space-x-3 text-zinc-400 font-mono text-xs">
          <Loader2 className="w-5 h-5 animate-spin text-brand-red" />
          <span>VERIFYING CREDENTIALS...</span>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AdminLogin onSuccess={(loggedInUser) => setUser(loggedInUser)} />;
  }

  return <AdminDashboard initialUser={user} onLogout={handleLogout} />;
}
