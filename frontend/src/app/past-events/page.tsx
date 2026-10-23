import React from 'react';
import type { Metadata } from 'next';
import Image from 'next/image';
import { fetchPublicEvents } from '@/lib/api';
import PastEventsClient from '@/components/PastEventsClient';

export const metadata: Metadata = {
  title: 'Past Events & Production Archive',
  description:
    'Retrospective of past underground club sessions, warehouse raves, and electronic music showcases produced by URBEN.ENTT in Bengaluru.',
};

export const revalidate = 60;

export default async function PastEventsPage() {
  const events = await fetchPublicEvents({ isPast: true });

  return (
    <div className="pt-28 pb-24 bg-[#080808] min-h-screen">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mb-12">
          <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-3">
            ARCHIVE & RETROSPECTIVES
          </div>
          <h1 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase mb-4">
            PAST PRODUCTIONS
          </h1>
          <p className="text-brand-muted text-sm sm:text-base leading-relaxed">
            A permanent record of past dancefloors, sound system takeovers, and intimate underground showcases across Bengaluru.
          </p>
        </div>

        <PastEventsClient initialEvents={events} />

        <div className="mt-20 p-8 sm:p-12 bg-[#0e0e0e] border border-white/10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-7 space-y-4">
              <span className="text-xs font-mono uppercase tracking-widest text-brand-red block">
                BENGALURU SCENE ARCHIVE REFERENCE
              </span>
              <h2 className="text-2xl sm:text-3xl font-display font-black text-white uppercase">
                THE SORTMYSCENE BENGALURU CALENDAR
              </h2>
              <p className="text-sm text-brand-muted leading-relaxed">
                As recorded on the official SortMyScene Bengaluru nightlife circuit reference, URBEN.ENTT collaborated with BLAH BLA for NOVA – BREAK THE FLOOR featuring VATSAA alongside the city’s most electrifying weekend schedules.
              </p>
              <div className="text-xs font-mono text-zinc-400 space-y-1">
                <div>• Verified Venue: BLAH BLA Bengaluru</div>
                <div>• Verified Scene: Minimal / Disco / Hip Hop</div>
                <div>• Associated Selectors: VATSAA, DJ T3RAN, DJ KATZ</div>
              </div>
            </div>

            <div className="lg:col-span-5">
              <div className="relative aspect-[4/5] w-full border border-white/15 overflow-hidden bg-black shadow-2xl">
                <Image
                  src="/assets/reference/bengaluru-schedule.png"
                  alt="SortMyScene Bengaluru Event Schedule Reference"
                  fill
                  sizes="(max-width: 1024px) 100vw, 40vw"
                  className="object-contain object-center"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
