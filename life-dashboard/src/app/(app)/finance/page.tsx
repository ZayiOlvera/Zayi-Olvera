import { createClient } from '@/lib/supabase/server'
import { formatCurrency } from '@/lib/utils'

export const dynamic = 'force-dynamic'

export default async function FinancePage() {
  const supabase = await createClient()

  const startOfYear = `${new Date().getFullYear()}-01-01`

  const [{ data: transactions }, { data: projects }] = await Promise.all([
    supabase
      .from('finance_transactions')
      .select('id, type, amount, category, description, date, project_id, projects(name, color)')
      .gte('date', startOfYear)
      .order('date', { ascending: false })
      .limit(50),
    supabase
      .from('projects')
      .select('id, name, color, slug')
      .eq('status', 'active'),
  ])

  const allTx = transactions ?? []
  const totalIncome = allTx.filter((t) => t.type === 'income').reduce((s, t) => s + t.amount, 0)
  const totalExpense = allTx.filter((t) => t.type === 'expense').reduce((s, t) => s + t.amount, 0)
  const net = totalIncome - totalExpense

  const projectSummary = (projects ?? []).map((p) => {
    const ptx = allTx.filter((t) => t.project_id === p.id)
    return {
      ...p,
      income: ptx.filter((t) => t.type === 'income').reduce((s, t) => s + t.amount, 0),
      expense: ptx.filter((t) => t.type === 'expense').reduce((s, t) => s + t.amount, 0),
    }
  }).filter((p) => p.income > 0 || p.expense > 0)

  return (
    <div className="p-6 max-w-5xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Finanzas</h1>
        <p className="text-zinc-400 text-sm mt-1">Resumen del año {new Date().getFullYear()}</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Ingresos YTD</p>
          <p className="text-2xl font-bold text-emerald-400">{formatCurrency(totalIncome)}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Gastos YTD</p>
          <p className="text-2xl font-bold text-red-400">{formatCurrency(totalExpense)}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Neto YTD</p>
          <p className={`text-2xl font-bold ${net >= 0 ? 'text-white' : 'text-red-400'}`}>{formatCurrency(net)}</p>
        </div>
      </div>

      {/* Per-project breakdown */}
      {projectSummary.length > 0 && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden mb-6">
          <div className="px-4 py-3 border-b border-zinc-800">
            <h2 className="text-zinc-300 text-sm font-semibold">Por proyecto</h2>
          </div>
          <table className="w-full">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Proyecto</th>
                <th className="text-right text-zinc-500 text-xs font-medium px-4 py-2">Ingresos</th>
                <th className="text-right text-zinc-500 text-xs font-medium px-4 py-2">Gastos</th>
                <th className="text-right text-zinc-500 text-xs font-medium px-4 py-2">Neto</th>
              </tr>
            </thead>
            <tbody>
              {projectSummary.map((p) => (
                <tr key={p.id} className="border-b border-zinc-800 last:border-0">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full" style={{ backgroundColor: p.color }} />
                      <span className="text-zinc-200 text-sm">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right text-emerald-400 text-sm">{formatCurrency(p.income)}</td>
                  <td className="px-4 py-3 text-right text-red-400 text-sm">{formatCurrency(p.expense)}</td>
                  <td className={`px-4 py-3 text-right text-sm font-medium ${p.income - p.expense >= 0 ? 'text-white' : 'text-red-400'}`}>
                    {formatCurrency(p.income - p.expense)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Transaction list */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
          <h2 className="text-zinc-300 text-sm font-semibold">Movimientos recientes</h2>
          <span className="text-zinc-600 text-xs">{allTx.length} movimientos</span>
        </div>
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Descripción</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Proyecto</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Categoría</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Fecha</th>
              <th className="text-right text-zinc-500 text-xs font-medium px-4 py-2">Monto</th>
            </tr>
          </thead>
          <tbody>
            {allTx.map((t) => {
              const rawP = t.projects
              const project = (Array.isArray(rawP) ? rawP[0] : rawP) as { name: string; color: string } | null
              return (
                <tr key={t.id} className="border-b border-zinc-800 last:border-0">
                  <td className="px-4 py-2.5 text-zinc-200 text-xs">{t.description}</td>
                  <td className="px-4 py-2.5">
                    {project && (
                      <div className="flex items-center gap-1.5">
                        <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: project.color }} />
                        <span className="text-zinc-500 text-xs">{project.name}</span>
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-zinc-500 text-xs capitalize">{t.category}</td>
                  <td className="px-4 py-2.5 text-zinc-500 text-xs">
                    {new Date(t.date).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}
                  </td>
                  <td className={`px-4 py-2.5 text-xs text-right font-medium ${t.type === 'income' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {t.type === 'income' ? '+' : '-'}{formatCurrency(t.amount)}
                  </td>
                </tr>
              )
            })}
            {allTx.length === 0 && (
              <tr>
                <td colSpan={5} className="text-center text-zinc-500 py-10 text-sm">
                  Sin movimientos registrados. Puedes pedirle a la IA que registre uno.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
