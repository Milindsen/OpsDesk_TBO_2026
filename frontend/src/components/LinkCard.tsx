import React from 'react';
import { Link } from 'react-router-dom';
import { ExternalLink, Link2 } from 'lucide-react';
import type { LinkType, TicketLink } from '../api/types';
import { PriorityBadge } from './PriorityBadge';
import { StatusBadge } from './StatusBadge';

interface LinkCardProps {
  link: TicketLink;
  className?: string;
}

const LINK_TYPE_CONFIG: Record<
  LinkType,
  { label: string; bg: string; text: string; border: string }
> = {
  strong: {
    label: 'Strong Link',
    bg: 'bg-emerald-950/70',
    text: 'text-emerald-300',
    border: 'border-emerald-600/50',
  },
  medium: {
    label: 'Medium Link',
    bg: 'bg-amber-950/70',
    text: 'text-amber-300',
    border: 'border-amber-600/50',
  },
  weak: {
    label: 'Weak Link',
    bg: 'bg-slate-800',
    text: 'text-slate-400',
    border: 'border-slate-700',
  },
};

export const LinkCard: React.FC<LinkCardProps> = ({ link, className = '' }) => {
  const typeConfig = LINK_TYPE_CONFIG[link.link_type] ?? LINK_TYPE_CONFIG.weak;
  const ticket = link.linked_ticket;

  return (
    <div
      className={`p-3 bg-slate-850 bg-slate-800/90 rounded-lg border border-slate-700/80 hover:border-slate-600 transition-all ${className}`}
    >
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <Link2 className="w-4 h-4 text-slate-400" />
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${typeConfig.bg} ${typeConfig.text} ${typeConfig.border}`}
          >
            {typeConfig.label} ({Math.round(link.score * 100)}%)
          </span>
        </div>
        {ticket && (
          <div className="flex items-center gap-1.5">
            <PriorityBadge priority={ticket.priority} />
            <StatusBadge status={ticket.status} />
          </div>
        )}
      </div>

      {ticket ? (
        <div>
          <Link
            to={`/tickets/${ticket.id}`}
            className="group flex items-center justify-between text-sm font-medium text-slate-200 hover:text-indigo-400 transition-colors"
          >
            <span className="truncate max-w-[280px]">{ticket.title}</span>
            <ExternalLink className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100 flex-shrink-0 ml-1" />
          </Link>
          <div className="text-xs text-slate-400 mt-0.5">
            TBOH: <span className="font-mono text-slate-300">{ticket.tboh}</span> • {ticket.agency_name ?? ticket.agency_id}
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-400">Target Ticket: {link.target_id}</div>
      )}

      <div className="mt-2.5 pt-2 border-t border-slate-700/50 text-xs text-slate-300/90 leading-relaxed bg-slate-900/40 p-2 rounded">
        <span className="text-slate-400 font-medium">Link Reason: </span>
        {link.reason}
      </div>
    </div>
  );
};
