export function DataOutputPanel({
  responseText = '',
  dataOutput = '',
  files = [],
  codeSuccess = null,
  codeError = null,
  isLoading = false
}) {
  const hasResults = Boolean(responseText || dataOutput)

  return (
    <div className="relative bg-white rounded-2xl shadow-md border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-800 uppercase tracking-wide">Analysis Results</p>
          {files?.length > 0 && (
            <p className="text-xs text-gray-500 mt-1">
              Files analyzed: {files.join(', ')}
            </p>
          )}
        </div>
        {codeSuccess !== null && (
          <span className={`text-xs font-semibold px-2 py-1 rounded-full ${codeSuccess ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-600'}`}>
            {codeSuccess ? 'Code executed' : 'Execution failed'}
          </span>
        )}
      </div>

      <div className="p-4 space-y-4">
        {hasResults ? (
          <>
            {responseText && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Summary</p>
                <p className="text-sm text-gray-800 whitespace-pre-wrap">{responseText}</p>
              </div>
            )}

            {dataOutput && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Execution Output</p>
                <pre className="bg-gray-900 text-gray-100 rounded-xl p-3 text-xs overflow-x-auto max-h-64 whitespace-pre-wrap">
                  {dataOutput}
                </pre>
              </div>
            )}

            {codeError && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-100 rounded-lg p-3">
                {codeError}
              </div>
            )}
          </>
        ) : (
          <p className="text-sm text-gray-500">
            Ask a question in quantitative mode to see the generated insights and raw code output here.
          </p>
        )}
      </div>

      {isLoading && (
        <div className="absolute inset-0 bg-white/70 backdrop-blur-sm flex items-center justify-center">
          <div className="animate-spin h-6 w-6 border-2 border-purple-400 border-t-transparent rounded-full" />
        </div>
      )}
    </div>
  )
}
