import React from 'react';
import type { TicketStatus } from '../api/types';

interface StatusBadgeProps {
  status: TicketStatus;
  className?: string;
}

const STATUS_CONFIG: Record<TicketStatus, { bg: string; text: string; border: string }> = {
  New: {
    bg: 'bg-sky-950/70',
    text: 'text-sky-300',
    border: 'border-sky-500/40',
  },
  Open: {
    bg: 'bg-emerald-950/70',
    text: 'text-emerald-300',
    border: 'border-emerald-500/40',
  },
  Pending: {
    bg: 'bg-amber-950/70',
    text: 'text-amber-300',
    border: 'border-amber-500/40',
  },
  Escalated: {
    bg: 'bg-rose-950/80',
    text: 'text-rose-300',
    border: 'border-rose-500/50',
  },
  Resolved: {
    bg: 'bg-violet-950/70',
    text: 'text-violet-300',
    border: 'border-violet-500/40',
  },
  Closed: {
    bg: 'bg-slate-800/90',
    text: 'text-slate-400',
    border: 'border-slate-700',
  },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className = '' }) => {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.New;

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      {status}
    </span>
  );
};
