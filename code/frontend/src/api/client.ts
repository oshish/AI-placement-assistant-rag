import type {
  AnalyticsDashboardData,
  ChatFilter,
  FilterOptions,
  HealthStatus,
  PaginatedQuestions,
  QuestionItem,
} from '../types';

const API_BASE = '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status} ${response.statusText}`;
      try {
        const errJson = await response.json();
        if (errJson.detail) {
          errorDetail = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
        }
      } catch {
        // use fallback text
      }
      throw new Error(errorDetail);
    }

    return (await response.json()) as T;
  } catch (error: any) {
    // If running in development without proxy, try direct port 8000 fallback
    if (error.message?.includes('Failed to fetch') || error.message?.includes('NetworkError')) {
      const directUrl = `http://localhost:8000/api${endpoint}`;
      try {
        const directResp = await fetch(directUrl, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
          },
        });
        if (directResp.ok) {
          return (await directResp.json()) as T;
        }
      } catch {
        // Keep original error
      }
    }
    throw error;
  }
}

export const api = {
  getHealth: (): Promise<HealthStatus> => {
    return request<HealthStatus>('/health');
  },

  getFilters: (): Promise<FilterOptions> => {
    return request<FilterOptions>('/filters');
  },

  getQuestions: (params: {
    page?: number;
    page_size?: number;
    search?: string;
    company?: string;
    role?: string;
    batch?: string;
    category?: string;
  } = {}): Promise<PaginatedQuestions> => {
    const query = new URLSearchParams();
    if (params.page) query.append('page', params.page.toString());
    if (params.page_size) query.append('page_size', params.page_size.toString());
    if (params.search) query.append('search', params.search);
    if (params.company) query.append('company', params.company);
    if (params.role) query.append('role', params.role);
    if (params.batch) query.append('batch', params.batch);
    if (params.category) query.append('category', params.category);

    const qs = query.toString();
    return request<PaginatedQuestions>(`/questions${qs ? `?${qs}` : ''}`);
  },

  getQuestionById: (id: string): Promise<QuestionItem> => {
    return request<QuestionItem>(`/questions/${encodeURIComponent(id)}`);
  },

  sendChatMessage: (payload: {
    query: string;
    filters?: ChatFilter;
    history?: { role: string; content: string }[];
    top_k?: number;
  }): Promise<{
    query: string;
    answer: string;
    sources: QuestionItem[];
    mode: 'rag' | 'fallback';
    total_retrieved: number;
  }> => {
    return request('/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  getAnalyticsDashboard: (): Promise<AnalyticsDashboardData> => {
    return request<AnalyticsDashboardData>('/analytics/dashboard');
  },
};
