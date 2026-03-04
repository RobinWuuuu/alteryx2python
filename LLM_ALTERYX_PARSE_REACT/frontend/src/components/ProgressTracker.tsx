import { useEffect, useRef, useState } from 'react'
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'

interface ProgressTrackerProps {
  status: 'idle' | 'running' | 'done' | 'error'
  progress: number // 0 to 1
  message?: string
  label?: string
}

export function ProgressTracker({ status, progress, message, label }: ProgressTrackerProps) {
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef<number | null>(null)

  useEffect(() => {
    if (status === 'running') {
      startRef.current = Date.now()
      setElapsed(0)
      const id = setInterval(() => {
        setElapsed(Math.floor((Date.now() - (startRef.current ?? Date.now())) / 1000))
      }, 1000)
      return () => clearInterval(id)
    }
  }, [status])

  if (status === 'idle') return null

  const pct = isNaN(progress) ? null : Math.round(progress * 100)

  return (
    <div className="rounded-xl border border-border bg-card p-4 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {status === 'running' && <Loader2 size={16} className="animate-spin text-primary" />}
          {status === 'done' && <CheckCircle2 size={16} className="text-success" />}
          {status === 'error' && <XCircle size={16} className="text-error" />}
          <span className="text-sm font-medium text-slate-200">
            {status === 'running' ? (label ?? 'Processing…') : status === 'done' ? 'Complete' : 'Failed'}
          </span>
        </div>
        {status === 'running' && (
          <span className="text-xs text-muted font-mono">{elapsed}s</span>
        )}
        {pct !== null && (
          <span className="text-xs font-medium text-primary">{pct}%</span>
        )}
      </div>

      {/* Progress bar */}
      {pct !== null && (
        <div className="h-1.5 bg-border rounded-full overflow-hidden mb-2">
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: `${pct}%`,
              background: status === 'error'
                ? '#ef4444'
                : status === 'done'
                ? '#10b981'
                : 'linear-gradient(90deg, #4f8ef7, #6366f1)',
            }}
          />
        </div>
      )}
      {pct === null && status === 'running' && (
        <div className="h-1.5 rounded-full overflow-hidden shimmer mb-2" />
      )}

      {/* Message */}
      {message && (
        <p className="text-xs text-muted leading-relaxed" style={{ wordBreak: 'break-word' }}>
          {message.replace(/\*\*/g, '')}
        </p>
      )}
    </div>
  )
}
