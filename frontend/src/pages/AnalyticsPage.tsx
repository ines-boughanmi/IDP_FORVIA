import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SectionCard } from '@/components/ui/SectionCard';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart';
import { ClusterDistributionChart } from '@/components/charts/ClusterDistributionChart';
import { SupplierRankingChart } from '@/components/charts/SupplierRankingChart';
import { fetchAnomalySummary, fetchClusterDistribution, fetchRiskDistribution, fetchTopRiskSuppliers } from '@/services/backendApi';
import { asNumber, formatNumber, formatPercent } from '@/utils/format';

export function AnalyticsPage() {
  const riskQuery = useQuery({ queryKey: ['analytics-risk-distribution'], queryFn: fetchRiskDistribution });
  const clusterQuery = useQuery({ queryKey: ['analytics-cluster-distribution'], queryFn: fetchClusterDistribution });
  const rankingQuery = useQuery({ queryKey: ['analytics-top-risk-suppliers'], queryFn: () => fetchTopRiskSuppliers(12) });
  const anomalyQuery = useQuery({ queryKey: ['analytics-anomaly-summary'], queryFn: fetchAnomalySummary });

  const riskBuckets = useMemo(() => {
    const payload = riskQuery.data?.data;
    return ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((level) => ({
      name: level,
      count: asNumber(payload?.[level]?.count),
      percentage: asNumber(payload?.[level]?.percentage),
    }));
  }, [riskQuery.data]);

  const clusterRows = useMemo(() => clusterQuery.data?.data.clusters ?? [], [clusterQuery.data]);
  const topSuppliers = rankingQuery.data?.data.suppliers ?? [];
  const anomalySummary = anomalyQuery.data?.data;

  if (riskQuery.isLoading || clusterQuery.isLoading || rankingQuery.isLoading || anomalyQuery.isLoading) {
    return <LoadingState label="Loading analytics center..." />;
  }

  if (riskQuery.error || clusterQuery.error || rankingQuery.error || anomalyQuery.error) {
    return <EmptyState title="Analytics unavailable" message="One or more analytics sources could not be loaded." />;
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Analytics center</p>
          <h1>Analytics</h1>
          <p>Distribution views and ranking charts prepared for executive reporting.</p>
        </div>
      </div>

      <section className="dashboard-grid">
        <SectionCard title="Risk distribution">
          <RiskDistributionChart data={riskBuckets} />
        </SectionCard>
        <SectionCard title="Supplier ranking">
          <SupplierRankingChart data={topSuppliers.slice(0, 10).map((item) => ({ supplier_id: asNumber(item.supplier_id), supplier_name: item.supplier_name, risk_score: asNumber(item.risk_score) }))} />
        </SectionCard>
        <SectionCard title="Cluster distribution">
          <ClusterDistributionChart data={clusterRows as Array<{ cluster_label: string; suppliers: number }>} />
        </SectionCard>
        <SectionCard title="Anomaly breakdown">
          <div className="detail-grid compact-grid">
            <div>
              <span>Transactions with anomalies</span>
              <strong>{formatNumber(anomalySummary?.transactions_with_anomalies)}</strong>
            </div>
            <div>
              <span>Anomaly rate</span>
              <strong>{formatPercent(anomalySummary?.anomaly_rate)}</strong>
            </div>
            <div>
              <span>Delayed transactions</span>
              <strong>{formatNumber(anomalySummary?.delayed_transactions)}</strong>
            </div>
            <div>
              <span>Delayed rate</span>
              <strong>{formatPercent(anomalySummary?.delayed_rate)}</strong>
            </div>
          </div>
        </SectionCard>
      </section>
    </div>
  );
}
