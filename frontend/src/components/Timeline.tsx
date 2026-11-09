import React from 'react';
import { formatDistanceToNow, parseISO } from 'date-fns';
import {
  Activity,
  AlertOctagon,
  ArrowRightLeft,
  CheckCircle,
  FileText,
  Mail,
  Link2,
  ShieldCheck,
  UserCheck,
} from 'lucide-react';
import type { TimelineEvent } from '../api/types';

interface TimelineProps {
  events: TimelineEvent[];
  className?: string;
}

function getEventIcon(eventType: string) {
  switch (eventType) {
    case 'status_change':
      return <ArrowRightLeft className="w-4 h-4 text-sky-400" />;
    case 'assignment':
      return <UserCheck className="w-4 h-4 text-emerald-400" />;
    case 'escalation':
      return <AlertOctagon className="w-4 h-4 text-rose-400" />;
    case 'note':
    case 'ticket_comment':
      return <FileText className="w-4 h-4 text-amber-400" />;
    case 'ticket_link':
      return <Link2 className="w-4 h-4 text-cyan-400" />;
    case 'side_convo_recipients_preserved':
    case 'recipients_preserved':
      return <ShieldCheck className="w-4 h-4 text-indigo-400" />;
    case 'side_convo':
    case 'side_conversation_created':
    case 'side_message_sent':
      return <Mail className="w-4 h-4 text-purple-400" />;
    case 'created':
      return <CheckCircle className="w-4 h-4 text-green-400" />;
    default:
      return <Activity className="w-4 h-4 text-slate-400" />;
  }
}

function getEventDescription(event: TimelineEvent): React.ReactNode {
  const p = event.payload || {};

  switch (event.event_type) {
    case 'status_change':
      if (p.from == null && p.to === 'New') return <span>Ticket created</span>;
      return (
        <span>
          Status changed from{' '}
          <span className="font-semibold text-slate-200">{String(p.from ?? 'Previous')}</span> to{' '}
          <span className="font-semibold text-indigo-300">{String(p.to ?? 'New')}</span>
          {Boolean(p.note) && <span className="block mt-1 text-slate-400 text-xs italic">"{String(p.note)}"</span>}
        </span>
      );
    case 'assignment':
      return (
        <span>
          Assigned to{' '}
          <span className="font-semibold text-emerald-300">
            {String(p.agent_name ?? p.assignee_name ?? p.assigned_to ?? p.assignee_id ?? 'Agent')}
          </span>{' '}
          by{' '}
          <span className="text-slate-300 font-medium">{event.actor_name ?? 'System'}</span>
          {Boolean(p.note) && <span className="block mt-1 text-slate-400 text-xs italic">"{String(p.note)}"</span>}
        </span>
      );
    case 'escalation':
      return (
        <span>
          Escalated to{' '}
          <span className="font-semibold text-rose-300">
            {String(p.em_name ?? p.escalation_manager_name ?? p.escalated_to ?? p.escalation_manager_id ?? 'Escalation Manager')}
          </span>{' '}
          by{' '}
          <span className="text-slate-300 font-medium">{event.actor_name ?? 'Agent'}</span>
          {Boolean(p.reason) && (
            <span className="block mt-1.5 p-2 rounded bg-rose-950/40 border border-rose-900/60 text-rose-200 text-xs">
              Reason: {String(p.reason)}
            </span>
          )}
        </span>
      );
    case 'note':
      return (
        <div>
          <span className="text-amber-200 font-medium">Internal Note Added</span>
          <div className="mt-1 p-2 bg-slate-900/60 rounded border border-slate-700/60 text-slate-200 text-xs">
            {String(p.body ?? p.note ?? 'Note details')}
          </div>
        </div>
      );
    case 'ticket_comment':
      return (
        <div>
          <span className="text-amber-200 font-medium">{p.visibility === 'internal' ? 'Internal note added' : 'Public comment added'}</span>
          <div className="mt-1 text-slate-300 text-xs">{String(p.preview ?? 'Comment recorded')}</div>
        </div>
      );
    case 'recipients_preserved':
    case 'side_convo_recipients_preserved':
      return (
        <span>
          <span className="text-indigo-300 font-medium">Recipients Preserved: </span>
          Side conversation recipients preserved after transfer
        </span>
      );
    case 'side_convo':
      return p.action === 'new_message' ? (
        <span>Added a {String(p.message_kind ?? 'external')} message to a side conversation</span>
      ) : (
        <span>
          Started {String(p.kind ?? 'supplier')} side conversation{' '}
          <span className="font-semibold text-purple-300">"{String(p.subject ?? 'Side Thread')}"</span>
          {Array.isArray(p.recipients) && <span className="block mt-1 text-slate-400 text-xs">Recipients: {p.recipients.map(String).join(', ')}</span>}
        </span>
      );
    case 'side_conversation_created':
      return <span>Started side conversation "{String(p.subject ?? 'Side Thread')}"</span>;
    case 'side_message_sent':
      return <span>Sent a message to side thread "{String(p.subject ?? 'Side Thread')}"</span>;
    case 'ticket_link':
      return (
        <span>
          Linked case <span className="font-semibold text-cyan-300">{String(p.target_title ?? p.target_ticket_id ?? 'Related ticket')}</span>
          <span className="block mt-1 text-slate-400 text-xs">{String(p.link_type ?? 'related')} · {String(p.reason ?? 'Related case')}</span>
        </span>
      );
    case 'unassignment':
      return <span>Ticket returned to the unassigned Triage queue</span>;
    case 'routing_unassigned':
      return <span>No eligible agent; ticket remains in Triage. {String(p.reason ?? '')}</span>;
    case 'created':
      return <span>Ticket created</span>;
    default:
      return (
        <span>
          {event.event_type.replace(/_/g, ' ')}
          {Object.keys(p).length > 0 && (
            <span className="text-slate-400 text-xs block mt-0.5">
              {JSON.stringify(p)}
            </span>
          )}
        </span>
      );
  }
}

export const Timeline: React.FC<TimelineProps> = ({ events, className = '' }) => {
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-8 text-xs text-slate-400 bg-slate-900/30 rounded border border-slate-800">
        No timeline events recorded yet.
      </div>
    );
  }

  // Sort newest first
  const sorted = [...events].sort((a, b) => {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });

  return (
    <div className={`flow-root ${className}`}>
      <ul className="-mb-8">
        {sorted.map((event, eventIdx) => {
          let timeAgo = '';
          try {
            timeAgo = formatDistanceToNow(parseISO(event.created_at), { addSuffix: true });
          } catch {
            timeAgo = event.created_at;
          }

          return (
            <li key={event.id || eventIdx}>
              <div className="relative pb-8">
                {eventIdx !== sorted.length - 1 ? (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-slate-800"
                    aria-hidden="true"
                  />
                ) : null}
                <div className="relative flex space-x-3 items-start">
                  <div>
                    <span className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center ring-4 ring-slate-900">
                      {getEventIcon(event.event_type)}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                    <div className="text-xs text-slate-300">
                      <div className="text-xs">{getEventDescription(event)}</div>
                      <div className="mt-1 text-[11px] text-slate-400">
                        by <span className="text-slate-300 font-medium">{event.actor_name ?? 'System'}</span>
                      </div>
                    </div>
                    <div className="text-right text-[11px] whitespace-nowrap text-slate-400">
                      <time dateTime={event.created_at}>{timeAgo}</time>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
