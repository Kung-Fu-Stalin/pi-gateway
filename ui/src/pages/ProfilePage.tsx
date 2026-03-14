import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { useAuthStore } from '../store/auth'
import api from '../api/client'

interface PacInfo {
  pac_url: string
  proxy_user: string
  proxy_pass: string
}

export default function ProfilePage() {
  const { user } = useAuthStore()
  const [oldPwd, setOldPwd] = useState('')
  const [newPwd, setNewPwd] = useState('')
  const [pwdMsg, setPwdMsg] = useState('')
  const [showPass, setShowPass] = useState(false)

  const { data: pac } = useQuery({
    queryKey: ['pac'],
    queryFn: () => api.get<PacInfo>('/users/me/pac').then(r => r.data),
  })

  const mutChangePwd = useMutation({
    mutationFn: () => api.post('/auth/change-password', { old_password: oldPwd, new_password: newPwd }),
    onSuccess: () => {
      setPwdMsg('Password changed successfully')
      setOldPwd('')
      setNewPwd('')
    },
    onError: () => setPwdMsg('Wrong current password'),
  })

  return (
    <div className="max-w-lg flex flex-col gap-6">
      <h2 className="text-xl font-bold">Profile</h2>

      {/* User info */}
      <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Username</span>
          <span>{user?.username}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">Role</span>
          <span>{user?.role}</span>
        </div>
      </div>

      {/* PAC info */}
      {pac && (
        <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-3">
          <h3 className="text-sm font-semibold text-gray-400">Proxy Settings</h3>
          <div className="flex flex-col gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">PAC URL</span>
              <a href={pac.pac_url} className="text-blue-400 hover:underline truncate max-w-xs" target="_blank">
                {pac.pac_url}
              </a>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Proxy user</span>
              <span className="font-mono">{pac.proxy_user}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Proxy pass</span>
              <div className="flex items-center gap-2">
                <span className="font-mono">{showPass ? pac.proxy_pass : '••••••••'}</span>
                <button
                  onClick={() => setShowPass(s => !s)}
                  className="text-xs text-gray-500 hover:text-white transition-colors"
                >
                  {showPass ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Change password */}
      <div className="bg-gray-900 rounded-xl p-4 flex flex-col gap-3">
        <h3 className="text-sm font-semibold text-gray-400">Change Password</h3>
        <input
          className="bg-gray-800 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Current password"
          type="password"
          value={oldPwd}
          onChange={e => setOldPwd(e.target.value)}
        />
        <input
          className="bg-gray-800 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="New password"
          type="password"
          value={newPwd}
          onChange={e => setNewPwd(e.target.value)}
        />
        {pwdMsg && (
          <p className={`text-xs ${pwdMsg.includes('success') ? 'text-green-400' : 'text-red-400'}`}>
            {pwdMsg}
          </p>
        )}
        <button
          onClick={() => oldPwd && newPwd && mutChangePwd.mutate()}
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm transition-colors"
        >
          Change
        </button>
      </div>
    </div>
  )
}