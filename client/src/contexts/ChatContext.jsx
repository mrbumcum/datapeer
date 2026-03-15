import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const CHAT_STORAGE_KEY = 'datapeer_chat'

const defaultQuantAnalysis = {
  code: '',
  explanation: '',
  dataOutput: '',
  summary: '',
  files: [],
  codeSuccess: null,
  codeError: null,
  updatedAt: null
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(CHAT_STORAGE_KEY)
    if (!raw) return null
    const data = JSON.parse(raw)
    return {
      messages: data.messages ?? [],
      analysisType: data.analysisType ?? 'qualitative',
      quantAnalysis: data.quantAnalysis ?? defaultQuantAnalysis,
      provider: data.provider ?? 'openai',
      model: data.model ?? 'gpt-5-mini-2025-08-07'
    }
  } catch {
    return null
  }
}

function saveToStorage(messages, analysisType, quantAnalysis, provider, model) {
  try {
    localStorage.setItem(
      CHAT_STORAGE_KEY,
      JSON.stringify({
        messages,
        analysisType,
        quantAnalysis: quantAnalysis ?? defaultQuantAnalysis,
        provider: provider ?? 'openai',
        model: model ?? 'gpt-5-mini-2025-08-07'
      })
    )
  } catch {
    // ignore storage errors
  }
}

const ChatContext = createContext(null)

export function ChatProvider({ children, apiBaseUrl = 'http://localhost:8000' }) {
  const [messages, setMessages] = useState([])
  const [analysisType, setAnalysisType] = useState('qualitative')
  const [quantAnalysis, setQuantAnalysis] = useState(defaultQuantAnalysis)
  const [provider, setProvider] = useState('openai')
  const [model, setModel] = useState('gpt-5-mini-2025-08-07')
  const [selectedFiles, setSelectedFiles] = useState([])
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const cached = loadFromStorage()
    if (cached) {
      setMessages(cached.messages)
      setAnalysisType(cached.analysisType)
      setQuantAnalysis(cached.quantAnalysis)
      setProvider(cached.provider ?? 'openai')
      setModel(cached.model ?? 'gpt-5-mini-2025-08-07')
    }
  }, [])

  useEffect(() => {
    saveToStorage(messages, analysisType, quantAnalysis, provider, model)
  }, [messages, analysisType, quantAnalysis, provider, model])

  const fetchSelectedFiles = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/files/selected`)
      if (!response.ok) throw new Error('Failed to fetch selected files')
      const data = await response.json()
      const files = data.files ?? []
      setSelectedFiles(files)
      return files
    } catch (error) {
      console.error('Error fetching selected files:', error)
      return []
    }
  }, [apiBaseUrl])

  const handleSendMessage = useCallback(
    async (text) => {
      const newMessage = { text, isUser: true, role: 'user' }
      setMessages((prev) => [...prev, newMessage])
      setIsLoading(true)

      try {
        const latestSelectedFiles = await fetchSelectedFiles()
        if (latestSelectedFiles.length === 0) {
          const errorMessage = {
            text: 'Please select at least one dataset from the Database page before asking questions.',
            isUser: false,
            role: 'assistant'
          }
          setMessages((prev) => [...prev, errorMessage])
          setIsLoading(false)
          return
        }

        const chatResponse = await fetch(`${apiBaseUrl}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            message: text,
            analysis_type: analysisType,
            selected_file_ids: latestSelectedFiles.map((f) => f.id),
            provider,
            model
          })
        })

        if (!chatResponse.ok) {
          const errorData = await chatResponse.json().catch(() => ({}))
          throw new Error(errorData.detail ?? 'Failed to get response from server')
        }

        const chatData = await chatResponse.json()
        const assistantMessage = {
          text: chatData.response ?? 'No response received',
          isUser: false,
          role: 'assistant'
        }
        setMessages((prev) => [...prev, assistantMessage])

        if (chatData.analysis_type === 'quantitative') {
          setQuantAnalysis({
            code: chatData.code ?? '',
            explanation: chatData.code_explanation ?? '',
            dataOutput: chatData.data_output ?? '',
            summary: chatData.response ?? '',
            files: chatData.files_analyzed ?? [],
            codeSuccess: chatData.code_success ?? null,
            codeError: chatData.code_error ?? null,
            updatedAt: new Date().toISOString()
          })
        }
      } catch (error) {
        console.error('Error sending message:', error)
        const errorMessage = {
          text: `Error: ${error.message ?? 'Failed to process your message. Please try again.'}`,
          isUser: false,
          role: 'assistant'
        }
        setMessages((prev) => [...prev, errorMessage])
      } finally {
        setIsLoading(false)
      }
    },
    [apiBaseUrl, analysisType, fetchSelectedFiles, provider, model]
  )

  const value = {
    messages,
    setMessages,
    analysisType,
    setAnalysisType,
    quantAnalysis,
    setQuantAnalysis,
    selectedFiles,
    setSelectedFiles,
    isLoading,
    fetchSelectedFiles,
    handleSendMessage,
    provider,
    setProvider,
    model,
    setModel
  }

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>
}

// Hook must live with context; fast-refresh lint waived for context modules
// eslint-disable-next-line react-refresh/only-export-components
export function useChat() {
  const ctx = useContext(ChatContext)
  if (!ctx) throw new Error('useChat must be used within ChatProvider')
  return ctx
}
