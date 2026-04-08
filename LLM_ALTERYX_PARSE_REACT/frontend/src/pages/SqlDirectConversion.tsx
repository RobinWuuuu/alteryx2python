import { useState } from 'react'
import { Database, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'
import { useAppStore, parsedToolIds } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import type { SqlDirectConvertResult } from '../api/types'
import { surfaceMessageError } from '../utils/errorSupport'

export function SqlDirectConversion() {
  const upload = useAppStore((s) => s.upload)
  const config = useAppStore((s) => s.config)
  const toolIdsRaw = useAppStore((s) => s.toolIdsRaw)
  const extraInstructions = useAppStore((s) => s.extraInstructions)

  const [status, setStatus]   = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [progress, setProgress] = useState(0)
  const [message, setMessage]  = useState('')
  const [result, setResult]    = useState<SqlDirectConvertResult | null>(null)
  const [showPrompt, setShowPrompt] = useState(false)

  const { run, cancel } = useStreamingJob<SqlDirectConvertResult>()

  const toolIds = parsedToolIds(toolIdsRaw)
  const canRun = !!upload.sessionId && !!config.api_key && toolIds.length > 0

  const handleRun = async () => {
    if (!canRun) return
    setStatus('running')
    setProgress(0)
    setMessage('Starting…')
    setResult(null)

    await run(
      '/api/convert/sql/direct',
      {
        session_id: upload.sessionId,
        config,
        tool_ids: toolIds,
        extra_instructions: extraInstructions,
      },
      {
        onProgress: (value, msg) => {
          setProgress(isNaN(value) ? progress : value)
          if (msg) setMessage(msg)
        },
        onResult: (data) => {
          setStatus('done')
          setProgress(1)
          setMessage('')
          setResult(data)
        },
        onError: (msg) => {
          setStatus('error')
          setMessage(msg)
          void surfaceMessageError(msg, {
            title: 'SQL Direct Conversion Failed',
            scope: 'sql-direct-convert-step1',
            action: 'Run SQL direct conversion',
          })
        },
      },
    )
  }

  const handleCancel = () => {
    cancel()
    setStatus('idle')
    setProgress(0)
    setMessage('')
  }

  return (
    <div className="space-y-5 max-w-4xl">
      <div>
        <h2 className="text-lg font-semibold text-slate-100 mb-1">SQL Direct Conversion</h2>
        <p className="text-sm text-muted">
          Generates SQL CTEs for each selected tool, then combines them into a single executable query.
        </p>
      </div>

      {(!upload.sessionId || !config.api_key || toolIds.length === 0) && (
        <div className="rounded-xl border border-border bg-card/50 p-4">
          <div className="flex items-center gap-2 mb-2.5">
            <AlertCircle size={14} className="text-warning" />
            <span className="text-xs font-medium text-slate-300">Before you start</span>
          </div>
          <div className="space-y-1.5 text-xs text-muted">
            {!upload.sessionId && <div>Upload an Alteryx workflow (.yxmd) in the sidebar</div>}
            {!config.api_key && <div>Provide your OpenAI API key in the sidebar</div>}
            {toolIds.length === 0 && <div>Specify tool IDs to convert in the sidebar</div>}
          </div>
        </div>
      )}

      {/* Action button */}
      <div className="flex gap-3">
        <button
          onClick={status === 'running' ? handleCancel : handleRun}
          disabled={status !== 'running' && !canRun}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={
            status === 'running'
              ? { background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'linear-gradient(135deg, #0f766e, #14b8a6)', color: 'white' }
          }
        >
          <Database size={16} />
          {status === 'running' ? 'Cancel' : 'Run SQL Conversion'}
        </button>
      </div>

      {/* Progress */}
      {(status === 'running' || status === 'error') && (
        <ProgressTracker
          status={status}
          progress={progress}
          message={message}
          label={`Generating SQL for ${toolIds.length} tool${toolIds.length !== 1 ? 's' : ''}…`}
        />
      )}

      {/* Result */}
      {status === 'done' && result && (
        <div className="space-y-4 fade-in">
          <div className="flex items-center gap-2 text-success text-sm font-medium">
            <Database size={16} />
            SQL conversion complete!
          </div>

          <CodeViewer
            code={result.final_sql}
            language="sql"
            filename={`sql_conversion_${toolIds.slice(0, 3).join('-')}.sql`}
          />

          {/* Prompt used (collapsible) */}
          <div className="rounded-xl border border-border overflow-hidden">
            <button
              onClick={() => setShowPrompt((p) => !p)}
              className="w-full flex items-center justify-between px-4 py-3 text-sm text-muted hover:bg-white/5 transition-colors"
            >
              <span>View Prompt Used</span>
              {showPrompt ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
            {showPrompt && (
              <div className="border-t border-border">
                <CodeViewer
                  code={result.prompt_used}
                  language="text"
                  filename="prompt.txt"
                  maxHeight="300px"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
