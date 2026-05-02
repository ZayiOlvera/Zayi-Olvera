import { formatRelativeDate } from '@/lib/utils'

interface UpcomingTask {
  task_id: string
  task_title: string
  task_status: string
  task_priority: string
  due_date: string
  project_name: string
  project_color: string
  assignee_name: string | null
}

interface UpcomingDeadlinesProps {
  tasks: UpcomingTask[]
}

const priorityConfig = {
  urgent: { label: '🔴', class: 'text-red-400' },
  high: { label: '🟠', class: 'text-orange-400' },
  medium: { label: '🟡', class: 'text-yellow-400' },
  low: { label: '🟢', class: 'text-emerald-400' },
}

export function UpcomingDeadlines({ tasks }: UpcomingDeadlinesProps) {
  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
      <h2 className="text-white font-semibold text-sm mb-3 flex items-center gap-2">
        <span>🗓</span> Próximos 14 días
      </h2>

      {tasks.length === 0 ? (
        <p className="text-zinc-500 text-sm text-center py-6">
          Sin deadlines próximos 🎉
        </p>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => (
            <div
              key={task.task_id}
              className="flex items-start gap-3 py-2 border-b border-zinc-800 last:border-0"
            >
              <div
                className="w-1 self-stretch rounded-full flex-shrink-0 mt-0.5"
                style={{ backgroundColor: task.project_color }}
              />
              <div className="flex-1 min-w-0">
                <p className="text-zinc-200 text-xs font-medium truncate">{task.task_title}</p>
                <p className="text-zinc-500 text-xs">{task.project_name}</p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-zinc-300 text-xs">{formatRelativeDate(task.due_date)}</p>
                <span className={`text-xs ${priorityConfig[task.task_priority as keyof typeof priorityConfig]?.class ?? ''}`}>
                  {priorityConfig[task.task_priority as keyof typeof priorityConfig]?.label}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
