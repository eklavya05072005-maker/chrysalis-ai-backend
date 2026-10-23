'use client';

import React from 'react';
import Link from 'next/link';
import { Disc3, Sparkles, Building2, PartyPopper, ArrowUpRight } from 'lucide-react';

const SERVICES = [
  {
    id: 'festivals',
    title: 'Festivals & Concerts',
    slug: 'festival',
    icon: Disc3,
    tagline: 'Large-scale stages, sound reinforcement & artist booking',
    description:
      'Turnkey festival curation, stage scenography, acoustic modeling, artist routing, and crowd logistics engineered for monumental open-air and arena experiences.',
    capabilities: ['Mainstage Production', 'Artist Hospitality & Lineups', 'Permits & Crowd Safety', 'Acoustic Engineering'],
  },
  {
    id: 'nightlife',
    title: 'Music & Nightlife',
    slug: 'nightlife',
    icon: Sparkles,
    iconColor: 'text-brand-red',
    tagline: 'Underground club sessions, dark aesthetics & premier selectors',
    description:
      'Curating electronic music sanctuaries in premier venues and hidden spaces across Bengaluru. From boiler-room style intimacy to high-BPM warehouse raves.',
    capabilities: ['Curated DJ Lineups', 'Lighting & Laser Design', 'Venue Partnerships', 'Sound System Optimization'],
  },
  {
    id: 'corporate',
    title: 'Corporate Events',
    slug: 'corporate',
    icon: Building2,
    tagline: 'Brand summits, award galas & visionary product reveals',
    description:
      'Transforming corporate gatherings into memorable sensory productions. High-end visual storytelling, seamless stage management, and executive hospitality.',
    capabilities: ['Keynote Scenography', 'Brand Activations', 'Interactive Installations', 'End-to-End Event Operations'],
  },
  {
    id: 'experiences',
    title: 'Experiences & Parties',
    slug: 'private_event',
    icon: PartyPopper,
    tagline: 'Themed immersive environments & curated private milestones',
    description:
      'Bespoke social gatherings driven by interactive mechanics—such as the proprietary MISTERY MATCH concept—combining storytelling, theatrical design, and private soundscapes.',
    capabilities: ['Custom Thematic Design', 'Gamified Social Mechanics', 'Exclusive Mixology Curation', 'Private Security & VIP Access'],
  },
];

export default function ServicesSection() {
  return (
    <section id="services-section" className="py-24 sm:py-32 bg-[#0c0c0c] relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="max-w-3xl mb-16">
          <div className="text-xs font-mono uppercase tracking-widest text-brand-red mb-3">
            CAPABILITIES & SPECIALIZATIONS
          </div>
          <h2 className="text-3xl sm:text-5xl font-display font-black text-white tracking-tight uppercase mb-4">
            WHAT WE CREATE
          </h2>
          <p className="text-brand-muted text-sm sm:text-base leading-relaxed">
            From monumental electronic music stages to intimate thematic gatherings, URBEN.ENTT engineers experiences that resonate long after the lights come up.
          </p>
        </div>

        {/* Services Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
          {SERVICES.map((service, index) => {
            const Icon = service.icon;
            return (
              <div
                key={service.id}
                className="group p-8 sm:p-10 bg-[#121212] border border-white/10 hover:border-brand-red/50 transition-all duration-300 relative flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <div className="p-3 bg-white/5 border border-white/10 group-hover:border-brand-red group-hover:bg-brand-red/10 transition-colors">
                      <Icon className="w-6 h-6 text-brand-red" />
                    </div>
                    <span className="text-xs font-mono text-zinc-600 group-hover:text-brand-red transition-colors">
                      0{index + 1}
                    </span>
                  </div>

                  <h3 className="text-2xl font-display font-black text-white uppercase tracking-wide mb-2 group-hover:text-brand-silver transition-colors">
                    {service.title}
                  </h3>
                  <p className="text-xs font-mono text-brand-red tracking-wider uppercase mb-4">
                    {service.tagline}
                  </p>
                  <p className="text-sm text-brand-muted leading-relaxed mb-6">
                    {service.description}
                  </p>

                  <div className="space-y-2 mb-8">
                    {service.capabilities.map((cap) => (
                      <div key={cap} className="flex items-center space-x-2 text-xs text-zinc-300">
                        <span className="w-1.5 h-1.5 bg-brand-red rounded-full" />
                        <span>{cap}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <Link
                  href={`/contact?type=${service.slug}`}
                  className="inline-flex items-center space-x-2 text-xs font-bold uppercase tracking-widest text-white group-hover:text-brand-red transition-colors pt-4 border-t border-white/5"
                >
                  <span>Enquire for this service</span>
                  <ArrowUpRight className="w-4 h-4" />
                </Link>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
