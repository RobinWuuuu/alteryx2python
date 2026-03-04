import { useState } from 'react'
import { Layers, ChevronDown, ChevronRight, CheckCircle2, Circle, AlertCircle, Download, Tag } from 'lucide-react'
import { useAppStore, parsedToolIds } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { runStep2, runStep3 } from '../api/client'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import { MarkdownViewer } from '../components/MarkdownViewer'
import type { Step1Result } from '../api/types'

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

// Key colours for description bullet labels
const LABEL_COLORS: Record<string, string> = {
  purpose:   '#00A650',
  inputs:    '#6CC24A',
  outputs:   '#00A650',
  operation: '#0891b2',
  notes:     '#f59e0b',
}

function DescriptionCard({ description }: { description: string }) {
  const lines = description
    .split('\n')
    .map((l) => l.trim())
    .filter((l) => l.startsWith('-'))
    .map((l) => l.replace(/^-\s*/, ''))

  if (lines.length === 0) {
    return <p className="text-xs text-slate-400 whitespace-pre-wrap">{description}</p>
  }

  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        const colonIdx = line.indexOf(':')
        const label = colonIdx > 0 ? line.slice(0, colonIdx).trim() : ''
        const value = colonIdx > 0 ? line.slice(colonIdx + 1).trim() : line
        const color = LABEL_COLORS[label.toLowerCase()] ?? '#94a3b8'
        return (
          <div key={i} className="flex gap-2 text-xs leading-relaxed">
            {label && (
              <span
                className="shrink-0 font-semibold capitalize px-1.5 py-0.5 rounded text-[10px]"
                style={{ color, background: `${color}18`, border: `1px solid ${color}30` }}
              >
                {label}
              </span>
            )}
            <span className="text-slate-300">{value}</span>
          </div>
        )
      })}
    </div>
  )
}

