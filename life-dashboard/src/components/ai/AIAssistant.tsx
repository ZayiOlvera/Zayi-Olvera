'use client'

import { useState, useRef, useEffect } from 'react'
import { VoiceButton } from './VoiceButton'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  toolCalls?: string[]
}

export function AIAssistant() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTool, setActiveTool] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 100)
    }
  }, [open])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text?: string) {
    const content = (text ?? input).trim()
    if (!content || loading) return

    const userMessage: Message = { role: 'user', content }
    const newMessages = [...messages, userMessage]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    setActiveTool(null)

    try {
      const response = await fetch('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMessages.map((m) => ({
            role: m.role,
            content: m.content,
          })),
        }),
      })

      if (!response.ok) throw new Error('Error en la respuesta')
      if (!response.body) throw new Error('No body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let assistantText = ''
      const toolCalls: string[] = []

      setMessages((prev) => [...prev, { role: 'assistant', content: '', toolCalls: [] }])

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') continue

          try {
            const parsed = JSON.parse(data)
            if (parsed.type === 'text') {
              assistantText += parsed.text
              setMessages((prev) => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                  role: 'assistant',
                  content: assistantText,
                  toolCalls,
                }
                return updated
              })
            } else if (parsed.type === 'tool_start') {
              toolCalls.push(parsed.name)
              setActiveTool(parsed.name)
              setMessages((prev) => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  toolCalls: [...toolCalls],
                }
                return updated
              })
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Lo siento, hubo un error. Por favor intenta de nuevo.' },
      ])
      console.error(err)
    } finally {
      setLoading(false)
      setActiveTool(null)
    }
  }

  const toolLabels: Record<string, string> = {
    create_task: 'Creando tarea...',
    list_tasks: 'Consultando tareas...',
    update_task: 'Actualizando tarea...',
    get_overdue_tasks: 'Revisando tareas vencidas...',
    get_project_summary: 'Revisando proyectos...',
    get_financial_summary: 'Analizando finanzas...',
    add_transaction: 'Registrando movimiento...',
    get_pipeline_summary: 'Consultando pipeline...',
    create_contact: 'Creando contacto...',
    update_deal_stage: 'Actualizando deal...',
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          'fixed bottom-6 right-6 w-14 h-14 rounded-full shadow-2xl flex items-center justify-center text-2xl transition-all z-50',
          open ? 'bg-zinc-800 rotate-45' : 'bg-violet-600 hover:bg-violet-500'
        )}
        title="Asistente IA"
      >
        {open ? '✕' : '⚡'}
      </button>

      {/* Chat panel */}
      {open && (
        <div className="fixed bottom-24 right-6 w-96 h-[520px] bg-zinc-900 border border-zinc-700 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 border-b border-zinc-800 flex items-center gap-2">
            <span className="text-lg">⚡</span>
            <div>
              <p className="text-white font-semibold text-sm">Jefe de Gabinete</p>
              <p className="text-zinc-500 text-xs">IA de Zayi Universe</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {messages.length === 0 && (
              <div className="text-center text-zinc-500 text-sm pt-8 space-y-3">
                <p className="text-3xl">⚡</p>
                <p className="font-medium text-zinc-400">¿En qué te ayudo?</p>
                <div className="space-y-1 text-xs text-zinc-600">
                  <p>"¿Qué tareas tengo pendientes?"</p>
                  <p>"Crea una tarea en Caloncho para el lunes"</p>
                  <p>"¿Cuánto hemos ingresado este mes?"</p>
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={cn(
                  'max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed',
                  msg.role === 'user'
                    ? 'ml-auto bg-violet-600 text-white'
                    : 'bg-zinc-800 text-zinc-200'
                )}
              >
                {msg.toolCalls && msg.toolCalls.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-1">
                    {msg.toolCalls.map((tool, ti) => (
                      <span key={ti} className="text-xs bg-zinc-700 text-zinc-400 px-1.5 py-0.5 rounded">
                        🔧 {tool.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
                {msg.content || (loading && i === messages.length - 1 ? (
                  <span className="text-zinc-500">{activeTool ? toolLabels[activeTool] : 'Pensando...'}</span>
                ) : null)}
              </div>
            ))}

            {loading && messages[messages.length - 1]?.role !== 'assistant' && (
              <div className="max-w-[85%] bg-zinc-800 rounded-xl px-3 py-2 text-sm text-zinc-500">
                {activeTool ? toolLabels[activeTool] : 'Pensando...'}
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-zinc-800 flex gap-2">
            <VoiceButton
              onTranscript={(text) => {
                setInput(text)
                setTimeout(() => sendMessage(text), 100)
              }}
            />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
              placeholder="Escribe o usa el micrófono..."
              className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-sm text-white placeholder-zinc-500 focus:outline-none focus:border-violet-500"
              disabled={loading}
            />
            <button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              className="px-3 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 disabled:cursor-not-allowed text-white rounded-xl text-sm transition-colors"
            >
              →
            </button>
          </div>
        </div>
      )}
    </>
  )
}
