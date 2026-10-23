'use client';

import React, { useRef, useState, useEffect } from 'react';
import Link from 'next/link';
import { Play, Pause, Volume2, VolumeX, ArrowDown, Sparkles, Film, Calendar, MapPin } from 'lucide-react';
import { UrbenEvent } from '@/types';

interface HeroVideoProps {
  featuredEvent?: UrbenEvent | null;
  onOpenFilmModal?: () => void;
}

export default function HeroVideo({ featuredEvent, onOpenFilmModal }: HeroVideoProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(true);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Attempt autoplay muted
    const video = videoRef.current;
    if (video) {
      video.muted = true;
      const playPromise = video.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => setIsPlaying(true))
          .catch(() => {
            // Browser autoplay policy prevented playback
            setIsPlaying(false);
          });
      }
    }
  }, []);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const toggleSound = () => {
    const video = videoRef.current;
    if (!video) return;
    video.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const scrollToContent = () => {
    const nextSection = document.getElementById('featured-event-section') || document.getElementById('brand-intro');
    if (nextSection) {
      nextSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section
      id="hero-section"
      className="relative w-full h-[100svh] min-h-[640px] flex items-center justify-center overflow-hidden bg-black select-none"
      aria-label="URBEN.ENTT Experience Hero"
    >
      {/* Background Video / Fallback Poster */}
      <div className="absolute inset-0 w-full h-full z-0 overflow-hidden">
        {!hasError ? (
          <video
            ref={videoRef}
            src="/assets/videos/hero-promo.mov"
            poster="/assets/events/nocturne/main-poster.png"
            autoPlay
            loop
            muted
            playsInline
            preload="metadata"
            onLoadedData={() => setVideoLoaded(true)}
            onError={() => setHasError(true)}
            className="w-full h-full object-cover object-center scale-[1.03] transition-opacity duration-1000"
            style={{ opacity: videoLoaded ? 1 : 0.8 }}
          />
        ) : (
          <div
            className="w-full h-full bg-cover bg-center"
            style={{ backgroundImage: `url('/assets/events/nocturne/main-poster.png')` }}
          />
        )}

        {/* Cinematic Gradient & Vignette Overlays */}
        <div className="absolute inset-0 hero-gradient-overlay" />
        <div className="absolute inset-0 cinematic-vignette opacity-80" />
        <div className="absolute inset-0 bg-black/35" />
      </div>

      {/* Hero Foreground Content */}
      <div className="relative z-10 max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center flex flex-col items-center justify-center h-full pt-16 pb-20">
        {/* Micro Label */}
        <div className="inline-flex items-center space-x-2 px-3 py-1.5 mb-6 border border-white/15 bg-black/40 backdrop-blur-md rounded-full text-xs font-mono tracking-widest text-brand-silver uppercase animate-fade-in">
          <Sparkles className="w-3.5 h-3.5 text-brand-red animate-pulse" />
          <span>EVENTS • CULTURE • EXPERIENCES</span>
        </div>

        {/* Master Tagline */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-black font-display tracking-tight text-white uppercase leading-[1.05] max-w-5xl animate-reveal">
          WE CREATE <br className="hidden sm:inline" />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-white via-zinc-100 to-zinc-400">
            MOMENTS THAT{' '}
          </span>
          <span className="relative inline-block text-white">
            MATTER
            <span className="text-brand-red font-sans">.</span>
            <span className="absolute -bottom-1 left-0 right-0 h-[3px] bg-gradient-to-r from-brand-red via-brand-red-glow to-transparent" />
          </span>
        </h1>

        {/* Dynamic Featured Event Preview Banner (Directly over cinematic background) */}
        {featuredEvent && (
          <div className="mt-8 max-w-2xl w-full p-4 sm:p-5 border border-white/10 bg-black/50 backdrop-blur-xl rounded-none text-left transition-all hover:border-brand-red/50 hover:bg-black/70 group">
            <div className="flex items-center justify-between text-xs font-mono uppercase text-brand-red mb-1.5">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-brand-red animate-ping" />
                <span className="font-bold tracking-wider">UPCOMING CONFIRMED EXPERIENCE</span>
              </span>
              <span className="text-zinc-400 font-sans tracking-widest">{featuredEvent.category}</span>
            </div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h2 className="text-xl sm:text-2xl font-display font-black text-white tracking-wide uppercase group-hover:text-brand-silver transition-colors">
                  {featuredEvent.title}
                </h2>
                <div className="flex flex-wrap items-center gap-y-1 gap-x-4 mt-1 text-xs text-brand-muted">
                  <span className="flex items-center space-x-1">
                    <Calendar className="w-3.5 h-3.5 text-brand-red" />
                    <span>31 October 2026 • {featuredEvent.timeDisplay}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-brand-red" />
                    <span>{featuredEvent.venueName}, {featuredEvent.city}</span>
                  </span>
                </div>
              </div>
              <Link
                href={`/events/${featuredEvent.slug}`}
                className="self-start sm:self-center px-4 py-2 text-xs font-bold uppercase tracking-wider text-white bg-white/10 hover:bg-brand-red border border-white/20 hover:border-brand-red transition-all duration-200"
              >
                View Event
              </Link>
            </div>
          </div>
        )}

        {/* CTA Buttons */}
        <div className="mt-8 flex flex-col sm:flex-row items-center gap-4 sm:gap-5 w-full sm:w-auto">
          <Link
            href="/events"
            id="hero-explore-cta"
            className="w-full sm:w-auto px-8 py-4 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold tracking-widest uppercase transition-all duration-200 shadow-xl hover:shadow-brand-red/40 hover:scale-[1.02] active:scale-[0.98] text-center"
          >
            EXPLORE EVENTS
          </Link>

          <button
            type="button"
            onClick={onOpenFilmModal}
            id="hero-watch-film-cta"
            className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-4 bg-white/5 hover:bg-white/10 text-white border border-white/20 hover:border-white/40 backdrop-blur-md text-xs font-bold tracking-widest uppercase transition-all duration-200"
          >
            <Film className="w-4 h-4 text-brand-red" />
            <span>WATCH FILM</span>
          </button>
        </div>
      </div>

      {/* Floating Video Controls (Bottom Right) */}
      <div className="absolute bottom-6 right-6 z-20 flex items-center space-x-2">
        <button
          type="button"
          onClick={togglePlay}
          className="p-2.5 rounded-full bg-black/60 hover:bg-brand-red text-white backdrop-blur-md border border-white/15 transition-all"
          aria-label={isPlaying ? 'Pause hero video' : 'Play hero video'}
          title={isPlaying ? 'Pause video' : 'Play video'}
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5 fill-white" />}
        </button>

        <button
          type="button"
          onClick={toggleSound}
          className="p-2.5 rounded-full bg-black/60 hover:bg-brand-red text-white backdrop-blur-md border border-white/15 transition-all"
          aria-label={isMuted ? 'Unmute video audio' : 'Mute video audio'}
          title={isMuted ? 'Unmute' : 'Mute'}
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* Scroll Down Indicator (Bottom Center) */}
      <button
        type="button"
        onClick={scrollToContent}
        className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center text-xs tracking-widest uppercase text-brand-muted hover:text-white transition-colors group"
        aria-label="Scroll down to content"
      >
        <span className="text-[10px] font-mono tracking-widest mb-1.5 opacity-70 group-hover:opacity-100">
          SCROLL
        </span>
        <div className="w-5 h-8 border border-white/20 rounded-full flex justify-center p-1 group-hover:border-brand-red transition-colors">
          <div className="w-1 h-2 bg-brand-red rounded-full animate-bounce" />
        </div>
      </button>
    </section>
  );
}
