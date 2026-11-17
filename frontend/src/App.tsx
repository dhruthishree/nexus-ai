import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, 
  Files, 
  Bot, 
  GitBranch, 
  BarChart3, 
  Settings, 
  Upload, 
  Trash2, 
  Send, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  FileText, 
  ChevronRight,
  ShieldCheck,
  Zap,
  DollarSign,
  Clock
} from 'lucide-react';
import { api } from './services/api';
import type { DocumentItem, RAGResponse, WorkflowResponse } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'documents' | 'assistant' | 'agents' | 'analytics' | 'settings'>('dashboard');
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);

  // Chat & Agent states
  const [question, setQuestion] = useState('');
  const [ragResult, setRagResult] = useState<RAGResponse | null>(null);
  const [workflowResult, setWorkflowResult] = useState<WorkflowResponse | null>(null);
  const [querying, setQuerying] = useState(false);
  const [selectedDocFilter, setSelectedDocFilter] = useState<string>('');

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadMessage(null);
      const res = await api.uploadDocument(file);
      setUploadMessage(res.message);
      await loadDocuments();
    } catch (err: any) {
      setUploadMessage(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to remove this document and its vector embeddings?')) return;
    try {
      await api.deleteDocument(id);
      await loadDocuments();
    } catch (err) {
      alert('Delete failed');
    }
  };

  const handleAsk = async (mode: 'rag' | 'workflow') => {
    if (!question.trim()) return;
    try {
      setQuerying(true);
      if (mode === 'rag') {
        const res = await api.queryRAG(question, selectedDocFilter || undefined);
        setRagResult(res);
      } else {
        const res = await api.executeWorkflow(question, selectedDocFilter || undefined);
        setWorkflowResult(res);
      }
    } catch (err: any) {
      alert(err.message || 'Query failed');
    } finally {
      setQuerying(false);
    }
  };

  const totalChunks = documents.reduce((acc, d) => acc + d.chunk_count, 0);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col justify-between shrink-0">
        <div>
          <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-600/30">
              N
            </div>
            <div>
              <h1 className="font-semibold text-sm tracking-wide text-white">NEXUS AI</h1>
              <p className="text-xs text-slate-400 font-mono">Enterprise Intelligence</p>
            </div>
          </div>

          <nav className="p-3 space-y-1">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
              { id: 'documents', label: 'Document Library', icon: Files },
              { id: 'assistant', label: 'Knowledge Assistant', icon: Bot },
              { id: 'agents', label: 'Agent Workflow', icon: GitBranch },
              { id: 'analytics', label: 'Analytics & Costs', icon: BarChart3 },
              { id: 'settings', label: 'Settings', icon: Settings },
            ].map((item) => {
              const Icon = item.icon;
              const active = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id as any)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-indigo-600/10 text-indigo-400 border border-indigo-500/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-900/80 rounded-lg p-3 border border-slate-800 text-xs text-slate-400 space-y-1">
            <div className="flex items-center justify-between text-slate-300 font-medium">
              <span>System Status</span>
              <span className="flex items-center gap-1 text-emerald-400 text-[10px]">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                Healthy
              </span>
            </div>
            <p>Gemini 2.5 Flash • ChromaDB</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto bg-slate-950">
        {/* Top Header */}
        <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-900/20 shrink-0">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span>Workspace</span>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="text-slate-200 capitalize font-medium">{activeTab.replace('-', ' ')}</span>
          </div>

          <div className="flex items-center gap-3">
            <label className="cursor-pointer bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-3.5 py-2 rounded-lg flex items-center gap-2 shadow-sm transition">
              <Upload className="w-3.5 h-3.5" />
              <span>{uploading ? 'Ingesting...' : 'Upload Document'}</span>
              <input type="file" onChange={handleFileUpload} accept=".pdf,.docx,.txt,.csv" className="hidden" disabled={uploading} />
            </label>
          </div>
        </header>

        {/* Dynamic Pages */}
        <div className="p-8 flex-1 max-w-7xl mx-auto w-full">
          {uploadMessage && (
            <div className="mb-6 p-4 rounded-lg bg-indigo-950/40 border border-indigo-800/60 text-indigo-300 text-sm flex items-center justify-between">
              <span>{uploadMessage}</span>
              <button onClick={() => setUploadMessage(null)} className="text-xs hover:underline">Dismiss</button>
            </div>
          )}

          {/* DASHBOARD */}
          {activeTab === 'dashboard' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Enterprise Intelligence Overview</h2>
                <p className="text-slate-400 text-sm mt-1">Real-time status of ingested enterprise documents, vector embeddings, and multi-agent systems.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                  { label: 'Total Ingested Documents', value: documents.length, icon: Files, color: 'text-indigo-400' },
                  { label: 'Indexed Semantic Chunks', value: totalChunks, icon: FileText, color: 'text-emerald-400' },
                  { label: 'Active Vector Space', value: 'ChromaDB HNSW', icon: ShieldCheck, color: 'text-sky-400' },
                  { label: 'Multi-Agent StateGraph', value: '4 Active Agents', icon: GitBranch, color: 'text-purple-400' },
                ].map((stat, i) => {
                  const Icon = stat.icon;
                  return (
                    <div key={i} className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-medium text-slate-400">{stat.label}</span>
                        <Icon className={`w-4 h-4 ${stat.color}`} />
                      </div>
                      <div className="text-2xl font-bold text-white mt-3">{stat.value}</div>
                    </div>
                  );
                })}
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800">
                  <h3 className="text-sm font-semibold text-white mb-4">Multi-Agent Workflow Lifecycle</h3>
                  <div className="space-y-3">
                    {[
                      { step: '1. Ingestion Agent', desc: 'SHA-256 deduplication, multi-format parsing (PDF/DOCX/TXT/CSV), recursive chunking.' },
                      { step: '2. Retrieval Agent', desc: 'Queries Gemini text-embedding-004 vectors against ChromaDB with cosine similarity.' },
                      { step: '3. Analysis Agent', desc: 'Extracts atomic facts and synthesizes context relations in JSON.' },
                      { step: '4. Verification Agent', desc: 'Cross-checks claims against source chunks, triggering automated retrieval retry if facts are missing.' },
                      { step: '5. Response Agent', desc: 'Outputs final answer with bracketed source citations and token/cost tracking.' },
                    ].map((step, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-950/60 border border-slate-800/60 text-xs">
                        <span className="font-semibold text-indigo-400">{step.step}</span>
                        <p className="text-slate-400 mt-1">{step.desc}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 flex flex-col justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white mb-4">Quick Test Queries</h3>
                    <div className="space-y-2">
                      {[
                        'What architectural patterns does NEXUS AI utilize for deduplication?',
                        'How does the verification agent handle insufficient context?',
                        'Summarize the core technical findings from the uploaded CSV dataset.',
                      ].map((q, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            setQuestion(q);
                            setActiveTab('assistant');
                          }}
                          className="w-full text-left p-3 rounded-lg bg-slate-950/60 hover:bg-slate-850 border border-slate-800/80 text-xs text-slate-300 hover:text-white transition flex items-center justify-between"
                        >
                          <span>{q}</span>
                          <ChevronRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-800/80 text-xs text-slate-500 flex justify-between">
                    <span>Google Cloud Consulting standard</span>
                    <span>Gemini 2.5 Flash</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* DOCUMENTS */}
          {activeTab === 'documents' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white tracking-tight">Document Library</h2>
                  <p className="text-slate-400 text-sm mt-1">Managed repository of untrusted source documents with SHA-256 integrity and chunk tracking.</p>
                </div>
                <button onClick={loadDocuments} className="p-2 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white text-xs flex items-center gap-2">
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>

              <div className="bg-slate-900/40 rounded-xl border border-slate-800 overflow-hidden">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800 font-semibold uppercase tracking-wider text-[10px]">
                    <tr>
                      <th className="px-6 py-3.5">Filename</th>
                      <th className="px-4 py-3.5">Type</th>
                      <th className="px-4 py-3.5">Size</th>
                      <th className="px-4 py-3.5">Chunks</th>
                      <th className="px-4 py-3.5">SHA-256 Hash</th>
                      <th className="px-4 py-3.5">Status</th>
                      <th className="px-6 py-3.5 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {documents.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="px-6 py-12 text-center text-slate-500 font-sans">
                          No documents uploaded yet. Upload a PDF, DOCX, TXT, or CSV to begin.
                        </td>
                      </tr>
                    ) : (
                      documents.map((doc) => (
                        <tr key={doc.id} className="hover:bg-slate-800/20 transition">
                          <td className="px-6 py-4 font-sans font-medium text-slate-200 flex items-center gap-2">
                            <FileText className="w-4 h-4 text-indigo-400 shrink-0" />
                            {doc.filename}
                          </td>
                          <td className="px-4 py-4 uppercase text-slate-400">{doc.file_type.replace('.', '')}</td>
                          <td className="px-4 py-4 text-slate-400">{(doc.file_size_bytes / 1024).toFixed(1)} KB</td>
                          <td className="px-4 py-4 text-indigo-400 font-semibold">{doc.chunk_count}</td>
                          <td className="px-4 py-4 text-slate-500 text-[11px]" title={doc.sha256_hash}>
                            {doc.sha256_hash.slice(0, 10)}...{doc.sha256_hash.slice(-6)}
                          </td>
                          <td className="px-4 py-4">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              doc.status === 'COMPLETED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                              doc.status === 'PROCESSING' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                              'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                              {doc.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => handleDelete(doc.id)}
                              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition"
                              title="Delete document and vector chunks"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* KNOWLEDGE ASSISTANT */}
          {activeTab === 'assistant' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">AI Knowledge Assistant</h2>
                <p className="text-slate-400 text-sm mt-1">Ask questions grounded in enterprise document evidence with exact citations.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-4">
                <div className="flex gap-4">
                  <input
                    type="text"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    placeholder="Ask a technical or operational question about your documents..."
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                    onKeyDown={(e) => e.key === 'Enter' && handleAsk('rag')}
                  />
                  <button
                    onClick={() => handleAsk('rag')}
                    disabled={querying || !question.trim()}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-6 py-3 rounded-lg flex items-center gap-2 transition shrink-0"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{querying ? 'Retrieving...' : 'Ask RAG'}</span>
                  </button>
                </div>

                <div className="flex items-center gap-4 text-xs text-slate-400">
                  <span>Scope Document:</span>
                  <select
                    value={selectedDocFilter}
                    onChange={(e) => setSelectedDocFilter(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded px-3 py-1 text-slate-200"
                  >
                    <option value="">All Documents</option>
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>{d.filename}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* RAG Answer Display */}
              {ragResult && (
                <div className="space-y-6">
                  <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                        <Bot className="w-4 h-4" />
                        Grounded Synthesis
                      </span>
                      <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3 text-slate-500" /> {ragResult.metrics.latency_seconds}s</span>
                        <span className="flex items-center gap-1"><Zap className="w-3 h-3 text-amber-500" /> {ragResult.metrics.total_tokens} tokens</span>
                        <span className="flex items-center gap-1"><DollarSign className="w-3 h-3 text-emerald-400" /> ${ragResult.metrics.estimated_cost_usd.toFixed(6)}</span>
                      </div>
                    </div>

                    <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                      {ragResult.answer}
                    </div>

                    {!ragResult.has_sufficient_context && (
                      <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 shrink-0" />
                        <span>Evidence threshold flag: Model reported lack of conclusive facts in the retrieved corpus.</span>
                      </div>
                    )}
                  </div>

                  {/* Citations List */}
                  {ragResult.citations.length > 0 && (
                    <div className="space-y-3">
                      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Citations & Supporting Context</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {ragResult.citations.map((cite) => (
                          <div key={cite.citation_id} className="p-4 rounded-lg bg-slate-900/40 border border-slate-800/80 text-xs space-y-2">
                            <div className="flex items-center justify-between text-slate-300 font-medium">
                              <span className="text-indigo-400 font-semibold">[{cite.citation_id}] {cite.document_filename}</span>
                              <span className="text-slate-500">Page {cite.page_number || 1} • {Math.round(cite.similarity_score * 100)}% match</span>
                            </div>
                            <p className="text-slate-400 font-mono text-[11px] bg-slate-950/60 p-2.5 rounded border border-slate-800/50">
                              "{cite.excerpt}"
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* MULTI-AGENT WORKFLOW */}
          {activeTab === 'agents' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Agent Workflow Monitor</h2>
                <p className="text-slate-400 text-sm mt-1">Inspect multi-agent coordination, fact verification, and state transition cycles.</p>
              </div>

              <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex gap-4">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Enter complex multi-step question for agent orchestration..."
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={() => handleAsk('workflow')}
                  disabled={querying || !question.trim()}
                  className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white text-xs font-semibold px-6 py-3 rounded-lg flex items-center gap-2 transition shrink-0"
                >
                  <GitBranch className="w-3.5 h-3.5" />
                  <span>{querying ? 'Agents Running...' : 'Execute Workflow'}</span>
                </button>
              </div>

              {workflowResult && (
                <div className="space-y-6">
                  {/* Verified Answer */}
                  <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                      <span className="text-xs font-semibold uppercase tracking-wider text-purple-400 flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        Multi-Agent Verified Synthesis
                      </span>
                      <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                        <span>Latency: {workflowResult.metrics.total_latency_seconds}s</span>
                        <span>Cost: ${workflowResult.metrics.total_cost_usd.toFixed(6)}</span>
                      </div>
                    </div>
                    <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
                      {workflowResult.final_answer}
                    </div>
                  </div>

                  {/* Extracted Facts & Verification Status */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Analysis Agent: Extracted Facts</h4>
                      <ul className="space-y-2 text-xs text-slate-300">
                        {workflowResult.analyzed_facts.map((fact, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-indigo-400 font-bold">•</span>
                            <span>{fact}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verification & Hallucination Guard</h4>
                      <div className={`p-3 rounded-lg text-xs ${
                        workflowResult.is_verified ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                      }`}>
                        <span className="font-semibold">{workflowResult.is_verified ? 'Verified Grounded' : 'Verification Flagged'}:</span>
                        <p className="mt-1">{workflowResult.verification_feedback}</p>
                      </div>
                    </div>
                  </div>

                  {/* Workflow Execution Logs Audit */}
                  <div className="p-5 rounded-xl bg-slate-900/40 border border-slate-800 space-y-3">
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">LangGraph Execution Audit Log</h4>
                    <div className="space-y-2 font-mono text-[11px]">
                      {workflowResult.workflow_logs.map((log, i) => (
                        <div key={i} className="p-2.5 rounded bg-slate-950/80 border border-slate-800/60 flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="text-indigo-400 font-semibold">{log.agent_name}</span>
                            <span className="text-slate-400">{log.details}</span>
                          </div>
                          <span className="text-slate-500 text-[10px]">{log.timestamp_utc.slice(11, 19)} UTC</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ANALYTICS */}
          {activeTab === 'analytics' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">Evaluation & Observability</h2>
                <p className="text-slate-400 text-sm mt-1">Operational token metrics, model unit economics, and latency benchmarks.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <span className="text-xs font-medium text-slate-400">Input Pricing</span>
                  <div className="text-xl font-bold text-white">$0.075 / 1M tokens</div>
                  <p className="text-xs text-slate-500">Gemini 2.5 Flash context input tier</p>
                </div>
                <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <span className="text-xs font-medium text-slate-400">Output Pricing</span>
                  <div className="text-xl font-bold text-white">$0.300 / 1M tokens</div>
                  <p className="text-xs text-slate-500">Candidate generation output tier</p>
                </div>
                <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800 space-y-2">
                  <span className="text-xs font-medium text-slate-400">Embedding Cost</span>
                  <div className="text-xl font-bold text-white">Free Tier / Standard</div>
                  <p className="text-xs text-slate-500">text-embedding-004 (768 dimensions)</p>
                </div>
              </div>
            </div>
          )}

          {/* SETTINGS */}
          {activeTab === 'settings' && (
            <div className="max-w-2xl space-y-6">
              <div>
                <h2 className="text-xl font-bold text-white tracking-tight">System Settings</h2>
                <p className="text-slate-400 text-sm mt-1">Configure models, temperature thresholds, and database connection strings.</p>
              </div>

              <div className="p-6 rounded-xl bg-slate-900/50 border border-slate-800 space-y-4 text-xs">
                <div>
                  <label className="text-slate-300 font-medium block mb-1.5">Embedding Model</label>
                  <input type="text" readOnly value="text-embedding-004" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-400 font-mono" />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1.5">Generation Model</label>
                  <input type="text" readOnly value="gemini-2.5-flash" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-400 font-mono" />
                </div>
                <div>
                  <label className="text-slate-300 font-medium block mb-1.5">Similarity Threshold</label>
                  <input type="text" readOnly value="0.35 (Cosine similarity)" className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-slate-400 font-mono" />
                </div>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
