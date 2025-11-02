import { useState, useEffect, useRef } from 'react'

const API_BASE_URL = 'http://localhost:8000'

export function CsvPreviewPanel({ selectedFiles }) {
  const [previews, setPreviews] = useState({})
  const [loading, setLoading] = useState({})
  const [errors, setErrors] = useState({})
  const fetchingRef = useRef(new Set())

  useEffect(() => {
    // Fetch previews for all selected files
    selectedFiles.forEach((file) => {
      // Only fetch if not already loaded, not loading, and not currently fetching
      if (!previews[file.id] && !loading[file.id] && !errors[file.id] && !fetchingRef.current.has(file.id)) {
        fetchingRef.current.add(file.id)
        setLoading(prev => ({ ...prev, [file.id]: true }))
        
        fetch(`${API_BASE_URL}/api/files/${file.id}/preview?rows=15`)
          .then(response => {
            if (!response.ok) {
              throw new Error('Failed to load preview')
            }
            return response.json()
          })
          .then(data => {
            setPreviews(prev => ({ ...prev, [file.id]: data }))
            setErrors(prev => {
              const newErrors = { ...prev }
              delete newErrors[file.id]
              return newErrors
            })
          })
          .catch(error => {
            setErrors(prev => ({ ...prev, [file.id]: error.message }))
          })
          .finally(() => {
            fetchingRef.current.delete(file.id)
            setLoading(prev => {
              const newLoading = { ...prev }
              delete newLoading[file.id]
              return newLoading
            })
          })
      }
    })

    // Remove previews for files that are no longer selected
    const selectedIds = new Set(selectedFiles.map(f => f.id))
    setPreviews(prev => {
      const newPreviews = {}
      let changed = false
      
      Object.keys(prev).forEach(fileIdStr => {
        const fileId = parseInt(fileIdStr)
        if (selectedIds.has(fileId)) {
          newPreviews[fileIdStr] = prev[fileIdStr]
        } else {
          changed = true
        }
      })
      
      return changed ? newPreviews : prev
    })

    // Clean up fetching ref for unselected files
    fetchingRef.current.forEach(fileId => {
      if (!selectedIds.has(fileId)) {
        fetchingRef.current.delete(fileId)
      }
    })
  }, [selectedFiles, previews, loading, errors])

  if (selectedFiles.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Selected CSV Files Preview</h2>
        <p className="text-gray-500 text-sm">No files selected. Check files above to preview their contents.</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        Selected CSV Files Preview
        <span className="ml-2 text-sm font-normal text-gray-600">
          ({selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''})
        </span>
      </h2>
      
      <div className="space-y-6">
        {selectedFiles.map((file) => {
          const preview = previews[file.id]
          const isLoading = loading[file.id]
          const error = errors[file.id]

          return (
            <div
              key={file.id}
              className="border border-gray-200 rounded-lg overflow-hidden"
            >
              {/* File Header */}
              <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-medium text-gray-800">{file.filename}</h3>
                    {preview && (
                      <p className="text-xs text-gray-500 mt-1">
                        {preview.previewed_rows} of {preview.total_rows} rows shown
                      </p>
                    )}
                  </div>
                  {isLoading && (
                    <span className="text-sm text-gray-500">Loading...</span>
                  )}
                  {error && (
                    <span className="text-sm text-red-600">Error loading preview</span>
                  )}
                </div>
              </div>

              {/* Preview Content */}
              <div className="overflow-x-auto max-h-96">
                {isLoading && (
                  <div className="p-8 text-center text-gray-500">
                    Loading preview...
                  </div>
                )}
                
                {error && (
                  <div className="p-8 text-center text-red-600">
                    {error}
                  </div>
                )}

                {preview && (
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        {preview.headers.map((header, idx) => (
                          <th
                            key={idx}
                            className="px-4 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {preview.rows.length === 0 ? (
                        <tr>
                          <td
                            colSpan={preview.headers.length}
                            className="px-4 py-8 text-center text-sm text-gray-500"
                          >
                            No data rows in file
                          </td>
                        </tr>
                      ) : (
                        preview.rows.map((row, rowIdx) => (
                          <tr key={rowIdx} className="hover:bg-gray-50">
                            {preview.headers.map((header, colIdx) => (
                              <td
                                key={colIdx}
                                className="px-4 py-2 text-xs text-gray-700 border-r border-gray-100 last:border-r-0 max-w-xs truncate"
                                title={row[header] || ''}
                              >
                                {row[header] || ''}
                              </td>
                            ))}
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

