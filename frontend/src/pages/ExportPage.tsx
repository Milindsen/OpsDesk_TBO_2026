import React, { useState } from 'react';
import {
  AlertCircle,
  CheckCircle2,
  Download,
  FileSpreadsheet,
  Sparkles,
} from 'lucide-react';
import { Nav } from '../components/Nav';
import type { Intent, Priority, TicketStatus } from '../api/types';

const STATUS_OPTIONS: TicketStatus[] = ['New', 'Open', 'Pending', 'Escalated', 'Resolved', 'Closed'];
const PRIORITY_OPTIONS: Priority[] = ['P1', 'P2', 'P3', 'P4'];
const INTENT_OPTIONS: Intent[] = [
  'refund',
  'cancellation',
  'amendment',
  'voucher',
  'inventory_sync',
  'payment',
  'special_request',
  'supplier_issue',
  'other',
];
const REGIONS = ['IN-West', 'IN-East', 'ME'];

export const ExportPage: React.FC = () => {
  // Filter states
  const [status, setStatus] = useState<string>('');
  const [priority, setPriority] = useState<string>('');
  const [intent, setIntent] = useState<string>('');
  const [region, setRegion] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Streaming export state
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [progressRows, setProgressRows] = useState<number>(0);
  const [completedStats, setCompletedStats] = useState<{ rows: number; durationSeconds: string } | null>(
    null
  );
  const [exportError, setExportError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setProgressRows(0);
    setCompletedStats(null);
    setExportError(null);

    const startTime = performance.now();
    const token = localStorage.getItem('opsdesk_token');

    // Build query params
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (priority) params.append('priority', priority);
    if (intent) params.append('intent', intent);
    if (region) params.append('region', region);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const baseUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';
    const exportUrl = `${baseUrl}/export/tickets?${params.toString()}`;

    try {
      const response = await fetch(exportUrl, {
        headers: {
          Authorization: token ? `Bearer ${token}` : '',
        },
      });

      if (!response.ok) {
        // Fallback demo simulation if backend export endpoint is unavailable
        throw new Error(`Export failed with HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Readable stream not supported by server');
      }

      const decoder = new TextDecoder();
      let totalLines = 0;
      const chunks: Uint8Array<ArrayBuffer>[] = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) {
          chunks.push(value as Uint8Array<ArrayBuffer>);
          const text = decoder.decode(value, { stream: true });
          const lines = text.split('\n').length - 1;
          totalLines += Math.max(lines, 1);
          setProgressRows(totalLines);
        }
      }

      const serverRows = Number(response.headers.get('X-Row-Count') ?? Math.max(0, totalLines - 1));
      const endTime = performance.now();
      const durationSec = ((endTime - startTime) / 1000).toFixed(2);

      // Trigger download
      const blob = new Blob(chunks, { type: 'text/csv' });
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `opsdesk_export_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);

      setCompletedStats({
        rows: serverRows,
        durationSeconds: durationSec,
      });
    } catch (err) {
      setExportError(err instanceof Error ? err.message : 'Export failed. Please retry.');
      setIsExporting(false);
      return;
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Nav />

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        <header className="h-16 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <Download className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">Data Export</h1>
              <span className="text-[11px] text-slate-400">
                High-throughput streaming dataset export with zero row cap
              </span>
            </div>
          </div>
        </header>

        <div className="p-8 max-w-4xl mx-auto w-full space-y-6">
          {/* Note Banner */}
          <div className="p-4 bg-indigo-950/40 border border-indigo-500/40 rounded-xl flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-indigo-200">
              <span className="font-bold text-white">No row cap — exports full dataset: </span>
              OpsDesk streaming export delivers large volumes of case data directly from Postgres
              without server memory accumulation.
            </div>
          </div>

          {/* Export Form Card */}
          <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-xl space-y-5">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider">
              Export Filters & Parameters
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Status */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Filter by Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">All Statuses</option>
                  {STATUS_OPTIONS.map((st) => (
                    <option key={st} value={st}>
                      {st}
                    </option>
                  ))}
                </select>
              </div>

              {/* Priority */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Filter by Priority
                </label>
                <select
                  value={priority}
                  onChange={(e) => setPriority(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">All Priorities</option>
                  {PRIORITY_OPTIONS.map((pr) => (
                    <option key={pr} value={pr}>
                      {pr}
                    </option>
                  ))}
                </select>
              </div>

              {/* Intent */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Filter by Intent
                </label>
                <select
                  value={intent}
                  onChange={(e) => setIntent(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">All Intents</option>
                  {INTENT_OPTIONS.map((it) => (
                    <option key={it} value={it}>
                      {it.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Region */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Filter by Region
                </label>
                <select
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">All Regions</option>
                  {REGIONS.map((rg) => (
                    <option key={rg} value={rg}>
                      {rg}
                    </option>
                  ))}
                </select>
              </div>

              {/* Date Range Start */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Date Range Start
                </label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              {/* Date Range End */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Date Range End
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Progress / Status display */}
            {isExporting && (
              <div className="p-4 bg-slate-900/80 rounded-lg border border-indigo-500/50 space-y-2 animate-pulse">
                <div className="flex items-center justify-between text-xs font-semibold text-indigo-300">
                  <div className="flex items-center gap-2">
                    <div className="w-3.5 h-3.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
                    <span>Streaming dataset from server...</span>
                  </div>
                  <span className="font-mono text-white">{progressRows.toLocaleString()} rows received</span>
                </div>
                <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                  <div className="h-full bg-indigo-500 animate-pulse w-full" />
                </div>
              </div>
            )}

            {/* Completed Success Banner */}
            {completedStats && (
              <div
                data-testid="export-success-banner"
                className="p-4 bg-emerald-950/60 border border-emerald-600/60 rounded-lg flex items-center justify-between text-emerald-200"
              >
                <div className="flex items-center gap-2.5">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  <div>
                    <div className="text-xs font-bold text-white">Export Complete</div>
                    <div className="text-xs text-emerald-300 font-mono">
                      {completedStats.rows.toLocaleString()} rows exported in {completedStats.durationSeconds}s
                    </div>
                  </div>
                </div>
                <span className="text-xs px-2.5 py-1 rounded bg-emerald-900/60 border border-emerald-700 text-emerald-300 font-mono font-bold">
                  CSV Ready
                </span>
              </div>
            )}

            {exportError && (
              <div className="p-3 bg-red-950/60 border border-red-700 rounded-lg text-xs text-red-200 flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
                <span>{exportError}</span>
              </div>
            )}

            {/* Action buttons */}
            <div className="pt-4 border-t border-slate-800 flex justify-end">
              <button
                type="button"
                onClick={handleExport}
                disabled={isExporting}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>{isExporting ? 'Streaming Export...' : 'Start Streaming Export'}</span>
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
