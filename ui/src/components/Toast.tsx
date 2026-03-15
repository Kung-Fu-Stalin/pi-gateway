import { create } from 'zustand'

interface Toast {
  id: number
  message: string
  type: 'error' | 'success'
}

interface ToastState {
  toasts: Toast[]
  add: (message: string, type?: 'error' | 'success') => void
  remove: (id: number) => void
}

export const useToast = create<ToastState>((set) => ({
  toasts: [],
  add: (message, type = 'error') => {
    const id = Date.now()
    set(s => ({ toasts: [...s.toasts, { id, message, type }] }))
    setTimeout(() => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })), 4000)
  },
  remove: (id) => set(s => ({ toasts: s.toasts.filter(t => t.id !== id) })),
}))

export default function ToastContainer() {
  const { toasts, remove } = useToast()

  return (
    <div className="fixed bottom-4 right-4 flex flex-col gap-2 z-50">
      {toasts.map(t => (
        <div
          key={t.id}
          onClick={() => remove(t.id)}
          className={`px-4 py-3 rounded-lg text-sm text-white shadow-lg cursor-pointer max-w-sm transition-all ${
            t.type === 'error' ? 'bg-red-600' : 'bg-green-600'
          }`}
        >
          {t.message}
        </div>
      ))}
    </div>
  )
}