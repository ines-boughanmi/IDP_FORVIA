import { isTokenExpired } from '@/utils/jwt';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export class ApiError extends Error {
  status: number;
  code?: string;
  details?: unknown;

  constructor(message: string, status: number, code?: string, details?: unknown) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export type ApiEnvelope<T> = {
  status: 'success' | 'error';
  data: T;
  metadata: Record<string, unknown>;
};

export function getStoredToken(): string | null {
  const token = localStorage.getItem('access_token');
  if (!token) return null;
  if (isTokenExpired(token)) {
    localStorage.removeItem('access_token');
    return null;
  }
  return token;
}

export async function request<T>(path: string, options: RequestInit = {}, withAuth = true): Promise<ApiEnvelope<T>> {
  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');

  const token = withAuth ? getStoredToken() : null;
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = payload?.message || payload?.detail || response.statusText;
    throw new ApiError(message, response.status, payload?.code, payload);
  }

  return payload as ApiEnvelope<T>;
}

export function toQueryString(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') return;
    search.set(key, String(value));
  });
  const query = search.toString();
  return query ? `?${query}` : '';
}
