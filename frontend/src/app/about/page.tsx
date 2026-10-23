import React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Sparkles, Eye, Compass, Shield, ArrowRight, MapPin } from 'lucide-react';

export const metadata: Metadata = {
  title: 'About URBEN.ENTT — Our Story & Philosophy',
  description:
    'We bring people together through thoughtfully created events, immersive experiences, and moments worth remembering.',
};

export default function AboutPage() {
  return (
    <div className="pt-28 pb-24 bg-[#080808] min-h-screen text-brand-silver">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Narrative */}
        <div className="max-w-4xl mb-20">
          <div className="inline-flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>ABOUT URBEN.ENTT</span>
          </div>
          <h1 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase leading-[1.08] mb-8">
            WE CREATE MOMENTS THAT MATTER.
          </h1>
          <p className="text-xl sm:text-2xl font-light text-zinc-300 leading-relaxed border-l-2 border-brand-red pl-6 py-2">
            “We bring people together through thoughtfully created events, immersive experiences, and moments worth remembering.”
          </p>
        </div>

        {/* Narrative Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 py-16 border-t border-b border-white/10">
          <div className="lg:col-span-5 space-y-4">
            <h2 className="text-2xl sm:text-3xl font-display font-black text-white uppercase">
              THE VISION & CULTURE
            </h2>
            <p className="text-xs font-mono uppercase text-brand-red tracking-widest">
              BENGALURU • SOUND • SCENOGRAPHY
            </p>
          </div>

          <div className="lg:col-span-7 space-y-6 text-brand-muted text-sm sm:text-base leading-relaxed">
            <p>
              URBEN.ENTT was conceived around a single core conviction: that modern nightlife and electronic music gatherings should transcend ordinary club nights to become complete sensory stories.
            </p>
            <p>
              By fusing architectural lighting, bespoke gothic and minimal scenography, and uncompromising acoustic curation, we build environments where dance music lovers and creative communities truly connect. Every element—from the visual tone of our posters to the interactive mechanics of activations like MISTERY MATCH—is designed to be intentional, energetic, and memorable.
            </p>
            <p>
              We operate across key cultural corridors in Bengaluru, collaborating with premier venues including Mall of Asia and BLAH BLA, alongside ticketing partners such as SortMyScene to ensure transparent, reliable, and premium access for all attendees.
            </p>
          </div>
        </div>

        {/* The 4 Brand Attributes */}
        <div className="py-20">
          <h3 className="text-xs font-mono uppercase tracking-widest text-brand-red mb-8">
            CORE BRAND ATTRIBUTES
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-8 bg-[#111111] border border-white/10">
              <Eye className="w-6 h-6 text-brand-red mb-4" />
              <h4 className="text-lg font-display font-bold text-white uppercase mb-2">
                CINEMATIC
              </h4>
              <p className="text-xs text-brand-muted leading-relaxed">
                Atmospheric visual storytelling with custom stage scenography, lighting cues, and theatrical mood design.
              </p>
            </div>

            <div className="p-8 bg-[#111111] border border-white/10">
              <Compass className="w-6 h-6 text-brand-red mb-4" />
              <h4 className="text-lg font-display font-bold text-white uppercase mb-2">
                CURATED
              </h4>
              <p className="text-xs text-brand-muted leading-relaxed">
                Strict sonic standards that celebrate high-grade techno, minimal, and underground artists rather than generic commercial sets.
              </p>
            </div>

            <div className="p-8 bg-[#111111] border border-white/10">
              <Sparkles className="w-6 h-6 text-brand-red mb-4" />
              <h4 className="text-lg font-display font-bold text-white uppercase mb-2">
                IMMERSIVE
              </h4>
              <p className="text-xs text-brand-muted leading-relaxed">
                Engaging social dimensions—like the signature numbered card matching system—that connect attendees beyond the music.
              </p>
            </div>

            <div className="p-8 bg-[#111111] border border-white/10">
              <Shield className="w-6 h-6 text-brand-red mb-4" />
              <h4 className="text-lg font-display font-bold text-white uppercase mb-2">
                RELIABLE
              </h4>
              <p className="text-xs text-brand-muted leading-relaxed">
                Verified ticketing, transparent age policies, and strict compliance with venue and safety protocols.
              </p>
            </div>
          </div>
        </div>

        {/* Venue Network Grid */}
        <div className="p-8 sm:p-12 bg-[#101010] border border-white/10">
          <div className="max-w-2xl mb-8">
            <span className="text-xs font-mono uppercase tracking-widest text-brand-red block mb-2">
              BENGALURU NETWORK
            </span>
            <h3 className="text-2xl font-display font-black text-white uppercase">
              COLLABORATING VENUES & SPACES
            </h3>
            <p className="text-xs text-brand-muted mt-2">
              Our productions span premier lifestyle destinations and established nightlife stages.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-xs font-mono">
            <div className="p-4 bg-white/5 border border-white/5">
              <MapPin className="w-4 h-4 text-brand-red mb-2" />
              <div className="text-white font-bold text-sm uppercase">MALL OF ASIA</div>
              <div className="text-zinc-500 mt-1">Byatarayanapura, North Bengaluru</div>
              <div className="text-brand-red text-[11px] mt-2">Location of NOCTURNE 2026</div>
            </div>

            <div className="p-4 bg-white/5 border border-white/5">
              <MapPin className="w-4 h-4 text-brand-red mb-2" />
              <div className="text-white font-bold text-sm uppercase">BLAH BLA</div>
              <div className="text-zinc-500 mt-1">Indiranagar, Bengaluru</div>
              <div className="text-brand-red text-[11px] mt-2">NOVA & Intimate Sessions</div>
            </div>

            <div className="p-4 bg-white/5 border border-white/5">
              <MapPin className="w-4 h-4 text-brand-red mb-2" />
              <div className="text-white font-bold text-sm uppercase">GYLT</div>
              <div className="text-zinc-500 mt-1">Hennur, Bengaluru</div>
              <div className="text-brand-red text-[11px] mt-2">Industrial Warehouse Sonics</div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-20 text-center">
          <h3 className="text-2xl sm:text-3xl font-display font-black text-white uppercase mb-4">
            LET’S CREATE SOMETHING UNFORGETTABLE
          </h3>
          <p className="text-brand-muted text-sm max-w-md mx-auto mb-6">
            Get in touch to explore co-productions, brand activations, or bespoke corporate experiences.
          </p>
          <Link
            href="/contact"
            className="inline-flex items-center space-x-2 px-8 py-3.5 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold tracking-widest uppercase transition-all"
          >
            <span>START A CONVERSATION</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
