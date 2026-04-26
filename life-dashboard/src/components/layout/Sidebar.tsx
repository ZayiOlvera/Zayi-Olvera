'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { PROJECTS } from '@/constants/projects'

const NAV_ITEMS = [
  { href: '/dashboard', label: 'Dashboard', icon: '⚡' },
  { href: '/tasks', label: 'Tareas', icon: '✅' },
  { href: '/finance', label: 'Finanzas', icon: '💰' },
  { href: '/crm', label: 'CRM', icon: '🤝' },
  { href: '/settings', label: 'Ajustes', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed left-0 top-0 h-full w-60 bg-zinc-900 border-r border-zinc-800 flex flex-col z-20">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-zinc-800">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="text-2xl">⚡</span>
          <div>
            <p className="text-white font-bold text-sm leading-none">Zayi Universe</p>
            <p className="text-zinc-500 text-xs mt-0.5">Centro de comando</p>
          </div>
        </Link>
      </div>

      {/* Main nav */}
      <nav className="px-3 py-3 space-y-0.5">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors',
              pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href))
                ? 'bg-zinc-800 text-white font-medium'
                : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
            )}
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>

      {/* Projects */}
      <div className="px-3 pt-4 pb-2 flex-1 overflow-y-auto">
        <p className="text-zinc-500 text-xs font-semibold uppercase tracking-wider px-3 mb-2">
          Proyectos
        </p>
        <div className="space-y-0.5">
          {PROJECTS.map((project) => (
            <Link
              key={project.slug}
              href={`/projects/${project.slug}`}
              className={cn(
                'flex items-center gap-2.5 px-3 py-1.5 rounded-lg text-sm transition-colors',
                pathname === `/projects/${project.slug}`
                  ? 'bg-zinc-800 text-white'
                  : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
              )}
            >
              <span
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ backgroundColor: project.color }}
              />
              <span className="truncate">{project.name}</span>
            </Link>
          ))}
        </div>
      </div>
    </aside>
  )
}
