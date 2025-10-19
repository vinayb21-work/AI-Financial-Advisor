import { Plus, MessageSquare, PanelLeftClose, PanelLeft, Trash2, Edit2, X, MoreVertical } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { cn } from '../lib/utils.ts'

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
  onRenameThread: (threadId: string, newTitle: string) => Promise<void>
  onDeleteThread: (threadId: string) => Promise<void>
  collapsed: boolean
  onToggleCollapse: () => void
}

export default function ChatSidebar({
  threads,
  currentThreadId,
  onSelectThread,
  onNewThread,
  onRenameThread,
  onDeleteThread,
  collapsed,
  onToggleCollapse,
}: ChatSidebarProps) {
  const [activeTab, setActiveTab] = useState<'chat' | 'history'>('chat')
  const [renameThreadId, setRenameThreadId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const [deleteThreadId, setDeleteThreadId] = useState<string | null>(null)
  const [menuOpenThreadId, setMenuOpenThreadId] = useState<string | null>(null)
  const menuRef = useRef<HTMLDivElement>(null)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpenThreadId(null)
      }
    }

    if (menuOpenThreadId) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [menuOpenThreadId])

  const handleRenameSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (renameThreadId && renameValue.trim()) {
      await onRenameThread(renameThreadId, renameValue.trim())
      setRenameThreadId(null)
      setRenameValue('')
    }
  }

  const handleDeleteConfirm = async () => {
    if (deleteThreadId) {
      await onDeleteThread(deleteThreadId)
      setDeleteThreadId(null)
    }
  }

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
                <div
                  key={thread.id}
                  className="relative group"
                >
                  <button
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
                      <p className="flex-1 truncate text-sm font-medium pr-8">
                        {thread.title}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="flex-shrink-0 text-xs text-gray-400">
                          {formatTime(thread.updated_at)}
                        </span>
                        {/* 3-dot menu (show in History tab only) */}
                        {activeTab === 'history' && (
                          <div className="relative" ref={menuOpenThreadId === thread.id ? menuRef : null}>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                setMenuOpenThreadId(menuOpenThreadId === thread.id ? null : thread.id)
                              }}
                              className="opacity-0 group-hover:opacity-100 rounded p-1 text-gray-400 hover:bg-gray-200 hover:text-gray-600 transition-opacity"
                              title="Options"
                            >
                              <MoreVertical className="h-4 w-4" />
                            </button>

                            {/* Dropdown menu */}
                            {menuOpenThreadId === thread.id && (
                              <div className="absolute right-0 top-8 z-50 w-40 rounded-lg border border-gray-200 bg-white py-1 shadow-lg">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setMenuOpenThreadId(null)
                                    setRenameThreadId(thread.id)
                                    setRenameValue(thread.title)
                                  }}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                                >
                                  <Edit2 className="h-4 w-4" />
                                  Rename
                                </button>
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    setMenuOpenThreadId(null)
                                    setDeleteThreadId(thread.id)
                                  }}
                                  className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                                >
                                  <Trash2 className="h-4 w-4" />
                                  Delete
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                    {thread.context && (
                      <p className="mt-1 text-xs text-gray-500">{thread.context}</p>
                    )}
                  </button>
                </div>
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

      {/* Rename Modal */}
      {renameThreadId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" onClick={() => setRenameThreadId(null)}>
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Rename Chat</h3>
              <button
                onClick={() => setRenameThreadId(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleRenameSubmit}>
              <input
                type="text"
                value={renameValue}
                onChange={(e) => setRenameValue(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-gray-500 focus:outline-none focus:ring-1 focus:ring-gray-500"
                placeholder="Enter new title"
                autoFocus
              />
              <div className="mt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setRenameThreadId(null)}
                  className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-800"
                  disabled={!renameValue.trim()}
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteThreadId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" onClick={() => setDeleteThreadId(null)}>
          <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Delete Chat</h3>
              <button
                onClick={() => setDeleteThreadId(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-6">
              Are you sure you want to delete this chat? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDeleteThreadId(null)}
                className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteConfirm}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

