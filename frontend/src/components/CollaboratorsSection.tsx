'use client';

import React from 'react';
import { ExternalLink, Handshake } from 'lucide-react';
import { Collaborator } from '@/types';

interface CollaboratorsSectionProps {
  collaborators: Collaborator[];
}

export default function CollaboratorsSection({ collaborators }: CollaboratorsSectionProps) {
  return (
    <section id="collaborators-section" className="py-20 bg-[#0a0a0a] border-t border-white/10 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <div className="inline-flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest mb-2">
            <Handshake className="w-3.5 h-3.5" />
            <span>ECOSYSTEM & COLLABORATION</span>
          </div>
          <h2 className="text-2xl sm:text-4xl font-display font-black text-white tracking-tight uppercase">
            TRUSTED PARTNERS
          </h2>
          <p className="text-brand-muted text-xs sm:text-sm mt-2">
            We collaborate with premier nightlife concepts, venues, and ticketing platforms across India to engineer unforgettable moments.
          </p>
        </div>

        {/* Collaborator Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {collaborators.map((collab) => (
            <div
              key={collab.id}
              className="p-8 bg-[#121212] border border-white/10 hover:border-brand-red/50 transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono uppercase tracking-widest text-brand-red">
                    COLLABORATOR
                  </span>
                  {collab.websiteUrl && (
                    <a
                      href={collab.websiteUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-zinc-500 hover:text-white transition-colors"
                      aria-label={`Visit ${collab.name} external link`}
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>

                <h3 className="text-2xl font-display font-black text-white uppercase group-hover:text-brand-silver transition-colors">
                  {collab.name}
                </h3>
                {collab.tagline && (
                  <p className="text-xs font-mono text-brand-red mt-1 uppercase">
                    &ldquo;{collab.tagline}&rdquo;
                  </p>
                )}
                <p className="text-xs text-brand-muted mt-3 leading-relaxed">
                  {collab.roleDescription}
                </p>
              </div>

              {collab.instagramHandle && (
                <div className="pt-4 mt-6 border-t border-white/5 text-[11px] font-mono text-zinc-400">
                  {collab.instagramHandle}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
