import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { Sidebar } from '@/components/layout/Sidebar'
import { TopBar } from '@/components/layout/TopBar'
import { AIAssistant } from '@/components/ai/AIAssistant'

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient()

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) redirect('/login')

  const { data: profile } = await supabase
    .from('profiles')
    .select('full_name, role')
    .eq('id', user.id)
    .single()

  return (
    <div className="min-h-screen bg-zinc-950 text-white">
      <Sidebar />
      <div className="ml-60">
        <TopBar
          userEmail={user.email}
          userName={profile?.full_name}
          userRole={profile?.role}
        />
        <main className="pt-14 min-h-screen">
          {children}
        </main>
      </div>
      <AIAssistant />
    </div>
  )
}
