import { createClient } from '@/lib/supabase/server'
import { formatCurrency } from '@/lib/utils'

export const dynamic = 'force-dynamic'

const STAGES = [
  { key: 'prospecting', label: 'Prospectos', color: '#6366F1' },
  { key: 'qualification', label: 'Calificación', color: '#8B5CF6' },
  { key: 'proposal', label: 'Propuesta', color: '#EC4899' },
  { key: 'negotiation', label: 'Negociación', color: '#F59E0B' },
  { key: 'won', label: 'Ganados', color: '#10B981' },
  { key: 'lost', label: 'Perdidos', color: '#EF4444' },
]

export default async function CRMPage() {
  const supabase = await createClient()

  const [{ data: deals }, { data: contacts }] = await Promise.all([
    supabase
      .from('crm_deals')
      .select('id, title, value, currency, stage, probability, expected_close, crm_contacts(full_name, company), projects(name)')
      .order('position', { ascending: true }),
    supabase
      .from('crm_contacts')
      .select('id, full_name, email, company, source, created_at')
      .order('created_at', { ascending: false })
      .limit(20),
  ])

  const dealsByStage = STAGES.reduce((acc, stage) => {
    acc[stage.key] = (deals ?? []).filter((d) => d.stage === stage.key)
    return acc
  }, {} as Record<string, typeof deals>)

  const activeDeals = (deals ?? []).filter((d) => !['won', 'lost'].includes(d.stage))
  const totalPipelineValue = activeDeals.reduce((s, d) => s + (d.value ?? 0), 0)
  const wonValue = (deals ?? []).filter((d) => d.stage === 'won').reduce((s, d) => s + (d.value ?? 0), 0)

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">CRM</h1>
        <p className="text-zinc-400 text-sm mt-1">Pipeline comercial — espacio de Daniela</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Deals activos</p>
          <p className="text-2xl font-bold text-white">{activeDeals.length}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Valor en pipeline</p>
          <p className="text-2xl font-bold text-violet-400">{formatCurrency(totalPipelineValue)}</p>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
          <p className="text-zinc-400 text-xs mb-1">Cerrado ganado</p>
          <p className="text-2xl font-bold text-emerald-400">{formatCurrency(wonValue)}</p>
        </div>
      </div>

      {/* Pipeline board */}
      <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">Pipeline</h2>
      <div className="grid grid-cols-4 gap-3 mb-8 overflow-x-auto">
        {STAGES.slice(0, 4).map((stage) => {
          const stageDeals = dealsByStage[stage.key] ?? []
          return (
            <div key={stage.key} className="bg-zinc-900 border border-zinc-800 rounded-xl p-3 min-w-[200px]">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: stage.color }} />
                  <span className="text-xs font-semibold text-zinc-300">{stage.label}</span>
                </div>
                <span className="text-xs text-zinc-600 bg-zinc-800 rounded-full px-1.5 py-0.5">{stageDeals.length}</span>
              </div>
              <div className="space-y-2">
                {stageDeals?.map((deal) => {
                  const rawC = deal?.crm_contacts
                  const contact = (Array.isArray(rawC) ? rawC[0] : rawC) as { full_name: string; company: string | null } | null
                  return (
                    <div key={deal.id} className="bg-zinc-800 rounded-lg p-2.5 border border-zinc-700">
                      <p className="text-zinc-200 text-xs font-medium">{deal.title}</p>
                      {contact && (
                        <p className="text-zinc-500 text-xs mt-0.5">
                          {contact.full_name}{contact.company ? ` · ${contact.company}` : ''}
                        </p>
                      )}
                      {deal.value && (
                        <p className="text-emerald-400 text-xs mt-1 font-medium">{formatCurrency(deal.value)}</p>
                      )}
                    </div>
                  )
                })}
                {stageDeals.length === 0 && (
                  <p className="text-zinc-700 text-xs text-center py-3">Vacío</p>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Contacts */}
      <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">Contactos recientes</h2>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Nombre</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Empresa</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Email</th>
              <th className="text-left text-zinc-500 text-xs font-medium px-4 py-2">Fuente</th>
            </tr>
          </thead>
          <tbody>
            {(contacts ?? []).map((contact) => (
              <tr key={contact.id} className="border-b border-zinc-800 last:border-0">
                <td className="px-4 py-2.5 text-zinc-200 text-sm">{contact.full_name}</td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">{contact.company ?? '—'}</td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs">{contact.email ?? '—'}</td>
                <td className="px-4 py-2.5 text-zinc-500 text-xs capitalize">{contact.source ?? '—'}</td>
              </tr>
            ))}
            {(contacts ?? []).length === 0 && (
              <tr>
                <td colSpan={4} className="text-center text-zinc-500 py-8 text-sm">
                  Sin contactos aún. Pídele a la IA que cree uno.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
