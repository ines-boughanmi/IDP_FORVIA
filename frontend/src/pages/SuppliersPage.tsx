import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { SectionCard } from '@/components/ui/SectionCard';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { fetchTopRiskSuppliers, searchSuppliers } from '@/services/backendApi';
import { asNumber, formatNumber } from '@/utils/format';

export function SuppliersPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({ supplierId: '', cluster: '', riskLevel: '', minScore: '', maxScore: '' });
  const [draft, setDraft] = useState(filters);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const query = useQuery({
    queryKey: ['suppliers-search', filters, page],
    queryFn: () => searchSuppliers({ ...filters, page, pageSize }),
  });

  const spotlightQuery = useQuery({ queryKey: ['top-risk-suppliers-sidebar'], queryFn: () => fetchTopRiskSuppliers(5) });
  const suppliers = query.data?.data.suppliers ?? [];
  const total = asNumber(query.data?.metadata.total);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (query.isLoading || spotlightQuery.isLoading) {
    return <LoadingState label="Loading supplier intelligence..." />;
  }

  if (query.error || spotlightQuery.error) {
    return <EmptyState title="Supplier intelligence unavailable" message="Supplier search data could not be loaded." />;
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Supplier intelligence center</p>
          <h1>Suppliers</h1>
          <p>Search suppliers by risk, cluster and score, then drill into their 360 view.</p>
        </div>
      </div>

      <SectionCard>
        <div className="filter-grid">
          <input className="input" placeholder="Supplier ID" value={draft.supplierId} onChange={(event) => setDraft((current) => ({ ...current, supplierId: event.target.value }))} />
          <input className="input" placeholder="Cluster" value={draft.cluster} onChange={(event) => setDraft((current) => ({ ...current, cluster: event.target.value }))} />
          <select className="input" value={draft.riskLevel} onChange={(event) => setDraft((current) => ({ ...current, riskLevel: event.target.value }))}>
            <option value="">All risk levels</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
          <input className="input" placeholder="Min score" value={draft.minScore} onChange={(event) => setDraft((current) => ({ ...current, minScore: event.target.value }))} />
          <input className="input" placeholder="Max score" value={draft.maxScore} onChange={(event) => setDraft((current) => ({ ...current, maxScore: event.target.value }))} />
          <button className="btn btn-primary" type="button" onClick={() => { setFilters(draft); setPage(1); }}>
            Apply filters
          </button>
        </div>
      </SectionCard>

      <section className="two-column-grid">
        <SectionCard title="Supplier search results" description={`${formatNumber(total)} suppliers matched.`}>
          <div className="table-wrap">
            <table className="data-table clickable">
              <thead>
                <tr>
                  <th>Supplier ID</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Cluster</th>
                  <th>Anomaly Rate</th>
                  <th>Frequency</th>
                  <th>Stability</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => (
                  <tr key={String(supplier.supplier_id)} onClick={() => navigate(`/supplier/${supplier.supplier_id}`)}>
                    <td>{supplier.supplier_id}</td>
                    <td>{formatNumber(asNumber(supplier.risk_score), 2)}</td>
                    <td>{supplier.risk_level}</td>
                    <td>{String(supplier.cluster_label ?? '-')}</td>
                    <td>{formatNumber(asNumber(supplier.anomaly_rate), 2)}</td>
                    <td>{formatNumber(asNumber(supplier.transaction_frequency))}</td>
                    <td>{formatNumber(asNumber(supplier.stability_score), 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} totalPages={totalPages} onChange={setPage} />
        </SectionCard>

        <SectionCard title="Top risk suppliers" description="Quick executive spotlight.">
          <div className="spotlight-list">
            {(spotlightQuery.data?.data.suppliers ?? []).map((supplier) => (
              <button key={String(supplier.supplier_id)} type="button" className="spotlight-row" onClick={() => navigate(`/supplier/${supplier.supplier_id}`)}>
                <strong>{supplier.supplier_id}</strong>
                <span>{formatNumber(asNumber(supplier.risk_score), 2)}</span>
              </button>
            ))}
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
