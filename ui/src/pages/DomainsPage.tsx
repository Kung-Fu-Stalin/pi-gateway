import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/auth'
import {
  getGroups, createGroup, deleteGroup,
  addDomain, deleteDomain, approveDomain, rejectDomain,
  type DomainGroup
} from '../api/domains'

function statusBadge(status: string) {
  const styles: Record<string, string> = {
    approved: 'bg-green-900 text-green-300',
    pending: 'bg-yellow-900 text-yellow-300',
    rejected: 'bg-red-900 text-red-300',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full ${styles[status] ?? ''}`}>
      {status}
    </span>
  )
}

export default function DomainsPage() {
  const { user } = useAuthStore()
  const isAdmin = user?.role === 'admin'
  const qc = useQueryClient()
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})
  const [newGroupName, setNewGroupName] = useState('')
  const [addingDomain, setAddingDomain] = useState<Record<number, string>>({})
  const [rejectReason, setRejectReason] = useState<Record<number, string>>({})

  const { data: groups = [], isLoading } = useQuery({
    queryKey: ['groups'],
    queryFn: getGroups,
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['groups'] })

  const mutCreateGroup = useMutation({
    mutationFn: createGroup,
    onSuccess: (g) => {
      invalidate()
      setNewGroupName('')
      setExpanded(e => ({ ...e, [g.id]: true }))
    },
  })

  const mutDeleteGroup = useMutation({ mutationFn: deleteGroup, onSuccess: invalidate })
  const mutAddDomain = useMutation({
    mutationFn: ({ groupId, domain }: { groupId: number; domain: string }) =>
      addDomain(groupId, domain),
    onSuccess: (_, { groupId }) => {
      invalidate()
      setAddingDomain(a => ({ ...a, [groupId]: '' }))
    },
  })
  const mutDeleteDomain = useMutation({
    mutationFn: ({ groupId, domainId }: { groupId: number; domainId: number }) =>
      deleteDomain(groupId, domainId),
    onSuccess: invalidate,
  })
  const mutApprove = useMutation({ mutationFn: approveDomain, onSuccess: invalidate })
  const mutReject = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason?: string }) => rejectDomain(id, reason),
    onSuccess: invalidate,
  })

  const toggle = (id: number) => setExpanded(e => ({ ...e, [id]: !e[id] }))

  if (isLoading) return <div className="text-gray-500">Loading...</div>

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold mb-6">Domains</h2>

      {/* Add group */}
      <div className="flex gap-2 mb-6">
        <input
          className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="New group name (e.g. chatgpt.com)"
          value={newGroupName}
          onChange={e => setNewGroupName(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && newGroupName && mutCreateGroup.mutate(newGroupName)}
        />
        <button
          onClick={() => newGroupName && mutCreateGroup.mutate(newGroupName)}
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition-colors"
        >
          Add Group
        </button>
      </div>

      {/* Groups list */}
      <div className="flex flex-col gap-2">
        {groups.map((group: DomainGroup) => (
          <div key={group.id} className="bg-gray-900 rounded-xl overflow-hidden">
            {/* Group header */}
            <div
              className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-gray-800 transition-colors"
              onClick={() => toggle(group.id)}
            >
              <div className="flex items-center gap-2">
                <span className="text-gray-400 text-xs">{expanded[group.id] ? '▼' : '▶'}</span>
                <span className="font-medium">{group.name}</span>
                <span className="text-xs text-gray-500">{group.domains.length} domains</span>
              </div>
              {isAdmin && (
                <button
                  onClick={e => { e.stopPropagation(); mutDeleteGroup.mutate(group.id) }}
                  className="text-gray-600 hover:text-red-400 text-xs px-2 py-1 transition-colors"
                >
                  Delete
                </button>
              )}
            </div>

            {/* Domains */}
            {expanded[group.id] && (
              <div className="border-t border-gray-800">
                {group.domains.map(d => (
                  <div key={d.id} className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800 last:border-0">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-300">{d.domain}</span>
                      {statusBadge(d.status)}
                      {d.reject_reason && (
                        <span className="text-xs text-gray-500 italic">{d.reject_reason}</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      {isAdmin && d.status === 'pending' && (
                        <>
                          <button
                            onClick={() => mutApprove.mutate(d.id)}
                            className="text-xs text-green-400 hover:text-green-300 transition-colors"
                          >
                            Approve
                          </button>
                          <input
                            className="bg-gray-800 text-white text-xs rounded px-2 py-1 w-28 outline-none"
                            placeholder="Reason..."
                            value={rejectReason[d.id] ?? ''}
                            onChange={e => setRejectReason(r => ({ ...r, [d.id]: e.target.value }))}
                          />
                          <button
                            onClick={() => mutReject.mutate({ id: d.id, reason: rejectReason[d.id] })}
                            className="text-xs text-red-400 hover:text-red-300 transition-colors"
                          >
                            Reject
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => mutDeleteDomain.mutate({ groupId: group.id, domainId: d.id })}
                        className="text-xs text-gray-600 hover:text-red-400 transition-colors"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}

                {/* Add domain */}
                <div className="flex gap-2 p-3">
                  <input
                    className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Add domain..."
                    value={addingDomain[group.id] ?? ''}
                    onChange={e => setAddingDomain(a => ({ ...a, [group.id]: e.target.value }))}
                    onKeyDown={e => {
                      if (e.key === 'Enter' && addingDomain[group.id]) {
                        mutAddDomain.mutate({ groupId: group.id, domain: addingDomain[group.id] })
                      }
                    }}
                  />
                  <button
                    onClick={() => addingDomain[group.id] && mutAddDomain.mutate({ groupId: group.id, domain: addingDomain[group.id] })}
                    className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}

        {groups.length === 0 && (
          <p className="text-gray-600 text-sm">No groups yet. Add one above.</p>
        )}
      </div>
    </div>
  )
}