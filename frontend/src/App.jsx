import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from './api'
import MineDetail from './components/MineDetail'
import MineTable from './components/MineTable'
import Overview from './components/Overview'
import AddMineModal from './components/AddMineModal'

const initialSummary = { total_mines: 0, open_alerts: 0, high_risk_mines: 0, documents_reviewed: 0, risk_distribution: { Low: 0, Medium: 0, High: 0 }, state_summary: [], critical_demo_active: false }

export default function App() {
  const [role, setRole] = useState('inspector')
  const [filters, setFilters] = useState({ state: '', risk_band: '', mine_type: '' })
  const [summary, setSummary] = useState(initialSummary)
  const [mines, setMines] = useState([])
  const [alerts, setAlerts] = useState([])
  const [notice, setNotice] = useState(null)
  const [error, setError] = useState('')
  const [selectedMine, setSelectedMine] = useState(null)
  const [addingMine, setAddingMine] = useState(false)
  const [scenarioBusy, setScenarioBusy] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [dashboard, mineList, alertList, appConfig] = await Promise.all([api.dashboard(), api.mines(filters), api.alerts(), api.config()])
      setSummary(dashboard); setMines(mineList); setAlerts(alertList); setNotice(appConfig); setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [filters])

  useEffect(() => { refresh(); const interval = setInterval(refresh, 30000); return () => clearInterval(interval) }, [refresh])

  const launchCriticalScenario = async () => {
    setScenarioBusy(true)
    try {
      const alert = await api.criticalDemo()
      await refresh()
      setSelectedMine(alert.mine_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setScenarioBusy(false)
    }
  }

  const states = useMemo(() => [...new Set(mines.map((mine) => mine.state))].sort(), [mines])
  if (selectedMine) return <MineDetail mineId={selectedMine} onBack={() => setSelectedMine(null)} onChanged={refresh} />

  return (
    <main className="min-h-screen bg-slate-50 pb-12">
      <header className="topbar"><div className="page-shell flex items-center justify-between gap-4"><div className="brand"><span className="brand-mark">क</span><div><p>KHADAAN DRISHTI</p><small>खदान दृष्टि · Mine Vision</small></div></div><div className="flex items-center gap-3"><button onClick={() => setAddingMine(true)} className="topbar-action">+ Add mine</button><div className="role-toggle"><button onClick={() => setRole('inspector')} className={role === 'inspector' ? 'selected' : ''}>Inspector</button><button onClick={() => setRole('admin')} className={role === 'admin' ? 'selected' : ''}>Admin / Ministry</button></div></div></div></header>
      <div className="page-shell pt-8">
        <section className="mb-6 flex flex-col justify-between gap-4 lg:flex-row lg:items-end"><div><p className="eyebrow">Compliance command centre</p><h1 className="page-title">{role === 'admin' ? 'Portfolio compliance overview' : 'Inspector action dashboard'}</h1><p className="max-w-2xl text-sm leading-6 text-slate-600">Turn AI-assisted document checks into owned corrective actions with visible evidence, deadlines, and audit history.</p></div><span className="workspace-indicator"><i /> Demo workspace · refreshes every 30 seconds</span></section>
        {error && <div className="error-card mb-5">{error}<span> Start the API and run the seed command if this is a fresh setup.</span></div>}
        {notice && <details className="notice-card mb-5"><summary><strong>Demo data scope</strong><span> Curated mine context + synthetic documents, scores, and alerts.</span></summary><p>{notice.data_notice} {notice.feed_notice}</p></details>}
        <section className="validation-strip mb-5" aria-label="Prototype validation and method"><div><p className="eyebrow">Method transparency</p><h2>Evidence-first, inspector-in-the-loop</h2><p>15 explainable checklist clauses · PDF text extraction with OCR fallback · every decision remains subject to human review.</p></div><div className="validation-facts"><span><b>{summary.total_mines || 24}</b> curated mine contexts</span><span><b>{summary.documents_reviewed}</b> demo analyses</span><span>No field-accuracy claim</span></div></section>
        <Overview role={role} summary={summary} alerts={alerts} onSelect={setSelectedMine} onCriticalScenario={launchCriticalScenario} scenarioBusy={scenarioBusy} />
        <section className="panel mt-5"><div className="panel-heading flex-wrap"><div><h2>Mine risk ranking</h2><p>Lower composite score ranks first for faster intervention.</p></div><div className="filter-row"><select value={filters.state} onChange={(event) => setFilters((current) => ({ ...current, state: event.target.value }))}><option value="">All states</option>{states.map((state) => <option key={state}>{state}</option>)}</select><select value={filters.risk_band} onChange={(event) => setFilters((current) => ({ ...current, risk_band: event.target.value }))}><option value="">All risk bands</option><option>High</option><option>Medium</option><option>Low</option></select><select value={filters.mine_type} onChange={(event) => setFilters((current) => ({ ...current, mine_type: event.target.value }))}><option value="">All mine types</option><option value="open-cast">Open-cast</option><option value="underground">Underground</option></select></div></div><MineTable mines={mines} onSelect={setSelectedMine} /></section>
      </div>
      {addingMine && <AddMineModal onClose={() => setAddingMine(false)} onCreated={async (mineId) => { setAddingMine(false); await refresh(); setSelectedMine(mineId) }} />}
    </main>
  )
}
