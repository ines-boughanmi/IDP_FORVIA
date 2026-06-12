export function asNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }
  return fallback;
}

export function formatNumber(value: unknown, fractionDigits = 0): string {
  return asNumber(value).toLocaleString('en-US', {
    minimumFractionDigits: fractionDigits,
    maximumFractionDigits: fractionDigits,
  });
}

export function formatCurrency(value: unknown): string {
  return `$${formatNumber(value, 2)}`;
}

export function formatPercent(value: unknown, fractionDigits = 1): string {
  return `${formatNumber(value, fractionDigits)}%`;
}

export function formatDateTime(value: unknown): string {
  if (typeof value !== 'string' || !value) return 'N/A';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatSupplier(supplierId: unknown, supplierName?: string | null): string {
  if (supplierName) return `${supplierName} (#${supplierId})`;
  return String(supplierId ?? 'N/A');
}

export function titleCase(value: string): string {
  return value
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (match) => match.toUpperCase());
}
