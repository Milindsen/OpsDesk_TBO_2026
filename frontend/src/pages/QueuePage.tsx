import React, { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  AlertOctagon,
  Globe2,
  Inbox,
  Layers,
  Link2,
  RefreshCw,
  Tag,
  UserCheck,
} from 'lucide-react';
import { useTickets } from '../api/queries';
import type { Intent, Ticket, TicketFilters } from '../api/types';
import { useAuth } from '../store/auth';
import { FilterBar } from '../components/FilterBar';
import { TicketTable } from '../components/TicketTable';
import { Nav } from '../components/Nav';

type QueueTab = 'all' | 'triage' | 'my_queue' | 'by_region' | 'by_intent' | 'linked' | 'escalation';

const REGIONS = ['IN-West', 'IN-East', 'ME'];
const INTENTS: Intent[] = [
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

export const QueuePage: React.FC = () => {
  const { user, isRole } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();

  // Active tab from URL query or default
  const activeTab = (searchParams.get('tab') as QueueTab) || 'all';

  // Sub-selector states for By Region & By Intent tabs
  const [selectedRegion, setSelectedRegion] = useState<string>('IN-West');
  const [selectedIntent, setSelectedIntent] = useState<Intent>('refund');

  // Ad-hoc filters from FilterBar
  const [userFilters, setUserFilters] = useState<TicketFilters>({});

  // Compute queries parameters based on tab + userFilters
  const queryFilters: TicketFilters = useMemo(() => {
    const base: TicketFilters = { ...userFilters };

    switch (activeTab) {
      case 'triage':
        base.unassigned = true;
        break;
      case 'my_queue':
        if (user?.id) {
          base.assignee_id = user.id;
        }
        break;
      case 'by_region':
        base.region = selectedRegion;
        break;
      case 'by_intent':
        base.intent = selectedIntent;
        break;
      case 'linked':
        base.has_links = true;
        break;
      case 'escalation':
        base.status = 'Escalated';
        break;
      case 'all':
      default:
        break;
    }

    return base;
  }, [activeTab, userFilters, selectedRegion, selectedIntent, user?.id]);

  const { data, isLoading, isError, error, refetch, isFetching } = useTickets(queryFilters);

  const tickets = data?.items ?? [];
  const totalCount = data?.total ?? tickets.length;

  const handleTabChange = (tab: QueueTab) => {
    setSearchParams({ tab });
    setUserFilters({}); // Reset local search on tab change
  };

  const isAgent = isRole('agent', 'lead');
  const isEM = isRole('escalation_manager', 'lead');

  // Grouped view for "Linked Cases" tab
  const groupedLinkedTickets = useMemo(() => {
    if (activeTab !== 'linked') return null;
    const groups: Record<string, Ticket[]> = {};
    for (const t of tickets) {
      const key = t.tboh || 'Unknown TBOH';
      if (!groups[key]) groups[key] = [];
      groups[key].push(t);
    }
    return groups;
  }, [activeTab, tickets]);

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      {/* Sidebar Nav */}
      <Nav />

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        {/* Header Bar */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              <span>Operations Queue</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-700/60 font-mono">
                {totalCount} {totalCount === 1 ? 'ticket' : 'tickets'}
              </span>
            </h1>
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

        <div className="p-6 flex-1 flex flex-col">
          {/* Tabs Navigation */}
          <div className="border-b border-slate-800 mb-4 overflow-x-auto">
            <nav className="flex space-x-2 pb-px">
              {/* All */}
              <button
                type="button"
                onClick={() => handleTabChange('all')}
                className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                  activeTab === 'all'
                    ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                }`}
              >
                <Inbox className="w-3.5 h-3.5" />
                <span>All Queue</span>
              </button>

              {/* Triage */}
              {isAgent && (
                <button
                  type="button"
                  onClick={() => handleTabChange('triage')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'triage'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Triage (Unassigned)</span>
                </button>
              )}

              {/* My Queue */}
              {isAgent && (
                <button
                  type="button"
                  onClick={() => handleTabChange('my_queue')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'my_queue'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <UserCheck className="w-3.5 h-3.5" />
                  <span>My Queue</span>
                </button>
              )}

              {/* By Region */}
              {isAgent && (
                <button
                  type="button"
                  onClick={() => handleTabChange('by_region')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'by_region'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <Globe2 className="w-3.5 h-3.5" />
                  <span>By Region</span>
                </button>
              )}

              {/* By Intent */}
              {isAgent && (
                <button
                  type="button"
                  onClick={() => handleTabChange('by_intent')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'by_intent'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <Tag className="w-3.5 h-3.5" />
                  <span>By Intent</span>
                </button>
              )}

              {/* Linked Cases */}
              {isAgent && (
                <button
                  type="button"
                  onClick={() => handleTabChange('linked')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'linked'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80'
                      : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-850'
                  }`}
                >
                  <Link2 className="w-3.5 h-3.5" />
                  <span>Linked Cases</span>
                </button>
              )}

              {/* Escalation Queue */}
              {isEM && (
                <button
                  type="button"
                  onClick={() => handleTabChange('escalation')}
                  className={`flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 ${
                    activeTab === 'escalation'
                      ? 'border-rose-500 text-rose-300 bg-rose-950/40'
                      : 'border-transparent text-rose-400/80 hover:text-rose-300 hover:bg-rose-950/20'
                  }`}
                >
                  <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                  <span>Escalation Queue</span>
                </button>
              )}
            </nav>
          </div>

          {/* Sub-selector bars for By Region / By Intent tabs */}
          {activeTab === 'by_region' && (
            <div className="mb-4 flex items-center gap-2 bg-slate-850 p-2.5 rounded-lg border border-slate-700">
              <span className="text-xs font-semibold text-slate-300">Select Region:</span>
              <div className="flex flex-wrap gap-1.5">
                {REGIONS.map((rg) => (
                  <button
                    key={rg}
                    type="button"
                    onClick={() => setSelectedRegion(rg)}
                    className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                      selectedRegion === rg
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {rg}
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'by_intent' && (
            <div className="mb-4 flex items-center gap-2 bg-slate-850 p-2.5 rounded-lg border border-slate-700">
              <span className="text-xs font-semibold text-slate-300">Select Intent:</span>
              <div className="flex flex-wrap gap-1.5">
                {INTENTS.map((it) => (
                  <button
                    key={it}
                    type="button"
                    onClick={() => setSelectedIntent(it)}
                    className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                      selectedIntent === it
                        ? 'bg-indigo-600 text-white'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {it.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Filter Bar */}
          <FilterBar
            filters={userFilters}
            onChange={setUserFilters}
            onClear={() => setUserFilters({})}
            hideStatus={activeTab === 'escalation'}
          />

          {/* Table rendering */}
          {activeTab === 'linked' && groupedLinkedTickets ? (
            <div className="space-y-6">
              {Object.keys(groupedLinkedTickets).length === 0 && !isLoading ? (
                <div className="p-8 text-center bg-slate-800/60 rounded-lg border border-slate-700 text-slate-400 text-xs">
                  No linked cases found with strong cross-ticket links.
                </div>
              ) : (
                Object.entries(groupedLinkedTickets).map(([tboh, groupTickets]) => (
                  <div key={tboh} className="bg-slate-850 p-4 rounded-lg border border-slate-700/80">
                    <div className="flex items-center justify-between mb-3 border-b border-slate-700 pb-2">
                      <div className="flex items-center gap-2">
                        <Link2 className="w-4 h-4 text-indigo-400" />
                        <span className="text-sm font-bold text-white font-mono">TBOH: {tboh}</span>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-300 border border-indigo-700/50">
                          {groupTickets.length} related cases
                        </span>
                      </div>
                    </div>
                    <TicketTable
                      tickets={groupTickets}
                      isLoading={isLoading}
                      isError={isError}
                      errorMessage={error instanceof Error ? error.message : undefined}
                      onRetry={() => refetch()}
                    />
                  </div>
                ))
              )}
            </div>
          ) : (
            <TicketTable
              tickets={tickets}
              isLoading={isLoading}
              isError={isError}
              errorMessage={error instanceof Error ? error.message : undefined}
              onRetry={() => refetch()}
              emptyTitle={activeTab === 'escalation' ? 'No escalated tickets' : undefined}
              emptyMessage={
                activeTab === 'escalation'
                  ? 'Great job! There are currently no tickets requiring escalation manager intervention.'
                  : undefined
              }
            />
          )}
        </div>
      </main>
    </div>
  );
};
