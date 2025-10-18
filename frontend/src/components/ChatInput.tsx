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
                >
                  {context}
                  <ChevronDown className="h-3.5 w-3.5" />
                </button>

                {showContextMenu && (
                  <div className="absolute bottom-full left-0 mb-2 w-48 overflow-hidden rounded-lg border border-gray-200 bg-white shadow-lg">
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
                          ctx === context && 'bg-gray-100 text-gray-900 font-medium'
                        )}
                      >
                        {ctx}
                      </button>
                    ))}
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

