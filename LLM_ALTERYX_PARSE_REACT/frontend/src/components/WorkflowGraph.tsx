import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type NodeProps,
  Handle,
  Position,
  BackgroundVariant,
  MarkerType,
  Panel,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import { Loader2, GitBranch, RefreshCw, LayoutDashboard, Sparkles, CheckCircle2, XCircle } from 'lucide-react'
import { useAppStore } from '../store/useAppStore'
import { streamPost } from '../api/client'
import axios from 'axios'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface WorkflowNode {
  tool_id: string
  tool_type: string
}

interface WorkflowConnection {
  origin_tool_id: string
  origin_connection: string
  destination_tool_id: string
  destination_connection: string
}

// ---------------------------------------------------------------------------
// Tool category coloring
// ---------------------------------------------------------------------------

type Category =
  | 'input' | 'output' | 'filter' | 'join'
  | 'formula' | 'aggregate' | 'select' | 'container' | 'other'

const CATEGORY_STYLES: Record<Category, { header: string; border: string; badge: string; dot: string }> = {
  input:     { header: 'bg-blue-900/60',   border: 'border-blue-500',   badge: 'bg-blue-500/20 text-blue-300',   dot: '#3b82f6' },
  output:    { header: 'bg-green-900/60',  border: 'border-green-500',  badge: 'bg-green-500/20 text-green-300', dot: '#22c55e' },
  filter:    { header: 'bg-orange-900/60', border: 'border-orange-500', badge: 'bg-orange-500/20 text-orange-300', dot: '#f97316' },
  join:      { header: 'bg-cyan-900/60',   border: 'border-cyan-500',   badge: 'bg-cyan-500/20 text-cyan-300',   dot: '#06b6d4' },
  formula:   { header: 'bg-purple-900/60', border: 'border-purple-500', badge: 'bg-purple-500/20 text-purple-300', dot: '#a855f7' },
  aggregate: { header: 'bg-yellow-900/60', border: 'border-yellow-500', badge: 'bg-yellow-500/20 text-yellow-300', dot: '#eab308' },
  select:    { header: 'bg-sky-900/60',    border: 'border-sky-400',    badge: 'bg-sky-500/20 text-sky-300',     dot: '#38bdf8' },
  container: { header: 'bg-slate-800/60',  border: 'border-slate-500',  badge: 'bg-slate-500/20 text-slate-300', dot: '#64748b' },
  other:     { header: 'bg-slate-800/60',  border: 'border-slate-600',  badge: 'bg-slate-600/20 text-slate-400', dot: '#475569' },
}

const CATEGORY_LABELS: Record<Category, string> = {
  input: 'Input', output: 'Output', filter: 'Filter',
  join: 'Join/Union', formula: 'Formula', aggregate: 'Aggregate',
  select: 'Select', container: 'Container', other: 'Other',
}

function getCategory(toolType: string): Category {
  const t = (toolType ?? '').toLowerCase()
  if (t.includes('input') || t === 'textinput' || t === 'qainput' || t === 'directoryinput') return 'input'
  if (t.includes('output')) return 'output'
  if (t === 'filter') return 'filter'
  if (t === 'join' || t === 'union' || t === 'appendfields' || t === 'fuzzymatching') return 'join'
  if (t.includes('formula') || t === 'generaterows') return 'formula'
  if (t === 'summarize' || t === 'sort' || t === 'sample' || t === 'uniquevalue' || t === 'transpose' || t === 'crosstab' || t === 'recordid') return 'aggregate'
  if (t === 'alteryxselect' || t.includes('select')) return 'select'
  if (t === 'toolcontainer') return 'container'
  return 'other'
}

const CATEGORY_ICONS: Record<Category, string> = {
  input: '📥', output: '📤', filter: '🔍', join: '🔗',
  formula: '⚡', aggregate: '📊', select: '✂️', container: '📦', other: '⚙️',
}

// ---------------------------------------------------------------------------
// Custom node component
// ---------------------------------------------------------------------------

const NODE_W = 200
const NODE_H_BASE = 72     // without description
const NODE_H_DESC = 118    // with description

type AlterxNodeData = {
  tool_id: string
  tool_type: string
  category: Category
  description?: string
}

