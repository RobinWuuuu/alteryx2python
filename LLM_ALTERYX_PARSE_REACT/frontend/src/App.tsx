import { useEffect, useState } from 'react'
import { Zap, Layers, Clock, GitBranch, PanelRightOpen, Database, Workflow } from 'lucide-react'
import { Sidebar } from './components/layout/Sidebar'
import { DirectConversion } from './pages/DirectConversion'
import { AdvancedConversion } from './pages/AdvancedConversion'
import { SqlDirectConversion } from './pages/SqlDirectConversion'
import { SqlAdvancedConversion } from './pages/SqlAdvancedConversion'
import { FabricAdvancedConversion } from './pages/FabricAdvancedConversion'
import { HistoryPanel } from './components/HistoryPanel'
import { WorkflowGraph } from './components/WorkflowGraph'
import { surfaceMessageError } from './utils/errorSupport'

type AppMode = 'python' | 'sql' | 'fabric'
type PythonTab  = 'direct' | 'advanced' | 'workflow' | 'history'
type SqlTab     = 'sql-direct' | 'sql-advanced' | 'workflow' | 'history'
type FabricTab  = 'fabric-advanced'
type Tab = PythonTab | SqlTab | FabricTab

const PYTHON_TABS: { id: PythonTab; label: string; icon: React.ReactNode }[] = [
  { id: 'direct',   label: 'Direct',   icon: <Zap size={13} /> },
  { id: 'advanced', label: 'Advanced', icon: <Layers size={13} /> },
  { id: 'workflow', label: 'Workflow', icon: <GitBranch size={13} /> },
  { id: 'history',  label: 'History',  icon: <Clock size={13} /> },
]

const SQL_TABS: { id: SqlTab; label: string; icon: React.ReactNode }[] = [
  { id: 'sql-direct',   label: 'SQL Direct',   icon: <Database size={13} /> },
  { id: 'sql-advanced', label: 'SQL Advanced', icon: <Layers size={13} /> },
  { id: 'workflow',     label: 'Workflow',     icon: <GitBranch size={13} /> },
  { id: 'history',      label: 'History',      icon: <Clock size={13} /> },
]

const FABRIC_TABS: { id: FabricTab; label: string; icon: React.ReactNode }[] = [
  { id: 'fabric-advanced', label: 'Advanced', icon: <Layers size={13} /> },
]

const MODE_COLORS = {
  python: { active: 'linear-gradient(135deg, #006C38, #00A650)', shadow: 'rgba(0,166,80,0.25)', ring: 'rgba(0,166,80,0.4)' },
  sql:    { active: 'linear-gradient(135deg, #164e63, #0891b2)', shadow: 'rgba(8,145,178,0.25)', ring: 'rgba(8,145,178,0.4)' },
  fabric: { active: 'linear-gradient(135deg, #4c1d95, #7c3aed)', shadow: 'rgba(124,58,237,0.25)', ring: 'rgba(124,58,237,0.4)' },
}

