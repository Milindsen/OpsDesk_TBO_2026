import React from 'react';
import { RotateCcw, Search } from 'lucide-react';
import type { Intent, Priority, TicketFilters, TicketStatus } from '../api/types';

interface FilterBarProps {
  filters: TicketFilters;
  onChange: (filters: TicketFilters) => void;
  onClear: () => void;
  availableRegions?: string[];
  hideStatus?: boolean; // Useful on tabs that have fixed status (e.g. Escalation Queue)
}

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

const DEFAULT_REGIONS = ['IN-West', 'IN-East', 'ME'];

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onChange,
  onClear,
  availableRegions = DEFAULT_REGIONS,
  hideStatus = false,
}) => {
  const handleFilterChange = (key: keyof TicketFilters, value: unknown) => {
    onChange({
      ...filters,
      [key]: value === '' ? undefined : value,
      page: 1, // Reset page on filter change
    });
  };

  const hasActiveFilters = Boolean(
    filters.status ||
    filters.intent ||
    filters.region ||
    filters.priority ||
    filters.tboh
  );

  return (
    <div className="flex flex-wrap items-center gap-2.5 p-3 bg-slate-800/80 rounded-lg border border-slate-700 mb-4">
      {/* TBOH Search */}
      <div className="relative flex-1 min-w-[180px]">
        <Search className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={filters.tboh ?? ''}
          onChange={(e) => handleFilterChange('tboh', e.target.value)}
          placeholder="Search TBOH / Booking ID..."
          className="w-full pl-8 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500"
        />
      </div>

      {/* Status Filter */}
      {!hideStatus && (
        <select
          value={filters.status ?? ''}
          onChange={(e) => handleFilterChange('status', e.target.value)}
          className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          {STATUS_OPTIONS.map((st) => (
            <option key={st} value={st}>
              {st}
            </option>
          ))}
        </select>
      )}

      {/* Priority Filter */}
      <select
        value={filters.priority ?? ''}
        onChange={(e) => handleFilterChange('priority', e.target.value)}
        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        <option value="">All Priorities</option>
        {PRIORITY_OPTIONS.map((pr) => (
          <option key={pr} value={pr}>
            {pr}
          </option>
        ))}
      </select>

      {/* Intent Filter */}
      <select
        value={filters.intent ?? ''}
        onChange={(e) => handleFilterChange('intent', e.target.value)}
        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        <option value="">All Intents</option>
        {INTENT_OPTIONS.map((it) => (
          <option key={it} value={it}>
            {it.replace(/_/g, ' ')}
          </option>
        ))}
      </select>

      {/* Region Filter */}
      <select
        value={filters.region ?? ''}
        onChange={(e) => handleFilterChange('region', e.target.value)}
        className="px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
      >
        <option value="">All Regions</option>
        {availableRegions.map((rg) => (
          <option key={rg} value={rg}>
            {rg}
          </option>
        ))}
      </select>

      {/* Clear Filters */}
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClear}
          className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-700/60 hover:bg-slate-700 rounded transition-colors"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Clear
        </button>
      )}
    </div>
  );
};