function AlterxNode({ data }: NodeProps) {
  const d = data as AlterxNodeData
  const cat = d.category
  const styles = CATEGORY_STYLES[cat]
  const icon = CATEGORY_ICONS[cat]

  return (
    <div
      className={`rounded-xl border-2 ${styles.border} overflow-hidden shadow-lg`}
      style={{ width: NODE_W, background: '#16162a' }}
    >
      {/* Coloured header strip */}
      <div className={`${styles.header} px-3 py-1.5 flex items-center gap-1.5`}>
        <span className="text-sm">{icon}</span>
        <span className="text-xs font-semibold text-white/90 truncate leading-none">
          {d.tool_type}
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-1.5 flex items-center justify-between">
        <span className="text-xs text-slate-400">ID</span>
        <span className="text-sm font-mono font-bold text-slate-100">{d.tool_id}</span>
      </div>

      {/* Description (shown when LLM descriptions are loaded) */}
      {d.description && (
        <div className="px-3 pb-2 border-t border-white/5 pt-1.5">
          <p
            className="text-[10px] leading-[1.35] text-slate-400 italic"
            style={{
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical' as const,
              overflow: 'hidden',
            }}
          >
            {d.description}
          </p>
        </div>
      )}

      {/* Handles */}
      <Handle type="target" position={Position.Left}
        style={{ background: '#4a4a6a', width: 8, height: 8, border: '2px solid #1a1a2e' }} />
      <Handle type="source" position={Position.Right}
        style={{ background: '#4a4a6a', width: 8, height: 8, border: '2px solid #1a1a2e' }} />
    </div>
  )
}

const nodeTypes = { alterx: AlterxNode }

// ---------------------------------------------------------------------------
// Dagre layout
// ---------------------------------------------------------------------------

function applyDagreLayout(nodes: Node[], edges: Edge[], nodeH: number): Node[] {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR', ranksep: 80, nodesep: 30, edgesep: 20 })

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: nodeH }))
  edges.forEach((e) => g.setEdge(e.source, e.target))
  dagre.layout(g)

  return nodes.map((n) => {
    const pos = g.node(n.id)
    return { ...n, position: { x: pos.x - NODE_W / 2, y: pos.y - nodeH / 2 } }
  })
}

// ---------------------------------------------------------------------------
// Convert API data → React Flow nodes + edges
// ---------------------------------------------------------------------------

function buildGraph(
  apiNodes: WorkflowNode[],
  apiConns: WorkflowConnection[],
  descriptions: Record<string, string>,
): { nodes: Node[]; edges: Edge[] } {
  const hasDescs = Object.keys(descriptions).length > 0
  const nodeH = hasDescs ? NODE_H_DESC : NODE_H_BASE

  const nodes: Node[] = apiNodes.map((n) => ({
    id: n.tool_id,
    type: 'alterx',
    position: { x: 0, y: 0 },
    data: {
      tool_id: n.tool_id,
      tool_type: n.tool_type,
      category: getCategory(n.tool_type),
      description: descriptions[n.tool_id],
    },
  }))

  const edges: Edge[] = apiConns.map((c, i) => ({
    id: `e-${i}`,
    source: c.origin_tool_id,
    target: c.destination_tool_id,
    label: c.destination_connection && c.destination_connection !== 'Input'
      ? c.destination_connection
      : undefined,
    labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' },
    labelBgStyle: { fill: '#1a1a28', fillOpacity: 0.9 },
    labelBgPadding: [4, 2] as [number, number],
    style: { stroke: '#3a3a5a', strokeWidth: 1.5 },
    markerEnd: { type: MarkerType.ArrowClosed, color: '#3a3a5a', width: 14, height: 14 },
    animated: false,
  }))

  const laid = applyDagreLayout(nodes, edges, nodeH)
  return { nodes: laid, edges }
}

// ---------------------------------------------------------------------------
// Legend
// ---------------------------------------------------------------------------

