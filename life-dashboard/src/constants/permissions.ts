export type Role = 'admin' | 'collaborator' | 'viewer' | 'project_member'

export const PERMISSIONS = {
  admin: {
    canViewFinance: true,
    canEditFinance: true,
    canViewCRM: true,
    canEditCRM: true,
    canManageUsers: true,
    canEditProjects: true,
    canViewAllProjects: true,
  },
  collaborator: {
    canViewFinance: false,
    canEditFinance: false,
    canViewCRM: true,
    canEditCRM: true,
    canManageUsers: false,
    canEditProjects: false,
    canViewAllProjects: true,
  },
  viewer: {
    canViewFinance: false,
    canEditFinance: false,
    canViewCRM: false,
    canEditCRM: false,
    canManageUsers: false,
    canEditProjects: false,
    canViewAllProjects: true,
  },
  project_member: {
    canViewFinance: false,
    canEditFinance: false,
    canViewCRM: false,
    canEditCRM: false,
    canManageUsers: false,
    canEditProjects: false,
    canViewAllProjects: false,
  },
} satisfies Record<Role, Record<string, boolean>>

export function can(role: Role, permission: keyof typeof PERMISSIONS['admin']) {
  return PERMISSIONS[role]?.[permission] ?? false
}
