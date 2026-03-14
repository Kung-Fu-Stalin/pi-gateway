import { useState, useEffect, useRef } from 'react'
import { useAuthStore } from '../store/auth'
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

interface LogEntry {
  id: number
  timestamp: string
  client_ip: string
  username: string
  method: string
  url: string
  status_code: number
  bytes: number
}

interface LogsResponse {
  items: LogEntry[]
  total: number
  page: number
  limit: number
}

export default function LogsPage() {
  const [page, setPage] = useState(1)
  const [live, setLive] = useState(false)
  const [liveLines, setLiveLines] = useState<string[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  const limit = 50

  const { data, isLoading } = useQuery({
    queryKey: ['logs', page],
    queryFn: () =>
      api.get<LogsResponse>(`/logs?page=${page}&limit=${limit}`).then(r => r.data),
    enabled: !live,
    refetchInterval: live ? false : 10000,
  })

  useEffect(() => {
    if (!live) {
      wsRef.current?.close()
      wsRef.current = null
      return
    }

    const token = useAuthStore.getState().accessToken
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'

    const ws = new WebSocket(
      `${protocol}//${window.location.host}/ws/logs?token=${token}`
    )

    wsRef.current = ws

    ws.onopen = () => {
      console.log('Logs websocket connected')
    }

    ws.onmessage = (e) => {
      setLiveLines(prev => [...prev, e.data].slice(-200))
    }

    ws.onerror = () => {
      setLive(false)
      setLiveLines([])
    }

    ws.onclose = () => {
      setLive(false)
    }

    return () => {
      ws.close()
    }
  }, [live])

  const totalPages = data ? Math.ceil(data.total / limit) : 1

  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold">Logs</h2>

        <button
          onClick={() => {
            setLive(l => !l)
            setLiveLines([])
          }}
          className={`text-sm px-4 py-1.5 rounded-lg transition-colors ${
            live
              ? 'bg-red-700 hover:bg-red-600 text-white'
              : 'bg-gray-800 hover:bg-gray-700 text-gray-300'
          }`}
        >
          {live ? '⏹ Stop live' : '▶ Live'}
        </button>
      </div>

      {live ? (
        <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs text-green-400 h-[600px] overflow-auto flex flex-col gap-0.5">
          {liveLines.length === 0 && (
            <span className="text-gray-600">Waiting for logs...</span>
          )}

          {liveLines.map((line, i) => (
            <div key={i}>{line}</div>
          ))}
        </div>
      ) : (
        <>
          {isLoading && <div className="text-gray-500">Loading...</div>}

          {data && (
            <>
              <div className="bg-gray-900 rounded-xl overflow-hidden mb-4">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-500 text-xs border-b border-gray-800">
                      <th className="text-left px-4 py-2">Time</th>
                      <th className="text-left px-4 py-2">User</th>
                      <th className="text-left px-4 py-2">Method</th>
                      <th className="text-left px-4 py-2">URL</th>
                      <th className="text-left px-4 py-2">Status</th>
                      <th className="text-left px-4 py-2">Bytes</th>
                    </tr>
                  </thead>

                  <tbody>
                    {data.items.map(log => (
                      <tr
                        key={log.id}
                        className="border-b border-gray-800 last:border-0 hover:bg-gray-800 transition-colors"
                      >
                        <td className="px-4 py-2 text-gray-500 text-xs whitespace-nowrap">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </td>

                        <td className="px-4 py-2 text-gray-300">
                          {log.username}
                        </td>

                        <td className="px-4 py-2 text-gray-400">
                          {log.method}
                        </td>

                        <td className="px-4 py-2 text-gray-300 truncate max-w-xs">
                          {log.url}
                        </td>

                        <td className="px-4 py-2">
                          <span
                            className={`text-xs ${
                              log.status_code < 400
                                ? 'text-green-400'
                                : 'text-red-400'
                            }`}
                          >
                            {log.status_code}
                          </span>
                        </td>

                        <td className="px-4 py-2 text-gray-500 text-xs">
                          {log.bytes}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>Total: {data.total}</span>

                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 bg-gray-800 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors"
                  >
                    ←
                  </button>

                  <span className="px-3 py-1">
                    {page} / {totalPages}
                  </span>

                  <button
                    onClick={() =>
                      setPage(p => Math.min(totalPages, p + 1))
                    }
                    disabled={page === totalPages}
                    className="px-3 py-1 bg-gray-800 rounded-lg disabled:opacity-40 hover:bg-gray-700 transition-colors"
                  >
                    →
                  </button>
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
