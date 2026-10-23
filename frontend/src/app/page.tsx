import React from 'react';
import { fetchFeaturedEvent, fetchCollaborators } from '@/lib/api';
import HomeClientWrapper from '@/components/HomeClientWrapper';

export const revalidate = 60;

export default async function HomePage() {
  const [featuredEvent, collaborators] = await Promise.all([
    fetchFeaturedEvent(),
    fetchCollaborators(),
  ]);

  return (
    <HomeClientWrapper
      featuredEvent={featuredEvent}
      collaborators={collaborators}
    />
  );
}
