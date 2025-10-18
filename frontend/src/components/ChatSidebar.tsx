import { Plus, MessageSquare, PanelLeftClose, PanelLeft } from 'lucide-react'
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
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function ChatSidebar({
  threads,
  currentThreadId,
  onSelectThread,
  onNewThread,
  collapsed,
  onToggleCollapse,
}: ChatSidebarProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')

  // Filter threads based on active tab
  const displayThreads = activeTab === 'chat' 
    ? threads.filter(t => t.id === currentThreadId)
    : threads

  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  return (
    <div className={cn(
      "flex flex-col border-r border-gray-200 bg-white transition-all duration-300",
      collapsed ? "w-16" : "w-80"
    )}>
      <div className="flex items-center justify-between border-b border-gray-200 px-3 h-[88px]">
        {!collapsed ? (
          <>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setActiveTab('chat')}
                className={cn(
                  'text-sm font-medium transition relative',
                  activeTab === 'chat'
                    ? 'text-gray-900'
                    : 'text-gray-500 hover:text-gray-700'
                )}
              >
                Chat
                {activeTab === 'chat' && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-gray-900" />
                )}
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={cn(
                  'text-sm font-medium transition relative',
                  activeTab === 'history'
                    ? 'text-gray-900'
                    : 'text-gray-500 hover:text-gray-700'
                )}
              >
                History
                {activeTab === 'history' && (
                  <div className="absolute -bottom-4 left-0 right-0 h-0.5 bg-gray-900" />
                )}
              </button>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={onNewThread}
                className="flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-100"
              >
                <Plus className="h-4 w-4" />
                New Thread
              </button>
              <button
                onClick={onToggleCollapse}
                className="flex items-center justify-center rounded-lg p-1.5 text-gray-400 transition hover:bg-gray-100"
                title="Close sidebar"
              >
                <PanelLeftClose className="h-5 w-5" />
              </button>
            </div>
          </>
        ) : (
          <div className="mx-auto flex flex-col items-center gap-2">
            <button
              onClick={onToggleCollapse}
              className="rounded-lg p-1.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
              title="Open sidebar"
            >
              <PanelLeft className="h-5 w-5" />
            </button>
            <button
              onClick={onNewThread}
              className="rounded-lg p-1.5 text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
              title="New thread"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {!collapsed ? (
          displayThreads.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <MessageSquare className="h-12 w-12 text-gray-300" />
              <p className="mt-3 text-sm text-gray-500">
                {activeTab === 'chat' ? 'No active conversation' : 'No conversations yet'}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                Start a new thread to begin
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {displayThreads.map((thread) => (
                <button
                  key={thread.id}
                  onClick={() => {
                    onSelectThread(thread.id)
                    setActiveTab('chat')
                  }}
                  className={cn(
                    'w-full rounded-lg p-3 text-left transition',
                    currentThreadId === thread.id
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-700 hover:bg-gray-50'
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="flex-1 truncate text-sm font-medium">
                      {thread.title}
                    </p>
                    <span className="flex-shrink-0 text-xs text-gray-400">
                      {formatTime(thread.updated_at)}
                    </span>
                  </div>
                  {thread.context && (
                    <p className="mt-1 text-xs text-gray-500">{thread.context}</p>
                  )}
                </button>
              ))}
            </div>
          )
        ) : (
          <div className="flex flex-col items-center gap-2 py-4">
            {threads.slice(0, 5).map((thread) => (
              <button
                key={thread.id}
                onClick={() => {
                  onSelectThread(thread.id)
                  setActiveTab('chat')
                }}
                className={cn(
                  'rounded-lg p-2 transition',
                  currentThreadId === thread.id
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-400 hover:bg-gray-100 hover:text-gray-600'
                )}
                title={thread.title}
              >
                <MessageSquare className="h-5 w-5" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

