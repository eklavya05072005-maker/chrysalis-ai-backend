import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Disc3, Sparkles, Building2, PartyPopper, CheckCircle2, ArrowRight } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Production Services & Capabilities',
  description:
    'End-to-end event production, sound reinforcement, stage scenography, and immersive concept engineering by URBEN.ENTT.',
};

export default function ServicesPage() {
  return (
    <div className="pt-28 pb-24 bg-[#080808] min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="max-w-3xl mb-16">
          <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-3">
            CAPABILITIES & EXPERTISE
          </div>
          <h1 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase mb-4">
            WHAT WE ENGINEER
          </h1>
          <p className="text-brand-muted text-sm sm:text-base leading-relaxed">
            URBEN.ENTT pairs technical audio-visual precision with bold artistic direction to deliver turnkey events, festivals, and unforgettable nightlife gatherings.
          </p>
        </div>

        {/* Detailed Services Breakdown */}
        <div className="space-y-16">
          {/* 1. Festivals & Concerts */}
          <div className="p-8 sm:p-12 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-5 space-y-4">
                <div className="p-3 bg-white/5 border border-white/10 w-fit">
                  <Disc3 className="w-8 h-8 text-brand-red" />
                </div>
                <h2 className="text-3xl font-display font-black text-white uppercase">
                  FESTIVALS & CONCERTS
                </h2>
                <p className="text-xs font-mono text-brand-red uppercase tracking-wider">
                  Large-scale stages, sound reinforcement & artist routing
                </p>
                <p className="text-sm text-brand-muted leading-relaxed">
                  Turnkey festival curation, stage scenography, acoustic modeling, artist hospitality, and crowd logistics engineered for monumental open-air and arena experiences.
                </p>
                <div className="pt-2">
                  <Link
                    href="/contact?type=festival"
                    className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-white bg-brand-red hover:bg-brand-red-glow px-4 py-2.5 transition-colors"
                  >
                    <span>Enquire for Festivals</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              <div className="lg:col-span-7 bg-[#0a0a0a] border border-white/5 p-6 sm:p-8 space-y-4">
                <h3 className="text-xs font-mono uppercase text-zinc-400 tracking-wider">
                  DELIVERY SCOPE:
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-zinc-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Point source & line-array acoustic tuning</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Laser mapping & kinetic lighting rigs</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Artist hospitality & backline coordination</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>RFID & barcode access control systems</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 2. Music & Nightlife */}
          <div className="p-8 sm:p-12 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-5 space-y-4">
                <div className="p-3 bg-white/5 border border-white/10 w-fit">
                  <Sparkles className="w-8 h-8 text-brand-red" />
                </div>
                <h2 className="text-3xl font-display font-black text-white uppercase">
                  MUSIC & NIGHTLIFE
                </h2>
                <p className="text-xs font-mono text-brand-red uppercase tracking-wider">
                  Underground club takeovers & atmospheric ceremonies
                </p>
                <p className="text-sm text-brand-muted leading-relaxed">
                  Curating electronic music sanctuaries in premier venues and hidden spaces across Bengaluru. From boiler-room style intimacy to high-BPM warehouse raves.
                </p>
                <div className="pt-2">
                  <Link
                    href="/contact?type=booking"
                    className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-white bg-brand-red hover:bg-brand-red-glow px-4 py-2.5 transition-colors"
                  >
                    <span>Enquire for Nightlife</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              <div className="lg:col-span-7 bg-[#0a0a0a] border border-white/5 p-6 sm:p-8 space-y-4">
                <h3 className="text-xs font-mono uppercase text-zinc-400 tracking-wider">
                  DELIVERY SCOPE:
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-zinc-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Curated techno, house, and minimal selector lineups</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Custom gothic & industrial scenography</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>SortMyScene priority ticketing integration</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Dedicated VIP guestlist management</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 3. Corporate Events */}
          <div className="p-8 sm:p-12 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-5 space-y-4">
                <div className="p-3 bg-white/5 border border-white/10 w-fit">
                  <Building2 className="w-8 h-8 text-brand-red" />
                </div>
                <h2 className="text-3xl font-display font-black text-white uppercase">
                  CORPORATE EVENTS
                </h2>
                <p className="text-xs font-mono text-brand-red uppercase tracking-wider">
                  Brand summits, award galas & visionary product reveals
                </p>
                <p className="text-sm text-brand-muted leading-relaxed">
                  Transforming corporate gatherings into memorable sensory productions. High-end visual storytelling, seamless stage management, and executive hospitality.
                </p>
                <div className="pt-2">
                  <Link
                    href="/contact?type=corporate"
                    className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-white bg-brand-red hover:bg-brand-red-glow px-4 py-2.5 transition-colors"
                  >
                    <span>Enquire for Corporate</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              <div className="lg:col-span-7 bg-[#0a0a0a] border border-white/5 p-6 sm:p-8 space-y-4">
                <h3 className="text-xs font-mono uppercase text-zinc-400 tracking-wider">
                  DELIVERY SCOPE:
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-zinc-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Ultra-wide LED stage displays & show running</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Brand reveal cueing & pyrotechnics / CO2</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Executive attendee concierge & security</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Live broadcast & multi-camera recording</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 4. Experiences & Parties */}
          <div className="p-8 sm:p-12 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
              <div className="lg:col-span-5 space-y-4">
                <div className="p-3 bg-white/5 border border-white/10 w-fit">
                  <PartyPopper className="w-8 h-8 text-brand-red" />
                </div>
                <h2 className="text-3xl font-display font-black text-white uppercase">
                  EXPERIENCES & PARTIES
                </h2>
                <p className="text-xs font-mono text-brand-red uppercase tracking-wider">
                  Themed immersive environments & gamified social matchmaking
                </p>
                <p className="text-sm text-brand-muted leading-relaxed">
                  Bespoke social gatherings driven by interactive mechanics—such as the proprietary MISTERY MATCH concept—combining storytelling, theatrical design, and private soundscapes.
                </p>
                <div className="pt-2">
                  <Link
                    href="/contact?type=private_event"
                    className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-wider text-white bg-brand-red hover:bg-brand-red-glow px-4 py-2.5 transition-colors"
                  >
                    <span>Enquire for Themed Experiences</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              <div className="lg:col-span-7 bg-[#0a0a0a] border border-white/5 p-6 sm:p-8 space-y-4">
                <h3 className="text-xs font-mono uppercase text-zinc-400 tracking-wider">
                  DELIVERY SCOPE:
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-zinc-300">
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Custom game mechanics (e.g. MISTERY MATCH numbered cards)</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Themed costume & dress code curation</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Private mixology & craft cocktail bars</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-brand-red flex-shrink-0" />
                    <span>Exclusive venue takeovers across Bengaluru</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
