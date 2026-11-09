import React from 'react';
import { useNavigate } from 'react-router-dom';
import { formatDistanceToNow, parseISO } from 'date-fns';
import type { Ticket } from '../api/types';
import { PriorityBadge } from './PriorityBadge';
import { StatusBadge } from './StatusBadge';
import { IntentBadge } from './IntentBadge';
import { SLAChip } from './SLAChip';
import { LoadingSpinner } from './LoadingSpinner';
import { EmptyState } from './EmptyState';
import { ErrorState } from './ErrorState';

interface TicketTableProps {
  tickets: Ticket[] | undefined;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  onRetry?: () => void;
  emptyTitle?: string;
  emptyMessage?: string;
}

export const TicketTable: React.FC<TicketTableProps> = ({
  tickets,
  isLoading,
  isError,
  errorMessage,
  onRetry,
  emptyTitle = 'No tickets found',
  emptyMessage = 'There are no tickets matching your current view or filter criteria.',
}) => {
  const navigate = useNavigate();

  if (isLoading) {
    return (
      <div className="bg-slate-800/60 rounded-lg border border-slate-700 min-h-[300px] flex items-center justify-center">
        <LoadingSpinner message="Loading queue tickets..." />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-slate-800/60 rounded-lg border border-slate-700 min-h-[250px] p-6">
        <ErrorState message={errorMessage} onRetry={onRetry} />
      </div>
    );
  }

  if (!tickets || tickets.length === 0) {
    return (
      <div className="bg-slate-800/60 rounded-lg border border-slate-700 min-h-[250px] p-6">
        <EmptyState title={emptyTitle} message={emptyMessage} />
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-slate-700 bg-slate-800/90 shadow-sm">
      <table className="w-full text-left border-collapse text-sm">
        <thead>
          <tr className="border-b border-slate-700 bg-slate-900/80 text-xs font-semibold text-slate-400 uppercase tracking-wider">
            <th scope="col" className="py-2.5 px-3">Priority</th>
            <th scope="col" className="py-2.5 px-3">Title</th>
            <th scope="col" className="py-2.5 px-3">TBOH</th>
            <th scope="col" className="py-2.5 px-3">Agency</th>
            <th scope="col" className="py-2.5 px-3">Intent</th>
            <th scope="col" className="py-2.5 px-3">Status</th>
            <th scope="col" className="py-2.5 px-3">SLA</th>
            <th scope="col" className="py-2.5 px-3">Assignee</th>
            <th scope="col" className="py-2.5 px-3">Region</th>
            <th scope="col" className="py-2.5 px-3 text-right">Updated</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-700/60">
          {tickets.map((ticket) => {
            let relativeUpdated = '';
            try {
              relativeUpdated = formatDistanceToNow(parseISO(ticket.updated_at), { addSuffix: true });
            } catch {
              relativeUpdated = ticket.updated_at;
            }

            return (
              <tr
                key={ticket.id}
                onClick={() => navigate(`/tickets/${ticket.id}`)}
                className="hover:bg-slate-700/50 cursor-pointer transition-colors group"
              >
                {/* Priority */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <PriorityBadge priority={ticket.priority} />
                </td>

                {/* Title */}
                <td className="py-2 px-3 max-w-[280px]">
                  <div className="font-medium text-slate-100 group-hover:text-indigo-300 transition-colors truncate">
                    {ticket.title}
                  </div>
                  {ticket.contact_count > 1 && (
                    <span className="inline-block mt-0.5 text-[10px] font-semibold text-amber-400 bg-amber-950/70 border border-amber-600/40 px-1.5 py-0.2 rounded">
                      Repeat #{ticket.contact_count}
                    </span>
                  )}
                </td>

                {/* TBOH */}
                <td className="py-2 px-3 whitespace-nowrap font-mono text-xs text-indigo-300">
                  {ticket.tboh}
                </td>

                {/* Agency */}
                <td className="py-2 px-3 whitespace-nowrap text-slate-300 text-xs truncate max-w-[140px]">
                  {ticket.agency_name ?? ticket.agency_id}
                </td>

                {/* Intent */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <IntentBadge intent={ticket.intent} />
                </td>

                {/* Status */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <StatusBadge status={ticket.status} />
                </td>

                {/* SLA */}
                <td className="py-2 px-3 whitespace-nowrap">
                  <SLAChip status={ticket.sla_status} />
                </td>

                {/* Assignee */}
                <td className="py-2 px-3 whitespace-nowrap text-xs text-slate-300">
                  {ticket.assignee_name ?? (
                    <span className="text-slate-500 italic">Unassigned</span>
                  )}
                </td>

                {/* Region */}
                <td className="py-2 px-3 whitespace-nowrap text-xs text-slate-300">
                  <span className="px-1.5 py-0.5 rounded bg-slate-700/50 text-slate-300 border border-slate-600/40">
                    {ticket.region}
                  </span>
                </td>

                {/* Updated At */}
                <td className="py-2 px-3 whitespace-nowrap text-right text-xs text-slate-400 font-mono">
                  {relativeUpdated}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
