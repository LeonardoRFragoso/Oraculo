import { FileText, X } from 'lucide-react'
import { useState, useEffect } from 'react'

interface AttachedFile {
  filename: string
  file_id: string
  uploaded_at: string
  size: number
}

export default function AttachedFiles() {
  const [files, setFiles] = useState<AttachedFile[]>([])

  useEffect(() => {
    // Carregar arquivos do localStorage
    const loadFiles = () => {
      const savedFiles = localStorage.getItem('attached_files')
      if (savedFiles) {
        setFiles(JSON.parse(savedFiles))
      }
    }
    
    loadFiles()
    
    // Listener para atualizar quando novos arquivos forem adicionados
    window.addEventListener('files-updated', loadFiles)
    
    return () => {
      window.removeEventListener('files-updated', loadFiles)
    }
  }, [])

  const removeFile = (fileId: string) => {
    const updatedFiles = files.filter(f => f.file_id !== fileId)
    setFiles(updatedFiles)
    localStorage.setItem('attached_files', JSON.stringify(updatedFiles))
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (files.length === 0) return null

  return (
    <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
      <div className="flex items-center gap-2 mb-2">
        <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400" />
        <span className="text-sm font-semibold text-blue-900 dark:text-blue-300">
          Arquivos Anexados ({files.length})
        </span>
      </div>
      
      <div className="space-y-2">
        {files.map((file) => (
          <div
            key={file.file_id}
            className="flex items-center justify-between gap-2 p-2 bg-white dark:bg-gray-800 rounded border border-blue-200 dark:border-blue-700"
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <FileText className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                  {file.filename}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {formatSize(file.size)}
                </p>
              </div>
            </div>
            
            <button
              onClick={() => removeFile(file.file_id)}
              className="p-1 rounded hover:bg-red-100 dark:hover:bg-red-900/20 transition-colors"
              title="Remover arquivo"
            >
              <X className="w-4 h-4 text-red-600 dark:text-red-400" />
            </button>
          </div>
        ))}
      </div>
      
      <p className="text-xs text-blue-700 dark:text-blue-400 mt-2">
        💡 Esses arquivos estão indexados e disponíveis para consulta
      </p>
    </div>
  )
}
