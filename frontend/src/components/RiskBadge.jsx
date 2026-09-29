const styles = {
  Low: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Medium: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  High: 'bg-red-50 text-red-700 ring-red-600/20',
}

export function RiskBadge({ band }) {
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${styles[band] || 'bg-slate-100 text-slate-700 ring-slate-400/20'}`}>{band} risk</span>
}

export function SeverityBadge({ severity }) {
  return <span className={`font-semibold ${severity === 'High' ? 'text-minered' : severity === 'Medium' ? 'text-mineamber' : 'text-minegreen'}`}>{severity}</span>
}
