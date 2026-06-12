import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { formatNumber, formatSupplier } from '@/utils/format';

type SupplierRankingEntry = { supplier_id: number; supplier_name?: string | null; risk_score: number };

export function SupplierRankingChart({ data }: { data: SupplierRankingEntry[] }) {
  const mapped = data.map((entry) => ({
    name: formatSupplier(entry.supplier_id, entry.supplier_name),
    risk_score: entry.risk_score,
  }));

  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={mapped} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#244061" />
          <XAxis type="number" />
          <YAxis type="category" dataKey="name" width={180} />
          <Tooltip formatter={(value) => formatNumber(value, 2)} />
          <Bar dataKey="risk_score" fill="#ffae42" radius={[0, 10, 10, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
