import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/auth'
import { useAuth } from './hooks/useAuth'
import ToastContainer from './components/Toast'
import LoginPage from './pages/LoginPage'
import LogsPage from './pages/LogsPage'
import UsersPage from './pages/UsersPage'
import ProfilePage from './pages/ProfilePage'
import DomainsPage from './pages/DomainsPage'
import Layout from './components/Layout'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { accessToken } = useAuthStore()
  const { loading } = useAuth()

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="text-gray-500 text-sm">Loading...</div>
    </div>
  )

  if (!accessToken) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/domains" replace />} />
          <Route path="domains" element={<DomainsPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="users" element={<UsersPage />} />
          <Route path="logs" element={<LogsPage />} />
        </Route>
      </Routes>
    </>
  )
}