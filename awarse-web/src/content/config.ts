import { defineCollection, z } from 'astro:content';

const docs = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string().max(65),
    description: z.string().min(50).max(160),
    keywords: z.array(z.string()),
    category: z.enum(['healwright', 'seatprune', 'architecture', 'overview']),
    lastModified: z.coerce.date(),
    canonicalUrl: z.string().url().optional(),
  }),
});

export const collections = { docs };
