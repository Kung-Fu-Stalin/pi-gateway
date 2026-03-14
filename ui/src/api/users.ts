import api from './client'

export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  created_at: string
  last_login?: string
}

export const getUsers = () =>
  api.get<User[]>('/users').then(r => r.data)

export const createUser = (data: { username: string; password: string; role: 'admin' | 'user' }) =>
  api.post<User>('/users', data).then(r => r.data)

export const deleteUser = (id: number) =>
  api.delete(`/users/${id}`)

export const resetPassword = (id: number, password: string) =>
  api.post(`/users/${id}/reset-password`, { password })
