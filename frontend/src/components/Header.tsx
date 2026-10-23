'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, ArrowUpRight, ShieldCheck, Instagram } from 'lucide-react';

const NAV_LINKS = [
  { name: 'Home', href: '/' },
  { name: 'Events', href: '/events' },
  { name: 'Past Events', href: '/past-events' },
  { name: 'Services', href: '/services' },
  { name: 'About', href: '/about' },
  { name: 'Contact', href: '/contact' },
];

export default function Header() {
  const pathname = usePathname();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 40);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setIsMobileMenuOpen(false);
  }, [pathname]);

  const isAdminRoute = pathname?.startsWith('/event-admin');
  if (isAdminRoute) return null; // Admin dashboard has its own custom navigation

  return (
    <header
      id="site-header"
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-[#080808]/90 backdrop-blur-md border-b border-white/10 py-3 shadow-2xl'
          : 'bg-gradient-to-b from-black/80 via-black/40 to-transparent py-5'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        {/* Wordmark Logo */}
        <Link
          href="/"
          className="group flex items-center space-x-2 text-white tracking-widest font-display text-xl sm:text-2xl font-black uppercase transition-transform hover:scale-[1.02]"
          aria-label="URBEN.ENTT Home"
        >
          <span className="text-brand-silver group-hover:text-white transition-colors">
            URBEN<span className="text-brand-red font-sans">.</span>ENTT
          </span>
          <span className="hidden sm:inline-block w-1.5 h-1.5 rounded-full bg-brand-red animate-pulse" />
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center space-x-7" aria-label="Main Navigation">
          {NAV_LINKS.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.name}
                href={link.href}
                className={`text-sm tracking-wider uppercase font-medium transition-colors relative py-1 ${
                  isActive
                    ? 'text-white font-semibold'
                    : 'text-brand-muted hover:text-white'
                }`}
              >
                {link.name}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-brand-red rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Action Controls */}
        <div className="hidden lg:flex items-center space-x-4">
          <a
            href="https://instagram.com"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 text-brand-muted hover:text-white hover:bg-white/5 rounded-full transition-colors"
            aria-label="Follow URBEN.ENTT on Instagram"
          >
            <Instagram className="w-4 h-4" />
          </a>

          <Link
            href="/event-admin"
            className="p-2 text-zinc-500 hover:text-brand-muted hover:bg-white/5 rounded-full transition-colors"
            title="Admin Portal"
            aria-label="Event Admin Portal"
          >
            <ShieldCheck className="w-4 h-4" />
          </Link>

          <Link
            href="/contact"
            id="nav-enquire-cta"
            className="inline-flex items-center space-x-1.5 px-4 py-2 text-xs tracking-wider uppercase font-bold text-white bg-brand-red hover:bg-brand-red-glow rounded-none transition-all duration-200 shadow-md hover:shadow-brand-red/30 hover:scale-[1.03] active:scale-[0.98]"
          >
            <span>Enquire</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <div className="flex items-center space-x-2 lg:hidden">
          <Link
            href="/contact"
            className="px-3 py-1.5 text-xs uppercase font-bold bg-brand-red text-white"
          >
            Enquire
          </Link>
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-white hover:text-brand-red focus:outline-none focus:ring-2 focus:ring-brand-red"
            aria-expanded={isMobileMenuOpen}
            aria-label="Toggle mobile menu"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {isMobileMenuOpen && (
        <div className="lg:hidden bg-[#0a0a0a] border-b border-white/10 px-6 pt-4 pb-8 space-y-4 animate-fade-in shadow-2xl">
          <nav className="flex flex-col space-y-3" aria-label="Mobile Navigation">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.name}
                href={link.href}
                className={`text-base tracking-widest uppercase font-medium py-2 border-b border-white/5 ${
                  pathname === link.href ? 'text-brand-red font-bold' : 'text-brand-muted hover:text-white'
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>

          <div className="pt-4 flex items-center justify-between border-t border-white/10">
            <a
              href="https://instagram.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-xs uppercase tracking-wider text-brand-muted hover:text-white"
            >
              <Instagram className="w-4 h-4 text-brand-red" />
              <span>Instagram</span>
            </a>

            <Link
              href="/event-admin"
              className="flex items-center space-x-2 text-xs uppercase tracking-wider text-zinc-400 hover:text-white"
            >
              <ShieldCheck className="w-4 h-4 text-brand-red" />
              <span>Admin Portal</span>
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}
