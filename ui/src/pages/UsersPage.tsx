import { useState } from 'react'
import { useAuthStore } from '../store/auth'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getUsers, createUser, deleteUser, resetPassword, type User } from '../api/users'

export default function UsersPage() {
  const { user: currentUser } = useAuthStore()
  const qc = useQueryClient()
  const [newUser, setNewUser] = useState({ username: '', password: '', role: 'user' as 'admin' | 'user' })
  const [resetPwd, setResetPwd] = useState<Record<number, string>>({})

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const invalidate = () => qc.invalidateQueries({ queryKey: ['users'] })

  const mutCreate = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      invalidate()
      setNewUser({ username: '', password: '', role: 'user' })
    },
  })

  const mutDelete = useMutation({ mutationFn: deleteUser, onSuccess: invalidate })

  const mutReset = useMutation({
    mutationFn: ({ id, password }: { id: number; password: string }) => resetPassword(id, password),
    onSuccess: (_, { id }) => setResetPwd(r => ({ ...r, [id]: '' })),
  })

  if (isLoading) return <div className="text-gray-500">Loading...</div>

  return (
    <div className="max-w-2xl">
      <h2 className="text-xl font-bold mb-6">Users</h2>

      {/* Add user */}
      <div className="bg-gray-900 rounded-xl p-4 mb-6 flex flex-col gap-3">
        <h3 className="text-sm font-semibold text-gray-400">New User</h3>
        <div className="flex gap-2">
          <input
            className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Username"
            value={newUser.username}
            onChange={e => setNewUser(u => ({ ...u, username: e.target.value }))}
          />
          <input
            className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Password"
            type="password"
            value={newUser.password}
            onChange={e => setNewUser(u => ({ ...u, password: e.target.value }))}
          />
          <select
            className="bg-gray-800 text-white rounded-lg px-3 py-2 text-sm outline-none"
            value={newUser.role}
            onChange={e => setNewUser(u => ({ ...u, role: e.target.value as 'admin' | 'user' }))}
          >
            <option value="user">user</option>
            <option value="admin">admin</option>
          </select>
          <button
            onClick={() => newUser.username && newUser.password && mutCreate.mutate(newUser)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition-colors"
          >
            Create
          </button>
        </div>
        {mutCreate.isError && (
          <p className="text-red-400 text-xs">Username already exists</p>
        )}
      </div>

      {/* Users list */}
      <div className="flex flex-col gap-2">
        {users.map((user: User) => (
          <div key={user.id} className="bg-gray-900 rounded-xl px-4 py-3 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="font-medium">{user.username}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  user.role === 'admin' ? 'bg-purple-900 text-purple-300' : 'bg-gray-800 text-gray-400'
                }`}>
                  {user.role}
                </span>
              </div>
              {currentUser?.id !== user.id && (
                  <button
                    onClick={() => mutDelete.mutate(user.id)}
                    className="text-xs text-gray-600 hover:text-red-400 transition-colors"
                  >
                    Delete
                  </button>
                )}
            </div>

            {/* Reset password */}
            <div className="flex gap-2">
              <input
                className="flex-1 bg-gray-800 text-white rounded-lg px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="New password..."
                type="password"
                value={resetPwd[user.id] ?? ''}
                onChange={e => setResetPwd(r => ({ ...r, [user.id]: e.target.value }))}
              />
              <button
                onClick={() => resetPwd[user.id] && mutReset.mutate({ id: user.id, password: resetPwd[user.id] })}
                className="bg-gray-700 hover:bg-gray-600 text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
              >
                Reset pwd
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}