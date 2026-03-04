import { useState } from 'react'
import { ChevronDown, Loader2, Bot, ClipboardList, ListOrdered, PackageSearch,
         PanelLeftClose, Key, Hash, Workflow, Zap, Database,
         Upload, FileCheck, AlertCircle, X } from 'lucide-react'
import { useAppStore } from '../../store/useAppStore'
import { FileUpload } from '../FileUpload'
import { getSequence, getChildren, uploadFabricFile } from '../../api/client'

const MODEL_OPTIONS = [
  'gpt-4.1', 'gpt-4o', 'gpt-4o-mini', 'o1', 'o3-mini-high',
  'gpt-5', 'gpt-5.2', 'gpt-5-mini',
  'gpt-5.1-codex', 'gpt-5.1-codex-mini', 'gpt-5.1-codex-max',
]

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function Step({ n, title, optional, children, accent }: {
  n: number
  title: string
  optional?: boolean
  children: React.ReactNode
  accent?: { bg: string; color: string }
}) {
  const a = accent ?? { bg: 'rgba(0,166,80,0.18)', color: '#00A650' }
  return (
    <div>
      <div className="flex items-center gap-2 px-3 pt-3 pb-1.5">
        <span
          className="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0"
          style={{ background: a.bg, color: a.color }}
        >
          {n}
        </span>
        <span className="text-xs font-semibold text-slate-300 flex-1 leading-none">{title}</span>
        {optional && (
          <span className="text-[9px] uppercase tracking-wide text-muted border border-border rounded px-1 py-0.5 leading-none">
            opt
          </span>
        )}
      </div>
      <div className="px-3 pb-3">
        {children}
      </div>
    </div>
  )
}