export default function App() {
  const [appMode, setAppMode]       = useState<AppMode>('python')
  const [pythonTab, setPythonTab]   = useState<PythonTab>('direct')
  const [sqlTab, setSqlTab]         = useState<SqlTab>('sql-direct')
  const [fabricTab, setFabricTab]   = useState<FabricTab>('fabric-advanced')
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const currentTab: Tab =
    appMode === 'python' ? pythonTab :
    appMode === 'sql'    ? sqlTab    :
                           fabricTab

  const tabs =
    appMode === 'python' ? PYTHON_TABS :
    appMode === 'sql'    ? SQL_TABS    :
                           FABRIC_TABS

  function setTab(id: string) {
    if (appMode === 'python') setPythonTab(id as PythonTab)
    else if (appMode === 'sql') setSqlTab(id as SqlTab)
    else setFabricTab(id as FabricTab)
  }

  const colors = MODE_COLORS[appMode]

  useEffect(() => {
    const ignorePattern = /ResizeObserver loop/i

    const onWindowError = (event: ErrorEvent) => {
      if (!event.message || ignorePattern.test(event.message)) return
      void surfaceMessageError(event.message, {
        title: 'Unexpected App Error',
        scope: 'renderer-window-error',
        action: 'Handle unexpected frontend exception',
        extraDetails: event.error?.stack || `${event.filename}:${event.lineno}:${event.colno}`,
      })
    }

    const onUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason =
        event.reason instanceof Error
          ? event.reason.stack || event.reason.message
          : String(event.reason)
      if (ignorePattern.test(reason)) return
      void surfaceMessageError(reason, {
        title: 'Unexpected App Error',
        scope: 'renderer-unhandled-rejection',
        action: 'Handle unhandled promise rejection',
      })
    }

    window.addEventListener('error', onWindowError)
    window.addEventListener('unhandledrejection', onUnhandledRejection)
    return () => {
      window.removeEventListener('error', onWindowError)
      window.removeEventListener('unhandledrejection', onUnhandledRejection)
    }
  }, [])

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: '#0a0a0f' }}>

      {/* Top bar */}
      <div
        className="shrink-0 flex items-center justify-between px-4 border-b border-border"
        style={{ height: 44, background: 'linear-gradient(180deg, #0c160e 0%, #0d0d1a 100%)' }}
      >
        <div className="flex items-center gap-2.5">
          <div
            className="shrink-0 w-7 h-7 rounded-lg flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #006C38 0%, #00A650 65%, #6CC24A 100%)',
              boxShadow: '0 1px 6px rgba(0,166,80,0.35)',
            }}
          >
            <Workflow size={13} className="text-white" strokeWidth={2.3} />
          </div>
          <span
            className="text-sm font-black leading-none hidden sm:block"
            style={{
              background: 'linear-gradient(90deg, #ffffff 30%, #6CC24A 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Pipeline Conversion Engine
          </span>
        </div>

        {/* Mode switcher */}
        <div className="flex items-center bg-[#0d0d1a] rounded-lg p-0.5 border border-border/60">
          {([
            { mode: 'python' as const, label: 'Alteryx \u2192 Python', icon: <Zap size={11} /> },
            { mode: 'sql' as const, label: 'Alteryx \u2192 SQL', icon: <Database size={11} /> },
            { mode: 'fabric' as const, label: 'MS Fabric \u2192 Code', icon: <Workflow size={11} /> },
          ]).map((m) => (
            <button
              key={m.mode}
              onClick={() => setAppMode(m.mode)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all"
              style={
                appMode === m.mode
                  ? { background: MODE_COLORS[m.mode].active, color: 'white', boxShadow: `0 1px 8px ${MODE_COLORS[m.mode].shadow}` }
                  : { color: '#64748b', background: 'transparent' }
              }
            >
              {m.icon} {m.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main area */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        <div
          className="shrink-0 h-full overflow-hidden transition-all duration-200"
          style={{ width: sidebarOpen ? 280 : 0 }}
        >
          <Sidebar onCollapse={() => setSidebarOpen(false)} appMode={appMode} />
        </div>

        {!sidebarOpen && (
          <div className="shrink-0 w-9 flex flex-col items-center pt-2.5 border-r border-border bg-surface/50">
            <button
              onClick={() => setSidebarOpen(true)}
              className="p-1.5 rounded-lg text-muted hover:text-slate-200 hover:bg-white/5 transition-all"
              title="Open sidebar"
            >
              <PanelRightOpen size={15} />
            </button>
          </div>
        )}

        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

          {/* Tab bar */}
          <div className="flex items-end gap-0.5 px-4 pt-2 border-b border-border shrink-0" style={{ background: '#0d0d14' }}>
            {tabs.map((t) => {
              const active = currentTab === t.id
              return (
                <button
                  key={t.id}
                  onClick={() => setTab(t.id)}
                  className="relative flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium transition-all"
                  style={{ color: active ? '#fff' : '#64748b' }}
                >
                  {t.icon}
                  {t.label}
                  {active && (
                    <span
                      className="absolute bottom-0 left-2 right-2 h-[2px] rounded-t-full"
                      style={{ background: colors.active, boxShadow: `0 0 8px ${colors.shadow}` }}
                    />
                  )}
                </button>
              )
            })}
          </div>

          {/* Tab content */}
          <div className={`flex-1 min-h-0 ${currentTab === 'workflow' ? 'overflow-hidden p-5' : 'overflow-y-auto p-6'}`}>
            {currentTab === 'direct'          && <DirectConversion />}
            {currentTab === 'advanced'        && <AdvancedConversion />}
            {currentTab === 'sql-direct'      && <SqlDirectConversion />}
            {currentTab === 'sql-advanced'    && <SqlAdvancedConversion />}
            {currentTab === 'fabric-advanced' && <FabricAdvancedConversion />}
            {currentTab === 'workflow'        && <WorkflowGraph />}
            {currentTab === 'history'         && <HistoryPanel />}
          </div>

        </div>
      </div>
    </div>
  )
}
