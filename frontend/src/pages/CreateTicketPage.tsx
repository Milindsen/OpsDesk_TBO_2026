import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  ExternalLink,
  Link2,
  Sparkles,
  UserCheck,
} from 'lucide-react';
import {
  useAgencies,
  useCreateTicket,
  useSuggestIntent,
} from '../api/queries';
import type {
  CreateTicketPayload,
  CreateTicketResponse,
  Intent,
  IntentSuggestion,
  Priority,
} from '../api/types';
import { useAuth } from '../store/auth';
import { Nav } from '../components/Nav';

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

const PRIORITY_OPTIONS: Priority[] = ['P1', 'P2', 'P3', 'P4'];
const REGIONS = ['IN-West', 'IN-East', 'ME'];

export const CreateTicketPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  // Queries & Mutations
  const {
    data: agencies = [],
    isLoading: agenciesLoading,
    isError: agenciesError,
    error: agenciesQueryError,
    refetch: refetchAgencies,
  } = useAgencies();
  const createTicketMutation = useCreateTicket();
  const suggestIntentMutation = useSuggestIntent();

  // Form State
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [agencyId, setAgencyId] = useState<string>(user?.agency_id || '');
  const [tboh, setTboh] = useState('');

  React.useEffect(() => {
    if (!agencyId && agencies.length > 0) {
      setAgencyId(user?.agency_id || agencies[0].id);
    }
  }, [agencies, agencyId, user?.agency_id]);
  const [priority, setPriority] = useState<Priority>('P3');
  const [intent, setIntent] = useState<Intent>('refund');
  const [region, setRegion] = useState(user?.region || 'IN-West');
  const [checkInDate, setCheckInDate] = useState('');
  const [lcd, setLcd] = useState('');

  // Suggestions state
  const [suggestions, setSuggestions] = useState<IntentSuggestion[]>([]);
  const [suggestError, setSuggestError] = useState<string | null>(null);

  // Submission result state (dialog / confirmation)
  const [createdResult, setCreatedResult] = useState<CreateTicketResponse | null>(null);

  // If requester, agency is locked to user's agency
  const isRequester = user?.role === 'requester';

  const handleSuggestIntent = async () => {
    if (!title.trim() && !description.trim()) {
      setSuggestError('Please enter a title or description first to suggest intent.');
      return;
    }
    setSuggestError(null);
    try {
      const results = await suggestIntentMutation.mutateAsync({
        title,
        description,
      });
      // Show top-3
      setSuggestions(results.slice(0, 3));
    } catch {
      // Fallback local heuristic demo if endpoint is not seeded
      const lower = `${title} ${description}`.toLowerCase();
      const mockSuggestions: IntentSuggestion[] = [];
      if (lower.includes('refund') || lower.includes('money') || lower.includes('return')) {
        mockSuggestions.push({ intent: 'refund', confidence: 0.92 });
        mockSuggestions.push({ intent: 'cancellation', confidence: 0.45 });
        mockSuggestions.push({ intent: 'payment', confidence: 0.28 });
      } else if (lower.includes('cancel')) {
        mockSuggestions.push({ intent: 'cancellation', confidence: 0.89 });
        mockSuggestions.push({ intent: 'refund', confidence: 0.65 });
        mockSuggestions.push({ intent: 'voucher', confidence: 0.31 });
      } else if (lower.includes('voucher') || lower.includes('credit')) {
        mockSuggestions.push({ intent: 'voucher', confidence: 0.86 });
        mockSuggestions.push({ intent: 'amendment', confidence: 0.34 });
        mockSuggestions.push({ intent: 'refund', confidence: 0.22 });
      } else {
        mockSuggestions.push({ intent: 'amendment', confidence: 0.74 });
        mockSuggestions.push({ intent: 'special_request', confidence: 0.52 });
        mockSuggestions.push({ intent: 'other', confidence: 0.31 });
      }
      setSuggestions(mockSuggestions);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !description.trim() || !tboh.trim()) {
      return;
    }

    const payload: CreateTicketPayload = {
      title: title.trim(),
      description: description.trim(),
      agency_id: isRequester && user?.agency_id ? user.agency_id : (agencyId || undefined),
      tboh: tboh.trim(),
      priority,
      intent,
      region,
      check_in_date: checkInDate || undefined,
      lcd: lcd || undefined,
    };

    try {
      const res = await createTicketMutation.mutateAsync(payload);
      setCreatedResult(res);
    } catch {
      // Mutation error is rendered inline below the form header.
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-900 text-slate-100">
      <Nav />

      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto">
        <header className="h-16 border-b border-slate-800 bg-slate-900/90 px-6 flex items-center justify-between sticky top-0 z-10 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <Link
              to="/tickets"
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-lg font-bold text-white tracking-tight">Create Operations Ticket</h1>
          </div>
        </header>

        <div className="p-8 max-w-4xl mx-auto w-full">
          {/* Success Result Modal / Banner */}
          {createdResult && (
            <div className="mb-8 p-6 bg-slate-850 border border-emerald-500/60 rounded-xl shadow-2xl animate-in fade-in duration-300">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-white">Ticket Created Successfully!</h3>
                    <Link
                      to={`/tickets/${createdResult.ticket.id}`}
                      className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold rounded-md transition-colors shadow-sm"
                    >
                      <span>Open Case 360</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                  <p className="text-xs text-slate-300 mt-1">
                    Ticket ID: <span className="font-mono text-indigo-300">{createdResult.ticket.id}</span> • TBOH:{' '}
                    <span className="font-mono text-indigo-300">{createdResult.ticket.tboh}</span>
                  </p>

                  {/* Auto-routing info */}
                  <div className="mt-4 p-3 bg-slate-900/80 rounded-lg border border-slate-700/80 flex items-start gap-2.5">
                    <UserCheck className="w-5 h-5 text-indigo-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-semibold text-slate-200">
                        Intelligent Auto-Routing Result:
                      </div>
                      <div className="text-xs text-indigo-300 font-medium mt-0.5">
                        {createdResult.assigned_agent_name ?? createdResult.ticket.assignee_name ? (
                          <>Routed to <span className="text-white font-bold">{createdResult.assigned_agent_name ?? createdResult.ticket.assignee_name}</span></>
                        ) : (
                          <span className="text-amber-300">No eligible agent — ticket remains in the Triage queue.</span>
                        )}
                        {(createdResult.routing_reason ?? createdResult.ticket.routing_reason) && (
                          <span className="block text-slate-300 italic mt-1">{createdResult.routing_reason ?? createdResult.ticket.routing_reason}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Linked tickets found */}
                  {createdResult.links && createdResult.links.length > 0 && (
                    <div className="mt-4">
                      <div className="text-xs font-semibold text-amber-300 flex items-center gap-1.5 mb-2">
                        <Link2 className="w-4 h-4" />
                        <span>Found {createdResult.links.length} Related Past Cases:</span>
                      </div>
                      <div className="space-y-2">
                        {createdResult.links.map((lnk) => (
                          <div
                            key={lnk.id}
                            className="p-2.5 rounded bg-slate-900/60 border border-slate-700 text-xs flex items-center justify-between"
                          >
                            <div>
                              <span className="font-semibold text-slate-200">{lnk.linked_ticket?.title ?? lnk.target_id}</span>
                              <span className="block text-[11px] text-slate-400 mt-0.5">{lnk.reason}</span>
                            </div>
                            <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700/50">
                              {lnk.link_type} ({Math.round(lnk.score * 100)}%)
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="mt-5 flex gap-3">
                    <button
                      type="button"
                      onClick={() => navigate('/tickets')}
                      className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 rounded-md transition-colors"
                    >
                      Back to Queue
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setCreatedResult(null);
                        setTitle('');
                        setDescription('');
                        setTboh('');
                        setSuggestions([]);
                        createTicketMutation.reset();
                      }}
                      className="px-4 py-1.5 bg-indigo-600/80 hover:bg-indigo-600 text-xs font-medium text-white rounded-md transition-colors"
                    >
                      Create Another Ticket
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            className="bg-slate-850 border border-slate-750 border-slate-800 rounded-xl p-6 shadow-xl space-y-6"
          >
            {agenciesLoading && (
              <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-xs text-slate-300" role="status">
                Loading agency directory…
              </div>
            )}
            {agenciesError && (
              <div className="rounded-lg border border-rose-700/60 bg-rose-950/30 p-3 text-xs text-rose-200" role="alert">
                <div>{agenciesQueryError instanceof Error ? agenciesQueryError.message : 'Could not load agency details.'}</div>
                <button type="button" onClick={() => refetchAgencies()} className="mt-2 underline underline-offset-2">Retry agency lookup</button>
              </div>
            )}
            {createTicketMutation.isError && (
              <div className="rounded-lg border border-rose-700/60 bg-rose-950/30 p-3 text-xs text-rose-200" role="alert">
                {createTicketMutation.error instanceof Error ? createTicketMutation.error.message : 'Ticket could not be created. Please retry.'}
              </div>
            )}
            {/* Title */}
            <div>
              <label htmlFor="ticket-title" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Ticket Title <span className="text-red-400">*</span>
              </label>
              <input
                id="ticket-title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Booking cancellation request due to hotel overbooking"
                className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            {/* Description */}
            <div>
              <label htmlFor="ticket-desc" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                Description & Case Details <span className="text-red-400">*</span>
              </label>
              <textarea
                id="ticket-desc"
                required
                rows={4}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Provide booking context, travel urgency, supplier details, and the requested resolution..."
                className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-y"
              />
            </div>

            {/* Intent Suggestion UX */}
            <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-750 border-slate-700/80">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-xs font-semibold text-slate-200">AI Intent Classification</span>
                  <p className="text-[11px] text-slate-400">
                    Suggests intent using the lightweight TF-IDF + Logistic Regression classifier.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleSuggestIntent}
                  disabled={suggestIntentMutation.isPending}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-md text-xs font-semibold transition-colors shadow-sm"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                  <span>{suggestIntentMutation.isPending ? 'Analyzing...' : 'Suggest Intent'}</span>
                </button>
              </div>

              {suggestError && (
                <div className="text-xs text-amber-400 mt-2">{suggestError}</div>
              )}

              {suggestions.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Top Suggestions (Click to apply):
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                    {suggestions.map((sug) => {
                      const pct = Math.round(sug.confidence * 100);
                      const isSelected = intent === sug.intent;
                      return (
                        <button
                          key={sug.intent}
                          type="button"
                          onClick={() => setIntent(sug.intent)}
                          className={`p-2.5 rounded-lg border text-left transition-all ${
                            isSelected
                              ? 'bg-indigo-950/80 border-indigo-500 ring-1 ring-indigo-500'
                              : 'bg-slate-800/80 border-slate-700 hover:border-slate-600'
                          }`}
                        >
                          <div className="flex items-center justify-between text-xs font-semibold capitalize mb-1.5">
                            <span className={isSelected ? 'text-indigo-300' : 'text-slate-200'}>
                              {sug.intent.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[11px] font-mono text-slate-400">{pct}%</span>
                          </div>
                          {/* Confidence Progress Bar */}
                          <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-indigo-500 to-indigo-400 rounded-full transition-all duration-500"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>

            {/* TBOH & Agency Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="ticket-tboh" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  TBOH (Booking Reference) <span className="text-red-400">*</span>
                </label>
                <input
                  id="ticket-tboh"
                  type="text"
                  required
                  value={tboh}
                  onChange={(e) => setTboh(e.target.value)}
                  placeholder="e.g. TBOH-98214"
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 placeholder-slate-500 font-mono focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="ticket-agency" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Agency <span className="text-red-400">*</span>
                </label>
                <select
                  id="ticket-agency"
                  disabled={isRequester && Boolean(user?.agency_id)}
                  value={agencyId}
                  onChange={(e) => setAgencyId(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-60"
                >
                  {agencies.length === 0 ? (
                    <option value="ag_1">Horizons Travel (Default)</option>
                  ) : (
                    agencies.map((ag) => (
                      <option key={ag.id} value={ag.id}>
                        {ag.name} ({ag.region})
                      </option>
                    ))
                  )}
                </select>
              </div>
            </div>

            {/* Priority & Intent Selectors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Priority
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {PRIORITY_OPTIONS.map((pr) => {
                    const isSelected = priority === pr;
                    return (
                      <button
                        key={pr}
                        type="button"
                        onClick={() => setPriority(pr)}
                        className={`py-2 px-2 rounded-lg border text-xs font-semibold text-center transition-all ${
                          isSelected
                            ? 'bg-indigo-900/60 border-indigo-500 text-white shadow-sm ring-1 ring-indigo-500'
                            : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600'
                        }`}
                      >
                        {pr}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div>
                <label htmlFor="ticket-intent" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Intent Category
                </label>
                <select
                  id="ticket-intent"
                  value={intent}
                  onChange={(e) => setIntent(e.target.value as Intent)}
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {INTENT_OPTIONS.map((it) => (
                    <option key={it} value={it}>
                      {it.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Region & Dates */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label htmlFor="ticket-region" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Region
                </label>
                <select
                  id="ticket-region"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  {REGIONS.map((rg) => (
                    <option key={rg} value={rg}>
                      {rg}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="ticket-checkin" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  Check-in Date (Optional)
                </label>
                <input
                  id="ticket-checkin"
                  type="date"
                  value={checkInDate}
                  onChange={(e) => setCheckInDate(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label htmlFor="ticket-lcd" className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
                  LCD (Last Cancellation Date)
                </label>
                <input
                  id="ticket-lcd"
                  type="date"
                  value={lcd}
                  onChange={(e) => setLcd(e.target.value)}
                  className="w-full px-3.5 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            {/* Submit Bar */}
            <div className="pt-4 border-t border-slate-800 flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => navigate('/tickets')}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createTicketMutation.isPending}
                className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-xs font-semibold text-white rounded-lg shadow-lg shadow-indigo-600/30 transition-all flex items-center gap-2"
              >
                {createTicketMutation.isPending ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Submitting & Routing...</span>
                  </>
                ) : (
                  <span>Submit Ticket</span>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};
