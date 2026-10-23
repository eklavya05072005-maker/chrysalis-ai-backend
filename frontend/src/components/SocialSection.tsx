'use client';

import React from 'react';
import Image from 'next/image';
import { Instagram, ArrowUpRight } from 'lucide-react';

const SOCIAL_ITEMS = [
  {
    id: 'soc-1',
    image: '/assets/events/nocturne/main-poster.png',
    caption: 'NOCTURNE announcement at Mall of Asia. When the dark rises.',
    tag: '#Nocturne2026',
  },
  {
    id: 'soc-2',
    image: '/assets/events/nocturne/dj-katz-poster.png',
    caption: 'DJ KATZ takes the helm. Peak time hypnotic techno.',
    tag: '#DJKatz',
  },
  {
    id: 'soc-3',
    image: '/assets/events/nocturne/mystery-match.png',
    caption: 'Same number. Different souls. 17 Boys / 17 Girls.',
    tag: '#MisteryMatch',
  },
  {
    id: 'soc-4',
    image: '/assets/reference/bengaluru-schedule.png',
    caption: 'Curating the electronic underground scene in Bengaluru.',
    tag: '#BengaluruNightlife',
  },
];

export default function SocialSection() {
  return (
    <section id="social-section" className="py-20 bg-[#080808] border-t border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-12 gap-4">
          <div>
            <div className="flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest mb-2">
              <Instagram className="w-4 h-4" />
              <span>FOLLOW THE UNDERGROUND</span>
            </div>
            <h2 className="text-2xl sm:text-4xl font-display font-black text-white tracking-tight uppercase">
              INSTAGRAM DISPATCHES
            </h2>
          </div>
          <a
            href="https://instagram.com"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-2 text-xs font-mono uppercase tracking-widest text-brand-silver hover:text-brand-red transition-colors"
          >
            <span>@URBEN.ENTT</span>
            <ArrowUpRight className="w-4 h-4 text-brand-red" />
          </a>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {SOCIAL_ITEMS.map((item) => (
            <a
              key={item.id}
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              className="group relative aspect-square bg-[#151515] overflow-hidden border border-white/10 hover:border-brand-red/60 transition-all block"
            >
              <Image
                src={item.image}
                alt={item.caption}
                fill
                sizes="(max-width: 768px) 50vw, 25vw"
                className="object-cover object-center group-hover:scale-105 transition-transform duration-500 opacity-80 group-hover:opacity-100"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-4">
                <span className="text-[11px] font-mono text-brand-red font-bold uppercase">{item.tag}</span>
                <p className="text-xs text-white line-clamp-2 mt-1">{item.caption}</p>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
