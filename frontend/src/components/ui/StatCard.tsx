import { formatNumber } from '@/utils/format';

export function StatCard({ label, value, hint, tone = 'blue' }: { label: string; value: unknown; hint?: string; tone?: 'blue' | 'green' | 'amber' | 'red' }) {
  return (
    <article className={`stat-card tone-${tone}`}>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{typeof value === 'number' ? formatNumber(value) : String(value)}</strong>
      {hint && <span className="stat-hint">{hint}</span>}
    </article>
  );
}
