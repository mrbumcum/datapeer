import { useState } from 'react'
import sendIcon from '../assets/send-svgrepo-com.svg'

export function ChatBar({ onSendMessage, disabled = false }) {
  const [message, setMessage] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (message.trim() && !disabled) {
      onSendMessage?.(message.trim())
      setMessage('')
    }
  }

  return (
    <div className="border-t border-gray-200 bg-white px-4 py-3 flex-shrink-0">
      <form onSubmit={handleSubmit} className="flex items-center gap-3 max-w-4xl mx-auto">
        {/* Attachment icon */}
        <button
          type="button"
          className="flex-shrink-0 w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Attach file"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
        </button>
        
        {/* Input field */}
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask me anything..."
          disabled={disabled}
          className="flex-1 px-4 py-2.5 bg-gray-100 rounded-full text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-300 focus:bg-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        />
        
        {/* Action buttons */}
        <div className="flex items-center gap-2">
          {/* Send button */}
          <button
            type="submit"
            disabled={!message.trim() || disabled}
            className="flex-shrink-0 w-8 h-8 flex items-center justify-center text-white bg-purple-500 rounded-full hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="Send message"
          >
            <img src={sendIcon} alt="Send" className="w-4 h-4 brightness-0 invert" />
          </button>
        </div>
      </form>
    </div>
  )
}