function ModelSelect({ value, onChange, label }: {
  value: string
  onChange: (v: string) => void
  label: string
}) {
  return (
    <div className="mb-2 last:mb-0">
      <label className="block text-[10px] text-muted mb-1">{label}</label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-[#0d0d1a] border border-border rounded-md px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-primary/60 transition-colors cursor-pointer"
        >
          {MODEL_OPTIONS.map((o) => <option key={o} value={o}>{o}</option>)}
        </select>
        <ChevronDown size={11} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Fabric file upload widget (for sidebar)
// ---------------------------------------------------------------------------

function FabricFileUpload() {
  const fabricUpload    = useAppStore((s) => s.fabricUpload)
  const setFabricUpload = useAppStore((s) => s.setFabricUpload)
  const [uploading, setUploading] = useState(false)
  const [error, setError]         = useState<string | null>(null)
  const [dragOver, setDragOver]   = useState(false)

  async function handleFile(file: File) {
    if (!file.name.endsWith('.json') && !file.name.endsWith('.zip')) {
      setError('Only .json or .zip Fabric pipeline files are supported.')
      return
    }
    setUploading(true)
    setError(null)
    try {
      const res = await uploadFabricFile(file)
      setFabricUpload(res)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }

  if (fabricUpload) {
    return (
      <div className="rounded-lg p-3 fade-in" style={{ background: 'rgba(124,58,237,0.08)', border: '1px solid rgba(124,58,237,0.25)' }}>
        <div className="flex items-center gap-2 mb-1">
          <FileCheck size={14} style={{ color: '#8b5cf6' }} />
          <span className="text-xs font-medium text-slate-200 truncate">{fabricUpload.pipeline_name}</span>
        </div>
        <p className="text-[10px] text-muted truncate">{fabricUpload.filename}</p>
        <p className="text-[10px] mt-0.5" style={{ color: '#8b5cf6' }}>
          {fabricUpload.activity_count} activities
        </p>
        <button
          onClick={() => setFabricUpload(null)}
          className="mt-2 text-[10px] text-muted hover:text-slate-300 transition-colors flex items-center gap-1"
        >
          <X size={10} /> Replace file
        </button>
      </div>
    )
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleFile(f) }}
        onClick={() => {
          const input = document.createElement('input')
          input.type = 'file'
          input.accept = '.json,.zip'
          input.onchange = () => { const f = input.files?.[0]; if (f) handleFile(f) }
          input.click()
        }}
        className="rounded-lg border-2 border-dashed flex flex-col items-center justify-center gap-1.5 py-5 cursor-pointer transition-all"
        style={{
          borderColor: dragOver ? '#7c3aed' : '#2a2a3d',
          background: dragOver ? 'rgba(124,58,237,0.06)' : 'transparent',
        }}
      >
        {uploading ? (
          <Loader2 size={18} className="animate-spin" style={{ color: '#8b5cf6' }} />
        ) : (
          <Upload size={18} className="text-muted" />
        )}
        <p className="text-xs text-muted">{uploading ? 'Parsing…' : 'Drop .json / .zip'}</p>
        {!uploading && <p className="text-[10px] text-muted/60">or click to browse</p>}
      </div>
      {error && (
        <div className="mt-1.5 flex items-start gap-1 text-[10px] text-error">
          <AlertCircle size={11} className="mt-0.5 shrink-0" />
          {error}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Sidebar
// ---------------------------------------------------------------------------

const FABRIC_ACCENT = { bg: 'rgba(124,58,237,0.18)', color: '#8b5cf6' }

const MODE_HEADER = {
  python: {
    bg:         'linear-gradient(180deg, #0f1a12 0%, #12121a 100%)',
    iconBg:     'linear-gradient(135deg, #006C38, #00A650)',
    iconShadow: 'rgba(0,166,80,0.35)',
    icon:       <Zap size={13} className="text-white" strokeWidth={2.3} />,
    label:      'Alteryx → Python',
    labelColor: '#6CC24A',
  },
  sql: {
    bg:         'linear-gradient(180deg, #0b1720 0%, #12121a 100%)',
    iconBg:     'linear-gradient(135deg, #164e63, #0891b2)',
    iconShadow: 'rgba(8,145,178,0.35)',
    icon:       <Database size={13} className="text-white" strokeWidth={2.3} />,
    label:      'Alteryx → SQL',
    labelColor: '#38bdf8',
  },
  fabric: {
    bg:         'linear-gradient(180deg, #130d1f 0%, #12121a 100%)',
    iconBg:     'linear-gradient(135deg, #4c1d95, #7c3aed)',
    iconShadow: 'rgba(124,58,237,0.35)',
    icon:       <Workflow size={13} className="text-white" strokeWidth={2.3} />,
    label:      'MS Fabric → Code',
    labelColor: '#a78bfa',
  },
} as const

export function Sidebar({ onCollapse, appMode }: {
  onCollapse: () => void
  appMode: 'python' | 'sql' | 'fabric'
}) {
  const config               = useAppStore((s) => s.config)
  const setConfig            = useAppStore((s) => s.setConfig)
  const upload               = useAppStore((s) => s.upload)
  const sequenceStr          = useAppStore((s) => s.sequenceStr)
  const setSequenceStr       = useAppStore((s) => s.setSequenceStr)
  const toolIdsRaw           = useAppStore((s) => s.toolIdsRaw)
  const setToolIdsRaw        = useAppStore((s) => s.setToolIdsRaw)
  const extraInstructions    = useAppStore((s) => s.extraInstructions)
  const setExtraInstructions = useAppStore((s) => s.setExtraInstructions)
  const setChildToolIds      = useAppStore((s) => s.setChildToolIds)
  const childToolIds         = useAppStore((s) => s.childToolIds)

  const hdr = MODE_HEADER[appMode]

  const [seqLoading,     setSeqLoading]     = useState(false)
  const [seqError,       setSeqError]       = useState<string | null>(null)
  const [seqExpanded,    setSeqExpanded]    = useState(false)
  const [containerInput, setContainerInput] = useState('')
  const [childLoading,   setChildLoading]   = useState(false)
  const [childError,     setChildError]     = useState<string | null>(null)

  const handleGenerateSequence = async () => {
    if (!upload.sessionId) return
    setSeqLoading(true)
    setSeqError(null)
    try {
      const res = await getSequence(upload.sessionId)
      setSequenceStr(res.sequence_str)
    } catch (err) {
      setSeqError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setSeqLoading(false)
    }
  }

  const handleFetchChildren = async () => {
    if (!upload.sessionId || !containerInput.trim()) return
    setChildLoading(true)
    setChildError(null)
    try {
      const res = await getChildren(upload.sessionId, containerInput.trim())
      setChildToolIds(res.child_tool_ids)
    } catch (err) {
      setChildError(err instanceof Error ? err.message : 'Failed')
    } finally {
      setChildLoading(false)
    }
  }

  const seqCount = sequenceStr ? sequenceStr.split(',').filter(Boolean).length : 0

  return (
    <aside className="flex flex-col h-full bg-surface border-r border-border" style={{ width: 280 }}>

      {/* Brand header */}
      <div
        className="flex items-center justify-between px-3 py-3 border-b border-border shrink-0"
        style={{ background: hdr.bg }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="shrink-0 w-7 h-7 rounded-lg flex items-center justify-center"
            style={{ background: hdr.iconBg, boxShadow: `0 2px 8px ${hdr.iconShadow}` }}
          >
            {hdr.icon}
          </div>
          <span
            className="text-[13px] font-black leading-none"
            style={{ color: hdr.labelColor }}
          >
            {hdr.label}
          </span>
        </div>
        <button
          onClick={onCollapse}
          className="p-1 rounded text-muted hover:text-slate-200 hover:bg-white/5 transition-all"
          title="Collapse sidebar"
        >
          <PanelLeftClose size={14} />
        </button>
      </div>

      {/* Steps (scrollable) */}
      <div className="flex-1 overflow-y-auto divide-y divide-border/50">

        {appMode === 'fabric' ? (
          /* ── Fabric sidebar ── */
          <>
            {/* 1 · Upload Pipeline */}
            <Step n={1} title="Upload Pipeline" accent={FABRIC_ACCENT}>
              <FabricFileUpload />
            </Step>

            {/* 2 · API Key */}
            <Step n={2} title="OpenAI API Key" accent={FABRIC_ACCENT}>
              <div className="relative">
                <Key size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="password"
                  value={config.api_key}
                  onChange={(e) => setConfig({ api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full bg-[#0d0d1a] border border-border rounded-md pl-7 pr-3 py-1.5 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-[#7c3aed]/60 transition-colors"
                />
              </div>
            </Step>

            {/* 3 · Models */}
            <Step n={3} title="Models" accent={FABRIC_ACCENT}>
              <div className="flex items-center gap-1 mb-2">
                <Bot size={10} className="text-muted" />
                <span className="text-[10px] text-muted">Select model for each stage</span>
              </div>
              <ModelSelect
                label="Describe Activities (per-activity)"
                value={config.code_generate_model}
                onChange={(v) => setConfig({ code_generate_model: v })}
              />
              <ModelSelect
                label="Structure Guide"
                value={config.reasoning_model}
                onChange={(v) => setConfig({ reasoning_model: v })}
              />
              <ModelSelect
                label="Final Code Generation"
                value={config.code_combine_model}
                onChange={(v) => setConfig({ code_combine_model: v })}
              />
            </Step>

            {/* 4 · Extra Instructions */}
            <Step n={4} title="Extra Instructions" optional accent={FABRIC_ACCENT}>
              <textarea
                value={extraInstructions}
                onChange={(e) => setExtraInstructions(e.target.value)}
                placeholder="e.g. Use PySpark instead of pandas, prefix env vars with FABRIC_"
                rows={4}
                className="w-full bg-[#0d0d1a] border border-border rounded-md px-2.5 py-2 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-[#7c3aed]/60 transition-colors resize-none"
              />
            </Step>
          </>
        ) : (
          /* ── Alteryx sidebar (Python & SQL modes) ── */
          <>
            {/* 1 · Upload */}
            <Step n={1} title="Upload Workflow">
              <FileUpload />
            </Step>

            {/* 2 · API Key */}
            <Step n={2} title="OpenAI API Key">
              <div className="relative">
                <Key size={11} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted" />
                <input
                  type="password"
                  value={config.api_key}
                  onChange={(e) => setConfig({ api_key: e.target.value })}
                  placeholder="sk-..."
                  className="w-full bg-[#0d0d1a] border border-border rounded-md pl-7 pr-3 py-1.5 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-primary/60 transition-colors"
                />
              </div>
            </Step>

            {/* 3 · Models */}
            <Step n={3} title="Models">
              <div className="flex items-center gap-1 mb-2">
                <Bot size={10} className="text-muted" />
                <span className="text-[10px] text-muted">Select model for each stage</span>
              </div>
              <ModelSelect
                label="Code Generate (per-tool)"
                value={config.code_generate_model}
                onChange={(v) => setConfig({ code_generate_model: v })}
              />
              <ModelSelect
                label="Reasoning (descriptions)"
                value={config.reasoning_model}
                onChange={(v) => setConfig({ reasoning_model: v })}
              />
              <ModelSelect
                label="Code Combine (final)"
                value={config.code_combine_model}
                onChange={(v) => setConfig({ code_combine_model: v })}
              />
            </Step>

            {/* 4 · Get Tool IDs (helpers) */}
            <Step n={4} title="Get Tool IDs">

              {/* Execution sequence */}
              <div className="mb-3">
                <p className="text-[10px] text-muted uppercase tracking-wide mb-1.5">Execution Sequence</p>
                <div className="flex items-center gap-2 flex-wrap">
                  <button
                    onClick={handleGenerateSequence}
                    disabled={!upload.sessionId || seqLoading}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-all disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ background: 'rgba(0,166,80,0.1)', color: '#00A650', border: '1px solid rgba(0,166,80,0.25)' }}
                  >
                    {seqLoading
                      ? <Loader2 size={11} className="animate-spin" />
                      : <ListOrdered size={11} />}
                    Generate
                  </button>
                  {sequenceStr && (
                    <>
                      <span className="text-[10px] text-success font-mono">{seqCount} tools</span>
                      <button
                        onClick={() => setToolIdsRaw(sequenceStr)}
                        className="flex items-center gap-1 px-2 py-1.5 rounded-md text-[10px] font-medium transition-all ml-auto"
                        style={{ background: 'rgba(108,194,74,0.1)', color: '#6CC24A', border: '1px solid rgba(108,194,74,0.25)' }}
                        title="Paste all IDs into Tool IDs field"
                      >
                        <ClipboardList size={10} /> Use IDs
                      </button>
                    </>
                  )}
                </div>
                {seqError && <p className="text-[10px] text-error mt-1">{seqError}</p>}
                {sequenceStr && (
                  <div className="mt-1.5">
                    <button
                      onClick={() => setSeqExpanded((v) => !v)}
                      className="text-[10px] text-muted hover:text-slate-400 transition-colors"
                    >
                      {seqExpanded ? '▾ Hide sequence' : '▸ Show sequence'}
                    </button>
                    {seqExpanded && (
                      <p className="text-[10px] font-mono text-slate-400 break-all mt-1 p-2 rounded bg-[#0d0d1a] border border-border leading-relaxed">
                        {sequenceStr}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Container children */}
              <div>
                <p className="text-[10px] text-muted uppercase tracking-wide mb-1.5">Container Children</p>
                <div className="flex gap-1.5">
                  <input
                    value={containerInput}
                    onChange={(e) => setContainerInput(e.target.value)}
                    placeholder="Container Tool ID"
                    className="flex-1 min-w-0 bg-[#0d0d1a] border border-border rounded-md px-2.5 py-1.5 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-primary/60 transition-colors"
                  />
                  <button
                    onClick={handleFetchChildren}
                    disabled={!upload.sessionId || !containerInput.trim() || childLoading}
                    className="px-2.5 py-1.5 rounded-md transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0"
                    style={{ background: 'rgba(0,166,80,0.1)', color: '#00A650', border: '1px solid rgba(0,166,80,0.25)' }}
                  >
                    {childLoading ? <Loader2 size={11} className="animate-spin" /> : <PackageSearch size={11} />}
                  </button>
                </div>
                {childError && <p className="text-[10px] text-error mt-1">{childError}</p>}
                {childToolIds.length > 0 && (
                  <p className="text-[10px] font-mono text-slate-400 break-all mt-1.5 p-2 rounded bg-[#0d0d1a] border border-border leading-relaxed">
                    [{childToolIds.join(', ')}]
                  </p>
                )}
              </div>
            </Step>

            {/* 5 · Tool IDs */}
            <Step n={5} title="Tool IDs for Conversion">
              <div className="flex items-center gap-1 mb-1.5">
                <Hash size={10} className="text-muted" />
                <span className="text-[10px] text-muted">Comma-separated</span>
              </div>
              <textarea
                value={toolIdsRaw}
                onChange={(e) => setToolIdsRaw(e.target.value)}
                placeholder="e.g. 644, 645, 646"
                rows={2}
                className="w-full bg-[#0d0d1a] border border-border rounded-md px-2.5 py-2 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-primary/60 transition-colors font-mono resize-none"
              />
            </Step>

            {/* 6 · Extra Instructions */}
            <Step n={6} title="Extra Instructions" optional>
              <textarea
                value={extraInstructions}
                onChange={(e) => setExtraInstructions(e.target.value)}
                placeholder="e.g. These tools clean the CD data, use lowercase column names"
                rows={3}
                className="w-full bg-[#0d0d1a] border border-border rounded-md px-2.5 py-2 text-xs text-slate-200 placeholder-muted focus:outline-none focus:border-primary/60 transition-colors resize-none"
              />
            </Step>
          </>
        )}

      </div>
    </aside>
  )
}
