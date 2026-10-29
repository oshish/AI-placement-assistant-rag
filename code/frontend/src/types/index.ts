export interface HealthStatus {
  status: string;
  collection_count: number;
  gemini_model: string;
  gemini_configured: boolean;
  embedding_model: string;
}

export interface QuestionMetadata {
  company_name: string;
  role_name: string;
  batch: string;
  category: string;
  source_record_id?: string;
  question_index?: number;
  [key: string]: any;
}

export interface QuestionItem {
  id: string;
  text: string;
  metadata: QuestionMetadata;
  similarity_score?: number;
  retrieval_mode?: string;
}

export interface PaginatedQuestions {
  items: QuestionItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface FilterOptions {
  companies: string[];
  roles: string[];
  batches: string[];
  categories: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: QuestionItem[];
  mode?: 'rag' | 'fallback';
  timestamp: string;
}

export interface ChatFilter {
  company_name?: string;
  role_name?: string;
  batch?: string;
  category?: string;
}

export interface AnalyticsDashboardData {
  overview: {
    total_questions: number;
    total_companies: number;
    total_roles: number;
    total_batches: number;
    total_experiences: number;
    total_company_role_records: number;
  };
  topics: { topic: string; count: number }[];
  oa_topics: { topic: string; count: number }[];
  companies: { company_name: string; question_count: number; role_count: number }[];
  categories: { category: string; count: number; percentage: number }[];
  batches: { batch: string; question_count: number }[];
  roles: { role_name: string; question_count: number }[];
  experiences: {
    total: number;
    outcomes: Record<string, number>;
    hiring_modes: Record<string, number>;
    sample_tips: {
      company_name: string;
      role_name: string;
      batch: string;
      advice: string;
      outcome: string;
    }[];
  };
  filter_options: FilterOptions;
}
