-- ============================================================
-- PROFILES (extends auth.users)
-- ============================================================
CREATE TABLE profiles (
  id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  full_name   TEXT NOT NULL DEFAULT '',
  avatar_url  TEXT,
  role        TEXT NOT NULL DEFAULT 'viewer'
              CHECK (role IN ('admin', 'collaborator', 'viewer', 'project_member')),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-create profile on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY DEFINER AS $$
BEGIN
  INSERT INTO profiles (id, full_name, avatar_url)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email, ''),
    NEW.raw_user_meta_data->>'avatar_url'
  );
  RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================================
-- PROJECTS
-- ============================================================
CREATE TABLE projects (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug          TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  description   TEXT,
  category      TEXT NOT NULL DEFAULT 'business'
                CHECK (category IN ('music', 'production', 'education', 'social', 'business', 'creative')),
  status        TEXT NOT NULL DEFAULT 'active'
                CHECK (status IN ('active', 'paused', 'completed', 'archived')),
  color         TEXT NOT NULL DEFAULT '#6366F1',
  icon          TEXT DEFAULT '📁',
  notion_db_id  TEXT,
  notion_last_sync TIMESTAMPTZ,
  owner_id      UUID REFERENCES profiles(id),
  metadata      JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- PROJECT MEMBERS
-- ============================================================
CREATE TABLE project_members (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  user_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  role       TEXT NOT NULL DEFAULT 'viewer'
             CHECK (role IN ('owner', 'editor', 'viewer')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (project_id, user_id)
);

-- ============================================================
-- TASKS
-- ============================================================
CREATE TABLE tasks (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id      UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title           TEXT NOT NULL,
  description     TEXT,
  status          TEXT NOT NULL DEFAULT 'todo'
                  CHECK (status IN ('todo', 'in_progress', 'review', 'done', 'cancelled')),
  priority        TEXT NOT NULL DEFAULT 'medium'
                  CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
  assignee_id     UUID REFERENCES profiles(id),
  due_date        DATE,
  completed_at    TIMESTAMPTZ,
  position        INTEGER DEFAULT 0,
  tags            TEXT[] DEFAULT '{}',
  notion_id       TEXT UNIQUE,
  notion_url      TEXT,
  google_event_id TEXT,
  created_by      UUID NOT NULL REFERENCES profiles(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX tasks_project_status ON tasks(project_id, status);
CREATE INDEX tasks_assignee ON tasks(assignee_id);
CREATE INDEX tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX tasks_status_not_done ON tasks(status) WHERE status != 'done';

-- ============================================================
-- FINANCE TRANSACTIONS
-- ============================================================
CREATE TABLE finance_transactions (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  type           TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  amount         NUMERIC(12, 2) NOT NULL,
  currency       TEXT NOT NULL DEFAULT 'MXN',
  category       TEXT NOT NULL DEFAULT 'general',
  description    TEXT NOT NULL,
  date           DATE NOT NULL,
  tax_deductible BOOLEAN DEFAULT FALSE,
  receipt_url    TEXT,
  tags           TEXT[] DEFAULT '{}',
  created_by     UUID NOT NULL REFERENCES profiles(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX fin_project_date ON finance_transactions(project_id, date DESC);
CREATE INDEX fin_type_date ON finance_transactions(type, date DESC);

-- ============================================================
-- FINANCE PROJECTIONS
-- ============================================================
CREATE TABLE finance_projections (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id         UUID REFERENCES projects(id) ON DELETE CASCADE,
  month              DATE NOT NULL,
  projected_income   NUMERIC(12, 2) NOT NULL DEFAULT 0,
  projected_expense  NUMERIC(12, 2) NOT NULL DEFAULT 0,
  actual_income      NUMERIC(12, 2),
  actual_expense     NUMERIC(12, 2),
  notes              TEXT,
  created_by         UUID NOT NULL REFERENCES profiles(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (project_id, month)
);

-- ============================================================
-- CRM
-- ============================================================
CREATE TABLE crm_contacts (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  full_name    TEXT NOT NULL,
  email        TEXT,
  phone        TEXT,
  company      TEXT,
  role         TEXT,
  source       TEXT DEFAULT 'manual',
  tags         TEXT[] DEFAULT '{}',
  notes        TEXT,
  avatar_url   TEXT,
  assigned_to  UUID REFERENCES profiles(id),
  created_by   UUID NOT NULL REFERENCES profiles(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE crm_deals (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id     UUID NOT NULL REFERENCES crm_contacts(id) ON DELETE CASCADE,
  project_id     UUID REFERENCES projects(id),
  title          TEXT NOT NULL,
  value          NUMERIC(12, 2),
  currency       TEXT DEFAULT 'MXN',
  stage          TEXT NOT NULL DEFAULT 'prospecting'
                 CHECK (stage IN ('prospecting', 'qualification', 'proposal', 'negotiation', 'won', 'lost')),
  probability    INTEGER DEFAULT 0 CHECK (probability BETWEEN 0 AND 100),
  expected_close DATE,
  notes          TEXT,
  position       INTEGER DEFAULT 0,
  assigned_to    UUID REFERENCES profiles(id),
  won_at         TIMESTAMPTZ,
  lost_at        TIMESTAMPTZ,
  created_by     UUID NOT NULL REFERENCES profiles(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX crm_deals_stage ON crm_deals(stage, position);

CREATE TABLE crm_quotes (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  deal_id      UUID REFERENCES crm_deals(id) ON DELETE SET NULL,
  contact_id   UUID NOT NULL REFERENCES crm_contacts(id),
  project_id   UUID REFERENCES projects(id),
  quote_number TEXT UNIQUE NOT NULL,
  status       TEXT NOT NULL DEFAULT 'draft'
               CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'expired')),
  line_items   JSONB NOT NULL DEFAULT '[]',
  subtotal     NUMERIC(12, 2) NOT NULL DEFAULT 0,
  tax_total    NUMERIC(12, 2) NOT NULL DEFAULT 0,
  total        NUMERIC(12, 2) NOT NULL DEFAULT 0,
  currency     TEXT DEFAULT 'MXN',
  valid_until  DATE,
  notes        TEXT,
  created_by   UUID NOT NULL REFERENCES profiles(id),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- NOTION SYNC LOG
-- ============================================================
CREATE TABLE notion_sync_log (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id     UUID REFERENCES projects(id),
  notion_db_id   TEXT NOT NULL,
  direction      TEXT NOT NULL CHECK (direction IN ('notion_to_supabase', 'supabase_to_notion')),
  status         TEXT NOT NULL CHECK (status IN ('running', 'success', 'error')),
  records_synced INTEGER DEFAULT 0,
  error_message  TEXT,
  started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at    TIMESTAMPTZ
);

-- ============================================================
-- AI CONVERSATIONS
-- ============================================================
CREATE TABLE ai_conversations (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  title      TEXT,
  messages   JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- DASHBOARD AGGREGATE FUNCTION (single round-trip)
-- ============================================================
CREATE OR REPLACE FUNCTION get_dashboard_data()
RETURNS TABLE (
  project_id        UUID,
  project_slug      TEXT,
  project_name      TEXT,
  project_status    TEXT,
  project_color     TEXT,
  project_icon      TEXT,
  project_category  TEXT,
  todo_count        BIGINT,
  in_progress_count BIGINT,
  done_count        BIGINT,
  next_due_date     DATE,
  mtd_income        NUMERIC,
  mtd_expense       NUMERIC,
  notion_db_id      TEXT,
  notion_last_sync  TIMESTAMPTZ
) LANGUAGE SQL SECURITY DEFINER AS $$
  SELECT
    p.id,
    p.slug,
    p.name,
    p.status,
    p.color,
    p.icon,
    p.category,
    COUNT(t.id) FILTER (WHERE t.status = 'todo'),
    COUNT(t.id) FILTER (WHERE t.status = 'in_progress'),
    COUNT(t.id) FILTER (WHERE t.status = 'done'),
    MIN(t.due_date) FILTER (WHERE t.due_date >= CURRENT_DATE AND t.status NOT IN ('done', 'cancelled')),
    COALESCE(SUM(f.amount) FILTER (WHERE f.type = 'income' AND DATE_TRUNC('month', f.date) = DATE_TRUNC('month', NOW())), 0),
    COALESCE(SUM(f.amount) FILTER (WHERE f.type = 'expense' AND DATE_TRUNC('month', f.date) = DATE_TRUNC('month', NOW())), 0),
    p.notion_db_id,
    p.notion_last_sync
  FROM projects p
  LEFT JOIN tasks t ON t.project_id = p.id
  LEFT JOIN finance_transactions f ON f.project_id = p.id
  WHERE p.status != 'archived'
  GROUP BY p.id, p.slug, p.name, p.status, p.color, p.icon, p.category, p.notion_db_id, p.notion_last_sync
  ORDER BY p.name;
$$;

-- ============================================================
-- UPCOMING DEADLINES FUNCTION
-- ============================================================
CREATE OR REPLACE FUNCTION get_upcoming_tasks(days_ahead INTEGER DEFAULT 14)
RETURNS TABLE (
  task_id       UUID,
  task_title    TEXT,
  task_status   TEXT,
  task_priority TEXT,
  due_date      DATE,
  project_name  TEXT,
  project_color TEXT,
  assignee_name TEXT
) LANGUAGE SQL SECURITY DEFINER AS $$
  SELECT
    t.id,
    t.title,
    t.status,
    t.priority,
    t.due_date,
    p.name,
    p.color,
    pr.full_name
  FROM tasks t
  JOIN projects p ON p.id = t.project_id
  LEFT JOIN profiles pr ON pr.id = t.assignee_id
  WHERE
    t.due_date >= CURRENT_DATE
    AND t.due_date <= CURRENT_DATE + (days_ahead || ' days')::INTERVAL
    AND t.status NOT IN ('done', 'cancelled')
  ORDER BY t.due_date ASC, t.priority DESC
  LIMIT 20;
$$;

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$;

CREATE TRIGGER tasks_updated_at BEFORE UPDATE ON tasks
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER projects_updated_at BEFORE UPDATE ON projects
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER fin_updated_at BEFORE UPDATE ON finance_transactions
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER crm_contacts_updated_at BEFORE UPDATE ON crm_contacts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER crm_deals_updated_at BEFORE UPDATE ON crm_deals
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
