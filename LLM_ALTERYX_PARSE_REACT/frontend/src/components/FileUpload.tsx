import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileCheck, AlertCircle, Loader2 } from 'lucide-react'
import { uploadFile } from '../api/client'
import { useAppStore } from '../store/useAppStore'

export function FileUpload() {
  const setUpload = useAppStore((s) => s.setUpload)
  const upload = useAppStore((s) => s.upload)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (accepted: File[]) => {
    const file = accepted[0]
    if (!file) return
    setStatus('uploading')
    setError(null)
    try {
      const res = await uploadFile(file)
      setUpload({
        sessionId: res.session_id,
        filename: res.filename,
        nodeCount: res.node_count,
        connectionCount: res.connection_count,
        toolTypes: res.tool_types,
      })
      setStatus('idle')
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
      setStatus('error')
    }
  }, [setUpload])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/octet-stream': ['.yxmd', '.yxmc'] },
    maxFiles: 1,
  })

  if (upload.sessionId) {
    return (
      <div className="rounded-lg border border-success/30 bg-success/10 p-3 fade-in">
        <div className="flex items-center gap-2 text-success mb-1">
          <FileCheck size={16} />
          <span className="text-sm font-medium truncate">{upload.filename}</span>
        </div>
        <div className="flex gap-3 text-xs text-muted">
          <span>{upload.nodeCount} tools</span>
          <span>{upload.connectionCount} connections</span>
        </div>
        <button
          onClick={() => setUpload({ sessionId: null, filename: null, nodeCount: 0, connectionCount: 0, toolTypes: [] })}
          className="mt-2 text-xs text-muted hover:text-slate-300 transition-colors"
        >
          Replace file
        </button>
      </div>
    )
  }

  return (
    <div>
      <div
        {...getRootProps()}
        className={`
          relative rounded-lg border-2 border-dashed p-5 text-center cursor-pointer transition-all duration-200
          ${isDragActive
            ? 'border-primary bg-primary/10 scale-[1.02]'
            : 'border-border hover:border-primary/50 hover:bg-primary/5'
          }
          ${status === 'uploading' ? 'opacity-60 pointer-events-none' : ''}
        `}
      >
        <input {...getInputProps()} />
        {status === 'uploading' ? (
          <div className="flex flex-col items-center gap-2 text-muted">
            <Loader2 size={24} className="animate-spin text-primary" />
            <span className="text-sm">Uploading...</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <Upload size={24} className={isDragActive ? 'text-primary' : 'text-muted'} />
            <div>
              <p className="text-sm font-medium text-slate-300">
                {isDragActive ? 'Drop it here' : 'Drop .yxmd file'}
              </p>
              <p className="text-xs text-muted mt-0.5">or click to browse</p>
            </div>
          </div>
        )}
      </div>
      {status === 'error' && error && (
        <div className="mt-2 flex items-start gap-1.5 text-error text-xs">
          <AlertCircle size={13} className="mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
