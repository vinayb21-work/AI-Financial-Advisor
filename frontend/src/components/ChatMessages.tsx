import { useEffect, useRef } from 'react'
import { Loader2, User, Bot, Calendar, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Message {
  id: string
  role: string
  content: string
  tool_calls?: any
  tool_results?: any
  created_at: string
}

interface ChatMessagesProps {
  messages: Message[]
  loading?: boolean
}

export default function ChatMessages({ messages, loading }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Format conversation start time
  const formatConversationTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    // Set time to midnight for accurate day comparison
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate())
    const todayOnly = new Date(today.getFullYear(), today.getMonth(), today.getDate())
    const yesterdayOnly = new Date(yesterday.getFullYear(), yesterday.getMonth(), yesterday.getDate())

    if (dateOnly.getTime() === todayOnly.getTime()) {
      return `Today at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`
    } else if (dateOnly.getTime() === yesterdayOnly.getTime()) {
      return `Yesterday at ${date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })}`
    } else {
      const options: Intl.DateTimeFormatOptions = { 
        month: 'short', 
        day: 'numeric',
        hour: 'numeric', 
        minute: '2-digit',
        hour12: true
      }
      // Only add year if not current year
      if (date.getFullYear() !== today.getFullYear()) {
        options.year = 'numeric'
      }
      return date.toLocaleDateString('en-US', options)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto max-w-3xl space-y-6">
        {/* Show conversation start time */}
        {messages.length > 0 && (
          <div className="flex justify-center">
            <div className="rounded-full bg-gray-100 px-4 py-1.5 text-xs font-medium text-gray-600">
              {formatConversationTime(messages[0].created_at)}
            </div>
          </div>
        )}

        {messages.length === 0 && !loading && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <Bot className="h-16 w-16 text-gray-400" />
            <h2 className="mt-4 text-xl font-semibold text-gray-900">
              I can answer questions about any Jump meeting.
            </h2>
            <p className="mt-2 text-gray-600">
              What do you want to know?
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-4',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-100">
                <Bot className="h-5 w-5 text-gray-600" />
              </div>
            )}

            <div
              className={cn(
                'max-w-[80%] rounded-2xl px-4 py-3',
                message.role === 'user'
                  ? 'bg-gray-100 text-gray-900'
                  : 'bg-white text-gray-900 shadow-sm ring-1 ring-gray-200'
              )}
            >
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {message.content}
              </p>

              {/* Render tool results if any */}
              {message.tool_results && message.tool_results.length > 0 && (
                <div className="mt-3 space-y-2">
                  {message.tool_results.map((result: any, idx: number) => (
                    <div
                      key={idx}
                      className="rounded-lg border border-gray-200 bg-gray-50 p-3"
                    >
                      <p className="text-xs font-medium text-gray-700">
                        🔧 {result.function_name || 'Tool'}
                      </p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {result.tool_call_id}
                      </p>
                      {result.result.status && (
                        <p className="mt-1 text-xs text-gray-700">
                          Status: {result.result.status}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-200">
                <User className="h-5 w-5 text-gray-600" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-4">
            <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-100">
              <Bot className="h-5 w-5 text-gray-600" />
            </div>
            <div className="rounded-2xl bg-white px-4 py-3 shadow-sm ring-1 ring-gray-200">
              <Loader2 className="h-5 w-5 animate-spin text-gray-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}

