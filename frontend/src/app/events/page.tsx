import React from 'react';
import type { Metadata } from 'next';
import { fetchPublicEvents } from '@/lib/api';
import EventsListClient from '@/components/EventsListClient';

export const metadata: Metadata = {
  title: 'Confirmed Events & Productions',
  description:
    'Explore upcoming electronic music events, underground nightlife sessions, and headline productions curated by URBEN.ENTT in Bengaluru.',
};

export const revalidate = 60;

export default async function EventsPage() {
  const events = await fetchPublicEvents({ isPast: false });

  return (
    <div className="pt-28 pb-24 bg-[#080808] min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mb-12">
          <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-3">
            URBEN.ENTT CALENDAR
          </div>
          <h1 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase mb-4">
            CONFIRMED EXPERIENCES
          </h1>
          <p className="text-brand-muted text-sm sm:text-base leading-relaxed">
            Every production is engineered with precision—featuring custom lighting, world-class acoustic arrays, and verified ticketing via SortMyScene.
          </p>
        </div>

        <EventsListClient events={events} />
      </div>
    </div>
  );
}
