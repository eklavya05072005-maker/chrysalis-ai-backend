import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://urben.entt';

  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/event-admin', '/api/admin', '/api/auth'],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
