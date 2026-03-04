import { useState } from 'react'
import { Database, ChevronDown, ChevronRight, CheckCircle2, Circle, AlertCircle, Download, Tag } from 'lucide-react'
import { useAppStore, parsedToolIds } from '../store/useAppStore'
import { useStreamingJob } from '../hooks/useStreamingJob'
import { runSqlStep2, runSqlStep3 } from '../api/client'
import { ProgressTracker } from '../components/ProgressTracker'
import { CodeViewer } from '../components/CodeViewer'
import { MarkdownViewer } from '../components/MarkdownViewer'
import type { Step1Result, SqlStep2Result, SqlStep3Result } from '../api/types'

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

function StepHeader({ n, title, status }: {
  n: number; title: string; status: 'idle' | 'running' | 'done' | 'error'
}) {
  const colors = {
    idle:    { text: 'text-muted',    bg: 'bg-border' },
    running: { text: 'text-primary',  bg: 'bg-primary' },
    done:    { text: 'text-success',  bg: 'bg-success' },
    error:   { text: 'text-error',    bg: 'bg-error' },
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

export function SqlAdvancedConversion() {
  const upload = useAppStore((s) => s.upload)
  const config = useAppStore((s) => s.config)
  const toolIdsRaw = useAppStore((s) => s.toolIdsRaw)
  const extraInstructions = useAppStore((s) => s.extraInstructions)

  // Step 1 — same structure as Python (tool descriptions)
  const [step1Status, setStep1Status] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [step1Progress, setStep1Progress] = useState(0)
  const [step1Message, setStep1Message] = useState('')
  const [step1Result, setStep1Result] = useState<Step1Result | null>(null)

  // Step 2 — SQL structure guide
  const [step2Status, setStep2Status] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [step2Result, setStep2Result] = useState<SqlStep2Result | null>(null)
  const [step2Error, setStep2Error] = useState<string | null>(null)

  // Step 3 — Final SQL
  const [step3Status, setStep3Status] = useState<'idle' | 'running' | 'done' | 'error'>('idle')
  const [step3Result, setStep3Result] = useState<SqlStep3Result | null>(null)
  const [step3Error, setStep3Error] = useState<string | null>(null)

  const [showDescriptions, setShowDescriptions] = useState(false)
  const [showPrompts, setShowPrompts] = useState(false)

  const { run: runStep1SSE, cancel: cancelStep1 } = useStreamingJob<Step1Result>()

  const toolIds = parsedToolIds(toolIdsRaw)
  const canRun = !!upload.sessionId && !!config.api_key && toolIds.length > 0

  const resetAll = () => {
    setStep1Status('idle'); setStep1Progress(0); setStep1Message(''); setStep1Result(null)
    setStep2Status('idle'); setStep2Result(null); setStep2Error(null)
    setStep3Status('idle'); setStep3Result(null); setStep3Error(null)
  }

  // ---- Step 1: Tool descriptions (reuses the same backend endpoint as Python) ----
  const handleStep1 = async () => {
    if (!canRun) return
    resetAll()
    setStep1Status('running')
    setStep1Progress(0)
    setStep1Message('Starting…')

    await runStep1SSE(
      '/api/convert/sql/advanced/step1',
      { session_id: upload.sessionId, config, tool_ids: toolIds, extra_instructions: extraInstructions },
      {
        onProgress: (value, msg) => {
          setStep1Progress(isNaN(value) ? step1Progress : value)
          if (msg) setStep1Message(msg)
        },
        onResult: (data) => {
          setStep1Status('done')
          setStep1Progress(1)
          setStep1Message('')
          setStep1Result(data)
        },
        onError: (_msg) => setStep1Status('error'),
      },
    )
  }

  // ---- Step 2: SQL structure guide ----
  const handleStep2 = async () => {
    if (!step1Result) return
    setStep2Status('running')
    setStep2Result(null)
    setStep2Error(null)
    try {
      const res = await runSqlStep2(
        upload.sessionId!,
        config,
        toolIds,
        extraInstructions,
        step1Result.descriptions,
        step1Result.execution_sequence,
      )
      setStep2Status('done')
      setStep2Result(res)
    } catch (err) {
      setStep2Status('error')
      setStep2Error(err instanceof Error ? err.message : String(err))
    }
  }

  // ---- Step 3: Final SQL ----
  const handleStep3 = async () => {
    if (!step1Result || !step2Result) return
    setStep3Status('running')
    setStep3Result(null)
    setStep3Error(null)
    try {
      const res = await runSqlStep3(
        upload.sessionId!,
        config,
        toolIds,
        extraInstructions,
        step1Result.descriptions,
        step1Result.execution_sequence,
        step2Result.sql_structure_guide,
      )
      setStep3Status('done')
      setStep3Result(res)
    } catch (err) {
      setStep3Status('error')
      setStep3Error(err instanceof Error ? err.message : String(err))
    }
  }

  const buildCombinedDownload = () => {
    const desc = step1Result?.descriptions.map(d => `Tool ${d.tool_id} (${d.tool_type}):\n${d.description}`).join('\n\n') ?? ''
    const now = new Date().toISOString().slice(0, 19).replace('T', ' ')
    return `# Complete SQL Workflow Output
Date: ${now}
Tools: ${toolIds.join(', ')}

## Tool Descriptions
${desc}

---

## SQL CTE Structure Guide
${step2Result?.sql_structure_guide ?? ''}

---

## Final SQL Script
\`\`\`sql
${step3Result?.final_sql ?? ''}
\`\`\`

---

## Prompts Used

### Structure Guide Prompt
${step2Result?.sql_structure_prompt ?? ''}

### Final SQL Prompt
${step3Result?.final_prompt ?? ''}
`
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted">
        Three-step SQL conversion: tool descriptions → SQL structure guide → final SQL script with CTEs.
      </p>

      {!canRun && (
        <div className="flex items-start gap-2 rounded-lg border border-warning/30 bg-warning/10 px-3 py-2.5 text-xs text-warning">
          <AlertCircle size={14} className="mt-0.5 shrink-0" />
          <span>
            {!upload.sessionId && 'Upload a .yxmd file. '}
            {!config.api_key && 'Enter your OpenAI API key. '}
            {toolIds.length === 0 && 'Enter tool IDs in the sidebar.'}
          </span>
        </div>
      )}

      {/* ---- STEP 1 ---- */}
      <div className="rounded-xl border border-border bg-card p-5">
        <StepHeader n={1} title="Generate Tool Descriptions" status={step1Status} />
        <p className="text-xs text-muted mb-3">Analyzes each Alteryx tool to build context for SQL generation.</p>

        <button
          onClick={step1Status === 'running' ? cancelStep1 : handleStep1}
          disabled={step1Status !== 'running' && !canRun}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={
            step1Status === 'running'
              ? { background: 'rgba(239,68,68,0.15)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.3)' }
              : { background: 'rgba(20,184,166,0.15)', color: '#14b8a6', border: '1px solid rgba(20,184,166,0.3)' }
          }
        >
          <Database size={14} />
          {step1Status === 'running' ? 'Cancel' : step1Status === 'done' ? 'Re-run Step 1' : 'Run Step 1'}
        </button>

        {(step1Status === 'running' || step1Status === 'error') && (
          <ProgressTracker
            status={step1Status}
            progress={step1Progress}
            message={step1Message}
            label={`Generating descriptions for ${toolIds.length} tool${toolIds.length !== 1 ? 's' : ''}…`}
          />
        )}

        {step1Status === 'done' && step1Result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-success text-xs font-medium">
                <CheckCircle2 size={14} />
                {step1Result.descriptions.length} descriptions generated
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
                {step1Result.descriptions.map((d) => (
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
            <button
              onClick={() => {
                const text = step1Result!.descriptions.map(d => `Tool ${d.tool_id} (${d.tool_type}):\n${d.description}`).join('\n\n')
                downloadText(text, 'tool_descriptions.txt')
              }}
              className="mt-2 flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
            >
              <Download size={12} /> Download descriptions
            </button>
          </div>
        )}
      </div>

      {/* ---- STEP 2 ---- */}
      <div className={`rounded-xl border border-border bg-card p-5 transition-opacity ${step1Status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`}>
        <StepHeader n={2} title="Generate SQL Structure Guide" status={step2Status} />
        <p className="text-xs text-muted mb-3">Creates a CTE chain design and SQL patterns guide for the workflow.</p>

        <button
          onClick={handleStep2}
          disabled={step1Status !== 'done' || step2Status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'rgba(99,102,241,0.15)', color: '#6366f1', border: '1px solid rgba(99,102,241,0.3)' }}
        >
          {step2Status === 'running' ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-accent/50 border-t-accent rounded-full animate-spin" />
              Generating…
            </span>
          ) : (
            <><Circle size={14} />{step2Status === 'done' ? 'Re-run Step 2' : 'Run Step 2'}</>
          )}
        </button>

        {step2Status === 'error' && <p className="text-xs text-error mb-2">{step2Error}</p>}

        {step2Status === 'done' && step2Result && (
          <div className="fade-in">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-success text-xs font-medium">
                <CheckCircle2 size={14} /> SQL structure guide ready
              </div>
              <button
                onClick={() => downloadText(step2Result!.sql_structure_guide, 'sql_structure_guide.md')}
                className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-300 transition-colors"
              >
                <Download size={12} /> Download guide
              </button>
            </div>
            <MarkdownViewer content={step2Result.sql_structure_guide} maxHeight="350px" />
          </div>
        )}
      </div>

      {/* ---- STEP 3 ---- */}
      <div className={`rounded-xl border border-border bg-card p-5 transition-opacity ${step2Status !== 'done' ? 'opacity-40 pointer-events-none' : ''}`}>
        <StepHeader n={3} title="Generate Final SQL Script" status={step3Status} />
        <p className="text-xs text-muted mb-3">Generates a complete SQL script with CTEs following the structure guide.</p>

        <button
          onClick={handleStep3}
          disabled={step2Status !== 'done' || step3Status === 'running'}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed mb-3"
          style={{ background: 'linear-gradient(135deg, #0f766e, #14b8a6)', color: 'white' }}
        >
          {step3Status === 'running' ? (
            <span className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 border-2 border-white/50 border-t-white rounded-full animate-spin" />
              Generating…
            </span>
          ) : (
            <><Database size={14} />{step3Status === 'done' ? 'Re-run Step 3' : 'Run Step 3'}</>
          )}
        </button>

        {step3Status === 'error' && <p className="text-xs text-error mb-2">{step3Error}</p>}

        {step3Status === 'done' && step3Result && (
          <div className="space-y-3 fade-in">
            <div className="flex items-center gap-2 text-success text-xs font-medium">
              <CheckCircle2 size={14} /> Final SQL generated!
            </div>
            <CodeViewer
              code={step3Result.final_sql}
              language="sql"
              filename={`workflow_${toolIds.slice(0, 3).join('-')}.sql`}
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
                    <CodeViewer code={step2Result?.sql_structure_prompt ?? ''} language="text" maxHeight="200px" />
                  </div>
                  <div>
                    <p className="text-xs text-muted mb-1">Final SQL Prompt</p>
                    <CodeViewer code={step3Result.final_prompt} language="text" maxHeight="200px" />
                  </div>
                </div>
              )}
            </div>

            {/* Download all */}
            <button
              onClick={() => downloadText(buildCombinedDownload(), `complete_sql_workflow_${new Date().toISOString().slice(0,10)}.md`)}
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
