'use client';

import React, { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { Calendar, Clock, MapPin, Ticket, ArrowRight, Filter } from 'lucide-react';
import { UrbenEvent } from '@/types';

interface EventsListClientProps {
  events: UrbenEvent[];
}

const CATEGORIES = [
  'All',
  'Nightlife & Techno',
  'Festivals & Concerts',
  'Exclusive Parties',
  'Club Events',
];

export default function EventsListClient({ events }: EventsListClientProps) {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  const filteredEvents = events.filter((event) => {
    const matchesCategory =
      selectedCategory === 'All' || event.category === selectedCategory;
    const matchesSearch =
      event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.venueName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.city.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="space-y-12">
      {/* Filters & Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-4 sm:p-6 bg-[#111111] border border-white/10">
        {/* Category Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono uppercase text-zinc-500 mr-2 flex items-center">
            <Filter className="w-3.5 h-3.5 mr-1" />
            FILTER:
          </span>
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider transition-colors ${
                selectedCategory === cat
                  ? 'bg-brand-red text-white font-bold'
                  : 'bg-white/5 text-zinc-400 hover:text-white hover:bg-white/10'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="w-full md:w-64">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events or venue..."
            className="w-full px-3 py-1.5 bg-[#0a0a0a] border border-white/15 focus:border-brand-red text-white placeholder-zinc-600 text-xs font-mono focus:outline-none"
          />
        </div>
      </div>

      {/* Events Grid / Empty State */}
      {filteredEvents.length === 0 ? (
        <div className="p-16 text-center border border-white/10 bg-[#0f0f0f] space-y-4">
          <p className="text-xl font-display uppercase tracking-wider text-white">
            NO CONFIRMED PRODUCTIONS MATCHING CRITERIA
          </p>
          <p className="text-xs text-brand-muted max-w-md mx-auto">
            Stay tuned to our dispatches or reach out directly to inquire about hosting a private experience.
          </p>
          <button
            type="button"
            onClick={() => {
              setSelectedCategory('All');
              setSearchQuery('');
            }}
            className="px-4 py-2 bg-brand-red text-white text-xs font-mono uppercase tracking-wider"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredEvents.map((event) => (
            <div
              key={event.id}
              className="group bg-[#111111] border border-white/10 hover:border-brand-red/50 flex flex-col justify-between transition-all duration-300"
            >
              {/* Poster Header */}
              <div className="relative aspect-[4/5] w-full overflow-hidden bg-black">
                <Image
                  src={event.posterUrl}
                  alt={event.title}
                  fill
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                  className="object-cover object-center group-hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent" />

                {/* Status Badge */}
                <div className="absolute top-4 left-4 px-2.5 py-1 bg-black/80 backdrop-blur-md border border-white/15 text-brand-red text-[10px] font-mono uppercase tracking-widest font-bold">
                  {event.ticketStatus}
                </div>

                {event.isFeatured && (
                  <div className="absolute top-4 right-4 px-2 py-0.5 bg-brand-red text-white text-[10px] font-mono uppercase tracking-widest font-bold">
                    FEATURED
                  </div>
                )}

                <div className="absolute bottom-4 left-4 right-4">
                  <span className="text-[10px] font-mono text-brand-red tracking-widest uppercase block mb-1">
                    {event.category}
                  </span>
                  <h3 className="text-2xl font-display font-black text-white uppercase tracking-tight group-hover:text-brand-silver transition-colors">
                    {event.title}
                  </h3>
                </div>
              </div>

              {/* Body */}
              <div className="p-6 flex flex-col flex-grow justify-between space-y-4">
                <div className="space-y-3">
                  <p className="text-xs text-brand-muted line-clamp-2 leading-relaxed">
                    {event.shortDescription}
                  </p>

                  <div className="space-y-1.5 text-xs font-mono text-zinc-300 pt-2 border-t border-white/5">
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-3.5 h-3.5 text-brand-red flex-shrink-0" />
                      <span>{event.timeDisplay}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MapPin className="w-3.5 h-3.5 text-brand-red flex-shrink-0" />
                      <span className="truncate">{event.venueName}, {event.city}</span>
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="pt-4 border-t border-white/10 flex items-center justify-between gap-2">
                  <Link
                    href={`/events/${event.slug}`}
                    className="inline-flex items-center space-x-1.5 text-xs font-mono uppercase tracking-wider text-white hover:text-brand-red transition-colors"
                  >
                    <span>Event Details</span>
                    <ArrowRight className="w-3.5 h-3.5 text-brand-red" />
                  </Link>

                  <a
                    href={event.ticketUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 px-3 py-1.5 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-mono uppercase tracking-wider font-semibold"
                  >
                    <Ticket className="w-3 h-3" />
                    <span>Tickets</span>
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
