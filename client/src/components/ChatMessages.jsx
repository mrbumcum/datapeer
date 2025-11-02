import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'

export function ChatMessages({ messages = [], isLoading = false }) {
  const messagesEndRef = useRef(null)
  const containerRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isLoading])

  return (
    <div 
      ref={containerRef}
      className="flex-1 overflow-y-auto px-4 py-6 min-h-0"
      style={{ maxHeight: '100%' }}
    >
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 && !isLoading ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <ChatMessage 
                key={index} 
                message={msg.text || msg.content || msg} 
                isUser={msg.isUser || msg.role === 'user'} 
              />
            ))}
            {isLoading && (
              <ChatMessage 
                message="" 
                isUser={false} 
                isLoading={true}
              />
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  )
}
