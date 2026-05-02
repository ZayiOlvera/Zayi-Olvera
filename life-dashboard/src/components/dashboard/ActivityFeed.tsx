'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { formatRelativeDate } from '@/lib/utils'

interface ActivityItem {
  id: string
  type: 'task_created' | 'task_updated' | 'task_done'
  title: string
  projectName: string
  projectColor: string
  timestamp: string
  by?: string
}

export function ActivityFeed({ initialItems }: { initialItems: ActivityItem[] }) {
  const [items, setItems] = useState<ActivityItem[]>(initialItems)
  const supabase = createClient()

  useEffect(() => {
    const channel = supabase
      .channel('activity-feed')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'tasks' },
        (payload) => {
          // Real-time task creation — add to feed
          const newItem: ActivityItem = {
            id: payload.new.id,
            type: 'task_created',
            title: payload.new.title,
            projectName: '',
            projectColor: '#6366F1',
            timestamp: payload.new.created_at,
          }
          setItems((prev) => [newItem, ...prev].slice(0, 15))
        }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'tasks' },
        (payload) => {
          if (payload.new.status === 'done' && payload.old.status !== 'done') {
            const newItem: ActivityItem = {
              id: `done-${payload.new.id}-${Date.now()}`,
              type: 'task_done',
              title: payload.new.title,
              projectName: '',
              projectColor: '#16A34A',
              timestamp: payload.new.updated_at,
            }
            setItems((prev) => [newItem, ...prev].slice(0, 15))
          }
        }
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [supabase])

  const typeConfig = {
    task_created: { icon: '➕', color: 'text-blue-400', verb: 'Tarea creada' },
    task_updated: { icon: '✏️', color: 'text-yellow-400', verb: 'Tarea actualizada' },
    task_done: { icon: '✅', color: 'text-emerald-400', verb: 'Tarea completada' },
  }

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <h2 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
        <span>⚡</span> Actividad reciente
      </h2>

      {items.length === 0 ? (
        <p className="text-zinc-500 text-sm text-center py-6">
          Sin actividad reciente
        </p>
      ) : (
        <div className="space-y-2">
          {items.map((item) => {
            const config = typeConfig[item.type]
            return (
              <div key={item.id} className="flex items-start gap-2.5 py-1.5 border-b border-zinc-800 last:border-0">
                <span className="text-sm mt-0.5">{config.icon}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-zinc-200 text-xs truncate">{item.title}</p>
                  <p className="text-zinc-500 text-xs">{config.verb}</p>
                </div>
                <span className="text-zinc-600 text-xs flex-shrink-0">
                  {formatRelativeDate(item.timestamp)}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
