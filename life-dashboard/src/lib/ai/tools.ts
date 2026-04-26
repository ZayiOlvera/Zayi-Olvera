import Anthropic from '@anthropic-ai/sdk'
import { createAdminClient } from '@/lib/supabase/admin'

export const AI_TOOLS: Anthropic.Tool[] = [
  {
    name: 'create_task',
    description: 'Crea una nueva tarea en un proyecto. Úsala cuando el usuario pida añadir, crear o agendar algo.',
    input_schema: {
      type: 'object' as const,
      properties: {
        project_slug: { type: 'string', description: 'Slug del proyecto: caloncho, supremacy-studios, supremacy-rentals, camp-league, garden-sessions, clases-psicologia, instituto-olvera, guiones-personales' },
        title: { type: 'string', description: 'Título de la tarea' },
        description: { type: 'string', description: 'Descripción opcional' },
        priority: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'], description: 'Prioridad' },
        due_date: { type: 'string', description: 'Fecha límite en formato YYYY-MM-DD' },
      },
      required: ['project_slug', 'title'],
    },
  },
  {
    name: 'list_tasks',
    description: 'Lista tareas con filtros opcionales. Úsala para consultar qué tareas hay pendientes, en curso, etc.',
    input_schema: {
      type: 'object' as const,
      properties: {
        project_slug: { type: 'string', description: 'Filtrar por proyecto (opcional)' },
        status: { type: 'string', enum: ['todo', 'in_progress', 'review', 'done', 'cancelled'], description: 'Filtrar por estado' },
        priority: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
        due_before: { type: 'string', description: 'Solo tareas con fecha límite antes de esta fecha YYYY-MM-DD' },
      },
      required: [],
    },
  },
  {
    name: 'update_task',
    description: 'Actualiza el estado, prioridad, o fecha límite de una tarea existente.',
    input_schema: {
      type: 'object' as const,
      properties: {
        task_id: { type: 'string', description: 'ID UUID de la tarea' },
        status: { type: 'string', enum: ['todo', 'in_progress', 'review', 'done', 'cancelled'] },
        priority: { type: 'string', enum: ['low', 'medium', 'high', 'urgent'] },
        due_date: { type: 'string', description: 'YYYY-MM-DD' },
        title: { type: 'string' },
      },
      required: ['task_id'],
    },
  },
  {
    name: 'get_overdue_tasks',
    description: 'Retorna todas las tareas vencidas (fecha límite pasada y no completadas).',
    input_schema: {
      type: 'object' as const,
      properties: {},
      required: [],
    },
  },
  {
    name: 'get_project_summary',
    description: 'Retorna un resumen de un proyecto o de todos los proyectos: conteo de tareas y finanzas del mes.',
    input_schema: {
      type: 'object' as const,
      properties: {
        project_slug: { type: 'string', description: 'Omitir para obtener todos los proyectos' },
      },
      required: [],
    },
  },
  {
    name: 'get_financial_summary',
    description: 'Retorna ingresos, gastos y neto para un proyecto o todos, en un período dado.',
    input_schema: {
      type: 'object' as const,
      properties: {
        project_slug: { type: 'string', description: 'Omitir para total general' },
        period: { type: 'string', enum: ['mtd', 'ytd', 'last_30', 'last_90'], description: 'mtd=este mes, ytd=este año, last_30=últimos 30 días, last_90=últimos 90 días' },
      },
      required: ['period'],
    },
  },
  {
    name: 'add_transaction',
    description: 'Registra un ingreso o gasto en un proyecto.',
    input_schema: {
      type: 'object' as const,
      properties: {
        project_slug: { type: 'string' },
        type: { type: 'string', enum: ['income', 'expense'] },
        amount: { type: 'number', description: 'Monto en MXN' },
        category: { type: 'string', description: 'Categoría: talent, equipment, marketing, licensing, services, rent, taxes, other' },
        description: { type: 'string', description: 'Descripción del movimiento' },
        date: { type: 'string', description: 'Fecha en YYYY-MM-DD' },
        tax_deductible: { type: 'boolean', description: 'Si es deducible de impuestos' },
      },
      required: ['project_slug', 'type', 'amount', 'category', 'description', 'date'],
    },
  },
  {
    name: 'get_pipeline_summary',
    description: 'Retorna el resumen del CRM: conteo y valor total de deals por etapa.',
    input_schema: {
      type: 'object' as const,
      properties: {},
      required: [],
    },
  },
  {
    name: 'create_contact',
    description: 'Crea un nuevo contacto en el CRM.',
    input_schema: {
      type: 'object' as const,
      properties: {
        full_name: { type: 'string' },
        email: { type: 'string' },
        phone: { type: 'string' },
        company: { type: 'string' },
        role: { type: 'string', description: 'Cargo o rol del contacto' },
        source: { type: 'string', description: 'De dónde viene: referral, instagram, event, other' },
        notes: { type: 'string' },
      },
      required: ['full_name'],
    },
  },
  {
    name: 'update_deal_stage',
    description: 'Mueve un deal a otra etapa del pipeline.',
    input_schema: {
      type: 'object' as const,
      properties: {
        deal_id: { type: 'string' },
        stage: { type: 'string', enum: ['prospecting', 'qualification', 'proposal', 'negotiation', 'won', 'lost'] },
      },
      required: ['deal_id', 'stage'],
    },
  },
]

