import { useCallback, useEffect, useState } from 'react'
import { ChatMessages } from './ChatMessages'
import { ChatBar } from './ChatBar'
import { QuantitativeInsights } from './QuantitativeInsights'

const API_BASE_URL = 'http://localhost:8000'

export function ChatPanel() {
  const [messages, setMessages] = useState([])
  const [analysisType, setAnalysisType] = useState('qualitative')
  const [isLoading, setIsLoading] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState([])
  const [quantAnalysis, setQuantAnalysis] = useState({
    code: '',
    explanation: '',
    dataOutput: '',
    summary: '',
    files: [],
    codeSuccess: null,
    codeError: null,
    updatedAt: null
  })

  const fetchSelectedFiles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/selected`)
      if (!response.ok) {
        throw new Error('Failed to fetch selected files')
      }
      const data = await response.json()
      const files = data.files || []
      setSelectedFiles(files)
      return files
    } catch (error) {
      console.error('Error fetching selected files:', error)
      return []
    }
  }, [])

  useEffect(() => {
    fetchSelectedFiles()
    const interval = setInterval(fetchSelectedFiles, 20000)
    return () => clearInterval(interval)
  }, [fetchSelectedFiles])

  const handleSendMessage = async (text) => {
    const newMessage = {
      text,
      isUser: true,
      role: 'user'
    }
    setMessages(prev => [...prev, newMessage])
    setIsLoading(true)
    
    try {
      const latestSelectedFiles = await fetchSelectedFiles()
      
      if (latestSelectedFiles.length === 0) {
        const errorMessage = {
          text: "Please select at least one dataset from the Database page before asking questions.",
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
          selected_file_ids: latestSelectedFiles.map(f => f.id)
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

      if (chatData.analysis_type === 'quantitative') {
        setQuantAnalysis({
          code: chatData.code || '',
          explanation: chatData.code_explanation || '',
          dataOutput: chatData.data_output || '',
          summary: chatData.response || '',
          files: chatData.files_analyzed || [],
          codeSuccess: chatData.code_success ?? null,
          codeError: chatData.code_error || null,
          updatedAt: new Date().toISOString()
        })
      }
      
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
    <div className="flex-1 flex flex-col bg-linear-to-b from-blue-50 to-purple-50 min-h-0 overflow-hidden">
      {/* Toggle switch for analysis type */}
      <div className="flex justify-center pt-6 pb-4 shrink-0">
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

      <div className="flex-1 flex flex-col lg:flex-row gap-4 px-4 pb-6 overflow-hidden">
        {/* Chat column */}
        <div className="flex flex-col flex-1 min-h-0 bg-transparent rounded-3xl">
          <ChatMessages messages={messages} isLoading={isLoading} />
          <ChatBar onSendMessage={handleSendMessage} disabled={isLoading} />
        </div>

        {/* Analysis column */}
        {analysisType === 'quantitative' && (
          <QuantitativeInsights
            quantAnalysis={quantAnalysis}
            selectedFiles={selectedFiles}
            isLoading={isLoading}
          />
        )}
      </div>
    </div>
  )
}
