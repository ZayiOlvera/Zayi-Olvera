-- Seed the 8 projects for Zayi Olvera
-- Note: owner_id will need to be updated after first user signs up (or set via dashboard)

INSERT INTO projects (slug, name, description, category, status, color, icon) VALUES
  ('caloncho',           'Caloncho',              'Proyecto musical principal', 'music',      'active', '#7C3AED', '🎵'),
  ('supremacy-studios',  'Supremacy Studios',      'Compañía de producción audiovisual', 'production', 'active', '#DC2626', '🎬'),
  ('supremacy-rentals',  'Supremacy Rentals',      'Renta de equipo audiovisual', 'business',   'active', '#B91C1C', '🎥'),
  ('camp-league',        'Camp League',            'Proyecto de competencia musical', 'music',  'active', '#0891B2', '🎤'),
  ('garden-sessions',    'Garden Sessions',        'Sesiones creativas en vivo', 'creative',   'active', '#16A34A', '🌿'),
  ('clases-psicologia',  'Clases de Psicología',  'Servicio educativo de psicología', 'education', 'active', '#D97706', '🧠'),
  ('instituto-olvera',   'Instituto Olvera',       'Instituto educativo', 'education',          'active', '#2563EB', '🏫'),
  ('guiones-personales', 'Guiones Personales',     'Proyectos de escritura de guiones', 'creative', 'active', '#DB2777', '✍️')
ON CONFLICT (slug) DO NOTHING;
