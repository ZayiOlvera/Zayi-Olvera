import { formatCurrency } from '@/lib/utils'

interface DashboardStatsProps {
  totalOpenTasks: number
  totalInProgress: number
  totalMtdIncome: number
  nextDeadlineDate: string | null
  dealsInPipeline: number
}

export function DashboardStats({
  totalOpenTasks,
  totalInProgress,
  totalMtdIncome,
  nextDeadlineDate,
  dealsInPipeline,
}: DashboardStatsProps) {
  const stats = [
    {
      label: 'Tareas abiertas',
      value: totalOpenTasks.toString(),
      sub: `${totalInProgress} en curso`,
      color: 'text-white',
      icon: '✅',
    },
    {
      label: 'Ingresos MTM',
      value: formatCurrency(totalMtdIncome),
      sub: 'este mes',
      color: 'text-emerald-400',
      icon: '💰',
    },
    {
      label: 'Deals activos',
      value: dealsInPipeline.toString(),
      sub: 'en pipeline',
      color: 'text-blue-400',
      icon: '🤝',
    },
    {
      label: 'Próximo deadline',
      value: nextDeadlineDate
        ? new Date(nextDeadlineDate).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })
        : '—',
      sub: nextDeadlineDate ? 'próxima fecha' : 'sin fechas próximas',
      color: nextDeadlineDate ? 'text-yellow-400' : 'text-zinc-500',
      icon: '🗓',
    },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
        >
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{stat.icon}</span>
            <p className="text-zinc-400 text-xs font-medium">{stat.label}</p>
          </div>
          <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          <p className="text-zinc-600 text-xs mt-0.5">{stat.sub}</p>
        </div>
      ))}
    </div>
  )
}
