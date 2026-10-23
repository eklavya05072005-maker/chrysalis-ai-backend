export type EventStatus = 'draft' | 'review_pending' | 'approved' | 'published' | 'archived';
export type UserRole = 'event_admin' | 'owner' | 'developer';
export type EnquiryType = 'booking' | 'partnership' | 'festival' | 'private_event' | 'corporate' | 'press' | 'general';
export type EnquiryStatus = 'new' | 'in_progress' | 'contacted' | 'closed';

export interface Collaborator {
  id: string;
  name: string;
  slug: string;
  roleDescription: string;
  tagline?: string;
  logoUrl?: string;
  websiteUrl?: string;
  instagramHandle?: string;
  isActive: boolean;
}

export interface Artist {
  id: string;
  name: string;
  genre: string;
  bio?: string;
  imageUrl?: string;
  instagramHandle?: string;
  isHeadliner?: boolean;
  setTime?: string;
}

export interface EventMediaItem {
  id: string;
  mediaType: 'image' | 'video';
  url: string;
  thumbnailUrl?: string;
  title: string;
  altText: string;
  isHero?: boolean;
  isGallery?: boolean;
}

export interface UrbenEvent {
  id: string;
  title: string;
  slug: string;
  tagline: string;
  category: 'Nightlife & Techno' | 'Festivals & Concerts' | 'Immersive Experiences' | 'Exclusive Parties' | 'Club Events';
  status: EventStatus;
  isFeatured: boolean;
  isPast?: boolean;

  // Date & Time
  startDate: string; // ISO date string e.g. "2026-10-31T14:00:00Z"
  endDate?: string;
  timeDisplay: string; // "2:00 PM – 6:00 PM"

  // Venue
  venueName: string; // "Mall of Asia"
  city: string; // "Bengaluru"
  venueAddress: string;
  googleMapsUrl?: string;

  // Descriptions & Editorial
  shortDescription: string;
  fullDescription: string;
  experienceNotes?: string; // Activity notes like "MISTERY MATCH: SAME NUMBER. DIFFERENT SOULS."
  agePolicy: string; // "18+ | Club Rules & Cover Charges Apply"
  dressCode?: string;

  // Ticketing
  ticketingPlatform: 'SortMyScene' | 'Direct RSVP' | 'Guestlist' | 'Exclusive';
  ticketUrl: string;
  ticketPriceStarting?: number;
  ticketStatus: 'Tickets Live' | 'Filling Fast' | 'Sold Out' | 'Free Entry w/ Registration' | 'Archived';

  // Media
  posterUrl: string;
  heroBannerUrl?: string;
  promoVideoUrl?: string;
  gallery: EventMediaItem[];

  // Relationships
  collaborators: {
    collaborator: Collaborator;
    contributionNote?: string;
  }[];
  artists: Artist[];

  // Workflow Metadata
  createdBy: string;
  approvedBy?: string;
  publishedAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Enquiry {
  id: string;
  fullName: string;
  email: string;
  phone?: string;
  enquiryType: EnquiryType;
  eventDate?: string;
  estimatedGuests?: number;
  message: string;
  status: EnquiryStatus;
  notes?: string;
  createdAt: string;
}

export interface AdminUser {
  id: string;
  email: string;
  fullName: string;
  role: UserRole;
  isActive: boolean;
  lastLoginAt?: string;
}

export interface AuditLog {
  id: string;
  userId: string;
  userEmail: string;
  action: 'EVENT_CREATED' | 'SUBMITTED_FOR_REVIEW' | 'APPROVED' | 'PUBLISHED' | 'UNPUBLISHED' | 'ARCHIVED' | 'UPDATED' | 'DELETED';
  entityType: 'EVENT' | 'COLLABORATOR' | 'ENQUIRY' | 'USER';
  entityId: string;
  details?: Record<string, unknown>;
  createdAt: string;
}
