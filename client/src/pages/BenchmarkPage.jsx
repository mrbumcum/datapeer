import { useEffect, useMemo, useState } from 'react'

const API_BASE_URL = 'http://localhost:8000'

const MODEL_OPTIONS = [
  {
    provider: 'openai',
    model: 'gpt-5-mini-2025-08-07',
    label: 'OpenAI · GPT-5 mini · 2025‑08‑07'
  },
  {
    provider: 'openai',
    model: 'gpt-5.4',
    label: 'OpenAI · GPT-5.4'
  },
  {
    provider: 'claude',
    model: 'claude-haiku-4-5-20251001',
    label: 'Claude · Haiku 4.5'
  },
  {
    provider: 'claude',
    model: 'claude-sonnet-4-6',
    label: 'Claude · Sonnet 4.6'
  },
  {
    provider: 'claude',
    model: 'claude-opus-4-6',
    label: 'Claude · Opus 4.6'
  },
  {
    provider: 'gemini',
    model: 'gemini-2.5-flash-lite',
    label: 'Gemini · 2.5 Flash-Lite'
  },
  {
    provider: 'gemini',
    model: 'gemini-2.5-flash',
    label: 'Gemini · 2.5 Flash'
  },
  {
    provider: 'gemini',
    model: 'gemini-2.5-pro',
    label: 'Gemini · 2.5 Pro'
  }
]

const CONTEXT_MODES = [
  { value: 'none', label: 'None' },
  { value: 'light', label: 'Light (schema + shapes)' },
  { value: 'rich', label: 'Rich (schema + qualitative)' }
]

