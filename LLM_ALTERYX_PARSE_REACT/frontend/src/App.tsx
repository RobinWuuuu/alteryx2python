import { useState } from 'react'
import { Zap, Layers, Clock, GitBranch, PanelRightOpen, Database, Workflow } from 'lucide-react'
import { Sidebar } from './components/layout/Sidebar'
import { DirectConversion } from './pages/DirectConversion'
import { AdvancedConversion } from './pages/AdvancedConversion'
import { SqlDirectConversion } from './pages/SqlDirectConversion'
import { SqlAdvancedConversion } from './pages/SqlAdvancedConversion'
import { FabricAdvancedConversion } from './pages/FabricAdvancedConversion'
import { HistoryPanel } from './components/HistoryPanel'
import { WorkflowGraph } from './components/WorkflowGraph'

type AppMode = 'python' | 'sql' | 'fabric'
type PythonTab  = 'direct' | 'advanced' | 'workflow' | 'history'
type SqlTab     = 'sql-direct' | 'sql-advanced' | 'workflow' | 'history'
type FabricTab  = 'fabric-advanced'
type Tab = PythonTab | SqlTab | FabricTab

const PYTHON_TABS: { id: PythonTab; label: string; icon: React.ReactNode }[] = [
  { id: 'direct',   label: 'Direct',   icon: <Zap size={14} /> },
  { id: 'advanced', label: 'Advanced', icon: <Layers size={14} /> },
  { id: 'workflow', label: 'Workflow', icon: <GitBranch size={14} /> },
  { id: 'history',  label: 'History',  icon: <Clock size={14} /> },
]

const SQL_TABS: { id: SqlTab; label: string; icon: React.ReactNode }[] = [
  { id: 'sql-direct',   label: 'SQL Direct',   icon: <Database size={14} /> },
  { id: 'sql-advanced', label: 'SQL Advanced', icon: <Layers size={14} /> },
  { id: 'workflow',     label: 'Workflow',     icon: <GitBranch size={14} /> },
  { id: 'history',      label: 'History',      icon: <Clock size={14} /> },
]

const FABRIC_TABS: { id: FabricTab; label: string; icon: React.ReactNode }[] = [
  { id: 'fabric-advanced', label: 'Advanced', icon: <Layers size={14} /> },
]

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

  return (
    <div className="flex flex-col h-screen overflow-hidden" style={{ background: '#0a0a0f' }}>

      {/* ── Top bar: brand + mode toggle ── */}
      <div
        className="shrink-0 flex items-center justify-between px-4 border-b border-border"
        style={{ height: 42, background: 'linear-gradient(180deg, #0c160e 0%, #0d0d1a 100%)' }}
      >
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div
            className="shrink-0 w-6 h-6 rounded-md flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, #006C38 0%, #00A650 65%, #6CC24A 100%)',
              boxShadow: '0 1px 6px rgba(0,166,80,0.35)',
            }}
          >
            <Workflow size={12} className="text-white" strokeWidth={2.3} />
          </div>
          <span
            className="text-[13px] font-black leading-none hidden sm:block"
            style={{
              background: 'linear-gradient(90deg, #ffffff 30%, #6CC24A 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Pipeline Conversion Engine
          </span>
        </div>

        {/* Mode buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={() => setAppMode('python')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all"
            style={
              appMode === 'python'
                ? { background: 'linear-gradient(135deg, #006C38, #00A650)', color: 'white', boxShadow: '0 1px 8px rgba(0,166,80,0.3)' }
                : { color: '#94a3b8', background: 'transparent' }
            }
          >
            <Zap size={12} /> Alteryx → Python
          </button>

          <div className="w-px h-4 bg-border/60" />

          <button
            onClick={() => setAppMode('sql')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all"
            style={
              appMode === 'sql'
                ? { background: 'linear-gradient(135deg, #164e63, #0891b2)', color: 'white', boxShadow: '0 1px 8px rgba(8,145,178,0.3)' }
                : { color: '#94a3b8', background: 'transparent' }
            }
          >
            <Database size={12} /> Alteryx → SQL
          </button>

          <div className="w-px h-4 bg-border/60" />

          <button
            onClick={() => setAppMode('fabric')}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all"
            style={
              appMode === 'fabric'
                ? { background: 'linear-gradient(135deg, #4c1d95, #7c3aed)', color: 'white', boxShadow: '0 1px 8px rgba(124,58,237,0.3)' }
                : { color: '#94a3b8', background: 'transparent' }
            }
          >
            <Workflow size={12} /> MS Fabric → Code
          </button>
        </div>
      </div>

      {/* ── Main area: sidebar + content ── */}
      <div className="flex flex-1 min-h-0 overflow-hidden">

        {/* Sidebar (collapsible) */}
        <div
          className="shrink-0 h-full overflow-hidden transition-all duration-200"
          style={{ width: sidebarOpen ? 280 : 0 }}
        >
          <Sidebar onCollapse={() => setSidebarOpen(false)} appMode={appMode} />
        </div>

        {/* Thin strip shown when sidebar is closed */}
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

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

          {/* Tabs nav */}
          <div className="flex items-center gap-1 px-4 pt-2.5 pb-0 border-b border-border shrink-0">
            {tabs.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-t-lg text-sm font-medium transition-all"
                style={
                  currentTab === t.id
                    ? appMode === 'python'
                      ? { background: 'linear-gradient(135deg, #006C38, #00A650)', color: 'white', boxShadow: '0 2px 12px rgba(0,166,80,0.25)' }
                      : appMode === 'sql'
                      ? { background: 'linear-gradient(135deg, #164e63, #0891b2)', color: 'white', boxShadow: '0 2px 12px rgba(8,145,178,0.25)' }
                      : { background: 'linear-gradient(135deg, #4c1d95, #7c3aed)', color: 'white', boxShadow: '0 2px 12px rgba(124,58,237,0.25)' }
                    : { color: '#94a3b8', background: 'transparent' }
                }
              >
                {t.icon}
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className={`flex-1 min-h-0 ${currentTab === 'workflow' ? 'overflow-hidden p-5' : 'overflow-y-auto p-5'}`}>
            {currentTab === 'direct'       && <DirectConversion />}
            {currentTab === 'advanced'     && <AdvancedConversion />}
            {currentTab === 'sql-direct'   && <SqlDirectConversion />}
            {currentTab === 'sql-advanced'    && <SqlAdvancedConversion />}
            {currentTab === 'fabric-advanced' && <FabricAdvancedConversion />}
            {currentTab === 'workflow'        && <WorkflowGraph />}
            {currentTab === 'history'      && <HistoryPanel />}
          </div>

        </div>
      </div>
    </div>
  )
}
