import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Zayi Universe',
  description: 'Centro de comando personal de Zayi Olvera',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full bg-zinc-950 text-white">{children}</body>
    </html>
  )
}
