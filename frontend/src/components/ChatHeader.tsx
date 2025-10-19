import { RefreshCw, User } from 'lucide-react'
import { useAuthStore } from '../store/authStore.ts'
import { useMutation } from '@tanstack/react-query'
import { integrationApi } from '../lib/api.ts'
import { useState, useEffect } from 'react'

interface ChatHeaderProps {
  context: string
  onContextChange: (context: string) => void
}

export default function ChatHeader({ context }: ChatHeaderProps) {
  const { user, logout } = useAuthStore()
  const [syncMessage, setSyncMessage] = useState('')
  const [imageError, setImageError] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)

  // Reset image error when user changes
  useEffect(() => {
    setImageError(false)
  }, [user?.picture])

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('#user-menu')) {
        setShowUserMenu(false)
      }
    }
    
    if (showUserMenu) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [showUserMenu])

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
    <div className="flex items-center justify-between border-b border-gray-200 bg-white px-6 h-[88px]">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Ask Anything</h1>
          <div className="mt-1 flex items-center gap-2">
            <span className="text-sm text-gray-500">Searching:</span>
            <span className="inline-flex items-center rounded-md bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
              {context}
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
          {/* Sync Button */}
          <button
            onClick={() => syncAll.mutate()}
            disabled={syncAll.isPending}
            className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 transition hover:bg-gray-50 disabled:opacity-50"
            title="Sync all data"
          >
            <RefreshCw className={`h-4 w-4 ${syncAll.isPending ? 'animate-spin' : ''}`} />
            {syncMessage || 'Sync'}
          </button>

          {/* Profile Picture or Fallback Icon */}
          <div className="relative" id="user-menu">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="relative flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 overflow-hidden transition hover:ring-2 hover:ring-gray-300" 
              title={user?.name || user?.email || 'User'}
            >
              {user?.picture && !imageError ? (
                <img
                  src={user.picture}
                  alt={user.name || 'User'}
                  className="h-full w-full object-cover"
                  onError={() => setImageError(true)}
                  onLoad={() => setImageError(false)}
                />
              ) : (
                <User className="h-4 w-4 text-gray-600" />
              )}
            </button>

            {/* User Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-72 rounded-lg border border-gray-200 bg-white shadow-lg z-50">
                <div className="p-4 border-b border-gray-200">
                  <div className="flex items-start gap-3">
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-gray-100 overflow-hidden">
                      {user?.picture && !imageError ? (
                        <img
                          src={user.picture}
                          alt={user.name || 'User'}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <User className="h-5 w-5 text-gray-600" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {user?.name || 'User'}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {user?.email}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-2">
                  <div className="rounded-lg bg-gray-50 px-3 py-2 text-xs text-gray-600">
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">Gmail:</span>
                      <span className={user?.gmail_synced ? 'text-green-600' : 'text-gray-400'}>
                        {user?.gmail_synced ? '✓ Synced' : 'Not synced'}
                      </span>
                    </div>
                    <div className="flex justify-between mb-1">
                      <span className="font-medium">Calendar:</span>
                      <span className={user?.calendar_synced ? 'text-green-600' : 'text-gray-400'}>
                        {user?.calendar_synced ? '✓ Synced' : 'Not synced'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium">Hubspot:</span>
                      <span className={user?.hubspot_synced ? 'text-green-600' : 'text-gray-400'}>
                        {user?.hubspot_synced ? '✓ Synced' : 'Not synced'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-2 border-t border-gray-200">
                  <button
                    onClick={() => {
                      setShowUserMenu(false)
                      logout()
                    }}
                    className="w-full rounded-lg px-3 py-2 text-left text-sm text-red-600 transition hover:bg-red-50"
                  >
                    Sign out
                  </button>
                </div>
              </div>
            )}
          </div>
      </div>
    </div>
  )
}

