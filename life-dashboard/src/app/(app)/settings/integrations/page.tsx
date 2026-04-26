import { createClient } from '@/lib/supabase/server'
import { PROJECTS } from '@/constants/projects'

export const dynamic = 'force-dynamic'

export default async function IntegrationsPage() {
  const supabase = await createClient()

  const { data: projects } = await supabase
    .from('projects')
    .select('id, slug, name, notion_db_id, notion_last_sync')
    .order('name', { ascending: true })

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Integraciones</h1>
        <p className="text-zinc-400 text-sm mt-1">Conecta Notion y Google Calendar</p>
      </div>

      {/* Notion */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">N</span>
          <h2 className="text-zinc-300 text-sm font-semibold">Notion</h2>
        </div>
        <p className="text-zinc-500 text-xs mb-4">
          Conecta cada proyecto con una base de datos de Notion para sincronizar tareas.
          Pega la URL de la base de datos de Notion para cada proyecto.
        </p>
        <div className="space-y-3">
          {(projects ?? []).map((project) => {
            const meta = PROJECTS.find((p) => p.slug === project.slug)
            return (
              <div key={project.id} className="flex items-center gap-3">
                <span className="text-base w-6 text-center">{meta?.icon ?? '📁'}</span>
                <span className="text-zinc-300 text-xs w-36 truncate">{project.name}</span>
                <div className="flex-1 relative">
                  {project.notion_db_id ? (
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-emerald-400">✓ Conectado</span>
                      {project.notion_last_sync && (
                        <span className="text-zinc-600 text-xs">
                          · sync {new Date(project.notion_last_sync).toLocaleDateString('es-MX')}
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-xs text-zinc-600">Sin conectar</span>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        <p className="text-zinc-600 text-xs mt-4">
          Para conectar, pídele a la IA: "Conecta el proyecto Caloncho con esta base de datos de Notion: [URL]"
        </p>
      </div>

      {/* Google Calendar */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-4">
          <span className="text-lg">📅</span>
          <h2 className="text-zinc-300 text-sm font-semibold">Google Calendar</h2>
        </div>
        <p className="text-zinc-500 text-xs mb-4">
          Conecta tu Google Calendar para ver y crear eventos desde el dashboard.
        </p>
        <a
          href="/api/google-calendar/auth"
          className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 text-sm rounded-lg transition-colors"
        >
          Conectar Google Calendar →
        </a>
      </div>
    </div>
  )
}
