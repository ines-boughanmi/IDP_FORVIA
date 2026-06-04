import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { SectionCard } from '@/components/ui/SectionCard';
import { StatCard } from '@/components/ui/StatCard';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { Chip } from '@/components/ui/Chip';
import { fetchTransactionOverview } from '@/services/backendApi';
import { asNumber, formatDateTime, formatNumber, titleCase } from '@/utils/format';

export function TransactionDetailPage() {
  const navigate = useNavigate();
  const params = useParams();
  const transactionId = params.transactionId || '';
  const query = useQuery({ queryKey: ['transaction-overview', transactionId], queryFn: () => fetchTransactionOverview(transactionId), enabled: Boolean(transactionId) });

  const overview = query.data?.data;
  const profileEntries = useMemo(() => Object.entries(overview?.transaction_profile ?? {}), [overview]);

  if (query.isLoading) return <LoadingState label="Loading transaction 360 view..." />;
  if (query.error || !overview) return <EmptyState title="Transaction not found" message="No transaction overview could be loaded." />;

  return (
    <div className="page-stack">
      <div className="page-header between">
        <div>
          <p className="page-kicker">Transaction 360</p>
          <h1>Transaction {transactionId}</h1>
          <p>Detailed transaction investigation with supplier context and alert correlation.</p>
        </div>
        <button className="btn btn-secondary" type="button" onClick={() => navigate('/transactions')}>
          Back to transaction search
        </button>
      </div>

      <section className="stat-grid">
        <StatCard label="Risk Score" value={formatNumber(asNumber(overview.transaction_profile.risk_score), 2)} tone={String(overview.transaction_profile.risk_level) === 'CRITICAL' ? 'red' : 'blue'} />
        <StatCard label="Risk Level" value={String(overview.transaction_profile.risk_level ?? 'N/A')} tone={String(overview.transaction_profile.risk_level) === 'CRITICAL' ? 'red' : 'amber'} />
        <StatCard label="Supplier ID" value={String(overview.transaction_profile.supplier_id ?? 'N/A')} />
        <StatCard label="Alert Count" value={overview.alerts.length} />
      </section>

      <section className="two-column-grid">
        <SectionCard title="Transaction profile">
          <div className="detail-grid">
            {profileEntries.map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Risk components">
          <div className="detail-grid compact-grid">
            {Object.entries(overview.risk_components).map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Supplier information">
          <div className="detail-grid compact-grid">
            {Object.entries(overview.supplier_information ?? {}).map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Narrative">
          <p className="narrative-copy">{overview.explanation}</p>
          <div className="alert-inline-list">
            {overview.alerts.map((alert) => (
              <div key={alert.alert_id} className="alert-inline-card">
                <Chip tone={alert.risk_level === 'CRITICAL' ? 'red' : 'amber'}>{alert.entity_type.toUpperCase()}</Chip>
                <strong>{formatNumber(alert.risk_score, 2)}</strong>
                <p>{alert.explanation}</p>
                <small>{formatDateTime(alert.created_at)}</small>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
