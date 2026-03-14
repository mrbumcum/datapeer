import { useEffect } from 'react'
import { ChatMessages } from './ChatMessages'
import { ChatBar } from './ChatBar'
import { QuantitativeInsights } from './QuantitativeInsights'
import { useChat } from '../contexts/ChatContext'

export function ChatPanel() {
  const {
    messages,
    analysisType,
    setAnalysisType,
    quantAnalysis,
    selectedFiles,
    isLoading,
    fetchSelectedFiles,
    handleSendMessage
  } = useChat()

  useEffect(() => {
    fetchSelectedFiles()
    const interval = setInterval(fetchSelectedFiles, 20000)
    return () => clearInterval(interval)
  }, [fetchSelectedFiles])

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
