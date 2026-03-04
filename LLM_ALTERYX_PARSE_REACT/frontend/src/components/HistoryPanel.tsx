import { useState } from 'react'
import { Clock, ChevronDown, ChevronRight, Trash2, Download, Zap, Layers } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { CodeViewer } from './CodeViewer'
import { MarkdownViewer } from './MarkdownViewer'
import type { HistoryItem } from '../api/types'

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

function buildAdvancedDownload(item: HistoryItem): string {
  const desc = item.tool_descriptions?.map(d => `Tool ${d.tool_id} (${d.tool_type}):\n${d.description}`).join('\n\n') ?? ''
  return `# Complete Python Workflow Output

Date: ${item.timestamp}
Model: ${item.model_info}
Temperature: ${item.temperature}
Tool IDs: ${item.tool_ids}

## Tool Descriptions
${desc}

---

## Python Code Structure Guide
${item.workflow_description ?? ''}

---

## Final Python Code
\`\`\`python
${item.final_python_code ?? ''}
\`\`\`

---

## Prompts Used

### Structure Guide Prompt
${item.workflow_prompt ?? ''}

### Final Code Prompt
${item.final_prompt ?? ''}
`
}

function HistoryCard({ item }: { item: HistoryItem }) {
  const deleteHistory = useAppStore((s) => s.deleteHistory)
  const [expanded, setExpanded] = useState(false)

  const ts = item.timestamp.replace('T', ' ').slice(0, 19)

  return (
    <div className="rounded-xl border border-border bg-card overflow-hidden fade-in">
      {/* Header row */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/5 transition-colors"
        onClick={() => setExpanded((e) => !e)}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="shrink-0">
            {item.type === 'direct' ? (
              <Zap size={16} className="text-secondary" />
            ) : (
              <Layers size={16} className="text-accent" />
            )}
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${item.type === 'direct' ? 'bg-secondary/20 text-secondary' : 'bg-accent/20 text-accent'}`}>
                {item.type === 'direct' ? 'Direct' : 'Advanced'}
              </span>
              <span className="text-xs text-muted font-mono truncate">{item.tool_ids}</span>
            </div>
            <div className="flex items-center gap-1.5 mt-0.5">
              <Clock size={11} className="text-muted" />
              <span className="text-xs text-muted">{ts}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0 ml-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              if (item.type === 'direct' && item.final_script) {
                downloadText(item.final_script, `direct_${ts.replace(/[: ]/g, '-')}.py`)
              } else {
                downloadText(buildAdvancedDownload(item), `advanced_${ts.replace(/[: ]/g, '-')}.md`)
              }
            }}
            className="p-1.5 rounded-lg text-muted hover:text-slate-200 hover:bg-white/10 transition-all"
          >
            <Download size={14} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); deleteHistory(item.id) }}
            className="p-1.5 rounded-lg text-muted hover:text-error hover:bg-error/10 transition-all"
          >
            <Trash2 size={14} />
          </button>
          {expanded ? <ChevronDown size={14} className="text-muted" /> : <ChevronRight size={14} className="text-muted" />}
        </div>
      </div>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-border p-4 space-y-4">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div><span className="text-muted">Model:</span> <span className="text-slate-300">{item.model_info}</span></div>
            <div><span className="text-muted">Temperature:</span> <span className="text-slate-300">{item.temperature}</span></div>
            {item.extra_instructions && (
              <div className="col-span-2"><span className="text-muted">Instructions:</span> <span className="text-slate-300">{item.extra_instructions}</span></div>
            )}
          </div>

          {item.type === 'direct' && item.final_script && (
            <CodeViewer code={item.final_script} filename={`direct_${ts}.py`} maxHeight="350px" />
          )}

          {item.type === 'advanced' && (
            <>
              {item.tool_descriptions && item.tool_descriptions.length > 0 && (
                <div>
                  <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Tool Descriptions</h4>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {item.tool_descriptions.map((d) => (
                      <div key={d.tool_id} className="rounded-lg bg-surface p-3 text-xs">
                        <span className="font-semibold text-primary">Tool {d.tool_id}</span>
                        <span className="text-muted"> ({d.tool_type})</span>
                        <p className="text-slate-400 mt-1 line-clamp-3">{d.description.slice(0, 200)}…</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {item.workflow_description && (
                <div>
                  <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Structure Guide</h4>
                  <MarkdownViewer content={item.workflow_description} maxHeight="250px" />
                </div>
              )}
              {item.final_python_code && (
                <div>
                  <h4 className="text-xs font-semibold text-muted uppercase tracking-wider mb-2">Final Python Code</h4>
                  <CodeViewer code={item.final_python_code} filename={`advanced_${ts}.py`} maxHeight="350px" />
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

export function HistoryPanel() {
  const history = useAppStore((s) => s.history)
  const clearHistory = useAppStore((s) => s.clearHistory)

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <Clock size={40} className="text-muted mb-4 opacity-40" />
        <p className="text-muted text-sm">No history yet.</p>
        <p className="text-muted text-xs mt-1 opacity-70">Generations will appear here after completion.</p>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-muted">{history.length} generation{history.length !== 1 ? 's' : ''}</span>
        <button
          onClick={clearHistory}
          className="flex items-center gap-1.5 text-xs text-muted hover:text-error transition-colors px-2 py-1 rounded-lg hover:bg-error/10"
        >
          <Trash2 size={12} />
          Clear all
        </button>
      </div>
      <div className="space-y-3">
        {history.map((item) => <HistoryCard key={item.id} item={item} />)}
      </div>
    </div>
  )
}
