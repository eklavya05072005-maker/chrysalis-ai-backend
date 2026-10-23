import React from 'react';
import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import {
  Calendar,
  Clock,
  MapPin,
  Ticket,
  ShieldAlert,
  Sparkles,
  ArrowLeft,
  ExternalLink,
  Disc,
} from 'lucide-react';
import { fetchEventBySlug, fetchPublicEvents } from '@/lib/api';

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateStaticParams() {
  const events = await fetchPublicEvents();
  return events.map((e) => ({ slug: e.slug }));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const event = await fetchEventBySlug(slug);

  if (!event) {
    return {
      title: 'Event Not Found | URBEN.ENTT',
    };
  }

  return {
    title: `${event.title} — ${event.tagline}`,
    description: event.shortDescription,
    openGraph: {
      title: `${event.title} | URBEN.ENTT`,
      description: event.shortDescription,
      images: [event.posterUrl],
    },
  };
}

export const revalidate = 60;

export default async function EventDetailPage({ params }: PageProps) {
  const { slug } = await params;
  const event = await fetchEventBySlug(slug);

  if (!event) {
    notFound();
  }

  return (
    <div className="pt-24 pb-24 bg-[#080808] min-h-screen text-brand-silver">
      {/* Top Breadcrumb Bar */}
      <div className="border-b border-white/10 bg-[#0a0a0a]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between text-xs font-mono">
          <Link
            href="/events"
            className="inline-flex items-center space-x-2 text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>BACK TO ALL EVENTS</span>
          </Link>
          <div className="flex items-center space-x-3 text-zinc-500">
            <span>URBEN.ENTT</span>
            <span>/</span>
            <span className="text-brand-red uppercase">{event.slug}</span>
          </div>
        </div>
      </div>

      {/* Hero Header Strip */}
      <section className="relative py-12 sm:py-20 bg-gradient-to-b from-[#111111] to-[#080808] border-b border-white/10 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
            {/* Visual Poster */}
            <div className="lg:col-span-5">
              <div className="relative aspect-[3/4] w-full border border-white/15 overflow-hidden shadow-2xl red-edge-glow">
                <Image
                  src={event.posterUrl}
                  alt={event.title}
                  fill
                  sizes="(max-width: 768px) 100vw, 40vw"
                  className="object-cover object-center"
                  priority
                />
                <div className="absolute top-4 left-4 px-3 py-1 bg-brand-red text-white text-[11px] font-mono uppercase tracking-wider font-bold">
                  {event.ticketStatus}
                </div>
              </div>
            </div>

            {/* Event Summary Column */}
            <div className="lg:col-span-7 space-y-6">
              <div className="flex items-center space-x-2 text-xs font-mono text-brand-red tracking-widest uppercase">
                <span>{event.category}</span>
                <span>•</span>
                <span>BENGALURU</span>
              </div>

              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-display font-black text-white tracking-tight uppercase leading-none">
                {event.title}
              </h1>

              <p className="text-xl sm:text-2xl font-display font-medium text-brand-red tracking-wide uppercase">
                {event.tagline}
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 py-6 border-t border-b border-white/10 text-xs font-mono">
                <div className="flex items-start space-x-3">
                  <Calendar className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 block uppercase">DATE & TIME</span>
                    <span className="text-white font-semibold">Saturday, 31 October 2026</span>
                    <span className="text-zinc-400 block">{event.timeDisplay}</span>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <MapPin className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 block uppercase">LOCATION</span>
                    <span className="text-white font-semibold">{event.venueName}</span>
                    <span className="text-zinc-400 block">{event.city}</span>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <ShieldAlert className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 block uppercase">ADMISSION POLICY</span>
                    <span className="text-white font-semibold">{event.agePolicy}</span>
                  </div>
                </div>

                {event.dressCode && (
                  <div className="flex items-start space-x-3">
                    <Sparkles className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                    <div>
                      <span className="text-zinc-500 block uppercase">DRESS CODE</span>
                      <span className="text-white font-semibold">{event.dressCode}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Booking CTA Bar */}
              <div className="flex flex-col sm:flex-row items-center gap-4 pt-2">
                <a
                  href={event.ticketUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-8 py-4 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold tracking-widest uppercase transition-all duration-200 shadow-xl shadow-brand-red/25"
                >
                  <Ticket className="w-4 h-4" />
                  <span>GET TICKETS ON SORTMYSCENE</span>
                </a>

                {event.googleMapsUrl && (
                  <a
                    href={event.googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 px-6 py-4 bg-white/5 hover:bg-white/10 text-white border border-white/15 text-xs font-mono uppercase tracking-wider transition-colors"
                  >
                    <MapPin className="w-4 h-4 text-brand-red" />
                    <span>View Venue Map</span>
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Details Grid */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Left Column: Narrative, Activity & Gallery */}
          <div className="lg:col-span-8 space-y-12">
            <div className="space-y-4">
              <h2 className="text-2xl font-display font-black text-white uppercase tracking-wide">
                ABOUT THE PRODUCTION
              </h2>
              <div className="text-brand-muted text-sm sm:text-base leading-relaxed whitespace-pre-line space-y-4">
                {event.fullDescription}
              </div>
            </div>

            {event.experienceNotes && (
              <div className="p-8 bg-[#101010] border border-white/10 relative overflow-hidden">
                <div className="flex items-center space-x-2 text-xs font-mono uppercase text-brand-red tracking-widest mb-3">
                  <Sparkles className="w-4 h-4 fill-brand-red" />
                  <span>SIGNATURE INTERACTIVE SOCIAL MECHANIC</span>
                </div>
                <h3 className="text-2xl sm:text-3xl font-display font-black text-white uppercase mb-4">
                  MISTERY MATCH: SAME NUMBER. DIFFERENT SOULS.
                </h3>
                <p className="text-sm text-brand-muted leading-relaxed mb-6">
                  {event.experienceNotes}
                </p>

                <div className="relative aspect-[16/9] w-full border border-white/10 overflow-hidden bg-black">
                  <Image
                    src="/assets/events/nocturne/mystery-match.png"
                    alt="MISTERY MATCH Activity Feature"
                    fill
                    sizes="(max-width: 1024px) 100vw, 60vw"
                    className="object-cover object-center"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-6">
                    <span className="text-xs font-mono text-white bg-black/60 px-3 py-1 border border-white/10">
                      17 BOYS / 17 GIRLS • FIND YOUR COUNTERPART AT NOCTURNE
                    </span>
                  </div>
                </div>
              </div>
            )}

            {event.promoVideoUrl && (
              <div className="space-y-4">
                <h3 className="text-2xl font-display font-black text-white uppercase tracking-wide">
                  OFFICIAL EVENT PREVIEW FILM
                </h3>
                <div className="relative aspect-video w-full bg-black border border-white/10 overflow-hidden shadow-2xl">
                  <video
                    src={event.promoVideoUrl}
                    controls
                    poster={event.posterUrl}
                    preload="metadata"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>
            )}

            {event.gallery && event.gallery.length > 0 && (
              <div className="space-y-4">
                <h3 className="text-2xl font-display font-black text-white uppercase tracking-wide">
                  OFFICIAL VISUAL ASSETS
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {event.gallery
                    .filter((m) => m.mediaType === 'image')
                    .map((item) => (
                      <div
                        key={item.id}
                        className="relative aspect-[3/4] bg-[#141414] border border-white/10 overflow-hidden group"
                      >
                        <Image
                          src={item.url}
                          alt={item.altText}
                          fill
                          sizes="(max-width: 768px) 100vw, 30vw"
                          className="object-cover object-center group-hover:scale-105 transition-transform duration-500"
                        />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent flex items-end p-4">
                          <span className="text-xs font-mono text-white">{item.title}</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Lineup, Collaborators, Venue */}
          <div className="lg:col-span-4 space-y-8">
            <div className="p-6 bg-[#111111] border border-white/10">
              <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-4 flex items-center space-x-2">
                <Disc className="w-4 h-4 animate-spin text-brand-red" />
                <span>OFFICIAL ARTIST LINEUP</span>
              </div>

              <div className="space-y-6">
                {event.artists.map((artist) => (
                  <div key={artist.id} className="border-b border-white/5 pb-4 last:border-0 last:pb-0">
                    {artist.imageUrl && (
                      <div className="relative aspect-video w-full mb-3 border border-white/10 overflow-hidden">
                        <Image
                          src={artist.imageUrl}
                          alt={artist.name}
                          fill
                          sizes="(max-width: 1024px) 100vw, 25vw"
                          className="object-cover object-center"
                        />
                      </div>
                    )}
                    <div className="flex items-center justify-between">
                      <h4 className="text-lg font-display font-bold text-white uppercase">
                        {artist.name}
                      </h4>
                      {artist.isHeadliner && (
                        <span className="text-[10px] font-mono text-brand-red uppercase px-2 py-0.5 bg-brand-red/10 border border-brand-red/30">
                          HEADLINER
                        </span>
                      )}
                    </div>
                    <p className="text-xs font-mono text-brand-red mt-0.5">{artist.genre}</p>
                    {artist.bio && (
                      <p className="text-xs text-brand-muted mt-2 leading-relaxed">{artist.bio}</p>
                    )}
                    {artist.setTime && (
                      <p className="text-[11px] font-mono text-zinc-400 mt-2">
                        Set Time: <span className="text-white">{artist.setTime}</span>
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {event.collaborators && event.collaborators.length > 0 && (
              <div className="p-6 bg-[#111111] border border-white/10">
                <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-4">
                  COLLABORATION PARTNERS
                </div>
                <div className="space-y-4">
                  {event.collaborators.map((c) => (
                    <div key={c.collaborator.id} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
                      <div className="flex items-center justify-between">
                        <h5 className="text-sm font-display font-bold text-white uppercase">
                          {c.collaborator.name}
                        </h5>
                        {c.collaborator.websiteUrl && (
                          <a
                            href={c.collaborator.websiteUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-zinc-500 hover:text-white"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                      <p className="text-xs font-mono text-brand-red">
                        {c.collaborator.tagline || c.collaborator.roleDescription}
                      </p>
                      {c.contributionNote && (
                        <p className="text-xs text-zinc-400 mt-1">Role: {c.contributionNote}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="p-6 bg-[#111111] border border-white/10 space-y-3">
              <div className="text-xs font-mono uppercase tracking-widest text-brand-red">
                VENUE & ARRIVAL
              </div>
              <h4 className="text-lg font-display font-bold text-white uppercase">
                {event.venueName}
              </h4>
              <p className="text-xs text-brand-muted leading-relaxed">
                {event.venueAddress}
              </p>
              {event.googleMapsUrl && (
                <div className="pt-2">
                  <a
                    href={event.googleMapsUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 text-xs font-mono text-brand-red hover:underline uppercase"
                  >
                    <span>Open in Google Maps</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
