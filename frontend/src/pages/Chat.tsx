import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi, integrationApi } from '../lib/api'
import ChatHeader from '../components/ChatHeader'
import ChatSidebar from '../components/ChatSidebar'
import ChatMessages from '../components/ChatMessages'
import ChatInput from '../components/ChatInput'
import SetupPrompt from '../components/SetupPrompt'
import { useAuthStore } from '../store/authStore'

export default function Chat() {
  const { user, updateUser } = useAuthStore()
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null)
  const [context, setContext] = useState<string>('all meetings')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const queryClient = useQueryClient()

  // Poll sync status to keep frontend in sync with backend
  const { data: syncStatus } = useQuery({
    queryKey: ['syncStatus'],
    queryFn: async () => {
      const response = await integrationApi.getSyncStatus()
      return response.data
    },
    refetchInterval: 30000, // Poll every 30 seconds
  })

  // Update user state when sync status changes
  useEffect(() => {
    if (syncStatus) {
      updateUser({
        gmail_synced: syncStatus.gmail?.synced || false,
        calendar_synced: syncStatus.calendar?.synced || false,
        hubspot_synced: syncStatus.hubspot?.synced || false,
      })
    }
  }, [syncStatus, updateUser])

  // Fetch threads
  const { data: threads } = useQuery({
    queryKey: ['threads'],
    queryFn: async () => {
      const response = await chatApi.getThreads()
      return response.data
    },
  })

  // Fetch current thread messages
  const { data: currentThread } = useQuery({
    queryKey: ['thread', currentThreadId],
    queryFn: async () => {
      if (!currentThreadId) return null
      const response = await chatApi.getThread(currentThreadId)
      return response.data
    },
    enabled: !!currentThreadId,
  })

  // Restore context when switching threads
  useEffect(() => {
    if (currentThread?.context) {
      setContext(currentThread.context)
    } else if (!currentThreadId) {
      // Reset to default for new threads
      setContext('all meetings')
    }
  }, [currentThread?.context, currentThreadId])

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: (content: string) =>
      chatApi.sendMessage({
        content,
        thread_id: currentThreadId || undefined,
        context,
      }),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['threads'] })
      if (response.data.thread_id) {
        setCurrentThreadId(response.data.thread_id)
        queryClient.invalidateQueries({
          queryKey: ['thread', response.data.thread_id],
        })
      }
    },
  })

  const handleSendMessage = (content: string) => {
    sendMessageMutation.mutate(content)
  }

  const handleNewThread = () => {
    setCurrentThreadId(null)
    queryClient.invalidateQueries({ queryKey: ['threads'] })
  }

  const handleRenameThread = async (threadId: string, newTitle: string) => {
    try {
      await chatApi.updateThread(threadId, { title: newTitle })
      queryClient.invalidateQueries({ queryKey: ['threads'] })
      queryClient.invalidateQueries({ queryKey: ['thread', threadId] })
    } catch (error) {
      console.error('Error renaming thread:', error)
    }
  }

  const handleDeleteThread = async (threadId: string) => {
    try {
      await chatApi.deleteThread(threadId)
      if (currentThreadId === threadId) {
        setCurrentThreadId(null)
      }
      queryClient.invalidateQueries({ queryKey: ['threads'] })
    } catch (error) {
      console.error('Error deleting thread:', error)
    }
  }

  // Check if setup is needed - all integrations must be connected and synced
  const needsSetup =
    !user?.hubspot_connected ||
    !user?.gmail_synced ||
    !user?.calendar_synced ||
    !user?.hubspot_synced

  if (needsSetup) {
    return <SetupPrompt />
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <ChatSidebar
        threads={threads || []}
        currentThreadId={currentThreadId}
        onSelectThread={setCurrentThreadId}
        onNewThread={handleNewThread}
        onRenameThread={handleRenameThread}
        onDeleteThread={handleDeleteThread}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      <div className="flex flex-1 flex-col">
        <ChatHeader
          context={context}
          onContextChange={setContext}
        />

        <ChatMessages
          messages={currentThread?.messages || []}
          loading={sendMessageMutation.isPending}
        />

        <ChatInput
          onSend={handleSendMessage}
          disabled={sendMessageMutation.isPending}
          context={context}
          onContextChange={setContext}
        />
      </div>
    </div>
  )
}

