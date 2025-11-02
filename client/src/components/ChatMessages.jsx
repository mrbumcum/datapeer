import { ChatMessage } from './ChatMessage'

export function ChatMessages({ messages = [] }) {
  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>No messages yet. Start a conversation!</p>
          </div>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage 
              key={index} 
              message={msg.text || msg.content || msg} 
              isUser={msg.isUser || msg.role === 'user'} 
            />
          ))
        )}
      </div>
    </div>
  )
}
