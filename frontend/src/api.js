const request = async (path, options = {}) => {
  const response = await fetch(`/api${path}`, options)
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.detail || 'The request could not be completed.')
  }
  return response.json()
}

export const api = {
  dashboard: () => request('/dashboard'),
  config: () => request('/config'),
  mines: (filters = {}) => {
    const parameters = new URLSearchParams(Object.entries(filters).filter(([, value]) => value))
    return request(`/mines${parameters.size ? `?${parameters}` : ''}`)
  },
  createMine: (payload) => request('/mines', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  mine: (mineId) => request(`/mines/${mineId}`),
  alerts: (status = '') => request(`/alerts${status ? `?status=${status}` : ''}`),
  demoAlert: (mineId) => request('/alerts/demo', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mine_id: mineId }) }),
  criticalDemo: () => request('/demo-scenarios/critical', { method: 'POST' }),
  updateAlert: (id, payload) => request(`/alerts/${id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) }),
  upload: (mineId, file, documentType = 'Quarterly compliance dossier') => {
    const data = new FormData()
    data.append('file', file)
    const parameters = new URLSearchParams({ mine_id: mineId, document_type: documentType })
    return request(`/documents/upload?${parameters}`, { method: 'POST', body: data })
  },
}
