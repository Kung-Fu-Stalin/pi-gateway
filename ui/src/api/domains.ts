import api from './client'

export interface Domain {
  id: number
  domain: string
  status: 'pending' | 'approved' | 'rejected'
  reject_reason?: string
  created_at: string
}

export interface DomainGroup {
  id: number
  name: string
  created_at: string
  domains: Domain[]
}

export const getGroups = () =>
  api.get<DomainGroup[]>('/groups').then(r => r.data)

export const createGroup = (name: string) =>
  api.post<DomainGroup>('/groups', { name }).then(r => r.data)

export const deleteGroup = (id: number) =>
  api.delete(`/groups/${id}`)

export const addDomain = (groupId: number, domain: string) =>
  api.post<Domain>(`/groups/${groupId}/domains`, { domain }).then(r => r.data)

export const deleteDomain = (groupId: number, domainId: number) =>
  api.delete(`/groups/${groupId}/domains/${domainId}`)

export const approveDomain = (domainId: number) =>
  api.post(`/groups/domains/${domainId}/approve`)

export const rejectDomain = (domainId: number, reason?: string) =>
  api.post(`/groups/domains/${domainId}/reject`, { reason })

export const getPending = () =>
  api.get<DomainGroup[]>('/groups/pending').then(r => r.data)