import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { formatNumber } from '@/utils/format';

export function SupplierRankingChart({ data }: { data: Array<{ supplier_id: number; risk_score: number }> }) {
  const mapped = data.map((entry) => ({
    name: String(entry.supplier_id),
    risk_score: entry.risk_score,
  }));

  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={mapped} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#244061" />
          <XAxis type="number" />
          <YAxis type="category" dataKey="name" width={90} />
          <Tooltip formatter={(value) => formatNumber(value, 2)} />
          <Bar dataKey="risk_score" fill="#ffae42" radius={[0, 10, 10, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
