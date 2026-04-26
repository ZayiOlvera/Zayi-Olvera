'use client'

import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

interface TopBarProps {
  userEmail?: string
  userName?: string
  userRole?: string
}

export function TopBar({ userEmail, userName, userRole }: TopBarProps) {
  const router = useRouter()

  async function handleSignOut() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  const roleColors = {
    admin: 'bg-violet-900 text-violet-300',
    collaborator: 'bg-blue-900 text-blue-300',
    viewer: 'bg-zinc-800 text-zinc-400',
    project_member: 'bg-zinc-800 text-zinc-400',
  }

  return (
    <header className="h-14 border-b border-zinc-800 bg-zinc-950 flex items-center justify-between px-6 fixed top-0 right-0 left-60 z-10">
      <div className="flex items-center gap-2">
        <span className="text-zinc-400 text-sm">
          {new Date().toLocaleDateString('es-MX', { weekday: 'long', day: 'numeric', month: 'long' })}
        </span>
      </div>

      <div className="flex items-center gap-3">
        {userRole && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded-full capitalize ${roleColors[userRole as keyof typeof roleColors] ?? 'bg-zinc-800 text-zinc-400'}`}>
            {userRole}
          </span>
        )}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-violet-700 flex items-center justify-center text-white text-sm font-bold">
            {(userName || userEmail || 'U')[0].toUpperCase()}
          </div>
          <div className="hidden sm:block">
            <p className="text-white text-sm font-medium leading-none">{userName || userEmail}</p>
          </div>
        </div>
        <button
          onClick={handleSignOut}
          className="text-zinc-400 hover:text-white text-sm transition-colors"
          title="Cerrar sesión"
        >
          ↗
        </button>
      </div>
    </header>
  )
}
