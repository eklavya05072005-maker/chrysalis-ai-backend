import React from 'react';
import type { Metadata } from 'next';
import { Mail, Instagram, MapPin, Sparkles } from 'lucide-react';
import EnquiryForm from '@/components/EnquiryForm';
import { EnquiryType } from '@/types';

export const metadata: Metadata = {
  title: 'Contact & Inquiries',
  description:
    'Initiate a production enquiry, discuss artist bookings, or explore brand partnerships with the URBEN.ENTT team.',
};

interface ContactPageProps {
  searchParams: Promise<{ type?: string }>;
}

export default async function ContactPage({ searchParams }: ContactPageProps) {
  const { type } = await searchParams;
  const initialType: EnquiryType = (type as EnquiryType) || 'general';

  return (
    <div className="pt-28 pb-24 bg-[#080808] min-h-screen text-brand-silver">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-start">
          {/* Left Column: Narrative & Info */}
          <div className="lg:col-span-5 space-y-8">
            <div>
              <div className="inline-flex items-center space-x-2 text-brand-red font-mono text-xs uppercase tracking-widest mb-3">
                <Sparkles className="w-3.5 h-3.5" />
                <span>CONNECT WITH URBEN.ENTT</span>
              </div>
              <h1 className="text-4xl sm:text-6xl font-display font-black text-white tracking-tight uppercase leading-none mb-4">
                INITIATE AN ENQUIRY
              </h1>
              <p className="text-brand-muted text-sm sm:text-base leading-relaxed">
                Whether staging an upcoming electronic festival, curating an underground warehouse session, or exploring brand activations, our team is at your disposal.
              </p>
            </div>

            <div className="p-6 bg-[#111111] border border-white/10 space-y-6">
              <h2 className="text-xs font-mono uppercase tracking-widest text-brand-red">
                COMMUNICATION CHANNELS
              </h2>

              <div className="space-y-4 text-xs font-mono">
                <div className="flex items-start space-x-3 text-zinc-300">
                  <Mail className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 uppercase block">DIRECT EMAIL</span>
                    <a
                      href="mailto:contact@urben.entt"
                      className="text-white hover:text-brand-red transition-colors"
                    >
                      contact@urben.entt
                    </a>
                  </div>
                </div>

                <div className="flex items-start space-x-3 text-zinc-300">
                  <MapPin className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 uppercase block">PRODUCTION HQ</span>
                    <span className="text-white">Bengaluru, Karnataka, India</span>
                  </div>
                </div>

                <div className="flex items-start space-x-3 text-zinc-300">
                  <Instagram className="w-4 h-4 text-brand-red mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-zinc-500 uppercase block">INSTAGRAM DISPATCHES</span>
                    <a
                      href="https://instagram.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-white hover:text-brand-red transition-colors"
                    >
                      @urben.entt
                    </a>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 bg-white/[0.02] border-l-2 border-brand-red text-xs text-brand-muted space-y-2">
              <div className="text-white font-mono uppercase font-bold">PRODUCTION TURNAROUND</div>
              <p>
                All inquiries submitted via this form are routed to our operations and creative teams. Expect a direct response within 24 to 48 business hours.
              </p>
            </div>
          </div>

          {/* Right Column: Interactive Form */}
          <div className="lg:col-span-7 bg-[#101010] border border-white/10 p-6 sm:p-10 shadow-2xl">
            <h2 className="text-xl font-display font-black text-white uppercase tracking-wide mb-6">
              PROJECT BRIEF SPECIFICATIONS
            </h2>
            <EnquiryForm initialType={initialType} />
          </div>
        </div>
      </div>
    </div>
  );
}
