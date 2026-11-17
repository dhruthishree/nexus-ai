import type { DocumentItem, RAGResponse, WorkflowResponse } from '../types';

const API_BASE = '/api/v1';

export const api = {
  // Health
  getHealth: async () => {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },

  // Documents
  listDocuments: async (): Promise<DocumentItem[]> => {
    const res = await fetch(`${API_BASE}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  uploadDocument: async (file: File): Promise<{ message: string; document: DocumentItem; is_duplicate: boolean }> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  deleteDocument: async (id: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to delete document');
  },

  // RAG Query
  queryRAG: async (question: string, documentId?: string, topK: number = 5): Promise<RAGResponse> => {
    const res = await fetch(`${API_BASE}/rag/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, document_id: documentId, top_k: topK }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Query failed');
    }
    return res.json();
  },

  // Multi-Agent Workflow
  executeWorkflow: async (question: string, documentId?: string, topK: number = 5): Promise<WorkflowResponse> => {
    const res = await fetch(`${API_BASE}/workflow/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, document_id: documentId, top_k: topK }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Workflow execution failed');
    }
    return res.json();
  },
};
