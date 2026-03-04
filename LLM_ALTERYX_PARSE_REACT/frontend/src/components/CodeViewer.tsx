import { useState } from 'react'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, Download, Code2 } from 'lucide-react'

interface CodeViewerProps {
  code: string
  language?: string
  filename?: string
  maxHeight?: string
}

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export function CodeViewer({
  code,
  language = 'python',
  filename = 'output.py',
  maxHeight = '500px',
}: CodeViewerProps) {
  const [copied, setCopied] = useState(false)

  const lineCount = code.split('\n').length

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-xl overflow-hidden border border-border bg-[#1e1e2e]">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-[#16162a] border-b border-border">
        <div className="flex items-center gap-2 text-muted">
          <Code2 size={14} />
          <span className="text-xs font-mono">{language}</span>
          <span className="text-xs opacity-50">·</span>
          <span className="text-xs">{lineCount} lines</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadText(code, filename)}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs text-muted hover:text-slate-200 hover:bg-white/10 transition-all"
          >
            <Download size={13} />
            Download
          </button>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs transition-all"
            style={{
              color: copied ? '#10b981' : '#94a3b8',
              background: copied ? 'rgba(16,185,129,0.1)' : undefined,
            }}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
      </div>

      {/* Code */}
      <div className="code-scroll overflow-auto" style={{ maxHeight }}>
        <SyntaxHighlighter
          language={language}
          style={vscDarkPlus}
          showLineNumbers
          lineNumberStyle={{ color: '#4a4a6a', fontSize: '12px', minWidth: '2.5em' }}
          customStyle={{
            margin: 0,
            padding: '1rem',
            background: 'transparent',
            fontSize: '13px',
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}
