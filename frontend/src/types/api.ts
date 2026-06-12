export type ApiEnvelope<T> = {
  status: 'success' | 'error';
  data: T;
  metadata: Record<string, unknown>;
};

export type DashboardMetrics = {
  total_transactions: number;
  total_suppliers: number;
  avg_transaction_risk: number;
  avg_supplier_risk: number;
  critical_transactions: number;
  high_transactions: number;
  critical_suppliers: number;
  high_risk_suppliers: number;
  anomaly_rate: number;
  top_risk_supplier: SupplierSummary | null;
};

export type RiskDistributionResponse = Record<'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL', RiskDistributionBucket>;

export type ClusterDistributionItem = {
  cluster_id: number;
  cluster_label: string;
  suppliers: number;
  avg_risk_score?: number;
  avg_stability_score?: number;
  avg_anomaly_rate?: number;
};

export type ClusterDistributionResponse = {
  clusters: ClusterDistributionItem[];
};

export type AnomalySummary = {
  transactions_with_anomalies: number;
  anomaly_rate: number;
  delayed_transactions: number;
  delayed_rate: number;
  supplier_anomaly_rate_avg: number;
  critical_transaction_count: number;
  high_transaction_count: number;
};

export type SearchTransactionsResponse = {
  transactions: TransactionSummary[];
};

export type SearchSuppliersResponse = {
  suppliers: SupplierSummary[];
};

export type AlertsResponse = {
  alerts: AlertItem[];
};

export type TopRiskSuppliersResponse = {
  suppliers: SupplierSummary[];
};

export type RiskDistributionBucket = {
  count: number;
  percentage: number;
};

export type SupplierSummary = {
  supplier_id: number;
  supplier_name?: string | null;
  risk_score: number;
  risk_level: string;
  cluster_label?: string;
  explanation?: string;
};

export type TransactionSummary = {
  transaction_id: number;
  supplier_id: number;
  supplier_name?: string | null;
  risk_score: number;
  risk_level: string;
  explanation?: string;
  amount_gap_pct?: number;
  created_timestamp?: string;
};

export type AlertItem = {
  alert_id: string;
  entity_type: 'transaction' | 'supplier';
  supplier_id?: number;
  supplier_name?: string | null;
  risk_score: number;
  risk_level: string;
  explanation: string;
  created_at: string;
};

export type SupplierOverview = {
  supplier_profile: Record<string, unknown>;
  supplier_name?: string | null;
  risk_score: number;
  risk_level: string;
  cluster: {
    cluster_id: number;
    cluster_label: string;
  };
  behavior_metrics: Record<string, unknown>;
  anomaly_metrics: Record<string, unknown>;
  risk_explanation: string;
  transaction_statistics: Record<string, unknown>;
  recent_transactions?: TransactionSummary[];
};

export type TransactionOverview = {
  transaction_profile: Record<string, unknown>;
  risk_components: Record<string, unknown>;
  supplier_information: Record<string, unknown> | null;
  explanation: string;
  alerts: AlertItem[];
};

