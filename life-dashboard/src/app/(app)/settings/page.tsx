import { createClient } from '@/lib/supabase/server'
import Link from 'next/link'

export const dynamic = 'force-dynamic'

export default async function SettingsPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  const { data: profile } = await supabase
    .from('profiles')
    .select('full_name, role, created_at')
    .eq('id', user!.id)
    .single()

  const { data: teamMembers } = await supabase
    .from('profiles')
    .select('id, full_name, role, created_at')
    .order('created_at', { ascending: true })

  return (
    <div className="p-6 max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Ajustes</h1>
        <p className="text-zinc-400 text-sm mt-1">Configuración de tu cuenta y el sistema</p>
      </div>

      {/* Profile */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4">
        <h2 className="text-zinc-300 text-sm font-semibold mb-3">Tu perfil</h2>
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-violet-700 flex items-center justify-center text-white text-xl font-bold">
            {(profile?.full_name || user?.email || 'U')[0].toUpperCase()}
          </div>
          <div>
            <p className="text-white font-medium">{profile?.full_name || 'Sin nombre'}</p>
            <p className="text-zinc-400 text-sm">{user?.email}</p>
            <span className="text-xs bg-violet-900 text-violet-300 px-2 py-0.5 rounded-full capitalize mt-1 inline-block">
              {profile?.role}
            </span>
          </div>
        </div>
      </div>

      {/* Team */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 mb-4">
        <h2 className="text-zinc-300 text-sm font-semibold mb-3">Equipo ({teamMembers?.length ?? 0} miembros)</h2>
        <div className="space-y-2">
          {(teamMembers ?? []).map((member) => (
            <div key={member.id} className="flex items-center justify-between py-1.5">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-zinc-700 flex items-center justify-center text-white text-xs font-bold">
                  {(member.full_name || 'U')[0].toUpperCase()}
                </div>
                <span className="text-zinc-300 text-sm">{member.full_name || 'Sin nombre'}</span>
              </div>
              <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${
                member.role === 'admin' ? 'bg-violet-900 text-violet-300' :
                member.role === 'collaborator' ? 'bg-blue-900 text-blue-300' :
                'bg-zinc-800 text-zinc-400'
              }`}>
                {member.role}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Integrations link */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
        <h2 className="text-zinc-300 text-sm font-semibold mb-3">Integraciones</h2>
        <Link
          href="/settings/integrations"
          className="flex items-center justify-between py-2 text-sm text-zinc-400 hover:text-white transition-colors"
        >
          <span>Notion + Google Calendar</span>
          <span>→</span>
        </Link>
      </div>
    </div>
  )
}
