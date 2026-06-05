import { request, toQueryString } from './apiClient';
import type {
  AlertsResponse,
  AnomalySummary,
  ClusterDistributionResponse,
  DashboardMetrics,
  RiskDistributionResponse,
  SearchSuppliersResponse,
  SearchTransactionsResponse,
  SupplierOverview,
  TopRiskSuppliersResponse,
  TransactionOverview,
} from '@/types/api';

export type LoginPayload = {
  username: string;
  password: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  password: string;
};

export async function login(payload: LoginPayload) {
  return request<{ access_token: string; token_type: string }>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, false);
}

export async function getCurrentUser() {
  return request<{ user: { id: number; username: string; email: string; role: string } }>('/auth/me');
}

export async function register(payload: RegisterPayload) {
  return request<{ user: { id: number; username: string; email: string; role: string } }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, false);
}

export async function fetchExecutiveDashboard() {
  return request<DashboardMetrics>('/api/executive/dashboard');
}

export async function fetchAlerts() {
  return request<AlertsResponse>('/api/alerts');
}

export async function fetchTransactionAlerts() {
  return request<AlertsResponse>('/api/alerts/transactions');
}

export async function fetchSupplierAlerts() {
  return request<AlertsResponse>('/api/alerts/suppliers');
}

export async function fetchSupplierOverview(supplierId: string | number) {
  return request<SupplierOverview>(`/api/supplier/${supplierId}/overview`);
}

export async function fetchTransactionOverview(transactionId: string | number) {
  return request<TransactionOverview>(`/api/transaction/${transactionId}/overview`);
}

export async function fetchRiskDistribution() {
  return request<RiskDistributionResponse>('/api/analytics/risk-distribution');
}

export async function fetchTopRiskSuppliers(limit = 10) {
  return request<TopRiskSuppliersResponse>(`/api/analytics/top-risk-suppliers${toQueryString({ limit })}`);
}

export async function fetchClusterDistribution() {
  return request<ClusterDistributionResponse>('/api/analytics/cluster-distribution');
}

export async function fetchAnomalySummary() {
  return request<AnomalySummary>('/api/analytics/anomaly-summary');
}

export async function fetchChatbotStatus() {
  return request<{ ready: boolean; building: boolean; documents: number; sources: string[] }>(
    '/api/chatbot/status',
  );
}

export async function fetchChatbotQuery(question: string, conversationId?: number | null) {
  return request<{
    answer: string;
    sources: string[];
    confidence: number;
    conversation_id: number | null;
  }>('/api/chatbot/query', {
    method: 'POST',
    body: JSON.stringify({ question, conversation_id: conversationId ?? null }),
  });
}

export async function triggerChatbotReindex() {
  return request<{ status: string; message: string }>('/api/chatbot/reindex', {
    method: 'POST',
  });
}

export type ConversationSummary = {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ConversationMessage = {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  sources: string[];
  confidence: number;
  created_at: string;
};

export type ConversationDetail = ConversationSummary & {
  messages: ConversationMessage[];
};

export async function fetchConversations(): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>('/api/chatbot/conversations') as unknown as Promise<ConversationSummary[]>;
}

export async function fetchConversationDetail(id: number): Promise<ConversationDetail> {
  return request<ConversationDetail>(`/api/chatbot/conversations/${id}`) as unknown as Promise<ConversationDetail>;
}

export async function deleteConversation(id: number): Promise<{ deleted: number }> {
  return request<{ deleted: number }>(`/api/chatbot/conversations/${id}`, {
    method: 'DELETE',
  }) as unknown as Promise<{ deleted: number }>;
}

export async function deleteAllConversations(): Promise<{ deleted: number }> {
  return request<{ deleted: number }>('/api/chatbot/conversations', {
    method: 'DELETE',
  }) as unknown as Promise<{ deleted: number }>;
}
export async function searchTransactions(params: {
  supplierId?: string;
  riskLevel?: string;
  minScore?: string;
  maxScore?: string;
  dateFrom?: string;
  dateTo?: string;
  keyword?: string;
  page?: number;
  pageSize?: number;
}) {
  return request<SearchTransactionsResponse>(`/api/search/transactions${toQueryString({
    supplier_id: params.supplierId,
    risk_level: params.riskLevel,
    min_score: params.minScore,
    max_score: params.maxScore,
    date_from: params.dateFrom,
    date_to: params.dateTo,
    keyword: params.keyword,
    page: params.page,
    page_size: params.pageSize,
  })}`);
}

export async function searchSuppliers(params: {
  supplierId?: string;
  cluster?: string;
  riskLevel?: string;
  minScore?: string;
  maxScore?: string;
  page?: number;
  pageSize?: number;
}) {
  return request<SearchSuppliersResponse>(`/api/search/suppliers${toQueryString({
    supplier_id: params.supplierId,
    cluster: params.cluster,
    risk_level: params.riskLevel,
    min_score: params.minScore,
    max_score: params.maxScore,
    page: params.page,
    page_size: params.pageSize,
  })}`);
}