export function BenchmarkPage() {
  const [files, setFiles] = useState([])
  const [loadingFiles, setLoadingFiles] = useState(true)
  const [message, setMessage] = useState('')
  const [analysisType, setAnalysisType] = useState('qualitative')
  const [runs, setRuns] = useState(1)
  const [selectedModels, setSelectedModels] = useState(() => new Set())
  const [contextMode, setContextMode] = useState('none')
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState(null)
  const [manualRatings, setManualRatings] = useState({})
  const [isModelPickerOpen, setIsModelPickerOpen] = useState(false)

  useEffect(() => {
    const fetchSelectedFiles = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/files/selected`)
        if (!response.ok) throw new Error('Failed to fetch selected files')
        const data = await response.json()
        setFiles(data.files ?? [])
      } catch (err) {
        console.error('Error fetching selected files:', err)
      } finally {
        setLoadingFiles(false)
      }
    }

    fetchSelectedFiles()
  }, [])

  const selectedCount = files.length

  const toggleModel = (key) => {
    setSelectedModels((prev) => {
      const next = new Set(prev)
      if (next.has(key)) {
        next.delete(key)
      } else {
        next.add(key)
      }
      return next
    })
  }

  const selectedVariants = useMemo(() => {
    return MODEL_OPTIONS.filter((opt) => selectedModels.has(`${opt.provider}:${opt.model}`)).map((opt) => ({
      provider: opt.provider,
      model: opt.model,
      context_mode: contextMode
    }))
  }, [selectedModels, contextMode])

  const selectedModelOptions = useMemo(
    () => MODEL_OPTIONS.filter((opt) => selectedModels.has(`${opt.provider}:${opt.model}`)),
    [selectedModels]
  )

  const onChangeRating = (runKey, field, value) => {
    setManualRatings((prev) => ({
      ...prev,
      [runKey]: {
        ...(prev[runKey] || {}),
        [field]: value ? Number(value) : null
      }
    }))
  }

  const handleRunBenchmark = async () => {
    setError(null)
    if (!message.trim()) {
      setError('Please enter an analysis prompt.')
      return
    }
    if (files.length === 0) {
      setError('Please select at least one dataset on the Database page.')
      return
    }
    if (selectedVariants.length === 0) {
      setError('Please select at least one model.')
      return
    }
    if (runs < 1) {
      setError('Runs must be at least 1.')
      return
    }

    setIsRunning(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/benchmark`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          analysis_type: analysisType,
          selected_file_ids: files.map((f) => f.id),
          runs,
          variants: selectedVariants
        })
      })

      if (!response.ok) {
        const data = await response.json().catch(() => ({}))
        throw new Error(data.detail || 'Benchmark request failed')
      }

      const data = await response.json()
      const newResults = data.results ?? []
      setResults(newResults)
    } catch (err) {
      console.error('Error running benchmark:', err)
      setError(err.message || 'Failed to run benchmark.')
    } finally {
      setIsRunning(false)
    }
  }

  const handleDownloadCsv = () => {
    if (!results.length) return

    const headers = [
      'timestamp',
      'run_index',
      'provider',
      'model',
      'context_mode',
      'analysis_type',
      'latency_ms',
      'code_success',
      'code_error',
      'manual_correctness',
      'manual_usefulness',
      'prompt_snippet'
    ]

    const rows = results.map((run) => {
      const key = `${run.provider || ''}:${run.model || ''}:${run.context_mode || ''}:${run.run_index ?? 0}:${run.timestamp}`
      const rating = manualRatings[key] || {}
      const promptSnippet = message.length > 120 ? `${message.slice(0, 117)}...` : message
      return [
        run.timestamp,
        run.run_index ?? 0,
        run.provider || '',
        run.model || '',
        run.context_mode || '',
        run.analysis_type || '',
        run.latency_ms ?? '',
        run.code_success === null || run.code_success === undefined ? '' : run.code_success,
        (run.code_error || '').toString().slice(0, 160).replace(/\s+/g, ' '),
        rating.correctness ?? '',
        rating.usefulness ?? '',
        `"${promptSnippet.replace(/"/g, '""')}"`
      ]
    })

    const csvContent = [headers.join(','), ...rows.map((r) => r.join(','))].join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    link.download = `benchmark-results-${timestamp}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  const groupedSummary = useMemo(() => {
    if (!results.length) return []

    const groups = new Map()
    for (const run of results) {
      const key = `${run.provider || ''}:${run.model || ''}:${run.context_mode || ''}`
      if (!groups.has(key)) {
        groups.set(key, {
          provider: run.provider,
          model: run.model,
          context_mode: run.context_mode,
          analysis_type: run.analysis_type,
          count: 0,
          totalLatency: 0,
          successCount: 0
        })
      }
      const g = groups.get(key)
      g.count += 1
      g.totalLatency += run.latency_ms || 0
      if (run.code_success === true) g.successCount += 1
    }

    return Array.from(groups.values()).map((g) => ({
      ...g,
      avgLatency: g.count ? g.totalLatency / g.count : 0,
      successRate: g.count ? g.successCount / g.count : 0
    }))
  }, [results])

  return (
    <div className="h-screen flex flex-col bg-linear-to-b from-blue-50 to-purple-50 p-6">
      <div className="max-w-6xl mx-auto w-full flex flex-col gap-4 flex-1">
        <header className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
              <span className="inline-flex items-center rounded-full border border-gray-300 bg-white px-3 py-1 font-medium text-gray-800">
                Benchmark run
              </span>
              <span className="inline-flex items-center gap-1">
                <span
                  className={`h-2 w-2 rounded-full ${
                    isRunning ? 'bg-emerald-500 animate-pulse' : results.length ? 'bg-emerald-500' : 'bg-gray-300'
                  }`}
                />
                {isRunning ? 'Running…' : results.length ? 'Finished' : 'Idle'}
              </span>
              {results.length > 0 && (
                <span className="inline-flex items-center gap-1">
                  <span className="text-gray-400">•</span>
                  <span>Runs: {results.length}</span>
                </span>
              )}
            </div>
            <button
              type="button"
              onClick={handleDownloadCsv}
              disabled={!results.length}
              className="text-xs px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-40"
            >
              Download CSV
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs">
            <div className="flex flex-wrap gap-2 flex-1 min-w-0">
              {selectedModelOptions.map((opt) => (
                <button
                  key={`${opt.provider}:${opt.model}`}
                  type="button"
                  onClick={() => toggleModel(`${opt.provider}:${opt.model}`)}
                  className="inline-flex items-center gap-1 rounded-full bg-white px-3 py-1 text-gray-800 shadow-sm border border-gray-200 hover:bg-gray-50"
                >
                  <span>{opt.label}</span>
                  <span className="ml-1 text-gray-400 hover:text-gray-600">&times;</span>
                </button>
              ))}
              {selectedModelOptions.length === 0 && (
                <span className="text-gray-500">No models selected yet.</span>
              )}
            </div>
            <div className="relative ml-auto mt-2 md:mt-0">
              <button
                type="button"
                onClick={() => setIsModelPickerOpen((open) => !open)}
                className="inline-flex items-center gap-1 rounded-full border border-purple-200 bg-white px-3 py-1 text-xs font-medium text-purple-700 hover:bg-purple-50"
              >
                + Add model
              </button>
              {isModelPickerOpen && (
                <div className="absolute right-0 z-10 mt-2 w-64 rounded-xl border border-gray-200 bg-white shadow-lg text-xs">
                  <div className="max-h-64 overflow-auto p-2">
                    {MODEL_OPTIONS.map((opt) => {
                      const key = `${opt.provider}:${opt.model}`
                      const checked = selectedModels.has(key)
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => toggleModel(key)}
                          className={`flex w-full items-center justify-between gap-2 rounded-md px-2 py-1 text-left ${
                            checked ? 'bg-purple-50 text-gray-900' : 'hover:bg-gray-50 text-gray-700'
                          }`}
                        >
                          <span className="truncate">{opt.label}</span>
                          <span
                            className={`h-2 w-2 rounded-full ${
                              checked ? 'bg-purple-500' : 'border border-gray-300 bg-white'
                            }`}
                          />
                        </button>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 min-h-0">
          {/* Configuration panel */}
          <section className="bg-white rounded-2xl shadow-sm p-4 flex flex-col gap-4 lg:col-span-1">
            <div>
              <h2 className="text-sm font-semibold text-gray-800 mb-1">Datasets</h2>
              {loadingFiles ? (
                <p className="text-xs text-gray-500">Loading selected datasets…</p>
              ) : selectedCount === 0 ? (
                <p className="text-xs text-red-600">
                  No datasets selected. Go to the Database page and select at least one CSV.
                </p>
              ) : (
                <p className="text-xs text-gray-600">
                  Using <span className="font-medium">{selectedCount}</span> selected dataset
                  {selectedCount !== 1 ? 's' : ''}.
                </p>
              )}
            </div>

            <div>
              <h2 className="text-sm font-semibold text-gray-800 mb-1">Analysis prompt</h2>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                rows={5}
                className="w-full text-sm border border-gray-300 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400 bg-gray-50"
                placeholder="Ask a question for qualitative or quantitative EDA (e.g., 'Compare average revenue by region and highlight outliers')."
              />
            </div>

            <div className="flex flex-col gap-2">
              <h2 className="text-sm font-semibold text-gray-800 mb-1">Analysis mode</h2>
              <div className="inline-flex rounded-lg border border-gray-300 bg-gray-50 overflow-hidden text-xs">
                <button
                  type="button"
                  className={`px-3 py-1.5 flex-1 ${
                    analysisType === 'qualitative'
                      ? 'bg-purple-100 text-gray-900 font-medium'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => setAnalysisType('qualitative')}
                >
                  Qualitative
                </button>
                <button
                  type="button"
                  className={`px-3 py-1.5 flex-1 ${
                    analysisType === 'quantitative'
                      ? 'bg-purple-100 text-gray-900 font-medium'
                      : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
                  }`}
                  onClick={() => setAnalysisType('quantitative')}
                >
                  Quantitative
                </button>
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <h2 className="text-sm font-semibold text-gray-800 mb-1">Context mode</h2>
              <select
                value={contextMode}
                onChange={(e) => setContextMode(e.target.value)}
                className="text-xs border border-gray-300 rounded-lg px-3 py-1.5 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
              >
                {CONTEXT_MODES.map((mode) => (
                  <option key={mode.value} value={mode.value}>
                    {mode.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold text-gray-800">Runs</span>
                <input
                  type="number"
                  min={1}
                  max={10}
                  value={runs}
                  onChange={(e) => setRuns(Number(e.target.value) || 1)}
                  className="w-16 text-xs border border-gray-300 rounded-lg px-2 py-1 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-200 focus:border-purple-400"
                />
              </div>
              <button
                type="button"
                onClick={handleRunBenchmark}
                disabled={isRunning}
                className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {isRunning ? 'Running…' : 'Run benchmark'}
              </button>
            </div>

            {error && <p className="text-xs text-red-600">{error}</p>}
          </section>

          {/* Models and results */}
          <section className="bg-white rounded-2xl shadow-sm p-4 flex flex-col gap-4 lg:col-span-2 min-h-0">
            <div>
              <h2 className="text-sm font-semibold text-gray-800 mb-2">Summary</h2>
              {groupedSummary.length === 0 ? (
                <p className="text-xs text-gray-500">
                  No benchmark runs yet. Configure a prompt and models, then click &quot;Run benchmark&quot;.
                </p>
              ) : (
                <div className="border border-gray-200 rounded-xl overflow-hidden text-xs">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left font-semibold text-gray-700">Model</th>
                        <th className="px-3 py-2 text-left font-semibold text-gray-700">Context</th>
                        <th className="px-3 py-2 text-right font-semibold text-gray-700">Avg latency (ms)</th>
                        <th className="px-3 py-2 text-right font-semibold text-gray-700">Code success rate</th>
                        <th className="px-3 py-2 text-right font-semibold text-gray-700">Runs</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {groupedSummary.map((g) => (
                        <tr key={`${g.provider}:${g.model}:${g.context_mode}`}>
                          <td className="px-3 py-1.5 text-gray-800">
                            <div className="flex flex-col">
                              <span className="font-medium">{g.model}</span>
                              <span className="text-[11px] text-gray-500">{g.provider}</span>
                            </div>
                          </td>
                          <td className="px-3 py-1.5 text-gray-700">{g.context_mode}</td>
                          <td className="px-3 py-1.5 text-right text-gray-800">{g.avgLatency.toFixed(0)}</td>
                          <td className="px-3 py-1.5 text-right text-gray-800">
                            {g.analysis_type === 'quantitative'
                              ? `${(g.successRate * 100).toFixed(0)}%`
                              : '—'}
                          </td>
                          <td className="px-3 py-1.5 text-right text-gray-700">{g.count}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Individual runs */}
            <div className="flex-1 min-h-0 overflow-auto border border-gray-200 rounded-2xl p-3">
              {results.length === 0 ? (
                <p className="text-xs text-gray-500">Run a benchmark to see individual run details.</p>
              ) : (
                <div className="space-y-3">
                  {results.map((run, idx) => {
                    const key = `${run.provider || ''}:${run.model || ''}:${run.context_mode || ''}:${
                      run.run_index ?? idx
                    }:${run.timestamp}`
                    const rating = manualRatings[key] || {}
                    return (
                      <div
                        key={key}
                        className="border border-gray-200 rounded-xl p-3 bg-gray-50 text-xs flex flex-col gap-2"
                      >
                        <div className="flex flex-wrap justify-between gap-2">
                          <div className="flex flex-col">
                            <span className="font-semibold text-gray-900">
                              {run.provider} · {run.model}
                            </span>
                            <span className="text-[11px] text-gray-500">
                              Context: {run.context_mode} · Run {run.run_index ?? idx}
                            </span>
                          </div>
                          <div className="flex flex-wrap items-center gap-3 text-[11px] text-gray-700">
                            <span>
                              Latency:{' '}
                              <span className="font-semibold">
                                {run.latency_ms != null ? run.latency_ms.toFixed(0) : '—'} ms
                              </span>
                            </span>
                            {run.analysis_type === 'quantitative' && (
                              <span>
                                Code:{' '}
                                {run.code_success === true
                                  ? 'success'
                                  : run.code_success === false
                                  ? 'failed'
                                  : 'n/a'}
                              </span>
                            )}
                          </div>
                        </div>

                        {run.response && (
                          <details className="bg-white border border-gray-200 rounded-lg p-2">
                            <summary className="cursor-pointer text-[11px] font-medium text-gray-800">
                              Model response
                            </summary>
                            <pre className="mt-1 text-[11px] text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
                              {run.response}
                            </pre>
                          </details>
                        )}

                        {run.analysis_type === 'quantitative' && run.code && (
                          <details className="bg-white border border-gray-200 rounded-lg p-2">
                            <summary className="cursor-pointer text-[11px] font-medium text-gray-800">
                              Generated code
                            </summary>
                            <pre className="mt-1 text-[11px] text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
                              {run.code}
                            </pre>
                          </details>
                        )}

                        <div className="flex flex-wrap items-center gap-3">
                          <span className="text-[11px] font-semibold text-gray-800">Manual rating</span>
                          <label className="flex items-center gap-1 text-[11px] text-gray-700">
                            <span>Correctness</span>
                            <select
                              value={rating.correctness ?? ''}
                              onChange={(e) => onChangeRating(key, 'correctness', e.target.value)}
                              className="border border-gray-300 rounded px-1 py-0.5 text-[11px] bg-white"
                            >
                              <option value="">–</option>
                              {[1, 2, 3, 4, 5].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </select>
                          </label>
                          <label className="flex items-center gap-1 text-[11px] text-gray-700">
                            <span>Usefulness</span>
                            <select
                              value={rating.usefulness ?? ''}
                              onChange={(e) => onChangeRating(key, 'usefulness', e.target.value)}
                              className="border border-gray-300 rounded px-1 py-0.5 text-[11px] bg-white"
                            >
                              <option value="">–</option>
                              {[1, 2, 3, 4, 5].map((v) => (
                                <option key={v} value={v}>
                                  {v}
                                </option>
                              ))}
                            </select>
                          </label>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

