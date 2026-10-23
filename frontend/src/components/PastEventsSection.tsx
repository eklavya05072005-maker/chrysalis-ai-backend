'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Play, Calendar, MapPin, ArrowRight, Eye, Film } from 'lucide-react';
import VideoModal from '@/components/VideoModal';

interface PastEventItem {
  id: string;
  title: string;
  category: string;
  date: string;
  venue: string;
  city: string;
  headline: string;
  videoSrc?: string;
  imageSrc: string;
  collaborators: string[];
}

const PAST_EVENTS: PastEventItem[] = [
  {
    id: 'past-1',
    title: 'DJ T3RAN: LIVE REEL',
    category: 'Nightlife & Techno',
    date: 'August 2026',
    venue: 'GYLT',
    city: 'Bengaluru',
    headline: 'High-energy industrial acid set recorded live with underground club atmosphere.',
    videoSrc: '/assets/videos/past-event-reel.mov',
    imageSrc: '/assets/events/nocturne/dj-katz-poster.png',
    collaborators: ['APEX', 'GYLT'],
  },
  {
    id: 'past-2',
    title: 'NOVA — BREAK THE FLOOR',
    category: 'Exclusive Parties',
    date: 'September 2026',
    venue: 'BLAH BLA',
    city: 'Bengaluru',
    headline: 'VATSAA commanding the floor with Minimal, Disco, and Hip-Hop cadences.',
    videoSrc: '/assets/videos/past-event-reel.mov',
    imageSrc: '/assets/events/nocturne/main-poster.png',
    collaborators: ['BLAH BLA', 'SortMyScene'],
  },
  {
    id: 'past-3',
    title: 'BENGALURU SCENE SHOWCASE',
    category: 'Scene Archive',
    date: 'Fall 2026',
    venue: 'Multi-Venue Circuit',
    city: 'Bengaluru',
    headline: 'SortMyScene curated nightlife circuit across Bengaluru premier underground clubs.',
    imageSrc: '/assets/reference/bengaluru-schedule.png',
    collaborators: ['SortMyScene', 'URBEN.ENTT'],
  },
];

export default function PastEventsSection() {
  const [activeVideo, setActiveVideo] = useState<{ src: string; title: string } | null>(null);

  return (
    <section id="past-events-section" className="py-24 sm:py-32 bg-[#080808] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div>
            <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-3">
              ARCHIVE & AFTERMOVIES
            </div>
            <h2 className="text-3xl sm:text-5xl font-display font-black text-white tracking-tight uppercase">
              SELECTED PRODUCTIONS
            </h2>
          </div>
          <Link
            href="/past-events"
            className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-silver hover:text-brand-red transition-colors"
          >
            <span>VIEW FULL ARCHIVE</span>
            <ArrowRight className="w-4 h-4 text-brand-red" />
          </Link>
        </div>

        {/* Grid of Past Productions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {PAST_EVENTS.map((item) => (
            <div
              key={item.id}
              className="group bg-[#111111] border border-white/10 overflow-hidden flex flex-col justify-between hover:border-brand-red/50 transition-all duration-300"
            >
              <div className="relative aspect-video w-full overflow-hidden bg-black">
                <Image
                  src={item.imageSrc}
                  alt={item.title}
                  fill
                  sizes="(max-width: 768px) 100vw, 33vw"
                  className="object-cover object-center group-hover:scale-105 transition-transform duration-500 opacity-80 group-hover:opacity-100"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent" />

                {/* Video Play Button Overlay if videoSrc exists */}
                {item.videoSrc ? (
                  <button
                    type="button"
                    onClick={() => setActiveVideo({ src: item.videoSrc!, title: item.title })}
                    className="absolute inset-0 flex items-center justify-center group/btn"
                    aria-label={`Play aftermovie for ${item.title}`}
                  >
                    <div className="w-14 h-14 rounded-full bg-brand-red/90 group-hover/btn:bg-brand-red-glow text-white flex items-center justify-center shadow-xl transform group-hover/btn:scale-110 transition-all">
                      <Play className="w-5 h-5 fill-white ml-0.5" />
                    </div>
                    <span className="absolute bottom-3 left-3 text-[10px] font-mono uppercase tracking-wider text-white bg-black/60 px-2 py-0.5">
                      <Film className="w-3 h-3 inline mr-1 text-brand-red" />
                      CLICK TO PLAY FILM
                    </span>
                  </button>
                ) : (
                  <div className="absolute bottom-3 left-3 text-[10px] font-mono uppercase tracking-wider text-zinc-300 bg-black/60 px-2 py-0.5 flex items-center space-x-1">
                    <Eye className="w-3 h-3 text-brand-red" />
                    <span>SCHEDULE REFERENCE</span>
                  </div>
                )}
              </div>

              {/* Card Meta */}
              <div className="p-6 flex flex-col flex-grow justify-between space-y-4">
                <div>
                  <div className="flex items-center justify-between text-[11px] font-mono uppercase text-brand-red mb-2">
                    <span>{item.category}</span>
                    <span className="text-zinc-500">{item.date}</span>
                  </div>

                  <h3 className="text-xl font-display font-bold text-white uppercase group-hover:text-brand-silver transition-colors">
                    {item.title}
                  </h3>
                  <p className="text-xs text-brand-muted mt-2 leading-relaxed">
                    {item.headline}
                  </p>
                </div>

                <div className="pt-4 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-zinc-400">
                  <span className="flex items-center space-x-1">
                    <MapPin className="w-3 h-3 text-brand-red" />
                    <span>{item.venue}, {item.city}</span>
                  </span>
                  <div className="flex gap-1">
                    {item.collaborators.map((c) => (
                      <span key={c} className="text-[10px] bg-white/5 px-1.5 py-0.5 text-zinc-400">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Video Lightbox Modal */}
      {activeVideo && (
        <VideoModal
          isOpen={Boolean(activeVideo)}
          onClose={() => setActiveVideo(null)}
          videoSrc={activeVideo.src}
          title={activeVideo.title}
        />
      )}
    </section>
  );
}
