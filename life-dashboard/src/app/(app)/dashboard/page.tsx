import { createClient } from '@/lib/supabase/server'
import { ProjectCard } from '@/components/dashboard/ProjectCard'
import { DashboardStats } from '@/components/dashboard/DashboardStats'
import { UpcomingDeadlines } from '@/components/dashboard/UpcomingDeadlines'
import { ActivityFeed } from '@/components/dashboard/ActivityFeed'

export const dynamic = 'force-dynamic'

export default async function DashboardPage() {
  const supabase = await createClient()

  // Single round-trip for all project data
  const [{ data: projectsData }, { data: upcomingData }, { data: dealsData }] = await Promise.all([
    supabase.rpc('get_dashboard_data'),
    supabase.rpc('get_upcoming_tasks', { days_ahead: 14 }),
    supabase.from('crm_deals').select('id', { count: 'exact', head: true })
      .not('stage', 'in', '("won","lost")'),
  ])

  const projects = projectsData ?? []
  const upcoming = upcomingData ?? []

  // Aggregate stats
  const totalOpenTasks = projects.reduce((sum: number, p: { todo_count: number }) => sum + (p.todo_count || 0), 0)
  const totalInProgress = projects.reduce((sum: number, p: { in_progress_count: number }) => sum + (p.in_progress_count || 0), 0)
  const totalMtdIncome = projects.reduce((sum: number, p: { mtd_income: number }) => sum + (p.mtd_income || 0), 0)
  const nextDeadline = upcoming.length > 0 ? (upcoming[0] as { due_date: string }).due_date : null
  const dealsInPipeline = dealsData ?? 0

  // Recent activity (last 15 tasks updated)
  const { data: recentTasks } = await supabase
    .from('tasks')
    .select('id, title, status, updated_at, created_at, project_id, projects(name, color)')
    .order('updated_at', { ascending: false })
    .limit(15)

  type RawTask = {
    id: string; title: string; status: string; updated_at: string; created_at: string
    projects: { name: string; color: string } | { name: string; color: string }[] | null
  }
  const activityItems = (recentTasks ?? []).map((t: RawTask) => {
    const rawP = t.projects
    const proj = (Array.isArray(rawP) ? rawP[0] : rawP) as { name: string; color: string } | null
    return {
    id: t.id,
    type: t.status === 'done' ? 'task_done' as const : 'task_created' as const,
    title: t.title,
    projectName: proj?.name ?? '',
    projectColor: proj?.color ?? '#6366F1',
    timestamp: t.updated_at || t.created_at,
  }
  })

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-zinc-400 text-sm mt-1">
          Todos tus proyectos en un solo lugar
        </p>
      </div>

      {/* KPI strip */}
      <DashboardStats
        totalOpenTasks={totalOpenTasks}
        totalInProgress={totalInProgress}
        totalMtdIncome={totalMtdIncome}
        nextDeadlineDate={nextDeadline}
        dealsInPipeline={typeof dealsInPipeline === 'number' ? dealsInPipeline : 0}
      />

      {/* Main content: projects + sidebar */}
      <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-6">
        {/* Project grid */}
        <div>
          <h2 className="text-zinc-400 text-xs font-semibold uppercase tracking-wider mb-3">
            Proyectos activos
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-2 2xl:grid-cols-3 gap-4">
            {projects.map((project: {
              project_id: string
              project_slug: string
              project_name: string
              project_status: string
              project_color: string
              project_icon: string
              project_category: string
              todo_count: number
              in_progress_count: number
              done_count: number
              next_due_date: string | null
              mtd_income: number
              mtd_expense: number
              notion_db_id: string | null
              notion_last_sync: string | null
            }) => (
              <ProjectCard
                key={project.project_id}
                id={project.project_id}
                slug={project.project_slug}
                name={project.project_name}
                status={project.project_status}
                color={project.project_color}
                icon={project.project_icon}
                category={project.project_category}
                todoCount={project.todo_count || 0}
                inProgressCount={project.in_progress_count || 0}
                doneCount={project.done_count || 0}
                nextDueDate={project.next_due_date}
                mtdIncome={project.mtd_income || 0}
                mtdExpense={project.mtd_expense || 0}
                notionDbId={project.notion_db_id}
                notionLastSync={project.notion_last_sync}
              />
            ))}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-4">
          <UpcomingDeadlines tasks={upcoming as Parameters<typeof UpcomingDeadlines>[0]['tasks']} />
          <ActivityFeed initialItems={activityItems} />
        </div>
      </div>
    </div>
  )
}
