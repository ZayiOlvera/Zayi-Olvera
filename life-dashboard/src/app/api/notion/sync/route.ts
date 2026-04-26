import { NextRequest, NextResponse } from 'next/server'
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { createAdminClient } from '@/lib/supabase/admin'

type NotionPropertyValue =
  | { type: 'title'; title: Array<{ plain_text: string }> }
  | { type: 'date'; date: { start: string } | null }
  | { type: 'select'; select: { name: string } | null }
  | { type: string }

type NotionPage = {
  object: string
  id: string
  url: string
  properties: Record<string, NotionPropertyValue>
}

type NotionQueryResponse = {
  results: NotionPage[]
}

async function queryNotionDatabase(databaseId: string, token: string): Promise<NotionQueryResponse> {
  const response = await fetch(`https://api.notion.com/v1/databases/${databaseId}/query`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'Notion-Version': '2022-06-28',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ page_size: 100 }),
  })

  if (!response.ok) {
    const error = await response.text()
    throw new Error(`Notion API error: ${response.status} ${error}`)
  }

  return response.json()
}

export async function POST(req: NextRequest) {
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
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  if (!process.env.NOTION_TOKEN) {
    return NextResponse.json({ error: 'NOTION_TOKEN not configured' }, { status: 400 })
  }

  const { project_id } = await req.json() as { project_id?: string }

  const admin = createAdminClient()

  let projectQuery = admin.from('projects').select('id, slug, name, notion_db_id').not('notion_db_id', 'is', null)
  if (project_id) projectQuery = projectQuery.eq('id', project_id)
  const { data: projects } = await projectQuery

  if (!projects || projects.length === 0) {
    return NextResponse.json({ message: 'No projects with Notion databases configured', synced: 0 })
  }

  let totalSynced = 0
  const errors: string[] = []

  for (const project of projects) {
    if (!project.notion_db_id) continue

    const logEntry = await admin.from('notion_sync_log').insert({
      project_id: project.id,
      notion_db_id: project.notion_db_id,
      direction: 'notion_to_supabase',
      status: 'running',
    }).select().single()

    const logId = logEntry.data?.id
    let synced = 0

    try {
      const data = await queryNotionDatabase(project.notion_db_id, process.env.NOTION_TOKEN!)

      for (const page of data.results) {
        if (page.object !== 'page') continue

        const props = page.properties
        const titleProp = Object.values(props).find((p) => p.type === 'title') as { type: 'title'; title: Array<{ plain_text: string }> } | undefined
        const title = titleProp?.title?.[0]?.plain_text ?? 'Sin título'

        const dueDateProp = Object.values(props).find((p) => p.type === 'date') as { type: 'date'; date: { start: string } | null } | undefined
        const dueDate = dueDateProp?.date?.start ?? null

        const statusProp = Object.values(props).find((p) => p.type === 'select') as { type: 'select'; select: { name: string } | null } | undefined
        const notionStatus = statusProp?.select?.name?.toLowerCase() ?? 'todo'
        const statusMap: Record<string, string> = {
          'to do': 'todo', 'todo': 'todo',
          'in progress': 'in_progress', 'en curso': 'in_progress',
          'done': 'done', 'hecho': 'done', 'complete': 'done',
        }

        await admin.from('tasks').upsert({
          project_id: project.id,
          title,
          due_date: dueDate,
          status: statusMap[notionStatus] ?? 'todo',
          notion_id: page.id,
          notion_url: page.url,
          created_by: user.id,
        }, { onConflict: 'notion_id', ignoreDuplicates: false })

        synced++
      }

      totalSynced += synced
      await admin.from('projects').update({ notion_last_sync: new Date().toISOString() }).eq('id', project.id)

      if (logId) {
        await admin.from('notion_sync_log').update({
          status: 'success',
          records_synced: synced,
          finished_at: new Date().toISOString(),
        }).eq('id', logId)
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      errors.push(`${project.name}: ${message}`)
      if (logId) {
        await admin.from('notion_sync_log').update({
          status: 'error',
          error_message: message,
          finished_at: new Date().toISOString(),
        }).eq('id', logId)
      }
    }
  }

  return NextResponse.json({ synced: totalSynced, errors, projects_synced: projects.length })
}
