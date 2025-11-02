import { useState } from 'react'
import { ChatMessages } from './ChatMessages'
import { ChatBar } from './ChatBar'

export function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [analysisType, setAnalysisType] = useState('qualitative')

  const handleSendMessage = (text) => {
    const newMessage = {
      text,
      isUser: true,
      role: 'user'
    }
    setMessages(prev => [...prev, newMessage])
    
    // Here you can add logic to send to your backend API
    // For now, we'll just add a simple echo response
    setTimeout(() => {
      const aiResponse = {
        text: `You said: "${text}"`,
        isUser: false,
        role: 'assistant'
      }
      setMessages(prev => [...prev, aiResponse])
    }, 500)
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-b from-blue-50 to-purple-50">
      {/* Toggle switch for analysis type */}
      <div className="flex justify-center pt-6 pb-4">
        <div className="inline-flex rounded-lg border border-gray-300 bg-white overflow-hidden shadow-sm">
          {/* Qualitative option */}
          <button
            onClick={() => setAnalysisType('qualitative')}
            className={`flex items-center gap-2 px-6 py-2.5 text-sm font-medium transition-colors ${
              analysisType === 'qualitative'
                ? 'bg-purple-100 text-gray-800'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {analysisType === 'qualitative' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            <span>Qualitative</span>
          </button>
          
          {/* Divider */}
          <div className="w-px bg-gray-300" />
          
          {/* Quantitative option */}
          <button
            onClick={() => setAnalysisType('quantitative')}
            className={`flex items-center gap-2 px-6 py-2.5 text-sm font-medium transition-colors ${
              analysisType === 'quantitative'
                ? 'bg-purple-100 text-gray-800'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            {analysisType === 'quantitative' && (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            )}
            <span>Quantitative</span>
          </button>
        </div>
      </div>

      {/* Main chat area */}
      <ChatMessages messages={messages} />
      
      {/* Chat input bar */}
      <ChatBar onSendMessage={handleSendMessage} />
    </div>
  )
}
