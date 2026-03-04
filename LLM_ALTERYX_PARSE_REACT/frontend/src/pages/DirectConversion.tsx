import { useState } from 'react'
import { Zap, ChevronDown, ChevronRight, AlertCircle } from 'lucide-react'
import { useAppStore, parsedToolIds } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import type { DirectConvertResult } from '../api/types'

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

  const handleRun = async () => {
    if (!canRun) return
    resetDirect()
    setDirect({ status: 'running', progress: 0, message: 'Starting…' })

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
        onError: (msg) => setDirect({ status: 'error', message: msg }),
      },
    )
  }

  const handleCancel = () => {
    cancel()
    setDirect({ status: 'idle', progress: 0, message: '' })
  }

  return (
    <div className="space-y-5">
      {/* Description */}
      <p className="text-sm text-muted">
        Quick per-tool code generation + smart combine into a single Python script.
      </p>

      {/* Validation hints */}
      {(!upload.sessionId || !config.api_key || toolIds.length === 0) && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2.5 text-xs text-warning">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>
            {!upload.sessionId && 'Upload a .yxmd file. '}
            {!config.api_key && 'Enter your OpenAI API key. '}
            {toolIds.length === 0 && 'Enter tool IDs above.'}
          </span>
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
              : { background: 'linear-gradient(135deg, #006C38, #00A650)', color: 'white' }
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
          label={`Generating code for ${toolIds.length} tool${toolIds.length !== 1 ? 's' : ''}…`}
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
