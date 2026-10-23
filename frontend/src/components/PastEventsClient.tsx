'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import { Play, MapPin, Calendar, Film } from 'lucide-react';
import { UrbenEvent } from '@/types';
import VideoModal from '@/components/VideoModal';

interface PastEventsClientProps {
  initialEvents: UrbenEvent[];
}

export default function PastEventsClient({ initialEvents }: PastEventsClientProps) {
  const [activeVideo, setActiveVideo] = useState<{ src: string; title: string } | null>(null);

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {initialEvents.map((event) => (
          <div
            key={event.id}
            className="group bg-[#111111] border border-white/10 hover:border-brand-red/50 flex flex-col justify-between transition-all duration-300"
          >
            {/* Visual Media Header */}
            <div className="relative aspect-video w-full overflow-hidden bg-black">
              <Image
                src={event.posterUrl}
                alt={event.title}
                fill
                sizes="(max-width: 768px) 100vw, 33vw"
                className="object-cover object-center group-hover:scale-105 transition-transform duration-700 opacity-80 group-hover:opacity-100"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />

              {/* Aftermovie Trigger */}
              {event.promoVideoUrl && (
                <button
                  type="button"
                  onClick={() =>
                    setActiveVideo({
                      src: event.promoVideoUrl!,
                      title: `${event.title} Aftermovie`,
                    })
                  }
                  className="absolute inset-0 flex items-center justify-center group/btn"
                  aria-label={`Play aftermovie for ${event.title}`}
                >
                  <div className="w-14 h-14 rounded-full bg-brand-red/90 group-hover/btn:bg-brand-red-glow text-white flex items-center justify-center shadow-2xl transform group-hover/btn:scale-110 transition-transform">
                    <Play className="w-5 h-5 fill-white ml-0.5" />
                  </div>
                  <span className="absolute bottom-3 left-3 text-[10px] font-mono uppercase tracking-wider text-white bg-black/70 px-2 py-0.5">
                    <Film className="w-3 h-3 inline mr-1 text-brand-red" />
                    PLAY REEL
                  </span>
                </button>
              )}

              <div className="absolute top-3 right-3 text-[10px] font-mono uppercase px-2 py-0.5 bg-black/80 text-zinc-400 border border-white/10">
                ARCHIVED
              </div>
            </div>

            {/* Body */}
            <div className="p-6 flex flex-col flex-grow justify-between space-y-4">
              <div>
                <span className="text-[11px] font-mono text-brand-red tracking-widest uppercase block mb-1">
                  {event.category}
                </span>
                <h3 className="text-xl font-display font-bold text-white uppercase group-hover:text-brand-silver transition-colors">
                  {event.title}
                </h3>
                <p className="text-xs text-brand-muted mt-2 line-clamp-2 leading-relaxed">
                  {event.shortDescription}
                </p>
              </div>

              <div className="pt-4 border-t border-white/5 space-y-1.5 text-xs font-mono text-zinc-400">
                <div className="flex items-center space-x-2">
                  <Calendar className="w-3.5 h-3.5 text-brand-red" />
                  <span>{event.timeDisplay}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <MapPin className="w-3.5 h-3.5 text-brand-red" />
                  <span>{event.venueName}, {event.city}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Video Modal */}
      {activeVideo && (
        <VideoModal
          isOpen={Boolean(activeVideo)}
          onClose={() => setActiveVideo(null)}
          videoSrc={activeVideo.src}
          title={activeVideo.title}
        />
      )}
    </>
  );
}
