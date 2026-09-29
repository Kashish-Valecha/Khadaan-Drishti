import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { SeverityBadge } from './RiskBadge'

const colors = { Low: '#198754', Medium: '#d9950b', High: '#c94740' }
const severityRank = { High: 0, Medium: 1, Low: 2 }
const dateLabel = (value) => value ? new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium' }).format(new Date(value)) : 'No deadline set'

function Metric({ label, value, helper, tone = 'default' }) {
  return <div className={`metric-card ${tone}`}><p>{label}</p><strong>{value}</strong><span>{helper}</span></div>
}

export default function Overview({ role, summary, alerts, onSelect, onCriticalScenario, scenarioBusy }) {
  const donut = Object.entries(summary.risk_distribution).map(([name, value]) => ({ name, value }))
  const highPriority = alerts
    .filter((alert) => ['open', 'reviewed'].includes(alert.status))
    .sort((first, second) => severityRank[first.severity] - severityRank[second.severity] || new Date(first.due_date || 0) - new Date(second.due_date || 0))
    .slice(0, 5)
  return (
    <>
      <section className="metrics-grid">
        <Metric label="Mines monitored" value={summary.total_mines} helper="Public context plus inspector records" />
        <Metric label="Open corrective actions" value={summary.open_alerts} helper="Assigned actions awaiting closure" tone="warning" />
        <Metric label="High-risk mines" value={summary.high_risk_mines} helper="Composite compliance score below 50" tone="danger" />
        <Metric label="Documents reviewed" value={summary.documents_reviewed} helper="AI-assisted checklist analyses" />
      </section>

      {!summary.critical_demo_active && <section className="critical-demo-card"><div><p className="eyebrow">Presentation control</p><h2>Launch a controlled critical scenario</h2><p>Creates one labelled synthetic emission-control scenario for Moonidih, assigns an owner and deadline, and visibly moves the mine into the high-risk band. It never represents a live sensor feed.</p></div><button className="primary-button" disabled={scenarioBusy} onClick={onCriticalScenario}>{scenarioBusy ? 'Launching…' : 'Launch critical demo'}</button></section>}
      {summary.critical_demo_active && <section className="critical-demo-card active"><div><p className="eyebrow">Controlled scenario active</p><h2>Critical action is ready for the walkthrough</h2><p>Open Moonidih from the immediate action queue to upload closure proof, write the verification note, and complete the evidence-backed closure.</p></div><span className="scenario-status">Synthetic test signal</span></section>}

      <section className="grid gap-5 xl:grid-cols-5">
        <div className="panel xl:col-span-3">
          <div className="panel-heading"><div><h2>{role === 'admin' ? 'State compliance overview' : 'Immediate action queue'}</h2><p>{role === 'admin' ? 'Average composite score by state' : 'Open and reviewed actions ranked by severity, then deadline'}</p></div></div>
          {role === 'admin' ? (
            <div className="h-[280px]">
              <ResponsiveContainer><BarChart data={summary.state_summary} margin={{ left: -18, right: 8, top: 12 }}><XAxis dataKey="state" tick={{ fontSize: 11 }} interval={0} angle={-22} textAnchor="end" height={65} /><YAxis domain={[0, 100]} tick={{ fontSize: 12 }} /><Tooltip /><Bar dataKey="average_score" name="Average score" fill="#294144" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {highPriority.length ? highPriority.map((alert) => <button className="alert-row w-full text-left" key={alert.id} onClick={() => onSelect(alert.mine_id)}><div><p className="font-semibold text-coal-800">{alert.mine_name}</p><p className="text-xs text-slate-500">{alert.event_type.replaceAll('_', ' ')} · Owner: {alert.assigned_to || 'Unassigned'} · Due {dateLabel(alert.due_date)}</p></div><div className="text-right"><SeverityBadge severity={alert.severity} /><p className="mt-1 text-xs capitalize text-slate-500">{alert.status.replaceAll('_', ' ')}</p></div></button>) : <div className="empty-state">No open corrective actions. Use a mine page to run one controlled simulated alert.</div>}
            </div>
          )}
        </div>
        <div className="panel xl:col-span-2">
          <div className="panel-heading"><div><h2>Risk distribution</h2><p>Composite score bands</p></div></div>
          <div className="relative h-[250px]">
            <ResponsiveContainer><PieChart><Pie data={donut} dataKey="value" nameKey="name" innerRadius={62} outerRadius={94} paddingAngle={3}>{donut.map((entry) => <Cell key={entry.name} fill={colors[entry.name]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 grid place-items-center text-center"><strong className="text-3xl text-coal-800">{summary.total_mines}</strong><span className="-mt-8 text-xs text-slate-500">mines</span></div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-center text-xs">{donut.map((item) => <div key={item.name}><span className="mr-1 inline-block h-2 w-2 rounded-full" style={{ background: colors[item.name] }} /><span className="text-slate-500">{item.name}</span><b className="ml-1 text-coal-800">{item.value}</b></div>)}</div>
        </div>
      </section>
    </>
  )
}
