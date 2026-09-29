import { useState } from 'react'
import { api } from '../api'

const initialForm = { name: '', state: '', district: '', type: 'open-cast', operator: '', initial_score: 80, created_by: 'Inspector Demo User' }

export default function AddMineModal({ onClose, onCreated }) {
  const [form, setForm] = useState(initialForm)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const update = (event) => setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  const submit = async (event) => {
    event.preventDefault()
    setSaving(true); setError('')
    try {
      const mine = await api.createMine({ ...form, initial_score: Number(form.initial_score) })
      onCreated(mine.mine_id)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="add-mine-heading" onMouseDown={(event) => event.stopPropagation()}>
      <div className="panel-heading"><div><p className="eyebrow">Inspector workflow</p><h2 id="add-mine-heading">Add a mine record</h2><p>This creates a local inspector-entered profile. Verify its details with the authority before relying on it.</p></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close add mine form">x</button></div>
      {error && <div className="error-card mb-4">{error}</div>}
      <form className="form-grid" onSubmit={submit}>
        <label className="form-field form-field-wide">Mine name<input name="name" value={form.name} onChange={update} minLength="3" required placeholder="Example: Shivani Open Cast Mine" /></label>
        <label className="form-field">State<input name="state" value={form.state} onChange={update} minLength="2" required placeholder="Jharkhand" /></label>
        <label className="form-field">District<input name="district" value={form.district} onChange={update} minLength="2" required placeholder="Ramgarh" /></label>
        <label className="form-field">Mine type<select name="type" value={form.type} onChange={update}><option value="open-cast">Open-cast</option><option value="underground">Underground</option></select></label>
        <label className="form-field">Operator<input name="operator" value={form.operator} onChange={update} minLength="2" required placeholder="Mine operator" /></label>
        <label className="form-field">Initial assessment (0-100)<input name="initial_score" value={form.initial_score} onChange={update} type="number" min="0" max="100" step="1" required /></label>
        <label className="form-field">Recorded by<input name="created_by" value={form.created_by} onChange={update} minLength="2" required /></label>
        <div className="form-field-wide flex justify-end gap-3 pt-2"><button type="button" className="secondary-button" onClick={onClose}>Cancel</button><button disabled={saving} className="primary-button" type="submit">{saving ? 'Creating...' : 'Create mine profile'}</button></div>
      </form>
    </section>
  </div>
}
