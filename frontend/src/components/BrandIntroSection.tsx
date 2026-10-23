'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowRight, Sparkles, Compass, Eye, Shield } from 'lucide-react';

export default function BrandIntroSection() {
  return (
    <section id="brand-intro" className="py-24 sm:py-32 bg-[#090909] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          {/* Main Statement */}
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest">
              <Sparkles className="w-3.5 h-3.5" />
              <span>THE URBEN PHILOSOPHY</span>
            </div>

            <h2 className="text-3xl sm:text-5xl font-display font-black text-white tracking-tight uppercase leading-[1.1]">
              WE BRING PEOPLE TOGETHER THROUGH{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-silver via-zinc-300 to-zinc-500">
                THOUGHTFULLY CREATED EVENTS
              </span>
              , IMMERSIVE EXPERIENCES, AND MOMENTS WORTH REMEMBERING.
            </h2>

            <p className="text-brand-muted text-base sm:text-lg leading-relaxed">
              URBEN.ENTT is an event management and cultural experience collective rooted in Bengaluru. We bridge the underground electronic scene with cinematic stage design, curated artist lineups, and interactive social environments.
            </p>

            <div className="pt-2">
              <Link
                href="/about"
                className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-white hover:text-brand-red transition-colors group"
              >
                <span>EXPLORE OUR STORY & PILLARS</span>
                <ArrowRight className="w-4 h-4 text-brand-red group-hover:translate-x-1 transition-transform" />
              </Link>
            </div>
          </div>

          {/* Core Pillars */}
          <div className="lg:col-span-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
            <div className="p-6 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
              <div className="flex items-center space-x-3 text-brand-red mb-2">
                <Eye className="w-5 h-5" />
                <h3 className="text-sm font-display uppercase tracking-wider text-white font-bold">
                  CINEMATIC SCENOGRAPHY
                </h3>
              </div>
              <p className="text-xs text-brand-muted leading-relaxed">
                Atmospheric lighting, laser arrays, and custom thematic architecture that transform conventional venues into other worlds.
              </p>
            </div>

            <div className="p-6 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
              <div className="flex items-center space-x-3 text-brand-red mb-2">
                <Compass className="w-5 h-5" />
                <h3 className="text-sm font-display uppercase tracking-wider text-white font-bold">
                  CURATED SONIC CULTURE
                </h3>
              </div>
              <p className="text-xs text-brand-muted leading-relaxed">
                From hypnotic techno to deep minimal and house cadences, we platform uncompromising selectors and high-energy performers.
              </p>
            </div>

            <div className="p-6 bg-[#111111] border border-white/10 hover:border-brand-red/40 transition-colors">
              <div className="flex items-center space-x-3 text-brand-red mb-2">
                <Shield className="w-5 h-5" />
                <h3 className="text-sm font-display uppercase tracking-wider text-white font-bold">
                  EXPERIENTIAL SAFETY & PRECISION
                </h3>
              </div>
              <p className="text-xs text-brand-muted leading-relaxed">
                Flawless venue logistics, age verification, verified ticketing with SortMyScene, and dedicated crowd care.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
