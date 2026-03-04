import { useState } from 'react'
import {
  Layers, ChevronDown, ChevronRight, CheckCircle2, Circle,
  AlertCircle, Download, Tag,
} from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { runFabricStep2, runFabricStep3 } from '../api/client'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import { MarkdownViewer } from '../components/MarkdownViewer'
import type { FabricStep1Result, FabricActivity } from '../api/types'

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

const LABEL_COLORS: Record<string, string> = {
  purpose:   '#7c3aed',
  inputs:    '#8b5cf6',
  outputs:   '#7c3aed',
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

function StepHeader({ n, title, status }: {
  n: number; title: string; status: 'idle' | 'running' | 'done' | 'error'
}) {
  const colors = {
    idle:    { text: 'text-muted',     bg: '#2a2a3d' },
    running: { text: 'text-[#7c3aed]', bg: '#7c3aed' },
    done:    { text: 'text-[#7c3aed]', bg: '#7c3aed' },
    error:   { text: 'text-error',     bg: '#ef4444' },
  }
  const c = colors[status]
  return (
    <div className="flex items-center gap-3 mb-3">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white"
        style={{ background: c.bg }}
      >
        {status === 'done' ? <CheckCircle2 size={16} /> : n}
      </div>
      <span className={`font-semibold text-sm ${c.text}`}>{title}</span>
    </div>
  )
}

interface Step1State {
  status: 'idle' | 'running' | 'done' | 'error'
  progress: number
  message: string
  result: FabricStep1Result | null
}

interface Step2State {
  status: 'idle' | 'running' | 'done' | 'error'
  result: { structure_guide: string; structure_prompt: string } | null
  error: string | null
}

interface Step3State {
  status: 'idle' | 'running' | 'done' | 'error'
  result: { final_code: string; final_prompt: string } | null
  error: string | null
}

export function FabricAdvancedConversion() {
  const config            = useAppStore((s) => s.config)
  const extraInstructions = useAppStore((s) => s.extraInstructions)
  const fabricUpload      = useAppStore((s) => s.fabricUpload)

  const [step1, setStep1] = useState<Step1State>({
    status: 'idle', progress: 0, message: '', result: null,
  })
  const [step2, setStep2] = useState<Step2State>({ status: 'idle', result: null, error: null })
  const [step3, setStep3] = useState<Step3State>({ status: 'idle', result: null, error: null })

  const [showDescriptions, setShowDescriptions] = useState(false)
  const [showPrompts, setShowPrompts] = useState(false)

  const { run: runStep1SSE, cancel: cancelStep1 } = useStreamingJob<FabricStep1Result>()

  const canRun = !!fabricUpload && !!config.api_key

  function resetSteps() {
    setStep1({ status: 'idle', progress: 0, message: '', result: null })
    setStep2({ status: 'idle', result: null, error: null })
    setStep3({ status: 'idle', result: null, error: null })
  }

  // ── Step 1 ──
  const handleStep1 = async () => {
    if (!canRun || !fabricUpload) return
    resetSteps()
    setStep1({ status: 'running', progress: 0, message: 'Starting…', result: null })

    await runStep1SSE(
      '/api/fabric/advanced/step1',
      {
        session_id: fabricUpload.session_id,
        config,
        activity_names: fabricUpload.activity_names,
        extra_instructions: extraInstructions,
      },
      {
        onProgress: (value, message) => {
          setStep1((prev) => ({
            ...prev,
            ...(isNaN(value) ? {} : { progress: value }),
            ...(message ? { message } : {}),
          }))
        },
        onResult: (data) =>
          setStep1({ status: 'done', progress: 1, message: '', result: data }),
        onError: (_msg) =>
          setStep1((prev) => ({ ...prev, status: 'error', message: _msg })),
      },
    )
  }

  // ── Step 2 ──
  const handleStep2 = async () => {
    if (!step1.result || !fabricUpload) return
    setStep2({ status: 'running', result: null, error: null })
    try {
      const res = await runFabricStep2(
        fabricUpload.session_id,
        config,
        step1.result.activity_names,
        extraInstructions,
        step1.result.descriptions,
        step1.result.execution_sequence,
      )
      setStep2({ status: 'done', result: res, error: null })
    } catch (err) {
      setStep2({ status: 'error', result: null, error: err instanceof Error ? err.message : String(err) })
    }
  }

  // ── Step 3 ──
  const handleStep3 = async () => {
    if (!step1.result || !step2.result || !fabricUpload) return
    setStep3({ status: 'running', result: null, error: null })
    try {
      const res = await runFabricStep3(
        fabricUpload.session_id,
        config,
        step1.result.activity_names,
        extraInstructions,
        step1.result.descriptions,
        step1.result.execution_sequence,
        step2.result.structure_guide,
      )
      setStep3({ status: 'done', result: res, error: null })
    } catch (err) {
      setStep3({ status: 'error', result: null, error: err instanceof Error ? err.message : String(err) })
    }
  }

  function buildCombinedDownload() {
    const desc = (step1.result?.descriptions ?? [])
      .map((d: FabricActivity) => `Activity: ${d.activity_name} (${d.activity_type})\n${d.description}`)
      .join('\n\n')
    const now = new Date().toISOString().slice(0, 19).replace('T', ' ')
    return `# Fabric Pipeline → Python
Date: ${now}
Pipeline: ${fabricUpload?.pipeline_name ?? ''}

## Activity Descriptions
${desc}

---

## Code Structure Guide
${step2.result?.structure_guide ?? ''}

---

## Final Python Code
\`\`\`python
${step3.result?.final_code ?? ''}
\`\`\`

---

## Prompts Used

### Structure Guide Prompt
${step2.result?.structure_prompt ?? ''}

### Final Code Prompt
${step3.result?.final_prompt ?? ''}
`
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted">
        Three-step conversion: describe Fabric pipeline activities → structure guide → final Python/SQL code.
      </p>

      {!canRun && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2.5 text-xs text-warning">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>
            {!fabricUpload && 'Upload a Fabric pipeline file in the sidebar. '}
            {!config.api_key && 'Enter your OpenAI API key in the sidebar.'}
          </span>
        </div>
      )}

      {/* ── STEP 1 ── */}
      <div className="rounded-xl border border-border bg-card p-5">
        <StepHeader n={1} title="Describe Pipeline Activities" status={step1.status} />
        <p className="text-xs text-muted mb-3">
          Generates detailed descriptions of each Fabric activity to guide code generation.
        </p>

        <button
          onClick={step1.status === 'running' ? cancelStep1 : handleStep1}
          disabled={step1.status !== 'running' && !canRun}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={
            step1.status === 'running'
              ? { background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'rgba(124,58,237,0.12)', color: '#8b5cf6', border: '1px solid rgba(124,58,237,0.3)' }
          }
        >
          <Layers size={14} />
          {step1.status === 'running' ? 'Cancel' : step1.status === 'done' ? 'Re-run Step 1' : 'Run Step 1'}
        </button>

        {(step1.status === 'running' || step1.status === 'error') && (
          <ProgressTracker
            status={step1.status}
            progress={step1.progress}
            message={step1.message}
            label={`Describing ${fabricUpload?.activity_count ?? 0} activities…`}
          />
        )}

        {step1.status === 'done' && step1.result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs font-medium" style={{ color: '#7c3aed' }}>
                <CheckCircle2 size={14} />
                {step1.result.descriptions.length} activities described
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
                {step1.result.descriptions.map((d: FabricActivity) => (
                  <div key={d.activity_name} className="rounded-lg bg-surface border border-border p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <Tag size={11} style={{ color: '#7c3aed' }} className="shrink-0" />
                      <span className="text-xs font-semibold" style={{ color: '#8b5cf6' }}>{d.activity_name}</span>
                      <span className="text-xs text-muted">({d.activity_type})</span>
                    </div>
                    <DescriptionCard description={d.description} />
                  </div>
                ))}
              </div>
            )}

            <button
              onClick={() => {
                const text = step1.result!.descriptions
                  .map((d: FabricActivity) => `${d.activity_name} (${d.activity_type}):\n${d.description}`)
                  .join('\n\n')
                downloadText(text, 'fabric_activity_descriptions.txt')
              }}
              className="mt-2 flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
            >
              <Download size={12} /> Download descriptions
            </button>
          </div>
        )}
      </div>

      {/* ── STEP 2 ── */}
      <div
        className={`rounded-xl border bg-card p-5 transition-opacity ${step1.status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`}
        style={{ borderColor: '#2a2a3d' }}
      >
        <StepHeader n={2} title="Generate Code Structure Guide" status={step2.status} />
        <p className="text-xs text-muted mb-3">
          Maps Fabric activities to Python equivalents and defines the pipeline architecture.
        </p>

        <button
          onClick={handleStep2}
          disabled={step1.status !== 'done' || step2.status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'rgba(99,102,241,0.15)', color: '#6366f1', border: '1px solid rgba(99,102,241,0.3)' }}
        >
          {step2.status === 'running' ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-indigo-400/50 border-t-indigo-400 rounded-full animate-spin" />
              Generating…
            </span>
          ) : (
            <><Circle size={14} />{step2.status === 'done' ? 'Re-run Step 2' : 'Run Step 2'}</>
          )}
        </button>

        {step2.status === 'error' && (
          <p className="text-xs text-error mb-2">{step2.error}</p>
        )}

        {step2.status === 'done' && step2.result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-xs font-medium" style={{ color: '#7c3aed' }}>
                <CheckCircle2 size={14} /> Structure guide ready
              </div>
              <button
                onClick={() => downloadText(step2.result!.structure_guide, 'fabric_structure_guide.md')}
                className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
              >
                <Download size={12} /> Download guide
              </button>
            </div>
            <MarkdownViewer content={step2.result.structure_guide} maxHeight="350px" />
          </div>
        )}
      </div>

      {/* ── STEP 3 ── */}
      <div
        className={`rounded-xl border bg-card p-5 transition-opacity ${step2.status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`}
        style={{ borderColor: '#2a2a3d' }}
      >
        <StepHeader n={3} title="Generate Final Python Code" status={step3.status} />
        <p className="text-xs text-muted mb-3">
          Generates complete Jupyter-compatible Python code for the Fabric pipeline.
        </p>

        <button
          onClick={handleStep3}
          disabled={step2.status !== 'done' || step3.status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'linear-gradient(135deg, #4c1d95, #7c3aed)', color: 'white' }}
        >
          {step3.status === 'running' ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/50 border-t-white rounded-full animate-spin" />
              Generating…
            </span>
          ) : (
            <><Layers size={14} />{step3.status === 'done' ? 'Re-run Step 3' : 'Run Step 3'}</>
          )}
        </button>

        {step3.status === 'error' && (
          <p className="text-xs text-error mb-2">{step3.error}</p>
        )}

        {step3.status === 'done' && step3.result && (
          <div className="space-y-3 fade-in">
            <div className="flex items-center gap-2 text-xs font-medium" style={{ color: '#7c3aed' }}>
              <CheckCircle2 size={14} /> Final code generated!
            </div>

            <CodeViewer
              code={step3.result.final_code}
              language="python"
              filename={`${fabricUpload?.pipeline_name ?? 'fabric_pipeline'}.py`}
            />

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
                    <CodeViewer code={step2.result?.structure_prompt ?? ''} language="text" maxHeight="200px" />
                  </div>
                  <div>
                    <p className="text-xs text-muted mb-1">Final Code Prompt</p>
                    <CodeViewer code={step3.result.final_prompt} language="text" maxHeight="200px" />
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={() =>
                downloadText(
                  buildCombinedDownload(),
                  `${fabricUpload?.pipeline_name ?? 'fabric'}_${new Date().toISOString().slice(0, 10)}.md`,
                )
              }
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ background: 'rgba(124,58,237,0.15)', color: '#8b5cf6', border: '1px solid rgba(124,58,237,0.3)' }}
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