function StepHeader({
  n, title, status,
}: { n: number; title: string; status: 'idle' | 'running' | 'done' | 'error' }) {
  const colors = {
    idle: { text: 'text-muted', bg: 'bg-border' },
    running: { text: 'text-primary', bg: 'bg-primary' },
    done: { text: 'text-success', bg: 'bg-success' },
    error: { text: 'text-error', bg: 'bg-error' },
  }
  const c = colors[status]
  return (
    <div className="flex items-center gap-3 mb-3">
      <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white ${c.bg}`}>
        {status === 'done' ? <CheckCircle2 size={16} /> : n}
      </div>
      <span className={`font-semibold text-sm ${c.text}`}>{title}</span>
    </div>
  )
}

export function AdvancedConversion() {
  const upload = useAppStore((s) => s.upload)
  const config = useAppStore((s) => s.config)
  const toolIdsRaw = useAppStore((s) => s.toolIdsRaw)
  const extraInstructions = useAppStore((s) => s.extraInstructions)
  const adv1 = useAppStore((s) => s.adv1)
  const adv2 = useAppStore((s) => s.adv2)
  const adv3 = useAppStore((s) => s.adv3)
  const setAdv1 = useAppStore((s) => s.setAdv1)
  const setAdv2 = useAppStore((s) => s.setAdv2)
  const setAdv3 = useAppStore((s) => s.setAdv3)
  const resetAdvanced = useAppStore((s) => s.resetAdvanced)
  const addHistory = useAppStore((s) => s.addHistory)

  const [showDescriptions, setShowDescriptions] = useState(false)
  const [showPrompts, setShowPrompts] = useState(false)

  const { run: runStep1SSE, cancel: cancelStep1 } = useStreamingJob<Step1Result>()

  const toolIds = parsedToolIds(toolIdsRaw)
  const canRun = !!upload.sessionId && !!config.api_key && toolIds.length > 0

  // ---- Step 1 ----
  const handleStep1 = async () => {
    if (!canRun) return
    resetAdvanced()
    setAdv1({ status: 'running', progress: 0, message: 'Starting…' })

    await runStep1SSE(
      '/api/convert/advanced/step1',
      { session_id: upload.sessionId, config, tool_ids: toolIds, extra_instructions: extraInstructions },
      {
        onProgress: (value, message) => {
          setAdv1({
            ...(isNaN(value) ? {} : { progress: value }),
            ...(message ? { message } : {}),
          })
        },
        onResult: (data) => setAdv1({ status: 'done', progress: 1, message: '', result: data }),
        onError: (msg) => setAdv1({ status: 'error', message: msg }),
      },
    )
  }

  // ---- Step 2 ----
  const handleStep2 = async () => {
    if (!adv1.result) return
    setAdv2({ status: 'running', result: null, error: null })
    try {
      const res = await runStep2(
        upload.sessionId!,
        config,
        toolIds,
        extraInstructions,
        adv1.result.descriptions,
        adv1.result.execution_sequence,
      )
      setAdv2({ status: 'done', result: res })
    } catch (err) {
      setAdv2({ status: 'error', error: err instanceof Error ? err.message : String(err) })
    }
  }

  // ---- Step 3 ----
  const handleStep3 = async () => {
    if (!adv1.result || !adv2.result) return
    setAdv3({ status: 'running', result: null, error: null })
    try {
      const res = await runStep3(
        upload.sessionId!,
        config,
        toolIds,
        extraInstructions,
        adv1.result.descriptions,
        adv1.result.execution_sequence,
        adv2.result.workflow_description,
      )
      setAdv3({ status: 'done', result: res })
      // Save to history
      addHistory({
        id: crypto.randomUUID(),
        timestamp: new Date().toISOString(),
        type: 'advanced',
        tool_ids: toolIds.join(', '),
        extra_instructions: extraInstructions,
        model_info: `Gen: ${config.code_generate_model} | Reasoning: ${config.reasoning_model} | Combine: ${config.code_combine_model}`,
        temperature: config.temperature,
        tool_descriptions: adv1.result.descriptions,
        workflow_description: adv2.result.workflow_description,
        workflow_prompt: adv2.result.workflow_prompt,
        final_python_code: res.final_python_code,
        final_prompt: res.final_prompt,
      })
    } catch (err) {
      setAdv3({ status: 'error', error: err instanceof Error ? err.message : String(err) })
    }
  }

  const buildCombinedDownload = () => {
    const desc = adv1.result?.descriptions.map(d => `Tool ${d.tool_id} (${d.tool_type}):\n${d.description}`).join('\n\n') ?? ''
    const now = new Date().toISOString().slice(0, 19).replace('T', ' ')
    return `# Complete Python Workflow Output
Date: ${now}
Tools: ${toolIds.join(', ')}

## Tool Descriptions
${desc}

---

## Python Code Structure Guide
${adv2.result?.workflow_description ?? ''}

---

## Final Python Code
\`\`\`python
${adv3.result?.final_python_code ?? ''}
\`\`\`

---

## Prompts Used

### Structure Guide Prompt
${adv2.result?.workflow_prompt ?? ''}

### Final Code Prompt
${adv3.result?.final_prompt ?? ''}
`
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted">
        Three-step comprehensive conversion: tool descriptions → structure guide → final Python code.
      </p>

      {!canRun && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2.5 text-xs text-warning">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>
            {!upload.sessionId && 'Upload a .yxmd file. '}
            {!config.api_key && 'Enter your OpenAI API key. '}
            {toolIds.length === 0 && 'Enter tool IDs above.'}
          </span>
        </div>
      )}

      {/* ---- STEP 1 ---- */}
      <div className="rounded-xl border border-border bg-card p-5">
        <StepHeader n={1} title="Generate Tool Descriptions" status={adv1.status} />
        <p className="text-xs text-muted mb-3">Creates detailed technical descriptions for each tool to guide code generation.</p>

        <button
          onClick={adv1.status === 'running' ? cancelStep1 : handleStep1}
          disabled={adv1.status !== 'running' && !canRun}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={
            adv1.status === 'running'
              ? { background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'rgba(0,166,80,0.12)', color: '#00A650', border: '1px solid rgba(0,166,80,0.3)' }
          }
        >
          <Layers size={14} />
          {adv1.status === 'running' ? 'Cancel' : adv1.status === 'done' ? 'Re-run Step 1' : 'Run Step 1'}
        </button>

        {(adv1.status === 'running' || adv1.status === 'error') && (
          <ProgressTracker
            status={adv1.status}
            progress={adv1.progress}
            message={adv1.message}
            label={`Generating descriptions for ${toolIds.length} tool${toolIds.length !== 1 ? 's' : ''}…`}
          />
        )}

        {adv1.status === 'done' && adv1.result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-success text-xs font-medium">
                <CheckCircle2 size={14} />
                {adv1.result.descriptions.length} descriptions generated
              </div>
              <button
                onClick={() => setShowDescriptions((v) => !v)}
                className="flex items-center gap-1 text-xs text-muted hover:text-slate-300 transition-colors"
              >
                {showDescriptions ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                {showDescriptions ? 'Hide' : 'Show'} descriptions
              </button>
            </div>
            {showDescriptions && (
              <div className="space-y-2 mt-2 max-h-64 overflow-y-auto">
                {adv1.result.descriptions.map((d) => (
                  <div key={d.tool_id} className="rounded-lg bg-surface border border-border p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Tag size={11} className="text-primary shrink-0" />
                      <span className="text-xs font-semibold text-primary">Tool {d.tool_id}</span>
                      <span className="text-xs text-muted">({d.tool_type})</span>
                    </div>
                    <DescriptionCard description={d.description} />
                  </div>
                ))}
              </div>
            )}
            {adv1.result && (
              <button
                onClick={() => {
                  const text = adv1.result!.descriptions.map(d => `Tool ${d.tool_id} (${d.tool_type}):\n${d.description}`).join('\n\n')
                  downloadText(text, 'tool_descriptions.txt')
                }}
                className="mt-2 flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
              >
                <Download size={12} /> Download descriptions
              </button>
            )}
          </div>
        )}
      </div>

      {/* ---- STEP 2 ---- */}
      <div className={`rounded-xl border bg-card p-5 transition-opacity ${adv1.status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`} style={{ borderColor: adv1.status === 'done' ? '#2a2a3d' : '#2a2a3d' }}>
        <StepHeader n={2} title="Generate Python Code Structure Guide" status={adv2.status} />
        <p className="text-xs text-muted mb-3">Creates a comprehensive guide for code organization, naming, and patterns.</p>

        <button
          onClick={handleStep2}
          disabled={adv1.status !== 'done' || adv2.status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'rgba(99,102,241,0.15)', color: '#6366f1', border: '1px solid rgba(99,102,241,0.3)' }}
        >
          {adv2.status === 'running' ? (
            <span className="flex items-center gap-2"><span className="w-3.5 h-3.5 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />Generating…</span>
          ) : (
            <><Circle size={14} />{adv2.status === 'done' ? 'Re-run Step 2' : 'Run Step 2'}</>
          )}
        </button>

        {adv2.status === 'error' && (
          <p className="text-xs text-error mb-2">{adv2.error}</p>
        )}

        {adv2.status === 'done' && adv2.result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-success text-xs font-medium">
                <CheckCircle2 size={14} /> Structure guide ready
              </div>
              <button
                onClick={() => downloadText(adv2.result!.workflow_description, 'code_structure_guide.md')}
                className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
              >
                <Download size={12} /> Download guide
              </button>
            </div>
            <MarkdownViewer content={adv2.result.workflow_description} maxHeight="350px" />
          </div>
        )}
      </div>

      {/* ---- STEP 3 ---- */}
      <div className={`rounded-xl border bg-card p-5 transition-opacity ${adv2.status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`} style={{ borderColor: '#2a2a3d' }}>
        <StepHeader n={3} title="Generate Final Python Code" status={adv3.status} />
        <p className="text-xs text-muted mb-3">Generates complete, production-ready Python code following the structure guide.</p>

        <button
          onClick={handleStep3}
          disabled={adv2.status !== 'done' || adv3.status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'linear-gradient(135deg, #006C38, #00A650)', color: 'white' }}
        >
          {adv3.status === 'running' ? (
            <span className="flex items-center gap-2"><span className="w-3.5 h-3.5 border-2 border-white/50 border-t-white rounded-full animate-spin" />Generating…</span>
          ) : (
            <><Layers size={14} />{adv3.status === 'done' ? 'Re-run Step 3' : 'Run Step 3'}</>
          )}
        </button>

        {adv3.status === 'error' && (
          <p className="text-xs text-error mb-2">{adv3.error}</p>
        )}

        {adv3.status === 'done' && adv3.result && (
          <div className="space-y-3 fade-in">
            <div className="flex items-center gap-2 text-success text-xs font-medium">
              <CheckCircle2 size={14} /> Final code generated!
            </div>
            <CodeViewer
              code={adv3.result.final_python_code}
              language="python"
              filename={`workflow_${toolIds.slice(0, 3).join('-')}.py`}
            />

            {/* Prompts */}
            <div className="rounded-xl border border-border overflow-hidden">
              <button
                onClick={() => setShowPrompts((v) => !v)}
                className="w-full flex items-center justify-between px-4 py-3 text-sm text-muted hover:bg-white/5 transition-colors"
              >
                <span>View Prompts Used</span>
                {showPrompts ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              </button>
              {showPrompts && (
                <div className="border-t border-border space-y-3 p-4">
                  <div>
                    <p className="text-xs text-muted mb-1">Structure Guide Prompt</p>
                    <CodeViewer code={adv2.result?.workflow_prompt ?? ''} language="text" maxHeight="200px" />
                  </div>
                  <div>
                    <p className="text-xs text-muted mb-1">Final Code Prompt</p>
                    <CodeViewer code={adv3.result.final_prompt} language="text" maxHeight="200px" />
                  </div>
                </div>
              )}
            </div>

            {/* Download all */}
            <button
              onClick={() => downloadText(buildCombinedDownload(), `complete_workflow_${new Date().toISOString().slice(0,10)}.md`)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', border: '1px solid rgba(16,185,129,0.3)' }}
            >
              <Download size={14} />
              Download All Outputs
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
