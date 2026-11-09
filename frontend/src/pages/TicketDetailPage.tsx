import React, { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { formatDistanceToNow, parseISO } from 'date-fns';
import {
  AlertOctagon,
  ArrowLeft,
  Clock,
  Flame,
  Link2,
  Mail,
  MessageSquare,
  Plus,
  Send,
  X,
} from 'lucide-react';
import {
  useAddMessage,
  useAssignTicket,
  useCreateSideConversation,
  useEscalateTicket,
  useSideConversations,
  useTicket,
  useTicketLinks,
  useTimeline,
  useTransitionTicket,
  useUpdateTicket,
  useUsers,
  useTicketComments,
  useAddTicketComment,
  useUnassignTicket,
} from '../api/queries';
import type {
  MessageKind,
  TicketStatus,
} from '../api/types';
import { useAuth } from '../store/auth';
import { Nav } from '../components/Nav';
import { SLAChip } from '../components/SLAChip';
import { PriorityBadge } from '../components/PriorityBadge';
import { StatusBadge } from '../components/StatusBadge';
import { IntentBadge } from '../components/IntentBadge';
import { ContactBanner } from '../components/ContactBanner';
import { Timeline } from '../components/Timeline';
import { LinkCard } from '../components/LinkCard';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

const ALL_STATUSES: TicketStatus[] = [
  'New',
  'Open',
  'Pending',
  'Escalated',
  'Resolved',
  'Closed',
];

export const TicketDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user, isRole } = useAuth();

  // Queries
  const { data: ticket, isLoading, isError, error, refetch } = useTicket(id);
  const { data: links = [] } = useTicketLinks(id);
  const { data: timelineEvents = [] } = useTimeline(id);
  const { data: sideConversations = [] } = useSideConversations(id, Boolean(user && user.role !== 'requester'));
  const { data: ticketComments = [] } = useTicketComments(id);
  const { data: agents = [] } = useUsers('agent', Boolean(user && user.role !== 'requester'));
  const { data: escalationManagers = [] } = useUsers('escalation_manager', Boolean(user && user.role !== 'requester'));

  // Mutations
  const transitionMutation = useTransitionTicket();
  const updateTicketMutation = useUpdateTicket();
  const assignMutation = useAssignTicket();
  const escalateMutation = useEscalateTicket();
  const createSideConvoMutation = useCreateSideConversation();
  const addMessageMutation = useAddMessage();
  const addTicketCommentMutation = useAddTicketComment();
  const unassignMutation = useUnassignTicket();

  // Active Tab: timeline | side_convos | notes
  const [activeTab, setActiveTab] = useState<'timeline' | 'side_convos' | 'notes' | 'public_comments'>('timeline');

  // Actions card states
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus>('Open');
  const [statusNote, setStatusNote] = useState('');
  const [selectedAgentId, setSelectedAgentId] = useState<string>('');
  const [productBugLink, setProductBugLink] = useState('');

  // Escalation Modal state
  const [showEscalateModal, setShowEscalateModal] = useState(false);
  const [escalateManagerId, setEscalateManagerId] = useState('');
  const [escalateReason, setEscalateReason] = useState('');

  // New Side Conversation Modal state
  const [showSideConvoModal, setShowSideConvoModal] = useState(false);
  const [convoSubject, setConvoSubject] = useState('');
  const [convoKind, setConvoKind] = useState<'supplier' | 'agency'>('supplier');
  const [recipientInput, setRecipientInput] = useState('');
  const [convoRecipients, setConvoRecipients] = useState<string[]>([]);
  const [convoInitialMessage, setConvoInitialMessage] = useState('');
  const [convoMessageKind] = useState<MessageKind>('external');

  // Reply state in active side conversation
  const [replyBody, setReplyBody] = useState<Record<string, string>>({});

  // Internal Note form state in Notes tab
  const [newNoteBody, setNewNoteBody] = useState('');
  const [newPublicComment, setNewPublicComment] = useState('');

  useEffect(() => {
    setProductBugLink(ticket?.product_bug_link ?? '');
  }, [ticket?.product_bug_link]);

  // Sorting links by score
  const sortedLinks = useMemo(() => {
    return [...links].sort((a, b) => b.score - a.score);
  }, [links]);

  // Ticket comments are first-class records, separate from supplier/agency side conversations.
  const internalNotes = useMemo(() => ticketComments.filter((c) => c.visibility === 'internal').map((c) => ({
    id: c.id, author: c.author_name, body: c.body, date: c.created_at,
  })), [ticketComments]);
  const publicComments = useMemo(() => ticketComments.filter((c) => c.visibility === 'public').map((c) => ({
    id: c.id, author: c.author_name, body: c.body, date: c.created_at,
  })), [ticketComments]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen bg-slate-900 text-slate-100">
        <Nav />
        <main className="flex-1 flex items-center justify-center">
          <LoadingSpinner message="Loading Case 360 record..." />
        </main>
      </div>
    );
  }

  if (isError || !ticket) {
    return (
      <div className="flex min-h-screen bg-slate-900 text-slate-100">
        <Nav />
        <main className="flex-1 p-8 flex items-center justify-center">
          <ErrorState
            message={error instanceof Error ? error.message : 'Ticket not found or failed to load.'}
            onRetry={() => refetch()}
          />
        </main>
      </div>
    );
  }

  // Save optional product / bug tracker reference (staff-only field).
  const handleSaveProductBugLink = async () => {
    if (!id) return;
    await updateTicketMutation.mutateAsync({
      id,
      payload: { product_bug_link: productBugLink.trim() || null },
    });
  };

  // Handle status transition
  const handleTransition = async () => {
    if (!id) return;
    try {
      await transitionMutation.mutateAsync({
        id,
        payload: {
          status: selectedStatus,
          note: statusNote || undefined,
        },
      });
      setStatusNote('');
    } catch (err) {
      console.error(err);
    }
  };

  // Handle assign
  const handleAssign = async () => {
    if (!id || !selectedAgentId) return;
    try {
      await assignMutation.mutateAsync({
        id,
        payload: { assignee_id: selectedAgentId },
      });
    } catch (err) {
      console.error(err);
    }
  };

  // Handle escalate
  const handleEscalateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !escalateReason.trim()) return;
    const managerId = escalateManagerId || (escalationManagers[0]?.id ?? 'em_1');
    try {
      await escalateMutation.mutateAsync({
        id,
        payload: {
          escalation_manager_id: managerId,
          reason: escalateReason.trim(),
        },
      });
      setShowEscalateModal(false);
      setEscalateReason('');
    } catch (err) {
      console.error(err);
    }
  };

  // Recipient input tag handling
  const handleAddRecipient = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const val = recipientInput.trim().replace(',', '');
      if (val && !convoRecipients.includes(val)) {
        setConvoRecipients([...convoRecipients, val]);
        setRecipientInput('');
      }
    }
  };

  const handleRemoveRecipient = (email: string) => {
    setConvoRecipients(convoRecipients.filter((r) => r !== email));
  };

  // Submit new side conversation
  const handleCreateSideConvo = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !convoSubject.trim() || !convoInitialMessage.trim()) return;

    try {
      await createSideConvoMutation.mutateAsync({
        ticketId: id,
        payload: {
          subject: convoSubject.trim(),
          kind: convoKind,
          recipients: convoRecipients.map((em) => ({ email: em })),
          initial_message: convoInitialMessage.trim(),
          kind_message: convoMessageKind,
        },
      });
      setShowSideConvoModal(false);
      setConvoSubject('');
      setConvoRecipients([]);
      setConvoInitialMessage('');
      setRecipientInput('');
    } catch (err) {
      console.error(err);
    }
  };

  // Reply in side convo
  const handleSendReply = async (convoId: string, kind: MessageKind = 'external') => {
    if (!id) return;
    const body = replyBody[convoId]?.trim();
    if (!body) return;

    try {
      await addMessageMutation.mutateAsync({
        ticketId: id,
        conversationId: convoId,
        payload: { body, kind },
      });
      setReplyBody({ ...replyBody, [convoId]: '' });
    } catch (err) {
      console.error(err);
    }
  };

  // Add a customer-visible update to the durable ticket conversation.
  const handleAddPublicComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newPublicComment.trim()) return;
    await addTicketCommentMutation.mutateAsync({
      ticketId: id,
      payload: { body: newPublicComment.trim(), visibility: 'public' },
    });
    setNewPublicComment('');
  };

  // Add a persistent ticket-level internal note.
  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !newNoteBody.trim()) return;
    await addTicketCommentMutation.mutateAsync({ ticketId: id, payload: { body: newNoteBody.trim(), visibility: 'internal' } });
    setNewNoteBody('');
  };

  const isAgentOrLead = isRole('agent', 'lead');
  const isEM = isRole('escalation_manager', 'lead');

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Nav />

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <Link
              to="/tickets"
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs text-indigo-400 font-semibold">{ticket.tboh}</span>
                <span className="text-slate-600">•</span>
                <h1 className="text-base font-bold text-white tracking-tight truncate max-w-xl">
                  {ticket.title}
                </h1>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <PriorityBadge priority={ticket.priority} />
            <StatusBadge status={ticket.status} />
            <SLAChip status={ticket.sla_status} />
          </div>
        </header>

        {/* 2/3 and 1/3 Case 360 Grid */}
        <div className="p-6 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto w-full">
          {/* ================= LEFT COLUMN (8 cols = 2/3) ================= */}
          <div className="lg:col-span-8 space-y-5">
            {/* Contact Banner: KEY DEMO FEATURE */}
            <ContactBanner
              contactCount={ticket.contact_count}
              intent={ticket.intent}
              agencyName={ticket.agency_name}
            />

            {/* Ticket Header & Description Card */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-700/60 pb-3 mb-4">
                <div className="flex items-center gap-2">
                  <IntentBadge intent={ticket.intent} />
                  <span className="text-xs text-slate-400">
                    Agency: <span className="text-slate-200 font-medium">{ticket.agency_name ?? ticket.agency_id}</span>
                  </span>
                </div>
                <div className="text-xs text-slate-400 font-mono">
                  Created {ticket.created_at ? formatDistanceToNow(parseISO(ticket.created_at), { addSuffix: true }) : ''}
                </div>
              </div>

              <div className="prose prose-invert max-w-none text-sm text-slate-200 leading-relaxed whitespace-pre-line">
                {ticket.description}
              </div>
            </div>

            {/* Tabs for Timeline | Side Conversations | Notes */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
              <div className="flex border-b border-slate-700 bg-slate-900/60 px-4 pt-2">
                <button
                  type="button"
                  onClick={() => setActiveTab('timeline')}
                  className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    activeTab === 'timeline'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80 rounded-t-lg'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>Timeline ({timelineEvents.length})</span>
                </button>

                <button
                  type="button"
                  onClick={() => setActiveTab('public_comments')}
                  className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    activeTab === 'public_comments'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80 rounded-t-lg'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Public Updates ({publicComments.length})</span>
                </button>

                {user?.role !== 'requester' && <button
                  type="button"
                  onClick={() => setActiveTab('side_convos')}
                  className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    activeTab === 'side_convos'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80 rounded-t-lg'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <Mail className="w-3.5 h-3.5" />
                  <span>Side Conversations ({sideConversations.length})</span>
                </button>}

                {user?.role !== 'requester' && <button
                  type="button"
                  onClick={() => setActiveTab('notes')}
                  className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                    activeTab === 'notes'
                      ? 'border-indigo-500 text-indigo-300 bg-slate-800/80 rounded-t-lg'
                      : 'border-transparent text-slate-400 hover:text-slate-200'
                  }`}
                >
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Internal Notes ({internalNotes.length})</span>
                </button>}
              </div>

              <div className="p-5">
                {/* 1. Timeline Tab */}
                {activeTab === 'timeline' && (
                  <div>
                    <Timeline events={timelineEvents} />
                  </div>
                )}

                {/* 2. Side Conversations Tab */}
                {activeTab === 'side_convos' && (
                  <div className="space-y-6">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-700/60">
                      <div>
                        <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                          Dedicated Side Threads
                        </h3>
                        <p className="text-[11px] text-slate-400">
                          External supplier & agency correspondence. Recipients are independent of ticket group.
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={() => setShowSideConvoModal(true)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold shadow-sm transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Start Side Thread</span>
                      </button>
                    </div>

                    {sideConversations.length === 0 ? (
                      <EmptyState
                        icon={<Mail className="w-6 h-6 text-slate-400" />}
                        title="No side conversations yet"
                        message="Start a supplier inquiry or agency alignment thread without exposing ticket group notes."
                        actionLabel="Create Side Conversation"
                        onAction={() => setShowSideConvoModal(true)}
                      />
                    ) : (
                      <div className="space-y-4">
                        {sideConversations.map((convo) => (
                          <div
                            key={convo.id}
                            className="bg-slate-900/80 rounded-lg border border-slate-700 overflow-hidden"
                          >
                            {/* Convo Header */}
                            <div className="p-3 bg-slate-800/90 border-b border-slate-700 flex flex-wrap items-center justify-between gap-2">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${
                                    convo.kind === 'supplier'
                                      ? 'bg-amber-950 text-amber-300 border border-amber-700/60'
                                      : 'bg-indigo-950 text-indigo-300 border border-indigo-700/60'
                                  }`}
                                >
                                  {convo.kind}
                                </span>
                                <span className="text-xs font-bold text-white">{convo.subject}</span>
                              </div>

                              {/* Recipients Chips */}
                              <div className="flex flex-wrap items-center gap-1.5">
                                <span className="text-[11px] text-slate-400">Recipients:</span>
                                {convo.recipients.map((rec) => (
                                  <span
                                    key={rec.email}
                                    className="px-2 py-0.5 rounded-full text-[11px] bg-slate-700 text-slate-200 border border-slate-600 font-mono"
                                  >
                                    {rec.name ? `${rec.name} <${rec.email}>` : rec.email}
                                  </span>
                                ))}
                              </div>
                            </div>

                            {/* Convo Messages */}
                            <div className="p-3 space-y-3 max-h-[350px] overflow-y-auto">
                              {convo.messages.map((msg) => (
                                <div
                                  key={msg.id}
                                  className={`p-3 rounded-lg border text-xs leading-relaxed ${
                                    msg.kind === 'internal'
                                      ? 'bg-amber-950/20 border-amber-700/40 text-amber-100 ml-4'
                                      : 'bg-slate-800/70 border-slate-700 text-slate-200 mr-4'
                                  }`}
                                >
                                  <div className="flex items-center justify-between mb-1 text-[11px] text-slate-400">
                                    <span className="font-semibold text-slate-300">{msg.author_name}</span>
                                    <span>
                                      {msg.sent_at
                                        ? formatDistanceToNow(parseISO(msg.sent_at), { addSuffix: true })
                                        : ''}
                                    </span>
                                  </div>
                                  <div className="whitespace-pre-line">{msg.body}</div>
                                </div>
                              ))}
                            </div>

                            {/* Reply Input */}
                            <div className="p-3 bg-slate-850 border-t border-slate-700/80 flex gap-2">
                              <input
                                type="text"
                                value={replyBody[convo.id] || ''}
                                onChange={(e) =>
                                  setReplyBody({ ...replyBody, [convo.id]: e.target.value })
                                }
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSendReply(convo.id);
                                  }
                                }}
                                placeholder="Type a message to recipients..."
                                className="flex-1 px-3 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                              />
                              <button
                                type="button"
                                onClick={() => handleSendReply(convo.id)}
                                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold flex items-center gap-1 transition-colors"
                              >
                                <Send className="w-3 h-3" />
                                <span>Send</span>
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Notes Tab */}
                {activeTab === 'public_comments' && (
                  <div className="space-y-5">
                    <form onSubmit={handleAddPublicComment} className="p-4 bg-slate-900/60 rounded-lg border border-slate-700">
                      <label className="block text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-1.5">
                        Add Public Update
                      </label>
                      <textarea
                        rows={3}
                        required
                        maxLength={10000}
                        value={newPublicComment}
                        onChange={(e) => setNewPublicComment(e.target.value)}
                        placeholder="Share a booking update or additional information visible to the agency…"
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                      />
                      <div className="mt-2 flex justify-end">
                        <button
                          type="submit"
                          disabled={addTicketCommentMutation.isPending || !newPublicComment.trim()}
                          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-md text-xs font-semibold transition-colors shadow-sm disabled:opacity-50"
                        >
                          {addTicketCommentMutation.isPending ? 'Posting…' : 'Post Public Update'}
                        </button>
                      </div>
                      {addTicketCommentMutation.isError && <p className="mt-2 text-xs text-rose-300" role="alert">Could not post the public update. Please retry.</p>}
                    </form>

                    {publicComments.length === 0 ? (
                      <EmptyState
                        icon={<MessageSquare className="w-6 h-6 text-slate-400" />}
                        title="No public updates yet"
                        message="New updates posted here are visible to the agency and appear in the case timeline."
                      />
                    ) : (
                      <div className="space-y-3">
                        {publicComments.map((comment) => (
                          <div key={comment.id} className="p-3.5 bg-indigo-950/20 border border-indigo-700/40 rounded-lg text-xs">
                            <div className="flex items-center justify-between mb-1.5 text-indigo-300/80">
                              <span className="font-semibold text-indigo-200">{comment.author}</span>
                              <span className="text-[11px] font-mono">{comment.date ? formatDistanceToNow(parseISO(comment.date), { addSuffix: true }) : ''}</span>
                            </div>
                            <div className="text-slate-200 whitespace-pre-line leading-relaxed">{comment.body}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'notes' && (
                  <div className="space-y-5">
                    {/* New Note Form */}
                    <form onSubmit={handleAddNote} className="p-4 bg-slate-900/60 rounded-lg border border-slate-700">
                      <label className="block text-xs font-semibold text-amber-300 uppercase tracking-wider mb-1.5">
                        Add Internal Note
                      </label>
                      <textarea
                        rows={3}
                        required
                        value={newNoteBody}
                        onChange={(e) => setNewNoteBody(e.target.value)}
                        placeholder="Internal notes are private to ops team and never shared with agencies or suppliers..."
                        className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-amber-500"
                      />
                      <div className="mt-2 flex justify-end">
                        <button
                          type="submit"
                          disabled={addTicketCommentMutation.isPending}
                          className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-md text-xs font-semibold transition-colors shadow-sm"
                        >
                          Post Internal Note
                        </button>
                      </div>
                    </form>

                    {/* Internal Notes List */}
                    {internalNotes.length === 0 ? (
                      <EmptyState
                        icon={<MessageSquare className="w-6 h-6 text-slate-400" />}
                        title="No internal notes recorded"
                        message="Add internal handover comments, supplier escalation observations, or supervisor approvals."
                      />
                    ) : (
                      <div className="space-y-3">
                        {internalNotes.map((note) => (
                          <div
                            key={note.id}
                            className="p-3.5 bg-amber-950/20 border border-amber-700/40 rounded-lg text-xs"
                          >
                            <div className="flex items-center justify-between mb-1.5 text-amber-300/80">
                              <span className="font-semibold text-amber-200">{note.author}</span>
                              <span className="text-[11px] font-mono">
                                {note.date ? formatDistanceToNow(parseISO(note.date), { addSuffix: true }) : ''}
                              </span>
                            </div>
                            <div className="text-slate-200 whitespace-pre-line leading-relaxed">{note.body}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ================= RIGHT COLUMN (4 cols = 1/3 sidebar) ================= */}
          <div className="lg:col-span-4 space-y-5">
            {/* 1. Routing Info Card */}
            {ticket.routing_reason && (
              <div className="bg-slate-850 border border-indigo-500/50 rounded-xl p-4 shadow-lg">
                <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider mb-2">
                  <Flame className="w-4 h-4" />
                  <span>Intelligent Routing</span>
                </div>
                <div className="text-xs text-slate-200 font-medium bg-slate-900/80 p-3 rounded-lg border border-slate-700/60">
                  <span className="text-slate-400 font-normal">Routed because: </span>
                  <span className="text-indigo-300 font-semibold">{ticket.routing_reason}</span>
                </div>
              </div>
            )}

            {/* 2. Actions Card (Role-Dependent) */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 shadow-lg space-y-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
                <span>Actions & Lifecycle</span>
                <span className="text-[10px] text-slate-400 font-normal">Role: {user?.role}</span>
              </h3>

              {/* Status Transition */}
              <div className="pt-2 border-t border-slate-700/60">
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                  Update Ticket Status
                </label>
                <div className="flex gap-2">
                  <select
                    value={selectedStatus}
                    onChange={(e) => setSelectedStatus(e.target.value as TicketStatus)}
                    className="flex-1 px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  >
                    {ALL_STATUSES.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleTransition}
                    disabled={transitionMutation.isPending}
                    className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded text-xs font-semibold transition-colors"
                  >
                    {transitionMutation.isPending ? 'Saving...' : 'Apply'}
                  </button>
                </div>
              </div>

              {/* Assign / Reassign (agent / lead / em) */}
              {(isAgentOrLead || isEM) && (
                <div className="pt-2 border-t border-slate-700/60">
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Assign / Reassign Agent
                  </label>
                  <div className="flex gap-2">
                    <select
                      value={selectedAgentId}
                      onChange={(e) => setSelectedAgentId(e.target.value)}
                      className="flex-1 px-2.5 py-1.5 bg-slate-900 border border-slate-700 rounded text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select an Agent...</option>
                      {agents.map((ag) => (
                        <option key={ag.id} value={ag.id}>
                          {ag.full_name} ({ag.region ?? 'Global'})
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleAssign}
                      disabled={!selectedAgentId || assignMutation.isPending}
                      className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-40 text-white rounded text-xs font-semibold transition-colors"
                    >
                      Assign
                    </button>
                  </div>
                  {ticket.assignee_id && (isAgentOrLead || isEM) && (
                    <button type="button" onClick={() => id && unassignMutation.mutate(id)} disabled={unassignMutation.isPending}
                      className="mt-2 w-full px-3 py-2 rounded-md border border-amber-700/60 text-amber-300 hover:bg-amber-950/40 text-xs font-semibold">
                      {unassignMutation.isPending ? 'Unassigning…' : 'Return to Triage (Unassign)'}
                    </button>
                  )}
                </div>
              )}

              {/* Escalate Button (agent / lead) */}
              {isAgentOrLead && (
                <div className="pt-2 border-t border-slate-700/60">
                  <button
                    type="button"
                    onClick={() => setShowEscalateModal(true)}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-rose-950/60 hover:bg-rose-900/60 border border-rose-700/60 text-rose-300 rounded text-xs font-semibold transition-colors shadow-sm"
                  >
                    <AlertOctagon className="w-4 h-4 text-rose-400" />
                    <span>Escalate to Manager</span>
                  </button>
                </div>
              )}
            </div>

            {/* 3. SLA Card */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 shadow-lg space-y-2.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white uppercase tracking-wider">SLA Target</span>
                <SLAChip status={ticket.sla_status} />
              </div>
              <div className="text-xs text-slate-300 space-y-1 pt-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Due Time:</span>
                  <span className="font-mono text-slate-200">
                    {ticket.sla_due ? new Date(ticket.sla_due).toLocaleString() : 'Within 4 Hours'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Priority Tier:</span>
                  <span className="font-semibold text-slate-200">{ticket.priority}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Total Contacts:</span>
                  <span className={`font-semibold ${ticket.contact_count > 1 ? 'text-amber-400' : 'text-slate-200'}`}>
                    {ticket.contact_count}
                  </span>
                </div>
              </div>
            </div>

            {/* 4. Case Details Card */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
              <span className="text-xs font-bold text-white uppercase tracking-wider">Case Details</span>
              <dl className="text-xs divide-y divide-slate-700/60 space-y-2 pt-1">
                <div className="flex justify-between pt-1">
                  <dt className="text-slate-400">Agency</dt>
                  <dd className="font-medium text-slate-200">{ticket.agency_name ?? ticket.agency_id}</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-slate-400">Assignee</dt>
                  <dd className="font-medium text-slate-200">{ticket.assignee_name ?? 'Unassigned'}</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-slate-400">Region</dt>
                  <dd className="font-medium text-slate-200">{ticket.region}</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-slate-400">Intent</dt>
                  <dd className="font-medium text-slate-200 capitalize">{ticket.intent.replace(/_/g, ' ')}</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-slate-400">Check-in Date</dt>
                  <dd className="font-mono text-slate-200">{ticket.check_in_date ?? 'Not provided'}</dd>
                </div>
                <div className="flex justify-between pt-2">
                  <dt className="text-slate-400">LCD (Last Cancel)</dt>
                  <dd className="font-mono text-slate-200">{ticket.lcd ?? 'Not provided'}</dd>
                </div>
              </dl>
            </div>

            {/* Optional product / bug linkage for product feedback loop */}
            {(isAgentOrLead || isEM) && (
              <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
                <span className="text-xs font-bold text-white uppercase tracking-wider">Suggested Product / Bug</span>
                <input
                  type="url"
                  value={productBugLink}
                  onChange={(e) => setProductBugLink(e.target.value)}
                  placeholder="https://tracker.example/BUG-123"
                  maxLength={500}
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 placeholder:text-slate-500 focus:border-indigo-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={handleSaveProductBugLink}
                  disabled={updateTicketMutation.isPending}
                  className="w-full rounded-md bg-slate-700 hover:bg-slate-600 disabled:opacity-50 px-3 py-2 text-xs font-semibold text-white"
                >
                  {updateTicketMutation.isPending ? 'Saving…' : 'Save Product / Bug Link'}
                </button>
                {updateTicketMutation.isError && <p className="text-xs text-rose-300" role="alert">Could not save the product/bug link.</p>}
              </div>
            )}

            {/* 5. Linked Tickets Card */}
            <div className="bg-slate-850 border border-slate-800 rounded-xl p-4 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Link2 className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold text-white uppercase tracking-wider">
                    Linked Cases ({links.length})
                  </span>
                </div>
                <span className="text-[10px] text-slate-400">High Confidence First</span>
              </div>

              {sortedLinks.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-400 bg-slate-900/50 rounded-lg border border-slate-700/60">
                  No prior contacts or linked cases found for TBOH {ticket.tboh}.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {sortedLinks.map((lnk) => (
                    <LinkCard key={lnk.id} link={lnk} />
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ================= ESCALATION MODAL ================= */}
        {showEscalateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-850 border border-rose-700/80 rounded-xl max-w-md w-full p-6 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-700">
                <div className="flex items-center gap-2 text-rose-300 font-bold text-sm">
                  <AlertOctagon className="w-5 h-5 text-rose-400" />
                  <span>Escalate Ticket to Manager</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowEscalateModal(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleEscalateSubmit} className="mt-4 space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Escalation Manager
                  </label>
                  <select
                    value={escalateManagerId}
                    onChange={(e) => setEscalateManagerId(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:ring-1 focus:ring-rose-500"
                  >
                    {escalationManagers.map((em) => (
                      <option key={em.id} value={em.id}>
                        {em.full_name} ({em.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Escalation Reason & Context <span className="text-rose-400">*</span>
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={escalateReason}
                    onChange={(e) => setEscalateReason(e.target.value)}
                    placeholder="Specify why manager intervention is required (e.g. repeated unfulfilled refund, imminent flight check-in, high agency tier impact)..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-rose-500"
                  />
                </div>

                <div className="pt-3 border-t border-slate-700 flex justify-end gap-2.5">
                  <button
                    type="button"
                    onClick={() => setShowEscalateModal(false)}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={escalateMutation.isPending}
                    className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-xs font-semibold text-white rounded-md shadow-sm transition-colors"
                  >
                    {escalateMutation.isPending ? 'Escalating...' : 'Confirm Escalation'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ================= SIDE CONVERSATION CREATION MODAL ================= */}
        {showSideConvoModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in">
            <div className="bg-slate-850 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-700">
                <div className="flex items-center gap-2 text-indigo-300 font-bold text-sm">
                  <Mail className="w-5 h-5 text-indigo-400" />
                  <span>Start New Side Conversation</span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowSideConvoModal(false)}
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleCreateSideConvo} className="mt-4 space-y-4">
                {/* Kind Toggle */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Conversation Kind
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setConvoKind('supplier')}
                      className={`py-2 px-3 rounded-lg border text-xs font-semibold text-center transition-colors ${
                        convoKind === 'supplier'
                          ? 'bg-amber-950/80 border-amber-500 text-amber-200'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Supplier Inquiry
                    </button>
                    <button
                      type="button"
                      onClick={() => setConvoKind('agency')}
                      className={`py-2 px-3 rounded-lg border text-xs font-semibold text-center transition-colors ${
                        convoKind === 'agency'
                          ? 'bg-indigo-950/80 border-indigo-500 text-indigo-200'
                          : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Agency Alignment
                    </button>
                  </div>
                </div>

                {/* Subject */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Subject <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={convoSubject}
                    onChange={(e) => setConvoSubject(e.target.value)}
                    placeholder="e.g. Booking ref 98214 - Direct hotel supplier confirmation check"
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                {/* Recipients Multi-Input with chips */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    Recipients (Press Enter to add) <span className="text-red-400">*</span>
                  </label>
                  <div className="p-2 bg-slate-900 border border-slate-700 rounded-lg min-h-[42px] flex flex-wrap items-center gap-1.5">
                    {convoRecipients.map((rec) => (
                      <span
                        key={rec}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] bg-indigo-950 text-indigo-200 border border-indigo-700/60 font-mono"
                      >
                        <span>{rec}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveRecipient(rec)}
                          className="hover:text-red-300"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    ))}
                    <input
                      type="email"
                      value={recipientInput}
                      onChange={(e) => setRecipientInput(e.target.value)}
                      onKeyDown={handleAddRecipient}
                      placeholder={convoRecipients.length === 0 ? 'supplier@hotelops.com, press Enter...' : 'Add more...'}
                      className="flex-1 bg-transparent border-none text-xs text-slate-100 placeholder-slate-500 focus:outline-none min-w-[140px]"
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Note: Side conversation recipients are stored independently of the main ticket group.
                  </p>
                </div>

                {/* Message Body */}
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                    First Message <span className="text-red-400">*</span>
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={convoInitialMessage}
                    onChange={(e) => setConvoInitialMessage(e.target.value)}
                    placeholder="Write message to recipients..."
                    className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                {/* Submit Buttons */}
                <div className="pt-3 border-t border-slate-700 flex justify-end gap-2.5">
                  <button
                    type="button"
                    onClick={() => setShowSideConvoModal(false)}
                    className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 rounded-md"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={createSideConvoMutation.isPending || convoRecipients.length === 0}
                    className="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-semibold text-white rounded-md shadow-sm transition-colors"
                  >
                    {createSideConvoMutation.isPending ? 'Starting thread...' : 'Send Message'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};
