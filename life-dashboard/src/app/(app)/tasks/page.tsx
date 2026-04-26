import { createClient } from '@/lib/supabase/server'

export const dynamic = 'force-dynamic'

export default async function TasksPage() {
  const supabase = await createClient()

  const { data: tasks } = await supabase
    .from('tasks')
    .select('id, title, status, priority, due_date, created_at, projects(name, color, slug)')
    .not('status', 'in', '("done","cancelled")')
    .order('due_date', { ascending: true, nullsFirst: false })
    .limit(50)

  const priorityIcon: Record<string, string> = { urgent: '🔴', high: '🟠', medium: '🟡', low: '🟢' }
  const statusLabel: Record<string, string> = { todo: 'Por hacer', in_progress: 'En curso', review: 'En revisión' }

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Todas las tareas</h1>
        <p className="text-zinc-400 text-sm mt-1">Tareas abiertas en todos tus proyectos</p>
      </div>

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left text-zinc-500 text-xs font-semibold uppercase px-4 py-3 tracking-wide">Tarea</th>
              <th className="text-left text-zinc-500 text-xs font-semibold uppercase px-4 py-3 tracking-wide">Proyecto</th>
              <th className="text-left text-zinc-500 text-xs font-semibold uppercase px-4 py-3 tracking-wide">Estado</th>
              <th className="text-left text-zinc-500 text-xs font-semibold uppercase px-4 py-3 tracking-wide">Prioridad</th>
              <th className="text-left text-zinc-500 text-xs font-semibold uppercase px-4 py-3 tracking-wide">Fecha límite</th>
            </tr>
          </thead>
          <tbody>
            {(tasks ?? []).map((task) => {
              const raw = task.projects
              const project = (Array.isArray(raw) ? raw[0] : raw) as { name: string; color: string; slug: string } | null
              const isOverdue = task.due_date && new Date(task.due_date) < new Date()
              return (
                <tr key={task.id} className="border-b border-zinc-800 last:border-0 hover:bg-zinc-800/30 transition-colors">
                  <td className="px-4 py-3">
                    <p className="text-zinc-200 text-sm">{task.title}</p>
                  </td>
                  <td className="px-4 py-3">
                    {project && (
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: project.color }} />
                        <span className="text-zinc-400 text-xs">{project.name}</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs text-zinc-400">
                      {statusLabel[task.status] ?? task.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm">{priorityIcon[task.priority] ?? '🟡'}</span>
                  </td>
                  <td className="px-4 py-3">
                    {task.due_date ? (
                      <span className={`text-xs ${isOverdue ? 'text-red-400 font-medium' : 'text-zinc-400'}`}>
                        {isOverdue ? '⚠️ ' : ''}
                        {new Date(task.due_date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short', year: 'numeric' })}
                      </span>
                    ) : (
                      <span className="text-zinc-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              )
            })}
            {(tasks ?? []).length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-zinc-500 py-12 text-sm">
                  ¡No hay tareas pendientes! 🎉
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
