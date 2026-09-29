import { RiskBadge } from './RiskBadge'

export default function MineTable({ mines, onSelect }) {
  if (!mines.length) {
    return <div className="empty-state">No mines match the selected filters.</div>
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-100 text-left">
        <thead className="bg-slate-50 text-xs uppercase tracking-[0.08em] text-slate-500">
          <tr><th>Mine</th><th>Location</th><th>Operator</th><th>Compliance score</th><th>Risk</th><th /></tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white text-sm">
          {mines.map((mine, index) => (
            <tr className="table-row" key={mine.mine_id}>
              <td><span className="text-xs text-slate-400">#{String(index + 1).padStart(2, '0')}</span><p className="font-semibold text-coal-800">{mine.name}</p><p className="text-xs text-slate-500">{mine.type}</p></td>
              <td>{mine.district}<p className="text-xs text-slate-500">{mine.state}</p></td>
              <td className="max-w-[210px] text-slate-600">{mine.operator}</td>
              <td><span className="text-lg font-bold text-coal-800">{mine.score.composite_score}</span><span className="text-xs text-slate-400"> / 100</span></td>
              <td><RiskBadge band={mine.score.risk_band} /></td>
              <td><button className="link-button" onClick={() => onSelect(mine.mine_id)}>Inspect <span aria-hidden="true">→</span></button></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
