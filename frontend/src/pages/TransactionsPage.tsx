import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { SectionCard } from '@/components/ui/SectionCard';
import { Pagination } from '@/components/ui/Pagination';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingState } from '@/components/ui/LoadingState';
import { searchTransactions } from '@/services/backendApi';
import { asNumber, formatDateTime, formatNumber } from '@/utils/format';

export function TransactionsPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState({
    supplierId: '',
    riskLevel: '',
    minScore: '',
    maxScore: '',
    dateFrom: '',
    dateTo: '',
    keyword: '',
  });
  const [draft, setDraft] = useState(filters);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const query = useQuery({
    queryKey: ['transaction-search', filters, page],
    queryFn: () => searchTransactions({ ...filters, page, pageSize }),
  });

  const transactions = query.data?.data.transactions ?? [];
  const total = asNumber(query.data?.metadata.total);
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (query.isLoading) return <LoadingState label="Loading transaction investigation center..." />;
  if (query.error) return <EmptyState title="Transaction search unavailable" message="Transaction search data could not be loaded." />;

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Transaction investigation center</p>
          <h1>Transactions</h1>
          <p>Search and inspect transaction risk behavior with pagination and multiple filters.</p>
        </div>
      </div>

      <SectionCard>
        <div className="filter-grid transactions-grid">
          <input className="input" placeholder="Supplier ID" value={draft.supplierId} onChange={(event) => setDraft((current) => ({ ...current, supplierId: event.target.value }))} />
          <select className="input" value={draft.riskLevel} onChange={(event) => setDraft((current) => ({ ...current, riskLevel: event.target.value }))}>
            <option value="">All risk levels</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
            <option value="CRITICAL">CRITICAL</option>
          </select>
          <input className="input" placeholder="Min score" value={draft.minScore} onChange={(event) => setDraft((current) => ({ ...current, minScore: event.target.value }))} />
          <input className="input" placeholder="Max score" value={draft.maxScore} onChange={(event) => setDraft((current) => ({ ...current, maxScore: event.target.value }))} />
          <input className="input" type="date" value={draft.dateFrom} onChange={(event) => setDraft((current) => ({ ...current, dateFrom: event.target.value }))} />
          <input className="input" type="date" value={draft.dateTo} onChange={(event) => setDraft((current) => ({ ...current, dateTo: event.target.value }))} />
          <input className="input wide" placeholder="Keyword" value={draft.keyword} onChange={(event) => setDraft((current) => ({ ...current, keyword: event.target.value }))} />
          <button className="btn btn-primary" type="button" onClick={() => { setFilters(draft); setPage(1); }}>
            Apply filters
          </button>
        </div>
      </SectionCard>

      <SectionCard title="Transaction search results" description={`${formatNumber(total)} transactions matched.`}>
        <div className="table-wrap">
          <table className="data-table clickable">
            <thead>
              <tr>
                <th>Transaction ID</th>
                <th>Supplier ID</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Days in System</th>
                <th>Gap %</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((transaction) => (
                <tr key={String(transaction.transaction_id)} onClick={() => navigate(`/transaction/${transaction.transaction_id}`)}>
                  <td>{transaction.transaction_id}</td>
                  <td>{transaction.supplier_id}</td>
                  <td>{formatNumber(asNumber(transaction.risk_score), 2)}</td>
                  <td>{transaction.risk_level}</td>
                  <td>{formatNumber(asNumber(transaction.days_in_system))}</td>
                  <td>{formatNumber(asNumber(transaction.amount_gap_pct), 2)}%</td>
                  <td>{formatDateTime(transaction.created_timestamp)}</td>
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
