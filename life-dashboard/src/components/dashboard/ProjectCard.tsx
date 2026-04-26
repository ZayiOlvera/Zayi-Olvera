'use client'

import Link from 'next/link'
import { useState } from 'react'
import { formatCurrency, formatRelativeDate } from '@/lib/utils'
import { createClient } from '@/lib/supabase/client'

interface ProjectCardProps {
  id: string
  slug: string
  name: string
  status: string
  color: string
  icon: string
  category: string
  todoCount: number
  inProgressCount: number
  doneCount: number
  nextDueDate: string | null
  mtdIncome: number
  mtdExpense: number
  notionDbId: string | null
  notionLastSync: string | null
}

export function ProjectCard({
  id,
  slug,
  name,
  status,
  color,
  icon,
  todoCount,
  inProgressCount,
  doneCount,
  nextDueDate,
  mtdIncome,
  mtdExpense,
  notionDbId,
  notionLastSync,
}: ProjectCardProps) {
  const [quickTask, setQuickTask] = useState('')
  const [adding, setAdding] = useState(false)
  const [tasks, setTasks] = useState({ todo: todoCount, inProgress: inProgressCount, done: doneCount })

  async function handleQuickAdd(e: React.FormEvent) {
    e.preventDefault()
    if (!quickTask.trim() || adding) return
    setAdding(true)

    const supabase = createClient()
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { setAdding(false); return }

    const { error } = await supabase.from('tasks').insert({
      project_id: id,
      title: quickTask.trim(),
      status: 'todo',
      priority: 'medium',
      created_by: user.id,
    })

    if (!error) {
      setTasks((prev) => ({ ...prev, todo: prev.todo + 1 }))
      setQuickTask('')
    }
    setAdding(false)
  }

  const netMTD = mtdIncome - mtdExpense
  const totalTasks = tasks.todo + tasks.inProgress + tasks.done

  const statusConfig = {
    active: { label: 'Activo', color: 'bg-emerald-900 text-emerald-400' },
    paused: { label: 'Pausado', color: 'bg-yellow-900 text-yellow-400' },
    completed: { label: 'Completado', color: 'bg-blue-900 text-blue-400' },
    archived: { label: 'Archivado', color: 'bg-zinc-800 text-zinc-500' },
  }

  const statusInfo = statusConfig[status as keyof typeof statusConfig] ?? statusConfig.active

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden hover:border-zinc-700 transition-colors group">
      {/* Color accent bar */}
      <div className="h-1 w-full" style={{ backgroundColor: color }} />

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <Link href={`/projects/${slug}`} className="flex items-center gap-2 group-hover:opacity-90">
            <span className="text-xl">{icon}</span>
            <div>
              <h3 className="text-white font-semibold text-sm leading-tight">{name}</h3>
            </div>
          </Link>
          <span className={`text-xs font-medium px-1.5 py-0.5 rounded-full ${statusInfo.color}`}>
            {statusInfo.label}
          </span>
        </div>

        {/* Task counts */}
        <div className="flex gap-3 mb-3">
          <div className="text-center">
            <p className="text-xl font-bold text-white">{tasks.todo}</p>
            <p className="text-xs text-zinc-500">Por hacer</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-blue-400">{tasks.inProgress}</p>
            <p className="text-xs text-zinc-500">En curso</p>
          </div>
          <div className="text-center">
            <p className="text-xl font-bold text-emerald-400">{tasks.done}</p>
            <p className="text-xs text-zinc-500">Hechas</p>
          </div>
        </div>

        {/* Progress bar */}
        {totalTasks > 0 && (
          <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden mb-3">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${(tasks.done / totalTasks) * 100}%`,
                backgroundColor: color,
              }}
            />
          </div>
        )}

        {/* Finance MTD */}
        {(mtdIncome > 0 || mtdExpense > 0) && (
          <div className="flex items-center justify-between text-xs mb-3">
            <span className="text-emerald-400">+{formatCurrency(mtdIncome)}</span>
            <span className={netMTD >= 0 ? 'text-zinc-400' : 'text-red-400'}>
              {netMTD >= 0 ? '↑' : '↓'} {formatCurrency(Math.abs(netMTD))} neto
            </span>
          </div>
        )}

        {/* Next deadline */}
        {nextDueDate && (
          <div className="text-xs text-zinc-500 mb-3 flex items-center gap-1">
            <span>🗓</span>
            <span>Próximo: <span className="text-zinc-300">{formatRelativeDate(nextDueDate)}</span></span>
          </div>
        )}

        {/* Quick add task */}
        <form onSubmit={handleQuickAdd}>
          <input
            type="text"
            value={quickTask}
            onChange={(e) => setQuickTask(e.target.value)}
            placeholder="+ Añadir tarea..."
            className="w-full bg-zinc-800 hover:bg-zinc-700/80 focus:bg-zinc-800 border border-transparent focus:border-zinc-600 rounded-lg px-3 py-1.5 text-xs text-zinc-300 placeholder-zinc-600 focus:outline-none transition-colors"
            disabled={adding}
          />
        </form>

        {/* Notion sync indicator */}
        {notionDbId && (
          <div className="mt-2 flex items-center gap-1 text-xs text-zinc-600">
            <span>N</span>
            <span>{notionLastSync ? `Sync ${formatRelativeDate(notionLastSync)}` : 'Sin sync'}</span>
          </div>
        )}
      </div>
    </div>
  )
}
