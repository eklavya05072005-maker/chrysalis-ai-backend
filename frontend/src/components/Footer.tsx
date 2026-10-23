'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Instagram, ArrowUpRight, ShieldCheck, Mail, MapPin } from 'lucide-react';

export default function Footer() {
  const pathname = usePathname();
  if (pathname?.startsWith('/event-admin')) return null;

  return (
    <footer className="bg-[#050505] border-t border-white/10 pt-20 pb-12 text-brand-silver">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10 mb-16">
          {/* Brand Col */}
          <div className="lg:col-span-2 space-y-4">
            <Link
              href="/"
              className="inline-block text-2xl font-display font-black tracking-widest text-white uppercase"
            >
              URBEN<span className="text-brand-red font-sans">.</span>ENTT
            </Link>
            <p className="text-xs font-mono uppercase tracking-widest text-brand-red">
              WE CREATE MOMENTS THAT MATTER.
            </p>
            <p className="text-sm text-brand-muted max-w-sm leading-relaxed">
              Pioneering immersive nightlife, electronic music festival staging, and conceptual experiences across Bengaluru and beyond.
            </p>
            <div className="pt-2 flex items-center space-x-3 text-xs text-zinc-400 font-mono">
              <span className="flex items-center space-x-1">
                <MapPin className="w-3.5 h-3.5 text-brand-red" />
                <span>Bengaluru, Karnataka, India</span>
              </span>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-white font-bold">
              EXPERIENCE
            </h4>
            <ul className="space-y-2 text-xs font-mono uppercase tracking-wider text-brand-muted">
              <li>
                <Link href="/events" className="hover:text-brand-red transition-colors">
                  Upcoming Events
                </Link>
              </li>
              <li>
                <Link href="/events/nocturne" className="hover:text-brand-red transition-colors">
                  NOCTURNE 2026
                </Link>
              </li>
              <li>
                <Link href="/past-events" className="hover:text-brand-red transition-colors">
                  Past Productions & Reels
                </Link>
              </li>
              <li>
                <Link href="/services" className="hover:text-brand-red transition-colors">
                  Production Capabilities
                </Link>
              </li>
              <li>
                <Link href="/about" className="hover:text-brand-red transition-colors">
                  Brand Narrative
                </Link>
              </li>
            </ul>
          </div>

          {/* Collaborator Network */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-white font-bold">
              COLLABORATORS
            </h4>
            <ul className="space-y-2 text-xs font-mono uppercase tracking-wider text-brand-muted">
              <li>
                <span className="text-zinc-300">APEX</span>
                <span className="text-[10px] text-zinc-600 block">Pure Chaos</span>
              </li>
              <li>
                <span className="text-zinc-300">BLAH BLA</span>
                <span className="text-[10px] text-zinc-600 block">Energy Unleashed</span>
              </li>
              <li>
                <a
                  href="https://sortmyscene.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-brand-red transition-colors inline-flex items-center space-x-1"
                >
                  <span>SortMyScene</span>
                  <ArrowUpRight className="w-3 h-3 text-brand-red" />
                </a>
                <span className="text-[10px] text-zinc-600 block">Official Ticketing</span>
              </li>
            </ul>
          </div>

          {/* Direct Contact & Admin */}
          <div className="space-y-3">
            <h4 className="text-xs font-mono uppercase tracking-widest text-white font-bold">
              COMMUNICATIONS
            </h4>
            <div className="space-y-2 text-xs text-brand-muted">
              <Link
                href="/contact"
                className="inline-flex items-center space-x-1.5 text-white hover:text-brand-red transition-colors font-mono"
              >
                <Mail className="w-3.5 h-3.5 text-brand-red" />
                <span>Direct Inquiries</span>
              </Link>
              <div className="pt-2">
                <a
                  href="https://instagram.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white text-xs font-mono transition-colors"
                >
                  <Instagram className="w-3.5 h-3.5 text-brand-red" />
                  <span>@urben.entt</span>
                </a>
              </div>

              <div className="pt-4 border-t border-white/5">
                <Link
                  href="/event-admin"
                  className="inline-flex items-center space-x-1.5 text-[11px] font-mono text-zinc-500 hover:text-brand-silver transition-colors"
                >
                  <ShieldCheck className="w-3.5 h-3.5 text-brand-red" />
                  <span>Admin Gateway</span>
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between text-xs text-zinc-500 font-mono gap-4">
          <p>© {new Date().getFullYear()} URBEN.ENTT. All rights reserved.</p>
          <div className="flex items-center space-x-6">
            <span>Bengaluru • India</span>
            <span>CIN: EXPERIENCES-2026</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
