import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow, parseISO } from 'date-fns';
import {
  BarChart3,
  Lightbulb,
  RefreshCw,
} from 'lucide-react';
import { useInsights } from '../api/queries';
import type { Theme } from '../api/types';
import { Nav } from '../components/Nav';
import { StatusBadge } from '../components/StatusBadge';
import { PriorityBadge } from '../components/PriorityBadge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const DATE_RANGE_PRESETS = [
  { label: 'Past 7 days', days: 7 },
  { label: 'Past 14 days', days: 14 },
  { label: 'Past 30 days', days: 30 },
  { label: 'Past 90 days', days: 90 },
];

export const InsightsPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedPreset, setSelectedPreset] = useState<number>(7);
  const [customSince, setCustomSince] = useState<string>(() => {
    const d = new Date();
    d.setDate(d.getDate() - 7);
    return d.toISOString().split('T')[0];
  });

  const { data, isLoading, isError, error, refetch, isFetching } = useInsights(customSince);

  const handlePresetSelect = (days: number) => {
    setSelectedPreset(days);
    const d = new Date();
    d.setDate(d.getDate() - days);
    setCustomSince(d.toISOString().split('T')[0]);
  };

  const themes: Theme[] = data ?? [];

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Nav />

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        {/* Header */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
              <BarChart3 className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">
                Insights — Recurring Themes
              </h1>
              <span className="text-[11px] text-slate-400">
                Operations Lead intelligence and cross-ticket cluster analysis
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => refetch()}
              disabled={isFetching}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-300 font-medium transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin text-indigo-400' : ''}`} />
              <span>Refresh</span>
            </button>
          </div>
        </header>

        <div className="p-8 max-w-6xl mx-auto w-full space-y-6">
          {/* Controls bar */}
          <div className="bg-slate-850 p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 shadow-md">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-slate-300">Period:</span>
              <div className="flex rounded-lg bg-slate-900 p-1 border border-slate-700">
                {DATE_RANGE_PRESETS.map((p) => (
                  <button
                    key={p.days}
                    type="button"
                    onClick={() => handlePresetSelect(p.days)}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      selectedPreset === p.days
                        ? 'bg-indigo-600 text-white'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Since:</span>
              <div className="relative">
                <input
                  type="date"
                  value={customSince}
                  onChange={(e) => {
                    setCustomSince(e.target.value);
                    setSelectedPreset(0);
                  }}
                  className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Body with Loading / Error / Content */}
          {isLoading ? (
            <div className="p-12 bg-slate-850 rounded-xl border border-slate-800">
              <LoadingSpinner message="Clustering operational issues and computing theme trends..." />
            </div>
          ) : isError ? (
            <div className="p-6 bg-slate-850 rounded-xl border border-slate-800">
              <ErrorState
                message={error instanceof Error ? error.message : 'Failed to load theme insights.'}
                onRetry={() => refetch()}
              />
            </div>
          ) : themes.length === 0 ? (
            <EmptyState
              icon={<Lightbulb className="w-8 h-8 text-amber-400" />}
              title="No recurring issue themes discovered"
              message="No ticket clusters exceeded recurring similarity thresholds within the selected time period."
            />
          ) : (
            <div className="space-y-6">
              {themes.map((theme, index) => {
                const sampleTickets = theme.sample_tickets || [];

                return (
                  <div
                    key={theme.theme_name || index}
                    className="bg-slate-850 border border-slate-800 rounded-xl overflow-hidden shadow-lg transition-all hover:border-slate-700"
                  >
                    {/* Theme Header */}
                    <div className="p-5 border-b border-slate-750 border-slate-800 bg-slate-900/60 flex flex-wrap items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-700/60 flex items-center justify-center text-indigo-400 font-bold text-xs">
                          #{index + 1}
                        </div>
                        <div>
                          <h2 className="text-base font-bold text-white tracking-tight">
                            {theme.theme_name}
                          </h2>
                          <div className="text-xs text-slate-400 mt-0.5">
                            Rule-assisted themes from ticket text, public comments and external supplier/agency messages
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-600/30 text-indigo-300 border border-indigo-500/50">
                          {theme.count} {theme.count === 1 ? 'ticket' : 'tickets'}
                        </span>
                      </div>
                    </div>

                    {/* Mini Table of Sample Tickets */}
                    <div className="p-5">
                      <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                        Recent Sample Cases ({sampleTickets.slice(0, 5).length} of {theme.count})
                      </div>

                      {sampleTickets.length === 0 ? (
                        <div className="text-xs text-slate-500 italic py-2">
                          No sample records available for preview.
                        </div>
                      ) : (
                        <div className="overflow-x-auto rounded-lg border border-slate-700/80">
                          <table className="w-full text-left text-xs">
                            <thead className="bg-slate-900/80 border-b border-slate-700 text-slate-400 uppercase font-semibold">
                              <tr>
                                <th className="py-2 px-3">Priority</th>
                                <th className="py-2 px-3">Title</th>
                                <th className="py-2 px-3">Agency</th>
                                <th className="py-2 px-3">Status</th>
                                <th className="py-2 px-3 text-right">Created</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-700/50">
                              {sampleTickets.slice(0, 5).map((st) => {
                                let relativeDate = '';
                                try {
                                  relativeDate = formatDistanceToNow(parseISO(st.created_at), { addSuffix: true });
                                } catch {
                                  relativeDate = st.created_at;
                                }

                                return (
                                  <tr
                                    key={st.id}
                                    onClick={() => navigate(`/tickets/${st.id}`)}
                                    className="hover:bg-slate-700/40 cursor-pointer transition-colors group"
                                  >
                                    <td className="py-2 px-3">
                                      <PriorityBadge priority={st.priority} />
                                    </td>
                                    <td className="py-2 px-3 font-medium text-slate-200 group-hover:text-indigo-300 transition-colors">
                                      <div className="truncate max-w-md">{st.title}</div>
                                    </td>
                                    <td className="py-2 px-3 text-slate-300">
                                      {st.agency_name ?? st.agency_id}
                                    </td>
                                    <td className="py-2 px-3">
                                      <StatusBadge status={st.status} />
                                    </td>
                                    <td className="py-2 px-3 text-right text-slate-400 font-mono">
                                      {relativeDate}
                                    </td>
                                  </tr>
                                );
                              })}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
