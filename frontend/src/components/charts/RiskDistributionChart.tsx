import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip, Legend } from 'recharts';
import { formatPercent, titleCase } from '@/utils/format';

const COLORS = ['#7fb3ff', '#4f8cff', '#ffae42', '#d94f70'];

export function RiskDistributionChart({ data }: { data: Array<{ name: string; count: number; percentage: number }> }) {
  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie data={data} dataKey="count" nameKey="name" innerRadius={68} outerRadius={108} paddingAngle={2}>
            {data.map((entry, index) => (
              <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip formatter={(value, name, item) => [String(value), titleCase(String(name))]} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
      <div className="chart-legend-row">
        {data.map((entry, index) => (
          <span key={entry.name} className="legend-pill">
            <i style={{ backgroundColor: COLORS[index % COLORS.length] }} />
            {titleCase(entry.name)} {formatPercent(entry.percentage)}
          </span>
        ))}
      </div>
    </div>
  );
}
