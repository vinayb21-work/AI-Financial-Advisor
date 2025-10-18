import { useState } from 'react'
import { Send, Plus, Mic, ChevronDown, Calendar, Mail, Users, Clock, Database } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  context: string
  onContextChange: (context: string) => void
}

export default function ChatInput({
  onSend,
  disabled,
  context,
  onContextChange,
}: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [showContextMenu, setShowContextMenu] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSend(message)
      setMessage('')
    }
  }

  const contexts = [
    { value: 'all meetings', icon: Calendar, description: 'Search calendar events' },
    { value: 'recent emails', icon: Mail, description: 'Search last 30 days of emails' },
    { value: 'contacts', icon: Users, description: 'Search Hubspot contacts' },
    { value: 'upcoming events', icon: Clock, description: 'Search future calendar events' },
    { value: 'all data', icon: Database, description: 'Search everything' },
  ]

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-4xl">
        {/* Single unified input box - vertical layout */}
        <div className="relative rounded-3xl border border-gray-300 bg-white shadow-sm focus-within:border-gray-400 focus-within:ring-1 focus-within:ring-gray-400">
          {/* Input at top */}
          <div className="px-4 pt-4">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
              placeholder="Ask anything about your meetings..."
              disabled={disabled}
              className="max-h-32 min-h-[60px] w-full resize-none overflow-y-auto bg-transparent text-sm placeholder:text-gray-400 focus:outline-none disabled:opacity-50"
              rows={1}
            />
          </div>

          {/* Controls at bottom */}
          <div className="flex items-center justify-between border-t border-gray-200 px-3 py-2">
            <div className="flex items-center gap-2">
              <button
                type="button"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-300 text-gray-500 transition hover:bg-gray-50"
              >
                <Plus className="h-4 w-4" />
              </button>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setShowContextMenu(!showContextMenu)}
                  className="flex h-8 items-center gap-1.5 rounded-lg border border-gray-300 px-3 text-xs font-medium text-gray-600 transition hover:bg-gray-50"
                  title="Change search context"
                >
                  {(() => {
                    const currentContext = contexts.find(c => c.value === context)
                    const ContextIcon = currentContext?.icon || Database
                    return <ContextIcon className="h-3.5 w-3.5" />
                  })()}
                  {context}
                  <ChevronDown className="h-3.5 w-3.5" />
                </button>

                {showContextMenu && (
                  <div className="absolute bottom-full left-0 mb-2 w-64 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
                    {contexts.map((ctx) => {
                      const Icon = ctx.icon
                      return (
                        <button
                          key={ctx.value}
                          type="button"
                          onClick={() => {
                            onContextChange(ctx.value)
                            setShowContextMenu(false)
                          }}
                          className={cn(
                            'w-full px-4 py-2.5 text-left transition hover:bg-gray-50 flex items-start gap-3',
                            ctx.value === context && 'bg-gray-100 text-gray-900'
                          )}
                        >
                          <Icon className="h-4 w-4 mt-0.5 flex-shrink-0 text-gray-500" />
                          <div className="flex-1 min-w-0">
                            <div className={cn(
                              'text-sm font-medium',
                              ctx.value === context && 'text-gray-900'
                            )}>
                              {ctx.value}
                            </div>
                            <div className="text-xs text-gray-500 mt-0.5">
                              {ctx.description}
                            </div>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                className="flex h-8 w-8 items-center justify-center rounded-lg border border-gray-300 text-gray-500 transition hover:bg-gray-50"
              >
                <Mic className="h-4 w-4" />
              </button>

              <button
                type="submit"
                disabled={disabled || !message.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-gray-700 text-white transition hover:bg-gray-800 disabled:opacity-50"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  )
}