function Legend({ counts }: { counts: Record<string, number> }) {
  const cats = Object.entries(counts).filter(([, c]) => c > 0) as [Category, number][]
  return (
    <div className="flex flex-wrap gap-2">
      {cats.map(([cat, count]) => (
        <div key={cat} className="flex items-center gap-1.5 text-xs px-2 py-1 rounded-lg bg-[#1a1a28] border border-[#2a2a3d]">
          <span>{CATEGORY_ICONS[cat]}</span>
          <span className="text-slate-300">{CATEGORY_LABELS[cat]}</span>
          <span className="font-mono font-bold" style={{ color: CATEGORY_STYLES[cat].dot }}>{count}</span>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Inline describe-progress bar
// ---------------------------------------------------------------------------

function DescribeProgress({ progress, message, status }: {
  progress: number
  message: string
  status: 'running' | 'done' | 'error'
}) {
  const pct = Math.round(progress * 100)
  return (
    <div className="flex items-center gap-2 text-xs bg-[#1a1a28] border border-[#2a2a3d] rounded-lg px-3 py-2">
      {status === 'running' && <Loader2 size={12} className="animate-spin text-primary shrink-0" />}
      {status === 'done' && <CheckCircle2 size={12} className="text-success shrink-0" />}
      {status === 'error' && <XCircle size={12} className="text-error shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-muted truncate">{message || (status === 'done' ? 'Descriptions ready' : '')}</p>
        {status === 'running' && (
          <div className="h-1 bg-border rounded-full overflow-hidden mt-1">
            <div
              className="h-full rounded-full transition-all duration-300"
              style={{ width: `${pct}%`, background: 'linear-gradient(90deg, #4f8ef7, #6366f1)' }}
            />
          </div>
        )}
      </div>
      {status === 'running' && (
        <span className="text-muted font-mono shrink-0">{pct}%</span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

type DescStatus = 'idle' | 'running' | 'done' | 'error'

export function WorkflowGraph() {
  const sessionId = useAppStore((s) => s.upload.sessionId)
  const filename = useAppStore((s) => s.upload.filename)
  const config = useAppStore((s) => s.config)

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [rawNodes, setRawNodes] = useState<WorkflowNode[]>([])
  const [rawConns, setRawConns] = useState<WorkflowConnection[]>([])

  // LLM descriptions
  const [descriptions, setDescriptions] = useState<Record<string, string>>({})
  const [descStatus, setDescStatus] = useState<DescStatus>('idle')
  const [descProgress, setDescProgress] = useState(0)
  const [descMessage, setDescMessage] = useState('')
  const abortRef = useRef<AbortController | null>(null)

  const loadWorkflow = useCallback(async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await axios.get(`/api/workflow/${sessionId}`)
      setRawNodes(data.nodes)
      setRawConns(data.connections)
      const { nodes: laid, edges: builtEdges } = buildGraph(data.nodes, data.connections, {})
      setNodes(laid)
      setEdges(builtEdges)
      // Reset descriptions when workflow changes
      setDescriptions({})
      setDescStatus('idle')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflow')
    } finally {
      setLoading(false)
    }
  }, [sessionId, setNodes, setEdges])

  useEffect(() => { loadWorkflow() }, [loadWorkflow])

  // Re-layout nodes whenever descriptions update
  useEffect(() => {
    if (rawNodes.length === 0) return
    const { nodes: laid, edges: builtEdges } = buildGraph(rawNodes, rawConns, descriptions)
    setNodes(laid)
    setEdges(builtEdges)
  }, [descriptions]) // eslint-disable-line react-hooks/exhaustive-deps

  const generateDescriptions = useCallback(async () => {
    if (!sessionId || !config.api_key) return
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl

    setDescStatus('running')
    setDescProgress(0)
    setDescMessage('Starting…')

    try {
      const stream = streamPost<{ descriptions: Record<string, string> }>(
        '/api/workflow/describe',
        {
          session_id: sessionId,
          config: {
            api_key: config.api_key,
            code_generate_model: config.code_generate_model,
            temperature: config.temperature,
          },
        },
        ctrl.signal,
      )

      for await (const event of stream) {
        if (event.type === 'progress') setDescProgress(event.value)
        else if (event.type === 'message') setDescMessage(event.text)
        else if (event.type === 'result') {
          setDescriptions(event.data.descriptions)
          setDescStatus('done')
          setDescMessage('All descriptions generated')
        } else if (event.type === 'error') {
          setDescStatus('error')
          setDescMessage(event.message)
        }
      }
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        setDescStatus('error')
        setDescMessage(err instanceof Error ? err.message : 'Failed')
      }
    }
  }, [sessionId, config])

  // Category counts for legend
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    rawNodes.forEach((n) => {
      const cat = getCategory(n.tool_type)
      counts[cat] = (counts[cat] ?? 0) + 1
    })
    return counts
  }, [rawNodes])

  if (!sessionId) {
    return (
      <div className="flex flex-col items-center justify-center h-full py-20 text-center">
        <GitBranch size={48} className="text-muted mb-4 opacity-30" />
        <p className="text-muted text-sm">Upload a .yxmd file to visualize the workflow graph.</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3 text-muted">
        <Loader2 size={20} className="animate-spin text-primary" />
        <span className="text-sm">Building workflow graph…</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <p className="text-error text-sm">{error}</p>
        <button
          onClick={loadWorkflow}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-muted hover:text-slate-200 border border-border hover:bg-white/5 transition-all"
        >
          <RefreshCw size={13} /> Retry
        </button>
      </div>
    )
  }

  const canDescribe = !!config.api_key && descStatus !== 'running'
  const hasDescriptions = Object.keys(descriptions).length > 0

  return (
    <div className="flex flex-col h-full gap-3">
      {/* Header row */}
      <div className="flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <LayoutDashboard size={16} className="text-primary" />
          <span className="text-sm font-semibold text-slate-200">{filename ?? 'Workflow'}</span>
          <span className="text-xs text-muted">
            {rawNodes.length} tools · {edges.length} connections
          </span>
        </div>
        <div className="flex items-center gap-2">
          {/* Describe Tools button */}
          <button
            onClick={generateDescriptions}
            disabled={!canDescribe}
            title={!config.api_key ? 'Enter your OpenAI API key in the sidebar first' : 'Generate 1-sentence LLM descriptions for each tool node'}
            className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg border transition-all"
            style={
              canDescribe
                ? { color: '#a78bfa', borderColor: '#7c3aed44', background: '#7c3aed18' }
                : { color: '#475569', borderColor: '#2a2a3d', background: 'transparent', cursor: 'not-allowed' }
            }
          >
            {descStatus === 'running'
              ? <Loader2 size={12} className="animate-spin" />
              : <Sparkles size={12} />}
            {hasDescriptions ? 'Re-describe' : 'Describe Tools'}
          </button>

          <button
            onClick={loadWorkflow}
            className="flex items-center gap-1.5 text-xs text-muted hover:text-slate-200 px-2.5 py-1.5 rounded-lg border border-border hover:bg-white/5 transition-all"
          >
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
      </div>

      {/* Describe progress bar (visible while running or on completion/error) */}
      {descStatus !== 'idle' && (
        <div className="shrink-0">
          <DescribeProgress
            progress={descProgress}
            message={descMessage}
            status={descStatus === 'running' ? 'running' : descStatus === 'done' ? 'done' : 'error'}
          />
        </div>
      )}

      {/* Legend */}
      <div className="shrink-0">
        <Legend counts={categoryCounts} />
      </div>

      {/* Graph canvas */}
      <div
        className="flex-1 rounded-xl overflow-hidden border border-border"
        style={{ minHeight: 0 }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.15 }}
          minZoom={0.1}
          maxZoom={2}
          proOptions={{ hideAttribution: true }}
          style={{ background: '#0d0d1a' }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={20}
            size={1}
            color="#2a2a3d"
          />
          <Controls
            style={{
              background: '#1a1a28',
              border: '1px solid #2a2a3d',
              borderRadius: '8px',
            }}
          />
          <MiniMap
            nodeColor={(n) => {
              const cat = (n.data as AlterxNodeData).category
              return CATEGORY_STYLES[cat]?.dot ?? '#475569'
            }}
            style={{
              background: '#12121a',
              border: '1px solid #2a2a3d',
              borderRadius: '8px',
            }}
            maskColor="rgba(0,0,0,0.5)"
          />
          <Panel position="bottom-center">
            <p className="text-xs text-muted/50 select-none">
              Scroll to zoom · Drag to pan · Drag nodes to reposition
            </p>
          </Panel>
        </ReactFlow>
      </div>
    </div>
  )
}
