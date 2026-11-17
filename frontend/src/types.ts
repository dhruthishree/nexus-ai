export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  sha256_hash: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  error_message?: string;
  chunk_count: number;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  citation_id: number;
  document_id: string;
  document_filename: string;
  chunk_id: string;
  page_number?: number;
  similarity_score: number;
  excerpt: string;
}

export interface RAGMetrics {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  latency_seconds: number;
  estimated_cost_usd: number;
}

export interface RAGResponse {
  question: string;
  answer: string;
  citations: Citation[];
  has_sufficient_context: boolean;
  metrics: RAGMetrics;
  generated_at: string;
}

export interface WorkflowLog {
  step_name: string;
  agent_name: string;
  status: string;
  details: string;
  timestamp_utc: string;
}

export interface WorkflowResponse {
  question: string;
  final_answer: string;
  citations: Citation[];
  has_sufficient_context: boolean;
  is_verified: boolean;
  verification_feedback: string;
  analyzed_facts: string[];
  workflow_logs: WorkflowLog[];
  metrics: {
    total_input_tokens: number;
    total_output_tokens: number;
    total_cost_usd: number;
    total_latency_seconds: number;
    retrieval_retry_count: number;
  };
}
