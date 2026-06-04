import { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SectionCard } from '@/components/ui/SectionCard';
import { SearchInput } from '@/components/ui/SearchInput';
import { Chip } from '@/components/ui/Chip';
import { Pagination } from '@/components/ui/Pagination';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { fetchAlerts, fetchSupplierAlerts, fetchTransactionAlerts } from '@/services/backendApi';
import { asNumber, formatNumber, formatDateTime } from '@/utils/format';

type Tab = 'all' | 'transactions' | 'suppliers';

export function AlertsPage() {
  const [tab, setTab] = useState<Tab>('all');
  const [search, setSearch] = useState('');
  const [level, setLevel] = useState<'ALL' | 'HIGH' | 'CRITICAL'>('ALL');
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const query = useQuery({
    queryKey: ['alerts', tab],
    queryFn: () => {
      if (tab === 'transactions') return fetchTransactionAlerts();
      if (tab === 'suppliers') return fetchSupplierAlerts();
      return fetchAlerts();
    },
  });

  const alerts = query.data?.data.alerts ?? [];

  const filteredAlerts = useMemo(() => {
    const normalized = search.trim().toLowerCase();
    return alerts.filter((alert) => {
      const matchesSearch =
        !normalized ||
        String(alert.alert_id).toLowerCase().includes(normalized) ||
        String(alert.explanation).toLowerCase().includes(normalized) ||
        String(alert.entity_type).toLowerCase().includes(normalized);

      const matchesLevel = level === 'ALL' || alert.risk_level === level;
      return matchesSearch && matchesLevel;
    });
  }, [alerts, level, search]);

  const totalPages = Math.max(1, Math.ceil(filteredAlerts.length / pageSize));
  const visibleAlerts = filteredAlerts.slice((page - 1) * pageSize, page * pageSize);

  if (query.isLoading) {
    return <LoadingState label="Loading alert center..." />;
  }

  if (query.error) {
    return <EmptyState title="Alert center unavailable" message="The alert data source could not be loaded." />;
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Alert operations</p>
          <h1>Alert Center</h1>
          <p>Review all HIGH and CRITICAL entities with local search, filtering and pagination.</p>
        </div>
      </div>

      <SectionCard>
        <div className="toolbar-row">
          <div className="tab-row">
            {(['all', 'transactions', 'suppliers'] as Tab[]).map((item) => (
              <button key={item} type="button" className={`tab-btn${tab === item ? ' active' : ''}`} onClick={() => { setTab(item); setPage(1); }}>
                {item === 'all' ? 'All Alerts' : item === 'transactions' ? 'Transaction Alerts' : 'Supplier Alerts'}
              </button>
            ))}
          </div>

          <div className="toolbar-filters">
            <SearchInput value={search} onChange={setSearch} placeholder="Search alerts" />
            <select className="input" value={level} onChange={(event) => setLevel(event.target.value as 'ALL' | 'HIGH' | 'CRITICAL')}>
              <option value="ALL">All Levels</option>
              <option value="HIGH">HIGH</option>
              <option value="CRITICAL">CRITICAL</option>
            </select>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Alert table" description={`Showing ${visibleAlerts.length} of ${filteredAlerts.length} alerts.`}>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Alert ID</th>
                <th>Entity</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Explanation</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {visibleAlerts.map((alert) => (
                <tr key={alert.alert_id}>
                  <td>{alert.alert_id}</td>
                  <td>{alert.entity_type}</td>
                  <td>{formatNumber(asNumber(alert.risk_score), 2)}</td>
                  <td>
                    <Chip tone={alert.risk_level === 'CRITICAL' ? 'red' : 'amber'}>{alert.risk_level}</Chip>
                  </td>
                  <td>{alert.explanation}</td>
                  <td>{formatDateTime(alert.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination page={page} totalPages={totalPages} onChange={setPage} />
      </SectionCard>
    </div>
  );
}
