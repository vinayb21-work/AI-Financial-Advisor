import { useState } from 'react'
import { Send, Plus, Mic, ChevronDown } from 'lucide-react'
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
    'all meetings',
    'recent emails',
    'contacts',
    'upcoming events',
    'all data',
  ]

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      <form onSubmit={handleSubmit} className="mx-auto max-w-3xl">
        <div className="relative flex items-end gap-2">
          <button
            type="button"
            className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
          >
            <Plus className="h-5 w-5" />
          </button>

          <div className="flex-1">
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
              className="max-h-32 min-h-[2.5rem] w-full resize-none rounded-2xl border border-gray-300 bg-white px-4 py-2.5 text-sm placeholder:text-gray-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              rows={1}
            />
          </div>

          <div className="flex items-center gap-2">
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowContextMenu(!showContextMenu)}
                className={cn(
                  'flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition',
                  'border border-gray-300 bg-white hover:bg-gray-50'
                )}
              >
                {context}
                <ChevronDown className="h-4 w-4" />
              </button>

              {showContextMenu && (
                <div className="absolute bottom-full right-0 mb-2 w-48 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
                  {contexts.map((ctx) => (
                    <button
                      key={ctx}
                      type="button"
                      onClick={() => {
                        onContextChange(ctx)
                        setShowContextMenu(false)
                      }}
                      className={cn(
                        'w-full px-4 py-2 text-left text-sm transition hover:bg-gray-50',
                        ctx === context && 'bg-blue-50 text-blue-600'
                      )}
                    >
                      {ctx}
                    </button>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-full text-gray-400 transition hover:bg-gray-100 hover:text-gray-600"
            >
              <Mic className="h-5 w-5" />
            </button>

            <button
              type="submit"
              disabled={disabled || !message.trim()}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-600 text-white transition hover:bg-blue-700 disabled:opacity-50"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}

