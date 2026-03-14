import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import api from '../api/client'

const navItems = [
  { to: '/domains', label: 'Domains' },
  { to: '/profile', label: 'Profile' },
]

const adminItems = [
  { to: '/users', label: 'Users' },
  { to: '/logs', label: 'Logs' },
]

export default function Layout() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await api.post('/auth/logout')
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex bg-gray-950 text-white">
      <aside className="w-56 bg-gray-900 flex flex-col p-4 gap-1 shrink-0">
        <h1 className="text-lg font-bold text-white mb-6 px-2">Pi Gateway</h1>

        {navItems.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            {label}
          </NavLink>
        ))}

        {user?.role === 'admin' && (
          <>
            <div className="text-xs text-gray-600 px-2 mt-4 mb-1 uppercase tracking-wider">Admin</div>
            {adminItems.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  `px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive ? 'bg-blue-600 text-white' : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </>
        )}

        <div className="mt-auto pt-4 border-t border-gray-800">
          <div className="text-xs text-gray-500 px-2 mb-2">{user?.username}</div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white transition-colors"
          >
            Logout
          </button>
        </div>
      </aside>

      <main className="flex-1 p-8 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}