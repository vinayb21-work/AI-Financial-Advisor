import { X, RefreshCw } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useMutation } from '@tanstack/react-query'
import { integrationApi } from '@/lib/api'
import { useState } from 'react'

interface ChatHeaderProps {
  context: string
  onContextChange: (context: string) => void
}

export default function ChatHeader({ context }: ChatHeaderProps) {
  const { user, logout } = useAuthStore()
  const [syncMessage, setSyncMessage] = useState('')

  const syncAll = useMutation({
    mutationFn: async () => {
      setSyncMessage('Syncing...')
      await Promise.all([
        integrationApi.syncGmail(),
        integrationApi.syncCalendar(),
        integrationApi.syncHubspot()
      ])
    },
    onSuccess: () => {
      setSyncMessage('✓ Synced!')
      setTimeout(() => setSyncMessage(''), 3000)
    },
    onError: () => {
      setSyncMessage('✗ Error')
      setTimeout(() => setSyncMessage(''), 3000)
    }
  })

  return (
    <div className="border-b border-gray-200 bg-white px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Ask Anything</h1>
          <p className="mt-1 text-sm text-gray-500">
            Context set to {context}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Sync Button */}
          <button
            onClick={() => syncAll.mutate()}
            disabled={syncAll.isPending}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition hover:bg-blue-700 disabled:opacity-50"
            title="Sync all data"
          >
            <RefreshCw className={`h-4 w-4 ${syncAll.isPending ? 'animate-spin' : ''}`} />
            {syncMessage || 'Sync'}
          </button>

          {user?.picture && (
            <img
              src={user.picture}
              alt={user.name}
              className="h-8 w-8 rounded-full"
            />
          )}
          <button
            onClick={logout}
            className="rounded-lg p-2 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
            title="Logout"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

