import Anthropic from '@anthropic-ai/sdk'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { NextRequest } from 'next/server'
import { SYSTEM_PROMPT } from '@/lib/ai/system-prompt'
import { AI_TOOLS, handleToolCall } from '@/lib/ai/tools'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })

export async function POST(req: NextRequest) {
  // Authenticate
  const cookieStore = await cookies()
  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value, options }) => cookieStore.set(name, value, options))
        },
      },
    }
  )

  const { data: { user } } = await supabase.auth.getUser()
  if (!user) {
    return new Response('Unauthorized', { status: 401 })
  }

  const { messages } = await req.json() as { messages: Anthropic.MessageParam[] }

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      try {
        // Agentic loop: keep going until end_turn or no more tool calls
        let currentMessages = messages
        let iterations = 0
        const MAX_ITERATIONS = 10

        while (iterations < MAX_ITERATIONS) {
          iterations++

          const response = await anthropic.messages.create({
            model: 'claude-sonnet-4-6',
            max_tokens: 4096,
            system: [
              {
                type: 'text',
                text: SYSTEM_PROMPT,
                cache_control: { type: 'ephemeral' },
              },
            ],
            tools: AI_TOOLS.map((tool) => ({
              ...tool,
              cache_control: iterations === 1 ? { type: 'ephemeral' as const } : undefined,
            })),
            messages: currentMessages,
          })

          // Stream text blocks
          for (const block of response.content) {
            if (block.type === 'text') {
              const chunk = JSON.stringify({ type: 'text', text: block.text })
              controller.enqueue(encoder.encode(`data: ${chunk}\n\n`))
            } else if (block.type === 'tool_use') {
              const chunk = JSON.stringify({ type: 'tool_start', name: block.name })
              controller.enqueue(encoder.encode(`data: ${chunk}\n\n`))
            }
          }

          if (response.stop_reason === 'end_turn') break

          if (response.stop_reason === 'tool_use') {
            // Execute tools
            const toolResults: Anthropic.ToolResultBlockParam[] = []

            for (const block of response.content) {
              if (block.type === 'tool_use') {
                const result = await handleToolCall(block.name, block.input as Record<string, unknown>, user.id)
                toolResults.push({
                  type: 'tool_result',
                  tool_use_id: block.id,
                  content: JSON.stringify(result),
                })
              }
            }

            // Update message history for next iteration
            currentMessages = [
              ...currentMessages,
              { role: 'assistant' as const, content: response.content },
              { role: 'user' as const, content: toolResults },
            ]
          } else {
            break
          }
        }

        controller.enqueue(encoder.encode('data: [DONE]\n\n'))
        controller.close()
      } catch (error) {
        const errorChunk = JSON.stringify({ type: 'error', message: 'Error procesando tu solicitud' })
        controller.enqueue(encoder.encode(`data: ${errorChunk}\n\n`))
        controller.close()
        console.error('AI chat error:', error)
      }
    },
  })

  return new Response(stream, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  })
}
