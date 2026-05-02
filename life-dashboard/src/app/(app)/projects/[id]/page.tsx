import { createClient } from '@/lib/supabase/server'
import { notFound } from 'next/navigation'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

interface Props {
  params: Promise<{ id: string }>
}

export default async function ProjectPage({ params }: Props) {
  const { id } = await params
  const supabase = await createClient()

  const { data: project } = await supabase
    .from('projects')
    .select('*')
    .eq('slug', id)
    .single()

  if (!project) notFound()

  const [{ data: tasks }, { data: transactions }] = await Promise.all([
    supabase
      .from('tasks')
      .select('id, title, status, priority, due_date, assignee_id')
      .eq('project_id', project.id)
      .order('created_at', { ascending: false })
      .limit(20),
    supabase
      .from('finance_transactions')
      .select('id, type, amount, category, description, date')
      .eq('project_id', project.id)
      .order('date', { ascending: false })
      .limit(10),
  ])

  const todoTasks = (tasks ?? []).filter((t) => t.status === 'todo')
  const inProgressTasks = (tasks ?? []).filter((t) => t.status === 'in_progress')
  const doneTasks = (tasks ?? []).filter((t) => t.status === 'done')

  const statusConfig: Record<string, { label: string; class: string }> = {
    todo: { label: 'Por hacer', class: 'bg-zinc-800 text-zinc-400' },
    in_progress: { label: 'En curso', class: 'bg-blue-900 text-blue-400' },
    review: { label: 'En revisión', class: 'bg-yellow-900 text-yellow-400' },
    done: { label: 'Hecho', class: 'bg-emerald-900 text-emerald-400' },
    cancelled: { label: 'Cancelado', class: 'bg-zinc-800 text-zinc-600' },
  }

  const priorityIcon: Record<string, string> = {
    urgent: '🔴',
    high: '🟠',
    medium: '🟡',
    low: '🟢',
  }

  return (
    <div className="p-6 max-w-6xl">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm text-zinc-500 mb-4">
        <Link href="/dashboard" className="hover:text-white transition-colors">Dashboard</Link>
        <span>/</span>
        <span className="text-zinc-300">{project.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl" style={{ backgroundColor: project.color + '20', border: `2px solid ${project.color}` }}>
          {project.icon}
        </div>
        <div>
          <h1 className="text-2xl font-bold text-white">{project.name}</h1>
          <p className="text-zinc-400 text-sm">{project.description}</p>
        </div>
        <div className="ml-auto">
          <span
            className={`text-xs font-medium px-2 py-1 rounded-full ${
              project.status === 'active' ? 'bg-emerald-900 text-emerald-400' : 'bg-zinc-800 text-zinc-400'
            }`}
          >
            {project.status === 'active' ? 'Activo' : project.status}
          </span>
        </div>
      </div>

      {/* Task Kanban */}
      <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">Tareas</h2>
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Por hacer', tasks: todoTasks, key: 'todo' },
          { label: 'En curso', tasks: inProgressTasks, key: 'in_progress' },
          { label: 'Completado', tasks: doneTasks, key: 'done' },
        ].map((col) => (
          <div key={col.key} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-zinc-400 text-xs font-semibold uppercase tracking-wide">{col.label}</span>
              <span className="text-zinc-600 text-xs bg-zinc-800 rounded-full px-2 py-0.5">{col.tasks.length}</span>
            </div>
            <div className="space-y-2">
              {col.tasks.map((task) => (
                <div key={task.id} className="bg-zinc-800 rounded-lg p-2.5">
                  <div className="flex items-start gap-2">
                    <span className="text-xs mt-0.5">{priorityIcon[task.priority] ?? '🟡'}</span>
                    <p className="text-zinc-200 text-xs leading-relaxed">{task.title}</p>
                  </div>
                  {task.due_date && (
                    <p className="text-zinc-600 text-xs mt-1 ml-5">
                      📅 {new Date(task.due_date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}
                    </p>
                  )}
                </div>
              ))}
              {col.tasks.length === 0 && (
                <p className="text-zinc-700 text-xs text-center py-2">Sin tareas</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Finance summary */}
      {(transactions ?? []).length > 0 && (
        <>
          <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">Finanzas recientes</h2>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Descripción</th>
                  <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Categoría</th>
                  <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Fecha</th>
                  <th className="text-right text-zinc-500 text-xs font-medium px-4 py-2">Monto</th>
                </tr>
              </thead>
              <tbody>
                {(transactions ?? []).map((t) => (
                  <tr key={t.id} className="border-b border-zinc-800 last:border-0">
                    <td className="px-4 py-2 text-zinc-300 text-xs">{t.description}</td>
                    <td className="px-4 py-2 text-zinc-500 text-xs">{t.category}</td>
                    <td className="px-4 py-2 text-zinc-500 text-xs">
                      {new Date(t.date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}
                    </td>
                    <td className={`px-4 py-2 text-xs text-right font-medium ${t.type === 'income' ? 'text-emerald-400' : 'text-red-400'}`}>
                      {t.type === 'income' ? '+' : '-'}${t.amount.toLocaleString('es-MX')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
