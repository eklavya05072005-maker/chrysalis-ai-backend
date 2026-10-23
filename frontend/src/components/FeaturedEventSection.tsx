'use client';

import React from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Calendar, Clock, MapPin, Ticket, Flame, ArrowRight, ShieldAlert, Sparkles } from 'lucide-react';
import { UrbenEvent } from '@/types';

interface FeaturedEventSectionProps {
  event: UrbenEvent;
}

export default function FeaturedEventSection({ event }: FeaturedEventSectionProps) {
  return (
    <section
      id="featured-event-section"
      className="relative py-24 sm:py-32 bg-[#080808] border-t border-b border-white/10 overflow-hidden"
    >
      {/* Background ambient lighting */}
      <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-[500px] h-[500px] bg-brand-red/15 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[400px] h-[400px] bg-brand-red-dark/20 rounded-full blur-[120px] pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 sm:mb-16 gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest mb-3">
              <Flame className="w-4 h-4 fill-brand-red animate-pulse" />
              <span>HEADLINE EXPERIENCE • OCTOBER 2026</span>
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-black text-white tracking-tight uppercase">
              FEATURED PRODUCTION
            </h2>
          </div>
          <p className="text-brand-muted text-sm sm:text-base max-w-md">
            Our marquee underground celebration blending dark atmospheric scenography, world-class electronic sound, and interactive social immersion.
          </p>
        </div>

        {/* Featured Card Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center bg-[#0d0d0d] border border-white/10 p-6 sm:p-10 lg:p-12 relative group hover:border-brand-red/40 transition-colors duration-500">
          {/* Main Visual Poster Column */}
          <div className="lg:col-span-5 relative">
            <div className="relative aspect-[3/4] w-full overflow-hidden border border-white/15 shadow-2xl red-edge-glow">
              <Image
                src={event.posterUrl}
                alt={`${event.title} - ${event.tagline}`}
                fill
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 45vw, 40vw"
                className="object-cover object-center group-hover:scale-105 transition-transform duration-700"
                priority
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent" />
              
              {/* Badge Overlay */}
              <div className="absolute top-4 left-4 px-3 py-1 bg-brand-red text-white text-[11px] font-mono uppercase tracking-wider font-bold">
                CONFIRMED DATE
              </div>
              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between text-xs text-white font-mono bg-black/70 backdrop-blur-md px-3 py-2 border border-white/10">
                <span>{event.ticketingPlatform} VERIFIED</span>
                <span className="text-brand-red">{event.ticketStatus}</span>
              </div>
            </div>
          </div>

          {/* Details & Editorial Column */}
          <div className="lg:col-span-7 flex flex-col justify-between space-y-6">
            <div>
              <div className="flex items-center space-x-3 text-xs font-mono text-brand-red tracking-widest uppercase mb-2">
                <span>{event.category}</span>
                <span>•</span>
                <span>BENGALURU</span>
              </div>

              <h3 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase leading-none mb-2">
                {event.title}
              </h3>
              <p className="text-lg sm:text-xl font-display font-medium text-brand-red tracking-wide uppercase mb-6">
                {event.tagline}
              </p>

              <p className="text-brand-muted text-sm sm:text-base leading-relaxed mb-6">
                {event.shortDescription}
              </p>

              {/* Mystery Match Highlight Card */}
              {event.experienceNotes && (
                <div className="p-4 sm:p-5 border-l-2 border-brand-red bg-white/[0.03] mb-6">
                  <div className="flex items-center space-x-2 text-xs font-mono text-white uppercase font-bold mb-1">
                    <Sparkles className="w-3.5 h-3.5 text-brand-red" />
                    <span>MISTERY MATCH ACTIVITY INCLUDED</span>
                  </div>
                  <p className="text-xs sm:text-sm text-zinc-300">
                    {event.experienceNotes}
                  </p>
                </div>
              )}

              {/* Event Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-4 border-t border-b border-white/10 text-xs font-mono">
                <div className="flex items-center space-x-3 text-zinc-300">
                  <Calendar className="w-4 h-4 text-brand-red flex-shrink-0" />
                  <div>
                    <div className="text-zinc-500 uppercase">DATE</div>
                    <div className="text-white font-semibold">Saturday, 31 October 2026</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-zinc-300">
                  <Clock className="w-4 h-4 text-brand-red flex-shrink-0" />
                  <div>
                    <div className="text-zinc-500 uppercase">TIMINGS</div>
                    <div className="text-white font-semibold">{event.timeDisplay}</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-zinc-300">
                  <MapPin className="w-4 h-4 text-brand-red flex-shrink-0" />
                  <div>
                    <div className="text-zinc-500 uppercase">VENUE</div>
                    <div className="text-white font-semibold">{event.venueName}, Bengaluru</div>
                  </div>
                </div>

                <div className="flex items-center space-x-3 text-zinc-300">
                  <ShieldAlert className="w-4 h-4 text-brand-red flex-shrink-0" />
                  <div>
                    <div className="text-zinc-500 uppercase">ACCESS</div>
                    <div className="text-white font-semibold">{event.agePolicy}</div>
                  </div>
                </div>
              </div>

              {/* Collaborators Strip */}
              {event.collaborators && event.collaborators.length > 0 && (
                <div className="mt-4 pt-2">
                  <div className="text-[11px] font-mono text-zinc-500 uppercase tracking-widest mb-2">
                    COLLABORATORS & PARTNERS:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {event.collaborators.map((c) => (
                      <span
                        key={c.collaborator.id}
                        className="px-2.5 py-1 text-xs font-mono uppercase bg-white/5 border border-white/10 text-zinc-300"
                      >
                        {c.collaborator.name}{' '}
                        <span className="text-zinc-500 text-[10px]">
                          ({c.collaborator.tagline || c.contributionNote})
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row items-center gap-4 pt-4">
              <a
                href={event.ticketUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-3.5 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold tracking-widest uppercase transition-all duration-200 shadow-lg shadow-brand-red/20"
              >
                <Ticket className="w-4 h-4" />
                <span>GET TICKETS ON SORTMYSCENE</span>
              </a>

              <Link
                href={`/events/${event.slug}`}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-3.5 bg-white/5 hover:bg-white/10 text-white border border-white/15 text-xs font-bold tracking-widest uppercase transition-colors"
              >
                <span>FULL EVENT SPECS</span>
                <ArrowRight className="w-4 h-4 text-brand-red" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
