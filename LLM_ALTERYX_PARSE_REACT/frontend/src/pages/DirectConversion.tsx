import { useState } from 'react'
import { Zap, ChevronDown, ChevronRight, AlertCircle, Upload, Key, Hash } from 'lucide-react'
import { useAppStore, parsedToolIds } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import type { DirectConvertResult } from '../api/types'
import { surfaceMessageError } from '../utils/errorSupport'

export function DirectConversion() {
  const upload = useAppStore((s) => s.upload)
  const config = useAppStore((s) => s.config)
  const toolIdsRaw = useAppStore((s) => s.toolIdsRaw)
  const extraInstructions = useAppStore((s) => s.extraInstructions)
  const direct = useAppStore((s) => s.direct)
  const setDirect = useAppStore((s) => s.setDirect)
  const resetDirect = useAppStore((s) => s.resetDirect)
  const addHistory = useAppStore((s) => s.addHistory)

  const [showPrompt, setShowPrompt] = useState(false)
  const { run, cancel } = useStreamingJob<DirectConvertResult>()

  const toolIds = parsedToolIds(toolIdsRaw)
  const canRun = !!upload.sessionId && !!config.api_key && toolIds.length > 0

  const missingItems = [
    !upload.sessionId && { icon: <Upload size={12} />, text: 'Upload an Alteryx workflow (.yxmd)' },
    !config.api_key && { icon: <Key size={12} />, text: 'Provide your OpenAI API key in the sidebar' },
    toolIds.length === 0 && { icon: <Hash size={12} />, text: 'Specify tool IDs to convert in the sidebar' },
  ].filter(Boolean) as { icon: React.ReactNode; text: string }[]

  const handleRun = async () => {
    if (!canRun) return
    resetDirect()
    setDirect({ status: 'running', progress: 0, message: 'Starting\u2026' })

    await run(
      '/api/convert/direct',
      {
        session_id: upload.sessionId,
        config,
        tool_ids: toolIds,
        extra_instructions: extraInstructions,
      },
      {
        onProgress: (value, message) => {
          setDirect({
            ...(isNaN(value) ? {} : { progress: value }),
            ...(message ? { message } : {}),
          })
        },
        onResult: (data) => {
          setDirect({ status: 'done', progress: 1, message: '', result: { finalScript: data.final_script, promptUsed: data.prompt_used } })
          addHistory({
            id: crypto.randomUUID(),
            timestamp: new Date().toISOString(),
            type: 'direct',
            tool_ids: toolIds.join(', '),
            extra_instructions: extraInstructions,
            model_info: `Gen: ${config.code_generate_model} | Combine: ${config.code_combine_model}`,
            temperature: config.temperature,
            final_script: data.final_script,
            prompt_used: data.prompt_used,
          })
        },
        onError: (msg) => {
          setDirect({ status: 'error', message: msg })
          void surfaceMessageError(msg, {
            title: 'Direct Conversion Failed',
            scope: 'direct-convert-step1',
            action: 'Run direct conversion',
          })
        },
      },
    )
  }

  const handleCancel = () => {
    cancel()
    setDirect({ status: 'idle', progress: 0, message: '' })
  }

  return (
    <div className="space-y-5 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-slate-100 mb-1">Direct Conversion</h2>
        <p className="text-sm text-muted">
          Generates Python code for each selected tool, then combines them into one executable script.
        </p>
      </div>

      {/* Validation checklist */}
      {missingItems.length > 0 && (
        <div className="rounded-xl border border-border bg-card/50 p-4">
          <div className="flex items-center gap-2 mb-2.5">
            <AlertCircle size={14} className="text-warning" />
            <span className="text-xs font-medium text-slate-300">Before you start</span>
          </div>
          <div className="space-y-1.5">
            {missingItems.map((item, i) => (
              <div key={i} className="flex items-center gap-2 text-xs text-muted">
                <span className="text-warning/70">{item.icon}</span>
                {item.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={direct.status === 'running' ? handleCancel : handleRun}
          disabled={direct.status !== 'running' && !canRun}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          style={
            direct.status === 'running'
              ? { background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'linear-gradient(135deg, #006C38, #00A650)', color: 'white', boxShadow: canRun ? '0 2px 12px rgba(0,166,80,0.3)' : 'none' }
          }
        >
          <Zap size={16} />
          {direct.status === 'running' ? 'Cancel' : 'Run Direct Conversion'}
        </button>
      </div>

      {/* Progress */}
      {(direct.status === 'running' || direct.status === 'error') && (
        <ProgressTracker
          status={direct.status}
          progress={direct.progress}
          message={direct.message}
          label={`Generating code for ${toolIds.length} tool${toolIds.length !== 1 ? 's' : ''}\u2026`}
        />
      )}

      {/* Result */}
      {direct.status === 'done' && direct.result && (
        <div className="space-y-4 fade-in">
          <div className="flex items-center gap-2 text-success text-sm font-medium">
            <Zap size={16} />
            Conversion complete!
          </div>

          <CodeViewer
            code={direct.result.finalScript}
            language="python"
            filename={`direct_conversion_${toolIds.slice(0, 3).join('-')}.py`}
          />

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
                  code={direct.result.promptUsed}
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
