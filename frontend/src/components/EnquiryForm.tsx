'use client';

import React, { useState } from 'react';
import { Send, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { EnquiryType } from '@/types';

interface EnquiryFormProps {
  initialType?: EnquiryType;
}

export default function EnquiryForm({ initialType = 'general' }: EnquiryFormProps) {
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    phone: '',
    enquiryType: initialType,
    eventDate: '',
    estimatedGuests: '',
    message: '',
    websiteHoneypot: '', // Spam honeypot
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors((prev) => {
        const copy = { ...prev };
        delete copy[name];
        return copy;
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    // Spam honeypot check
    if (formData.websiteHoneypot) {
      setIsSuccess(true);
      return;
    }

    // Client validation
    const clientErrors: Record<string, string> = {};
    if (!formData.fullName.trim()) clientErrors.fullName = 'Full name is required';
    if (!formData.email.trim()) {
      clientErrors.email = 'Email address is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email.trim())) {
      clientErrors.email = 'Please enter a valid email address';
    }
    if (!formData.message.trim() || formData.message.trim().length < 10) {
      clientErrors.message = 'Please provide details of at least 10 characters';
    }

    if (Object.keys(clientErrors).length > 0) {
      setErrors(clientErrors);
      return;
    }

    setIsSubmitting(true);

    try {
      const res = await fetch('/api/enquiries', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const json = await res.json();

      if (!res.ok) {
        if (json.errors) {
          setErrors(json.errors);
        } else {
          setServerError(json.error || 'Failed to submit enquiry. Please try again.');
        }
      } else {
        setIsSuccess(true);
        setFormData({
          fullName: '',
          email: '',
          phone: '',
          enquiryType: 'general',
          eventDate: '',
          estimatedGuests: '',
          message: '',
          websiteHoneypot: '',
        });
      }
    } catch {
      setServerError('Network error. Please verify your connection and try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="p-8 sm:p-12 bg-[#121212] border border-brand-red/40 text-center animate-fade-in shadow-2xl">
        <CheckCircle2 className="w-16 h-16 text-brand-red mx-auto mb-4 animate-bounce" />
        <h3 className="text-2xl font-display font-black text-white uppercase tracking-tight mb-2">
          ENQUIRY RECEIVED
        </h3>
        <p className="text-brand-muted text-sm max-w-md mx-auto leading-relaxed mb-6">
          Thank you for reaching out to URBEN.ENTT. Our creative production and operations team will review your specifications and contact you shortly.
        </p>
        <button
          type="button"
          onClick={() => setIsSuccess(false)}
          className="px-6 py-2.5 bg-white/10 hover:bg-white/20 text-white text-xs font-mono uppercase tracking-widest transition-colors"
        >
          Send Another Enquiry
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      {/* Honeypot field (hidden from screen) */}
      <input
        type="text"
        name="websiteHoneypot"
        value={formData.websiteHoneypot}
        onChange={handleChange}
        tabIndex={-1}
        autoComplete="off"
        className="hidden"
        aria-hidden="true"
      />

      {serverError && (
        <div className="p-4 bg-red-950/60 border border-brand-red/60 text-white text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 text-brand-red flex-shrink-0" />
          <span>{serverError}</span>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        {/* Full Name */}
        <div>
          <label htmlFor="enquiry-name" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
            Full Name <span className="text-brand-red">*</span>
          </label>
          <input
            id="enquiry-name"
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            placeholder="e.g. Gautam Verma"
            required
            className={`w-full px-4 py-3 bg-[#111111] border ${
              errors.fullName ? 'border-brand-red ring-1 ring-brand-red' : 'border-white/15 focus:border-brand-red'
            } text-white placeholder-zinc-600 text-sm focus:outline-none transition-colors`}
          />
          {errors.fullName && (
            <p className="mt-1 text-[11px] text-brand-red font-mono">{errors.fullName}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="enquiry-email" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
            Email Address <span className="text-brand-red">*</span>
          </label>
          <input
            id="enquiry-email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="gautam@example.com"
            required
            className={`w-full px-4 py-3 bg-[#111111] border ${
              errors.email ? 'border-brand-red ring-1 ring-brand-red' : 'border-white/15 focus:border-brand-red'
            } text-white placeholder-zinc-600 text-sm focus:outline-none transition-colors`}
          />
          {errors.email && (
            <p className="mt-1 text-[11px] text-brand-red font-mono">{errors.email}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        {/* Phone */}
        <div>
          <label htmlFor="enquiry-phone" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
            Phone Number (Optional)
          </label>
          <input
            id="enquiry-phone"
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="+91 98450 00000"
            className="w-full px-4 py-3 bg-[#111111] border border-white/15 focus:border-brand-red text-white placeholder-zinc-600 text-sm focus:outline-none transition-colors"
          />
        </div>

        {/* Enquiry Type */}
        <div>
          <label htmlFor="enquiry-type" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
            Nature of Enquiry
          </label>
          <select
            id="enquiry-type"
            name="enquiryType"
            value={formData.enquiryType}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-[#111111] border border-white/15 focus:border-brand-red text-white text-sm focus:outline-none transition-colors"
          >
            <option value="general">General Inquiry</option>
            <option value="booking">Event Production & Staging</option>
            <option value="partnership">Brand Sponsorship & Activation</option>
            <option value="festival">Festival Curatorship</option>
            <option value="corporate">Corporate Gala & Launch</option>
            <option value="private_event">Private Themed Experience</option>
            <option value="press">Press & Media</option>
          </select>
        </div>

        {/* Target Date */}
        <div>
          <label htmlFor="enquiry-date" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
            Target Date (If Applicable)
          </label>
          <input
            id="enquiry-date"
            type="date"
            name="eventDate"
            value={formData.eventDate}
            onChange={handleChange}
            className="w-full px-4 py-3 bg-[#111111] border border-white/15 focus:border-brand-red text-white text-sm focus:outline-none transition-colors"
          />
        </div>
      </div>

      {/* Message */}
      <div>
        <label htmlFor="enquiry-message" className="block text-xs font-mono uppercase text-zinc-400 mb-2">
          Project Brief / Message <span className="text-brand-red">*</span>
        </label>
        <textarea
          id="enquiry-message"
          name="message"
          rows={5}
          value={formData.message}
          onChange={handleChange}
          placeholder="Tell us about your event concept, guest count, preferred venue or dates, sound/production requirements..."
          required
          className={`w-full px-4 py-3 bg-[#111111] border ${
            errors.message ? 'border-brand-red ring-1 ring-brand-red' : 'border-white/15 focus:border-brand-red'
          } text-white placeholder-zinc-600 text-sm focus:outline-none transition-colors`}
        />
        {errors.message && (
          <p className="mt-1 text-[11px] text-brand-red font-mono">{errors.message}</p>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        id="submit-enquiry-btn"
        className="w-full py-4 bg-brand-red hover:bg-brand-red-glow text-white text-xs font-bold tracking-widest uppercase transition-all duration-200 shadow-xl hover:shadow-brand-red/30 flex items-center justify-center space-x-2 disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {isSubmitting ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>TRANSMITTING ENQUIRY...</span>
          </>
        ) : (
          <>
            <Send className="w-4 h-4" />
            <span>SUBMIT PRODUCTION ENQUIRY</span>
          </>
        )}
      </button>

      <p className="text-[11px] text-zinc-500 font-mono text-center">
        Your enquiry is strictly confidential. URBEN.ENTT never shares contact information with unverified third parties.
      </p>
    </form>
  );
}
