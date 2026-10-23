import type { Metadata, Viewport } from 'next';
import { Inter, Syne } from 'next/font/google';
import './globals.css';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

const syne = Syne({
  subsets: ['latin'],
  variable: '--font-syne',
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://urben.entt'),
  title: {
    default: 'URBEN.ENTT — We Create Moments That Matter | Event Management & Experiences',
    template: '%s | URBEN.ENTT',
  },
  description:
    'URBEN.ENTT is a premier event management and immersive experiences company specializing in electronic music festivals, nightlife curation, underground culture, and high-impact corporate productions.',
  keywords: [
    'URBEN.ENTT',
    'Event Management',
    'Bengaluru Nightlife',
    'Techno Events',
    'NOCTURNE',
    'DJ KATZ',
    'Mall of Asia',
    'SortMyScene',
    'Festival Production',
    'Experiences',
  ],
  authors: [{ name: 'URBEN.ENTT Production Team' }],
  creator: 'URBEN.ENTT',
  openGraph: {
    type: 'website',
    locale: 'en_IN',
    url: 'https://urben.entt',
    title: 'URBEN.ENTT — We Create Moments That Matter',
    description: 'Premier event management, concert production, and immersive nightlife experiences.',
    siteName: 'URBEN.ENTT',
    images: [
      {
        url: '/assets/events/nocturne/main-poster.png',
        width: 1200,
        height: 630,
        alt: 'URBEN.ENTT Key Visual - NOCTURNE',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'URBEN.ENTT — We Create Moments That Matter',
    description: 'Premier event management and immersive nightlife experiences.',
    images: ['/assets/events/nocturne/main-poster.png'],
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  themeColor: '#080808',
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${syne.variable}`}>
      <body className="bg-background text-brand-silver font-sans antialiased selection:bg-brand-red selection:text-white">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 z-50 px-4 py-2 bg-brand-red text-white text-sm font-semibold rounded-md shadow-lg"
        >
          Skip to main content
        </a>
        <Header />
        <main id="main-content" className="min-h-screen">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}
