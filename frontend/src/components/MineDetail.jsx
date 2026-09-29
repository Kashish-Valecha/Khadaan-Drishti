import { useEffect, useRef, useState } from 'react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api'
import { RiskBadge, SeverityBadge } from './RiskBadge'

const formatDate = (value) => new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))

function ComponentScore({ label, detail, color }) {
  return <div className="rounded-xl border border-slate-100 bg-slate-50 p-4"><div className="flex items-end justify-between"><p className="text-sm font-semibold text-coal-700">{label}</p><strong className="text-2xl text-coal-800">{detail.score}</strong></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full" style={{ width: `${detail.score}%`, background: color }} /></div><p className="mt-2 text-xs text-slate-500">Baseline {detail.baseline}; deductions {detail.deductions.reduce((sum, item) => sum + item.points, 0).toFixed(1)}</p>{detail.deductions.length > 0 && <ul className="mt-3 space-y-1 text-xs text-slate-600">{detail.deductions.slice(0, 3).map((deduction, index) => <li key={`${deduction.label}-${index}`}>−{deduction.points} {deduction.label}</li>)}</ul>}</div>
}

export default function MineDetail({ mineId, onBack, onChanged }) {
  const [mine, setMine] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [passportDrafts, setPassportDrafts] = useState({})
  const fileInput = useRef(null)

  const loadMine = async () => {
    try { setMine(await api.mine(mineId)); setError('') } catch (err) { setError(err.message) }
  }
  useEffect(() => { loadMine(); const interval = setInterval(loadMine, 30000); return () => clearInterval(interval) }, [mineId])

  const runAction = async (alert, status) => {
    const draft = passportDraft(alert)
    if (status === 'action_taken' && (!draft.closure_evidence_document_id || !draft.closure_note.trim())) {
      setError('Select or upload closure evidence and add an inspector verification note before closing this action.')
      return
    }
    setBusy(true)
    try {
      await api.updateAlert(alert.id, {
        status,
        taken_by: 'Inspector Demo User',
        notes: status === 'action_taken' ? 'Inspector verified the corrective action in the synthetic demo.' : 'Alert reviewed in the synthetic demo.',
        ...(status === 'action_taken' ? {
          closure_evidence_document_id: Number(draft.closure_evidence_document_id),
          closure_note: draft.closure_note.trim(),
        } : {}),
      })
      await loadMine(); onChanged()
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const defaultPassportDraft = (alert) => ({
    assigned_to: alert.assigned_to || '',
    due_date: alert.due_date ? new Date(alert.due_date).toISOString().slice(0, 10) : '',
    action_plan: alert.action_plan || '',
    closure_evidence_document_id: alert.closure_evidence_document_id ? String(alert.closure_evidence_document_id) : '',
    closure_note: alert.closure_note || '',
  })
  const passportDraft = (alert) => passportDrafts[alert.id] || defaultPassportDraft(alert)
  const updatePassportDraft = (alert, field, value) => setPassportDrafts((current) => ({
    ...current,
    [alert.id]: { ...(current[alert.id] || defaultPassportDraft(alert)), [field]: value },
  }))
  const savePassport = async (alert) => {
    const draft = passportDraft(alert)
    if (!draft.assigned_to.trim() || !draft.action_plan.trim() || !draft.due_date) {
      setError('Set an accountable owner, due date, and corrective action before saving the compliance passport.')
      return
    }
    setBusy(true)
    try {
      await api.updateAlert(alert.id, {
        status: alert.status,
        taken_by: 'Inspector Demo User',
        notes: 'Corrective action passport updated with accountable owner, deadline, and remedy.',
        assigned_to: draft.assigned_to.trim(),
        due_date: `${draft.due_date}T17:00:00`,
        action_plan: draft.action_plan.trim(),
      })
      await loadMine(); onChanged()
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const triggerDemoAlert = async () => {
    setBusy(true)
    try { await api.demoAlert(mineId); await loadMine(); onChanged() } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const upload = async (file) => {
    if (!file) return
    setBusy(true)
    try { await api.upload(mineId, file); await loadMine(); onChanged() } catch (err) { setError(err.message) } finally { setBusy(false); if (fileInput.current) fileInput.current.value = '' }
  }
  const uploadClosureEvidence = async (alert, file) => {
    if (!file) return
    setBusy(true)
    try {
      const document = await api.upload(mineId, file, 'Corrective action closure evidence')
      updatePassportDraft(alert, 'closure_evidence_document_id', String(document.id))
      if (!passportDraft(alert).closure_note) updatePassportDraft(alert, 'closure_note', 'Inspector verified the corrective action against the uploaded evidence.')
      await loadMine(); onChanged()
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }
  const uploadIncompleteSample = async () => {
    setBusy(true)
    try {
      const response = await fetch('/samples/incomplete_quarterly_submission.pdf')
      const blob = await response.blob()
      await api.upload(mineId, new File([blob], 'incomplete_quarterly_submission.pdf', { type: 'application/pdf' }))
      await loadMine(); onChanged()
    } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  if (error && !mine) return <main className="page-shell"><button className="link-button" onClick={onBack}>← Back to dashboard</button><div className="error-card">{error}</div></main>
  if (!mine) return <main className="page-shell"><div className="loading-card">Loading mine record…</div></main>

  const trend = mine.trend.map((point) => ({ ...point, label: new Date(point.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }) }))
  const latestDocument = mine.documents[0]
  const missing = latestDocument?.checklist_results.filter((item) => !item.found) || []
  const found = latestDocument?.checklist_results.filter((item) => item.found) || []
  return (
    <main className="page-shell pb-12">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3"><button className="link-button" onClick={onBack}>← Back to mine ranking</button><a className="secondary-button" href={`/api/mines/${encodeURIComponent(mineId)}/report.pdf`} target="_blank" rel="noreferrer">Download compliance report</a></div>
      <section className="detail-hero">
        <div><p className="eyebrow">Mine compliance file · {mine.mine_id}</p><h1>{mine.name}</h1><p>{mine.district}, {mine.state} · {mine.type} · {mine.operator}</p></div>
        <div className="flex items-center gap-4"><div className="text-right"><p className="text-xs font-medium uppercase tracking-wider text-slate-500">Composite score</p><strong className="text-4xl text-coal-800">{mine.score.composite_score}</strong><span className="text-slate-400"> / 100</span></div><RiskBadge band={mine.score.risk_band} /></div>
      </section>
      {error && <div className="error-card mt-5">{error}</div>}

      <section className="mt-5 grid gap-5 lg:grid-cols-3">
        <div className="panel lg:col-span-2"><div className="panel-heading"><div><h2>Explainable score breakdown</h2><p>{mine.score_breakdown.formula}</p></div><span className="text-xs text-slate-500">Updated {formatDate(mine.score.last_updated)}</span></div><div className="grid gap-3 md:grid-cols-3"><ComponentScore label="Safety" detail={mine.score_breakdown.safety} color="#c94740" /><ComponentScore label="Environmental" detail={mine.score_breakdown.environmental} color="#d9950b" /><ComponentScore label="Labor" detail={mine.score_breakdown.labor} color="#198754" /></div></div>
        <div className="panel"><div className="panel-heading"><div><h2>Controlled demo event</h2><p>Creates one deliberate High-severity test signal.</p></div></div><button disabled={busy} onClick={triggerDemoAlert} className="primary-button w-full">{busy ? 'Updating…' : 'Create test alert'}</button><p className="mt-3 text-xs leading-5 text-slate-500">Manual only: no background alert generator is running. The new event receives an owner, deadline, and corrective action plan.</p></div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-5">
        <div className="panel xl:col-span-3"><div className="panel-heading"><div><h2>Score trend</h2><p>Seeded historical checkpoints plus documented inspector decisions</p></div></div><div className="h-[265px]"><ResponsiveContainer><LineChart data={trend} margin={{ left: -18, right: 12, top: 12 }}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e7ecec" /><XAxis dataKey="label" tick={{ fontSize: 11 }} /><YAxis domain={[0, 100]} tick={{ fontSize: 12 }} /><Tooltip labelFormatter={(_, payload) => payload?.[0]?.payload?.reason || 'Score update'} /><Line type="monotone" dataKey="composite_score" name="Composite score" stroke="#294144" strokeWidth={3} dot={{ r: 4, fill: '#294144' }} /></LineChart></ResponsiveContainer></div></div>
        <div className="panel xl:col-span-2"><div className="panel-heading"><div><h2>AI-assisted document check</h2><p>Digital PDF text first; OCR fallback for scans</p></div></div><div className="space-y-3"><input ref={fileInput} onChange={(event) => upload(event.target.files?.[0])} type="file" accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp" className="file-input" /><button disabled={busy} onClick={uploadIncompleteSample} className="secondary-button w-full">Use incomplete demo PDF</button><p className="text-xs leading-5 text-slate-500">Upload corrective evidence before recording closure; the extracted checklist remains visible for human review.</p><a className="block text-center text-xs text-coal-600 underline" href="/samples/scanned_style_compliance_note.png" target="_blank">Open scanned-style OCR sample</a></div></div>
      </section>

      <section className="mt-5 grid gap-5 xl:grid-cols-2">
        <div className="panel"><div className="panel-heading"><div><h2>Latest document result</h2><p>{latestDocument ? `${latestDocument.source_filename} · ${latestDocument.overall_document_status.replace('_', ' ')}` : 'No document received'}</p></div></div>{latestDocument ? <><div className="mb-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-slate-100 px-2 py-1 text-slate-600">{found.length}/15 clauses found</span><span className="rounded-full bg-slate-100 px-2 py-1 text-slate-600">Uploaded {formatDate(latestDocument.upload_date)}</span><span className="rounded-full bg-amber-50 px-2 py-1 text-amber-800">Human review required</span></div><p className="evidence-method">PDF text → OCR fallback → deterministic 15-clause evidence matching. This prototype assists review; it does not issue legal compliance decisions.</p>{missing.length ? <ul className="space-y-2">{missing.map((item) => <li className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800" key={item.clause}>Missing: {item.clause}</li>)}</ul> : <p className="rounded-lg bg-emerald-50 px-3 py-3 text-sm text-emerald-800">All 15 demo checklist clauses were located in the latest document.</p>}<details className="evidence-trace"><summary>View matched evidence trace ({found.length} clauses)</summary><div>{found.map((item) => <p key={item.clause}><b>{item.clause}:</b> {item.evidence || 'Matched by the deterministic checklist rule.'}</p>)}</div></details></> : <div className="empty-state">Upload a PDF or image to create a checklist result.</div>}</div>
        <div className="panel">
          <div className="panel-heading"><div><h2>Compliance passport & closure</h2><p>Every signal has an owner, deadline, remedy, linked proof, and inspector decision.</p></div></div>
          <div className="space-y-3">
            {mine.alerts.length ? mine.alerts.map((alert) => {
              const draft = passportDraft(alert)
              const closureEvidence = mine.documents.find((document) => document.id === Number(draft.closure_evidence_document_id))
              return <div className="passport-card" key={alert.id}>
                <div className="flex items-start justify-between gap-3"><div><p className="font-semibold capitalize text-coal-800">{alert.event_type.replaceAll('_', ' ')}</p><p className="mt-1 text-xs leading-5 text-slate-500">{alert.description}</p></div><SeverityBadge severity={alert.severity} /></div>
                <div className="mt-3 grid gap-3 sm:grid-cols-2">
                  <label className="text-xs font-semibold text-slate-600">Accountable owner<input className="passport-input" value={draft.assigned_to} onChange={(event) => updatePassportDraft(alert, 'assigned_to', event.target.value)} disabled={alert.status === 'action_taken'} /></label>
                  <label className="text-xs font-semibold text-slate-600">Closure deadline<input className="passport-input" type="date" value={draft.due_date} onChange={(event) => updatePassportDraft(alert, 'due_date', event.target.value)} disabled={alert.status === 'action_taken'} /></label>
                </div>
                <label className="mt-3 block text-xs font-semibold text-slate-600">Required corrective action<textarea className="passport-input min-h-20" value={draft.action_plan} onChange={(event) => updatePassportDraft(alert, 'action_plan', event.target.value)} disabled={alert.status === 'action_taken'} /></label>
                {alert.status !== 'action_taken' ? <>
                  <div className="closure-proof">
                    <div><p className="passport-label">Required before closure</p><p>Link a mine document and record what the inspector verified. Closing without proof is blocked by the API.</p></div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <label className="text-xs font-semibold text-slate-600">Uploaded closure evidence<select className="passport-input" value={draft.closure_evidence_document_id} onChange={(event) => updatePassportDraft(alert, 'closure_evidence_document_id', event.target.value)} disabled={busy}><option value="">Select a mine document</option>{mine.documents.map((document) => <option value={document.id} key={document.id}>{document.source_filename || `Document #${document.id}`}</option>)}</select></label>
                      <label className="text-xs font-semibold text-slate-600">Or upload proof<input className="passport-input file-input compact" type="file" accept=".pdf,.png,.jpg,.jpeg,.tif,.tiff,.bmp" disabled={busy} onChange={(event) => uploadClosureEvidence(alert, event.target.files?.[0])} /></label>
                    </div>
                    <label className="block text-xs font-semibold text-slate-600">Inspector verification note<textarea className="passport-input min-h-20" placeholder="What was verified in the evidence?" value={draft.closure_note} onChange={(event) => updatePassportDraft(alert, 'closure_note', event.target.value)} disabled={busy} /></label>
                  </div>
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-3"><span className="text-xs capitalize text-slate-500">{alert.status.replaceAll('_', ' ')} · {formatDate(alert.timestamp)}</span><div className="flex flex-wrap gap-2"><button disabled={busy} onClick={() => savePassport(alert)} className="small-button">Save passport</button><button disabled={busy} onClick={() => runAction(alert, 'reviewed')} className="small-button">Review</button><button disabled={busy || !draft.closure_evidence_document_id || !draft.closure_note.trim()} onClick={() => runAction(alert, 'action_taken')} className="small-button active">Verify & close</button></div></div>
                </> : <div className="verified-closure"><div><span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-800">Closure verified</span><p className="mt-3 text-xs text-slate-600">Evidence: {closureEvidence?.source_filename || `Document #${alert.closure_evidence_document_id}`}</p><p className="mt-1 text-xs text-slate-600">Inspector note: {alert.closure_note}</p></div><span className="text-xs text-slate-500">{alert.closure_verified_at ? formatDate(alert.closure_verified_at) : 'Recorded'}</span></div>}
              </div>
            }) : <div className="empty-state">No alerts for this mine yet. Run one controlled simulated alert to create a compliance passport.</div>}
          </div>
        </div>
      </section>

      <section className="panel mt-5"><div className="panel-heading"><div><h2>Audit trail</h2><p>Inspector decisions retained with time and notes.</p></div></div>{mine.audit_trail.length ? <div className="divide-y divide-slate-100">{mine.audit_trail.map((entry) => <div className="py-3" key={entry.id}><div className="flex justify-between gap-4"><p className="font-semibold text-coal-800">{entry.action_taken}</p><p className="whitespace-nowrap text-xs text-slate-500">{formatDate(entry.timestamp)}</p></div><p className="mt-1 text-sm text-slate-600">{entry.notes}</p><p className="mt-1 text-xs text-slate-500">Recorded by {entry.taken_by}</p></div>)}</div> : <div className="empty-state">No inspector action has been recorded yet.</div>}</section>
    </main>
  )
}
