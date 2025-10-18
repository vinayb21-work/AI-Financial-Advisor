import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from '@/lib/api'
import ChatHeader from '@/components/ChatHeader'
import ChatSidebar from '@/components/ChatSidebar'
import ChatMessages from '@/components/ChatMessages'
import ChatInput from '@/components/ChatInput'
import SetupPrompt from '@/components/SetupPrompt'
import { useAuthStore } from '@/store/authStore'

export default function Chat() {
  const { user } = useAuthStore()
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null)
  const [context, setContext] = useState<string>('all meetings')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const queryClient = useQueryClient()

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

