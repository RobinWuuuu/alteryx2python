import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'

interface MarkdownViewerProps {
  content: string
  maxHeight?: string
}

export function MarkdownViewer({ content, maxHeight = '600px' }: MarkdownViewerProps) {
  return (
    <div
      className="overflow-auto rounded-xl border border-border bg-card p-5 prose prose-invert prose-sm max-w-none"
      style={{ maxHeight }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '')
            const inline = !match
            if (inline) {
              return (
                <code
                  className="bg-[#1e1e2e] text-primary px-1.5 py-0.5 rounded text-xs font-mono"
                  {...props}
                >
                  {children}
                </code>
              )
            }
            return (
              <SyntaxHighlighter
                language={match[1]}
                style={vscDarkPlus}
                customStyle={{
                  margin: '0.75rem 0',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                  fontFamily: "'JetBrains Mono', monospace",
                }}
              >
                {String(children).replace(/\n$/, '')}
              </SyntaxHighlighter>
            )
          },
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-slate-100 mb-4 pb-2 border-b border-border">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-semibold text-slate-200 mt-6 mb-3">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-slate-300 mt-4 mb-2">{children}</h3>
          ),
          p: ({ children }) => (
            <p className="text-slate-300 text-sm leading-relaxed mb-3">{children}</p>
          ),
          ul: ({ children }) => (
            <ul className="text-slate-300 text-sm space-y-1 list-disc list-inside mb-3">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="text-slate-300 text-sm space-y-1 list-decimal list-inside mb-3">{children}</ol>
          ),
          li: ({ children }) => <li className="text-sm">{children}</li>,
          strong: ({ children }) => <strong className="text-slate-100 font-semibold">{children}</strong>,
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-primary/50 pl-4 my-3 text-muted italic">{children}</blockquote>
          ),
          hr: () => <hr className="border-border my-4" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
