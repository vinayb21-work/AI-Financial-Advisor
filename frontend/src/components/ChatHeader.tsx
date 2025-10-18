import { X, Settings } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'

interface ChatHeaderProps {
  context: string
  onContextChange: (context: string) => void
}

export default function ChatHeader({ context }: ChatHeaderProps) {
  const { user, logout } = useAuthStore()

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

