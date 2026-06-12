import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useParams } from 'react-router-dom';
import { SectionCard } from '@/components/ui/SectionCard';
import { StatCard } from '@/components/ui/StatCard';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { fetchSupplierOverview } from '@/services/backendApi';
import { asNumber, formatDateTime, formatNumber, formatPercent, titleCase } from '@/utils/format';

export function SupplierDetailPage() {
  const navigate = useNavigate();
  const params = useParams();
  const supplierId = params.supplierId || '';
  const query = useQuery({ queryKey: ['supplier-overview', supplierId], queryFn: () => fetchSupplierOverview(supplierId), enabled: Boolean(supplierId) });

  const overview = query.data?.data;
  const profileEntries = useMemo(() => Object.entries(overview?.supplier_profile ?? {}), [overview]);

  if (query.isLoading) return <LoadingState label="Loading supplier 360 view..." />;
  if (query.error || !overview) return <EmptyState title="Supplier not found" message="No supplier overview could be loaded." />;

  return (
    <div className="page-stack">
      <div className="page-header between">
        <div>
          <p className="page-kicker">Supplier 360</p>
          <h1>Supplier {supplierId}</h1>
          <p>Behavior, anomaly and transaction profile for executive and analyst workflows.</p>
        </div>
        <button className="btn btn-secondary" type="button" onClick={() => navigate('/suppliers')}>
          Back to supplier search
        </button>
      </div>

      <section className="stat-grid">
        <StatCard label="Supplier ID" value={String(supplierId)} />
        <StatCard label="Supplier Name" value={overview.supplier_name ?? 'N/A'} />
        <StatCard label="Risk Score" value={formatNumber(overview.risk_score, 2)} tone={overview.risk_level === 'CRITICAL' ? 'red' : 'blue'} />
        <StatCard label="Risk Level" value={titleCase(overview.risk_level)} tone={overview.risk_level === 'CRITICAL' ? 'red' : 'amber'} />
        <StatCard label="Cluster" value={overview.cluster.cluster_label} />
        <StatCard label="Transaction Frequency" value={asNumber(overview.behavior_metrics.transaction_frequency)} />
      </section>

      <section className="two-column-grid">
        <SectionCard title="Supplier profile">
          <div className="detail-grid">
            {profileEntries.map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Behavioral metrics">
          <div className="detail-grid compact-grid">
            {Object.entries(overview.behavior_metrics).map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Anomaly metrics">
          <div className="detail-grid compact-grid">
            {Object.entries(overview.anomaly_metrics).map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatPercent(value) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Narrative">
          <p className="narrative-copy">{overview.risk_explanation}</p>
          <div className="detail-grid compact-grid">
            {Object.entries(overview.transaction_statistics).map(([key, value]) => (
              <div key={key}>
                <span>{titleCase(key)}</span>
                <strong>{typeof value === 'number' ? formatNumber(value, 2) : String(value ?? 'N/A')}</strong>
              </div>
            ))}
          </div>
        </SectionCard>
      </section>

      <SectionCard title="Recent transactions" description="Latest transaction history for this supplier.">
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {(overview.recent_transactions ?? []).map((transaction) => (
                <tr key={String(transaction.transaction_id)}>
                  <td>{transaction.transaction_id}</td>
                  <td>{formatNumber(asNumber(transaction.risk_score), 2)}</td>
                  <td>{transaction.risk_level}</td>
                  <td>{formatDateTime(transaction.created_timestamp)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
