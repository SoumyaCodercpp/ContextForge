const API_BASE = "http://localhost:8000";

export interface SearchRequest {
  question: string;
  top_k?: number;
  max_tokens?: number;
  dedup_threshold?: number;
  selection_strategy?: "greedy_by_density" | "greedy_by_score";
  document_ids?: number[];
}

export interface RetrievedChunk {
  chunk_id: number;
  document_id: number;
  text: string;
  score: number;
  chunk_index: number;
  page_number: number | null;
}

export interface DedupResultResponse {
  kept_count: number;
  removed_count: number;
  threshold: number;
  kept: RetrievedChunk[];
  removed: RetrievedChunk[];
}

export interface ScoredChunk {
  chunk_id: number;
  document_id: number;
  text: string;
  context_score: number;
  semantic_similarity: number;
  freshness_score: number;
  authority_score: number;
  density_score: number;
  chunk_index: number;
  page_number: number | null;
}

export interface SelectionResultResponse {
  selected_count: number;
  excluded_count: number;
  total_tokens: number;
  max_budget: number;
  strategy: string;
  savings: {
    tokens_used: number;
    tokens_available: number;
    tokens_saved: number;
    savings_percent: number;
    budget_utilization_percent: number;
  };
  selected: ScoredChunk[];
}

export interface SearchResponse {
  query: string;
  answer: string;
  pipeline_latency_ms: number;
  stages: {
    retrieved: number;
    after_dedup: number;
    after_scoring: number;
    after_selection: number;
  };
  token_summary: {
    tokens_used: number;
    tokens_available: number;
    tokens_saved: number;
    savings_percent: number;
    budget_utilization_percent: number;
  };
  retrieved: RetrievedChunk[];
  dedup: DedupResultResponse;
  scored: ScoredChunk[];
  selection: SelectionResultResponse;
  llm_usage: {
    model: string;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
    latency_ms: number;
  };
}

export interface MetricsResponse {
  total_documents: number;
  total_chunks: number;
  total_searches: number;
  avg_pipeline_latency_ms: number;
  vector_collection_info: Record<string, unknown>;
}

export interface UploadResponse {
  message: string;
  document_ids: number[];
  filenames: string[];
  total_chunks: number;
  processing_time_ms: number;
}

export interface DocumentInfo {
  id: number;
  filename: string;
  file_type: string;
  file_size_bytes: number;
  chunk_count: number;
  uploaded_at: string;
}

export async function listDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function searchDocuments(req: SearchRequest): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Search failed");
  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<UploadResponse> {
  const formData = new FormData();
  files.forEach((f) => formData.append("files", f));
  const res = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
}

export async function getMetrics(): Promise<MetricsResponse> {
  const res = await fetch(`${API_BASE}/metrics`);
  if (!res.ok) throw new Error("Failed to fetch metrics");
  return res.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}