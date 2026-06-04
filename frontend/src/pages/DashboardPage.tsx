import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SectionCard } from '@/components/ui/SectionCard';
import { StatCard } from '@/components/ui/StatCard';
import { LoadingState } from '@/components/ui/LoadingState';
import { EmptyState } from '@/components/ui/EmptyState';
import { RiskDistributionChart } from '@/components/charts/RiskDistributionChart';
import { ClusterDistributionChart } from '@/components/charts/ClusterDistributionChart';
import { SupplierRankingChart } from '@/components/charts/SupplierRankingChart';
import { fetchAnomalySummary, fetchClusterDistribution, fetchExecutiveDashboard, fetchRiskDistribution, fetchTopRiskSuppliers } from '@/services/backendApi';
import { asNumber, formatNumber, formatPercent, titleCase } from '@/utils/format';

export function DashboardPage() {
  const dashboardQuery = useQuery({ queryKey: ['executive-dashboard'], queryFn: fetchExecutiveDashboard });
  const riskQuery = useQuery({ queryKey: ['risk-distribution'], queryFn: fetchRiskDistribution });
  const rankingQuery = useQuery({ queryKey: ['top-risk-suppliers'], queryFn: () => fetchTopRiskSuppliers(10) });
  const clusterQuery = useQuery({ queryKey: ['cluster-distribution'], queryFn: fetchClusterDistribution });
  const anomalyQuery = useQuery({ queryKey: ['anomaly-summary'], queryFn: fetchAnomalySummary });

  const dashboard = dashboardQuery.data?.data;
  const riskBuckets = useMemo(() => {
    const payload = riskQuery.data?.data;
    return ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map((level) => ({
      name: level,
      count: asNumber(payload?.[level]?.count),
      percentage: asNumber(payload?.[level]?.percentage),
    }));
  }, [riskQuery.data]);

  const clusterRows = useMemo(() => {
    const payload = clusterQuery.data?.data as { clusters?: Array<Record<string, unknown>> } | undefined;
    return payload?.clusters ?? [];
  }, [clusterQuery.data]);

  const topSuppliers = useMemo(() => {
    const payload = rankingQuery.data?.data?.suppliers ?? [];
    return payload.slice(0, 10).map((item) => ({
      supplier_id: asNumber(item.supplier_id),
      risk_score: asNumber(item.risk_score),
    }));
  }, [rankingQuery.data]);

  const anomalySummary = anomalyQuery.data?.data;

  if (dashboardQuery.isLoading || riskQuery.isLoading || rankingQuery.isLoading || clusterQuery.isLoading || anomalyQuery.isLoading) {
    return <LoadingState label="Loading executive dashboard..." />;
  }

  if (dashboardQuery.error || riskQuery.error || rankingQuery.error || clusterQuery.error || anomalyQuery.error) {
    return <EmptyState title="Dashboard unavailable" message="One or more executive sources could not be loaded." />;
  }

  return (
    <div className="page-stack">
      <div className="page-header">
        <div>
          <p className="page-kicker">Executive overview</p>
          <h1>Dashboard</h1>
          <p>Enterprise KPIs and risk intelligence from the Phase 3 product datasets.</p>
        </div>
      </div>

      <section className="stat-grid">
        <StatCard label="Total Transactions" value={dashboard?.total_transactions ?? 0} hint="Loaded from executive API" />
        <StatCard label="Total Suppliers" value={dashboard?.total_suppliers ?? 0} hint="Unique supplier count" />
        <StatCard label="Average Transaction Risk" value={formatNumber(dashboard?.avg_transaction_risk, 2)} hint="Weighted by current engine" />
        <StatCard label="Average Supplier Risk" value={formatNumber(dashboard?.avg_supplier_risk, 2)} hint="Supplier intelligence score" />
        <StatCard label="Critical Transactions" value={dashboard?.critical_transactions ?? 0} tone="red" />
        <StatCard label="Critical Suppliers" value={dashboard?.critical_suppliers ?? 0} tone="amber" />
      </section>

      <section className="dashboard-grid">
        <SectionCard title="Risk Distribution" description="Transaction risk mix across the platform.">
          <RiskDistributionChart data={riskBuckets} />
        </SectionCard>

        <SectionCard title="Supplier Risk Ranking" description="Top suppliers by risk score.">
          <SupplierRankingChart data={topSuppliers} />
        </SectionCard>

        <SectionCard title="Cluster Breakdown" description="Supplier cluster footprint.">
          <ClusterDistributionChart data={clusterRows as Array<{ cluster_label: string; suppliers: number }>} />
        </SectionCard>

        <SectionCard title="Anomaly Summary" description="Current anomaly profile at platform level.">
          <div className="detail-grid compact-grid">
            <div>
              <span>Transaction anomaly rate</span>
              <strong>{formatPercent(anomalySummary?.anomaly_rate)}</strong>
            </div>
            <div>
              <span>Delayed transaction rate</span>
              <strong>{formatPercent(anomalySummary?.delayed_rate)}</strong>
            </div>
            <div>
              <span>Transactions with anomalies</span>
              <strong>{formatNumber(anomalySummary?.transactions_with_anomalies)}</strong>
            </div>
            <div>
              <span>High risk transactions</span>
              <strong>{formatNumber(anomalySummary?.high_transaction_count)}</strong>
            </div>
          </div>
        </SectionCard>
      </section>

      <SectionCard title="Executive spotlight" description="Use this summary in future board-level reporting and chatbot narratives.">
        <div className="spotlight-grid">
          <div className="spotlight-box">
            <span>Top risk supplier</span>
            <strong>{dashboard?.top_risk_supplier?.supplier_id ?? 'N/A'}</strong>
            <p>
              {titleCase(String(dashboard?.top_risk_supplier?.risk_level ?? 'unknown'))} - score {formatNumber(dashboard?.top_risk_supplier?.risk_score, 2)}
            </p>
          </div>
          <div className="spotlight-box">
            <span>Critical exposure</span>
            <strong>{formatNumber(dashboard?.critical_transactions)}</strong>
            <p>Transactions requiring immediate attention.</p>
          </div>
          <div className="spotlight-box">
            <span>Supplier concentration</span>
            <strong>{formatNumber(dashboard?.total_suppliers)}</strong>
            <p>Unique suppliers tracked in the executive layer.</p>
          </div>
        </div>
      </SectionCard>
    </div>
  );
}