// ================================================================
// Tool handlers — each calls Supabase with the admin client
// ================================================================

type ToolInput = Record<string, unknown>

export async function handleToolCall(toolName: string, input: ToolInput, userId: string): Promise<unknown> {
  const supabase = createAdminClient()

  switch (toolName) {
    case 'create_task': {
      const { project_slug, title, description, priority, due_date } = input as {
        project_slug: string; title: string; description?: string; priority?: string; due_date?: string
      }
      const { data: project } = await supabase.from('projects').select('id').eq('slug', project_slug).single()
      if (!project) return { error: `Proyecto "${project_slug}" no encontrado` }

      const { data, error } = await supabase.from('tasks').insert({
        project_id: project.id,
        title,
        description,
        priority: priority ?? 'medium',
        due_date: due_date ?? null,
        status: 'todo',
        created_by: userId,
      }).select().single()

      if (error) return { error: error.message }
      return { success: true, task: data, message: `Tarea "${title}" creada en ${project_slug}` }
    }

    case 'list_tasks': {
      const { project_slug, status, priority, due_before } = input as {
        project_slug?: string; status?: string; priority?: string; due_before?: string
      }
      let query = supabase
        .from('tasks')
        .select('id, title, status, priority, due_date, project_id, projects(name, slug)')
        .order('due_date', { ascending: true })
        .limit(20)

      if (project_slug) {
        const { data: proj } = await supabase.from('projects').select('id').eq('slug', project_slug).single()
        if (proj) query = query.eq('project_id', proj.id)
      }
      if (status) query = query.eq('status', status)
      if (priority) query = query.eq('priority', priority)
      if (due_before) query = query.lte('due_date', due_before)

      const { data, error } = await query
      if (error) return { error: error.message }
      return { tasks: data, count: data?.length ?? 0 }
    }

    case 'update_task': {
      const { task_id, ...updates } = input as { task_id: string; [key: string]: unknown }
      const cleanUpdates: Record<string, unknown> = {}
      if (updates.status) {
        cleanUpdates.status = updates.status
        if (updates.status === 'done') cleanUpdates.completed_at = new Date().toISOString()
      }
      if (updates.priority) cleanUpdates.priority = updates.priority
      if (updates.due_date) cleanUpdates.due_date = updates.due_date
      if (updates.title) cleanUpdates.title = updates.title

      const { data, error } = await supabase.from('tasks').update(cleanUpdates).eq('id', task_id).select().single()
      if (error) return { error: error.message }
      return { success: true, task: data }
    }

    case 'get_overdue_tasks': {
      const today = new Date().toISOString().split('T')[0]
      const { data, error } = await supabase
        .from('tasks')
        .select('id, title, status, priority, due_date, projects(name, color)')
        .lt('due_date', today)
        .not('status', 'in', '("done","cancelled")')
        .order('due_date', { ascending: true })

      if (error) return { error: error.message }
      return { overdue_tasks: data, count: data?.length ?? 0 }
    }

    case 'get_project_summary': {
      const { data, error } = await supabase.rpc('get_dashboard_data')
      if (error) return { error: error.message }

      const { project_slug } = input as { project_slug?: string }
      if (project_slug) {
        const project = (data ?? []).find((p: { project_slug: string }) => p.project_slug === project_slug)
        return project ?? { error: 'Proyecto no encontrado' }
      }
      return { projects: data }
    }

    case 'get_financial_summary': {
      const { project_slug, period } = input as { project_slug?: string; period: string }
      const periodMap: Record<string, string> = {
        mtd: `DATE_TRUNC('month', NOW())`,
        ytd: `DATE_TRUNC('year', NOW())`,
        last_30: `NOW() - INTERVAL '30 days'`,
        last_90: `NOW() - INTERVAL '90 days'`,
      }

      let query = supabase
        .from('finance_transactions')
        .select('type, amount, project_id, projects(name, slug)')

      if (project_slug) {
        const { data: proj } = await supabase.from('projects').select('id').eq('slug', project_slug).single()
        if (proj) query = query.eq('project_id', proj.id)
      }

      const { data, error } = await query
      if (error) return { error: error.message }

      const income = (data ?? []).filter((t: { type: string }) => t.type === 'income').reduce((s: number, t: { amount: number }) => s + t.amount, 0)
      const expense = (data ?? []).filter((t: { type: string }) => t.type === 'expense').reduce((s: number, t: { amount: number }) => s + t.amount, 0)
      return { income, expense, net: income - expense, period, project: project_slug ?? 'todos' }
    }

    case 'add_transaction': {
      const { project_slug, type, amount, category, description, date, tax_deductible } = input as {
        project_slug: string; type: string; amount: number; category: string; description: string; date: string; tax_deductible?: boolean
      }
      const { data: project } = await supabase.from('projects').select('id').eq('slug', project_slug).single()
      if (!project) return { error: `Proyecto "${project_slug}" no encontrado` }

      const { data, error } = await supabase.from('finance_transactions').insert({
        project_id: project.id,
        type,
        amount,
        category,
        description,
        date,
        tax_deductible: tax_deductible ?? false,
        created_by: userId,
      }).select().single()

      if (error) return { error: error.message }
      return { success: true, transaction: data }
    }

    case 'get_pipeline_summary': {
      const { data, error } = await supabase
        .from('crm_deals')
        .select('stage, value')
        .not('stage', 'in', '("won","lost")')

      if (error) return { error: error.message }

      const summary: Record<string, { count: number; total: number }> = {}
      for (const deal of (data ?? [])) {
        if (!summary[deal.stage]) summary[deal.stage] = { count: 0, total: 0 }
        summary[deal.stage].count++
        summary[deal.stage].total += deal.value ?? 0
      }
      return { pipeline: summary }
    }

    case 'create_contact': {
      const { full_name, email, phone, company, role, source, notes } = input as {
        full_name: string; email?: string; phone?: string; company?: string; role?: string; source?: string; notes?: string
      }
      const { data, error } = await supabase.from('crm_contacts').insert({
        full_name,
        email,
        phone,
        company,
        role,
        source: source ?? 'manual',
        notes,
        created_by: userId,
      }).select().single()

      if (error) return { error: error.message }
      return { success: true, contact: data }
    }

    case 'update_deal_stage': {
      const { deal_id, stage } = input as { deal_id: string; stage: string }
      const updates: Record<string, unknown> = { stage }
      if (stage === 'won') updates.won_at = new Date().toISOString()
      if (stage === 'lost') updates.lost_at = new Date().toISOString()

      const { data, error } = await supabase.from('crm_deals').update(updates).eq('id', deal_id).select().single()
      if (error) return { error: error.message }
      return { success: true, deal: data }
    }

    default:
      return { error: `Herramienta desconocida: ${toolName}` }
  }
}
