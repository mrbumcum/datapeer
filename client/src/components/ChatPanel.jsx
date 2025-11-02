import { useState } from 'react'
import { ChatMessages } from './ChatMessages'
import { ChatBar } from './ChatBar'

const API_BASE_URL = 'http://localhost:8000'

export function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [analysisType, setAnalysisType] = useState('qualitative')
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (text) => {
    const newMessage = {
      text,
      isUser: true,
      role: 'user'
    }
    setMessages(prev => [...prev, newMessage])
    setIsLoading(true)
    
    try {
      // Fetch selected files
      const filesResponse = await fetch(`${API_BASE_URL}/api/files/selected`)
      if (!filesResponse.ok) {
        throw new Error('Failed to fetch selected files')
      }
      
      const filesData = await filesResponse.json()
      const selectedFiles = filesData.files || []
      
      if (selectedFiles.length === 0) {
        const errorMessage = {
          text: "Please select at least one dataset from the Database page before asking questions.",
          isUser: false,
          role: 'assistant'
        }
        setMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }
      
      // Only proceed if qualitative is selected (as requested)
      if (analysisType !== 'qualitative') {
        const errorMessage = {
          text: "Quantitative analysis is not yet implemented. Please use qualitative analysis.",
          isUser: false,
          role: 'assistant'
        }
        setMessages(prev => [...prev, errorMessage])
        setIsLoading(false)
        return
      }
      
      // Send message to backend with selected files
      const chatResponse = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: text,
          analysis_type: analysisType,
          selected_file_ids: selectedFiles.map(f => f.id)
        })
      })
      
      if (!chatResponse.ok) {
        const errorData = await chatResponse.json().catch(() => ({}))
        throw new Error(errorData.detail || 'Failed to get response from server')
      }
      
      const chatData = await chatResponse.json()
      const aiResponse = {
        text: chatData.response || "No response received",
        isUser: false,
        role: 'assistant'
      }
      setMessages(prev => [...prev, aiResponse])
      
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage = {
        text: `Error: ${error.message || 'Failed to process your message. Please try again.'}`,
        isUser: false,
        role: 'assistant'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-gradient-to-b from-blue-50 to-purple-50 min-h-0 overflow-hidden">
      {/* Toggle switch for analysis type */}
      <div className="flex justify-center pt-6 pb-4 flex-shrink-0">
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
      <ChatMessages messages={messages} isLoading={isLoading} />
      
      {/* Chat input bar */}
      <ChatBar onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
