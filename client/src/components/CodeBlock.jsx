import { useMemo, useState } from 'react'
import { Highlight, themes } from 'prism-react-renderer'

export function CodeBlock({
  code = '',
  explanation = '',
  language = 'python',
  isLoading = false,
  updatedAt = null
}) {
  const [copied, setCopied] = useState(false)
  const hasCode = Boolean(code && code.trim())

  const timestamp = useMemo(() => {
    if (!updatedAt) return null
    try {
      return new Intl.DateTimeFormat('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }).format(new Date(updatedAt))
    } catch {
      return null
    }
  }, [updatedAt])

  const handleCopy = async () => {
    if (!hasCode || !navigator?.clipboard) return
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (error) {
      console.error('Failed to copy code', error)
    }
  }

  return (
    <div className="bg-gray-900 text-gray-100 rounded-2xl shadow-lg border border-gray-800 overflow-hidden">
      <div className="flex items-start justify-between p-4 border-b border-gray-800">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-purple-300">Generated Code</p>
          <p className="text-xs text-gray-400 mt-1 line-clamp-2">
            {explanation || (hasCode ? 'LLM-produced analysis code' : 'Ask a quantitative question to generate code')}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {timestamp && (
            <span className="text-xs text-gray-500">Updated {timestamp}</span>
          )}
          <button
            type="button"
            disabled={!hasCode}
            onClick={handleCopy}
            className="px-3 py-1.5 text-xs font-medium rounded-full bg-gray-800 hover:bg-gray-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="relative">
        {hasCode ? (
          <Highlight
            code={code}
            language={language}
            theme={themes.nightOwl}
          >
            {({ className, style, tokens, getLineProps, getTokenProps }) => (
              <pre className={`${className} text-sm overflow-x-auto p-4`} style={{ ...style, margin: 0 }}>
                {tokens.map((line, i) => (
                  <div key={i} {...getLineProps({ line, key: i })}>
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token, key })} />
                    ))}
                  </div>
                ))}
              </pre>
            )}
          </Highlight>
        ) : (
          <div className="p-6 text-center text-gray-500 text-sm">
            Quantitative code will appear here after you ask a question.
          </div>
        )}

        {isLoading && (
          <div className="absolute inset-0 bg-gray-900/70 backdrop-blur-sm flex items-center justify-center">
            <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full" />
          </div>
        )}
      </div>
    </div>
  )
}
