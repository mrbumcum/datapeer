import { useState, useEffect } from 'react'

const API_BASE_URL = 'http://localhost:8000'

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

function formatDate(dateString) {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

export function DatabasePage() {
  const [files, setFiles] = useState([])
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchFiles()
  }, [])

  const fetchFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files`)
      const data = await response.json()
      setFiles(data.files || [])
    } catch (error) {
      console.error('Error fetching files:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    if (!file.name.endsWith('.csv')) {
      alert('Please upload a CSV file')
      return
    }

    setUploading(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch(`${API_BASE_URL}/api/files/upload`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }

      await fetchFiles()
      event.target.value = '' // Reset file input
    } catch (error) {
      console.error('Error uploading file:', error)
      alert(`Upload failed: ${error.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleSelectionChange = async (fileId, isSelected) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/files/${fileId}/selection`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_selected: isSelected })
      })

      if (!response.ok) {
        throw new Error('Failed to update selection')
      }

      // Update local state
      setFiles(files.map(file =>
        file.id === fileId ? { ...file, is_selected: isSelected ? 1 : 0 } : file
      ))
    } catch (error) {
      console.error('Error updating selection:', error)
      alert('Failed to update selection')
    }
  }

  const handleDelete = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file?')) {
      return
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/files/${fileId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to delete file')
      }

      await fetchFiles()
    } catch (error) {
      console.error('Error deleting file:', error)
      alert('Failed to delete file')
    }
  }

  const selectedCount = files.filter(f => f.is_selected === 1).length

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-blue-50 to-purple-50 p-8">
      <div className="max-w-4xl mx-auto w-full flex flex-col flex-1">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">Database</h1>
        <p className="text-gray-600 mb-6">
          Upload CSV files to be used for data analysis. Select files using the checkboxes to include them in LLM processing.
        </p>

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-800 mb-4">Upload CSV File</h2>
          <label className="block">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={uploading}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-md file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                disabled:opacity-50 disabled:cursor-not-allowed"
            />
          </label>
          {uploading && (
            <p className="mt-2 text-sm text-gray-600">Uploading...</p>
          )}
        </div>

        {/* Files List Section */}
        <div className="bg-white rounded-lg shadow-md p-6 flex-1 overflow-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-800">
              Uploaded Files
            </h2>
            {selectedCount > 0 && (
              <span className="text-sm text-blue-600 font-medium">
                {selectedCount} file{selectedCount !== 1 ? 's' : ''} selected
              </span>
            )}
          </div>

          {loading ? (
            <p className="text-gray-500">Loading files...</p>
          ) : files.length === 0 ? (
            <p className="text-gray-500 text-center py-8">
              No files uploaded yet. Upload a CSV file to get started.
            </p>
          ) : (
            <div className="space-y-3">
              {files.map((file) => (
                <div
                  key={file.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1">
                    <input
                      type="checkbox"
                      checked={file.is_selected === 1}
                      onChange={(e) => handleSelectionChange(file.id, e.target.checked)}
                      className="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 focus:ring-2"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-800 truncate">
                        {file.filename}
                      </p>
                      <div className="flex gap-4 mt-1 text-sm text-gray-500">
                        <span>{formatFileSize(file.file_size)}</span>
                        <span>•</span>
                        <span>{formatDate(file.uploaded_at)}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleDelete(file.id)}
                    className="ml-4 px-3 py-1 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded transition-colors"
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
