import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { titleCase, formatNumber } from '@/utils/format';

export function ClusterDistributionChart({ data }: { data: Array<{ cluster_label: string; suppliers: number; avg_risk_score?: number }> }) {
  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#244061" />
          <XAxis dataKey="cluster_label" tickFormatter={(value) => titleCase(String(value))} />
          <YAxis />
          <Tooltip formatter={(value) => formatNumber(value)} />
          <Bar dataKey="suppliers" fill="#7fb3ff" radius={[10, 10, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
