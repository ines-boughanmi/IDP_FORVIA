export function Chip({ children, active = false, tone = 'neutral' }: { children: string; active?: boolean; tone?: 'neutral' | 'blue' | 'green' | 'amber' | 'red' }) {
  return <span className={`chip chip-${tone}${active ? ' active' : ''}`}>{children}</span>;
}
