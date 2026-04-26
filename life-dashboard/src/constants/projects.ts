export const PROJECTS = [
  {
    slug: 'caloncho',
    name: 'Caloncho',
    category: 'music' as const,
    color: '#7C3AED',
    icon: '🎵',
  },
  {
    slug: 'supremacy-studios',
    name: 'Supremacy Studios',
    category: 'production' as const,
    color: '#DC2626',
    icon: '🎬',
  },
  {
    slug: 'supremacy-rentals',
    name: 'Supremacy Rentals',
    category: 'business' as const,
    color: '#B91C1C',
    icon: '🎥',
  },
  {
    slug: 'camp-league',
    name: 'Camp League',
    category: 'music' as const,
    color: '#0891B2',
    icon: '🎤',
  },
  {
    slug: 'garden-sessions',
    name: 'Garden Sessions',
    category: 'creative' as const,
    color: '#16A34A',
    icon: '🌿',
  },
  {
    slug: 'clases-psicologia',
    name: 'Clases de Psicología',
    category: 'education' as const,
    color: '#D97706',
    icon: '🧠',
  },
  {
    slug: 'instituto-olvera',
    name: 'Instituto Olvera',
    category: 'education' as const,
    color: '#2563EB',
    icon: '🏫',
  },
  {
    slug: 'guiones-personales',
    name: 'Guiones Personales',
    category: 'creative' as const,
    color: '#DB2777',
    icon: '✍️',
  },
] as const

export type ProjectSlug = typeof PROJECTS[number]['slug']

export const PROJECT_BY_SLUG = Object.fromEntries(
  PROJECTS.map((p) => [p.slug, p])
) as Record<ProjectSlug, typeof PROJECTS[number]>
