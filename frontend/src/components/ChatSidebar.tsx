import { Plus, MessageSquare, Clock } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface Thread {
  id: string
  title: string
  context?: string
  created_at: string
  updated_at: string
}

interface ChatSidebarProps {
  threads: Thread[]
  currentThreadId: string | null
  onSelectThread: (threadId: string) => void
  onNewThread: () => void
}

export default function ChatSidebar({
  threads,
  currentThreadId,
  onSelectThread,
  onNewThread,
}: ChatSidebarProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')

  return (
    <div className="flex w-80 flex-col border-r border-gray-200 bg-white">
      <div className="border-b border-gray-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex gap-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={cn(
                'text-sm font-medium transition',
                activeTab === 'chat'
                  ? 'text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              Chat
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={cn(
                'text-sm font-medium transition',
                activeTab === 'history'
                  ? 'text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              )}
            >
              History
            </button>
          </div>

          <button
            onClick={onNewThread}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-blue-700"
          >
            <Plus className="h-4 w-4" />
            New thread
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <MessageSquare className="h-12 w-12 text-gray-300" />
            <p className="mt-3 text-sm text-gray-500">No conversations yet</p>
            <p className="mt-1 text-xs text-gray-400">
              Start a new thread to begin
            </p>
          </div>
        ) : (
          <div className="space-y-1">
            {threads.map((thread) => (
              <button
                key={thread.id}
                onClick={() => onSelectThread(thread.id)}
                className={cn(
                  'w-full rounded-lg p-3 text-left transition',
                  currentThreadId === thread.id
                    ? 'bg-blue-50 text-blue-900'
                    : 'text-gray-700 hover:bg-gray-50'
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="flex-1 truncate text-sm font-medium">
                    {thread.title}
                  </p>
                  <Clock className="h-3 w-3 flex-shrink-0 text-gray-400" />
                </div>
                {thread.context && (
                  <p className="mt-1 text-xs text-gray-500">{thread.context}</p>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

