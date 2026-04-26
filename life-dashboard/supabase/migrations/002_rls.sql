-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

-- Helper: check if current user has a given global role
CREATE OR REPLACE FUNCTION auth_role()
RETURNS TEXT LANGUAGE SQL SECURITY DEFINER STABLE AS $$
  SELECT role FROM profiles WHERE id = auth.uid();
$$;

-- ============================================================
-- PROFILES
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_all" ON profiles
  FOR SELECT USING (TRUE);

CREATE POLICY "profiles_update_self_or_admin" ON profiles
  FOR UPDATE USING (
    auth.uid() = id OR auth_role() = 'admin'
  );

-- ============================================================
-- PROJECTS
-- ============================================================
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "projects_select" ON projects
  FOR SELECT USING (
    auth_role() IN ('admin', 'viewer', 'collaborator')
    OR EXISTS (
      SELECT 1 FROM project_members
      WHERE project_id = projects.id AND user_id = auth.uid()
    )
  );

CREATE POLICY "projects_insert_admin" ON projects
  FOR INSERT WITH CHECK (auth_role() = 'admin');

CREATE POLICY "projects_update_admin" ON projects
  FOR UPDATE USING (auth_role() = 'admin');

CREATE POLICY "projects_delete_admin" ON projects
  FOR DELETE USING (auth_role() = 'admin');

-- ============================================================
-- PROJECT MEMBERS
-- ============================================================
ALTER TABLE project_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "project_members_select" ON project_members
  FOR SELECT USING (auth_role() IN ('admin', 'viewer', 'collaborator') OR user_id = auth.uid());

CREATE POLICY "project_members_manage_admin" ON project_members
  FOR ALL USING (auth_role() = 'admin');

-- ============================================================
-- TASKS
-- ============================================================
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tasks_select" ON tasks
  FOR SELECT USING (
    auth_role() IN ('admin', 'viewer', 'collaborator')
    OR EXISTS (
      SELECT 1 FROM project_members
      WHERE project_id = tasks.project_id AND user_id = auth.uid()
    )
  );

CREATE POLICY "tasks_insert" ON tasks
  FOR INSERT WITH CHECK (
    auth_role() IN ('admin', 'collaborator')
    OR EXISTS (
      SELECT 1 FROM project_members
      WHERE project_id = tasks.project_id AND user_id = auth.uid()
        AND role IN ('owner', 'editor')
    )
  );

CREATE POLICY "tasks_update" ON tasks
  FOR UPDATE USING (
    auth_role() IN ('admin', 'collaborator')
    OR assignee_id = auth.uid()
    OR EXISTS (
      SELECT 1 FROM project_members
      WHERE project_id = tasks.project_id AND user_id = auth.uid()
        AND role IN ('owner', 'editor')
    )
  );

CREATE POLICY "tasks_delete" ON tasks
  FOR DELETE USING (
    auth_role() = 'admin'
    OR created_by = auth.uid()
  );

-- ============================================================
-- FINANCE — admin only
-- ============================================================
ALTER TABLE finance_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE finance_projections ENABLE ROW LEVEL SECURITY;

CREATE POLICY "finance_transactions_admin" ON finance_transactions
  FOR ALL USING (auth_role() = 'admin');

CREATE POLICY "finance_projections_admin" ON finance_projections
  FOR ALL USING (auth_role() = 'admin');

-- ============================================================
-- CRM — admin + collaborator
-- ============================================================
ALTER TABLE crm_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_deals ENABLE ROW LEVEL SECURITY;
ALTER TABLE crm_quotes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "crm_contacts_access" ON crm_contacts
  FOR ALL USING (auth_role() IN ('admin', 'collaborator'));

CREATE POLICY "crm_deals_access" ON crm_deals
  FOR ALL USING (auth_role() IN ('admin', 'collaborator'));

CREATE POLICY "crm_quotes_access" ON crm_quotes
  FOR ALL USING (auth_role() IN ('admin', 'collaborator'));

-- ============================================================
-- NOTION SYNC LOG — admin only
-- ============================================================
ALTER TABLE notion_sync_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "notion_sync_log_admin" ON notion_sync_log
  FOR ALL USING (auth_role() = 'admin');

-- ============================================================
-- AI CONVERSATIONS — own rows only
-- ============================================================
ALTER TABLE ai_conversations ENABLE ROW LEVEL SECURITY;

CREATE POLICY "ai_conversations_own" ON ai_conversations
  FOR ALL USING (user_id = auth.uid());
