export type Role = 'requester' | 'agent' | 'escalation_manager' | 'lead';
export type Priority = 'P1' | 'P2' | 'P3' | 'P4';
export type TicketStatus = 'New' | 'Open' | 'Pending' | 'Escalated' | 'Resolved' | 'Closed';
export type Intent = 'refund' | 'cancellation' | 'amendment' | 'voucher' | 'inventory_sync' | 'payment' | 'special_request' | 'supplier_issue' | 'other';
export type SLAStatus = 'ok' | 'at_risk' | 'breached';
export type LinkType = 'strong' | 'medium' | 'weak';
export type MessageKind = 'internal' | 'external';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  region?: string;
  agency_id?: string;
}

export interface Agency {
  id: string;
  name: string;
  region: string;
}

export interface Ticket {
  id: string;
  title: string;
  description: string;
  agency_id: string;
  agency_name?: string;
  tboh: string;
  priority: Priority;
  intent: Intent;
  status: TicketStatus;
  assignee_id?: string;
  assignee_name?: string;
  region: string;
  check_in_date?: string;
  lcd?: string;
  sla_due?: string;
  sla_status: SLAStatus;
  routing_reason?: string;
  contact_count: number;
  created_at: string;
  updated_at: string;
  product_bug_link?: string;
}

export interface TicketLink {
  id: string;
  source_id: string;
  target_id: string;
  linked_ticket: Ticket;
  link_type: LinkType;
  reason: string;
  score: number;
}

export interface TimelineEvent {
  id: string;
  ticket_id: string;
  actor_name?: string;
  event_type: string;
  payload: Record<string, unknown>;
  created_at: string;
}

export interface SideRecipient {
  id: string;
  email: string;
  name?: string;
}

export interface SideMessage {
  id: string;
  author_name: string;
  body: string;
  kind: MessageKind;
  sent_at: string;
}

export interface SideConversation {
  id: string;
  ticket_id: string;
  subject: string;
  kind: 'supplier' | 'agency';
  created_by_id: string;
  created_at: string;
  recipients: SideRecipient[];
  messages: SideMessage[];
}

export interface IntentSuggestion {
  intent: Intent;
  confidence: number;
}

export interface Theme {
  theme_name: string;
  count: number;
  sample_tickets: Array<Pick<Ticket, 'id' | 'title' | 'tboh' | 'priority' | 'status' | 'created_at' | 'agency_id' | 'agency_name'>>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface TicketFilters {
  status?: TicketStatus | string;
  intent?: Intent | string;
  region?: string;
  priority?: Priority | string;
  tboh?: string;
  assignee_id?: string;
  unassigned?: boolean;
  page?: number;
  page_size?: number;
  has_links?: boolean;
}

export interface CreateTicketPayload {
  title: string;
  description: string;
  agency_id?: string;
  tboh: string;
  priority: Priority;
  intent: Intent;
  region: string;
  check_in_date?: string;
  lcd?: string;
  product_bug_link?: string;
}

export interface CreateTicketResponse {
  ticket: Ticket;
  routing_reason?: string;
  assigned_agent_name?: string;
  links?: TicketLink[];
}

export interface UpdateTicketPayload {
  title?: string;
  description?: string;
  priority?: Priority;
  intent?: Intent;
  check_in_date?: string;
  lcd?: string;
  product_bug_link?: string | null;
}

export interface TransitionPayload {
  status: TicketStatus;
  note?: string;
}

export interface AssignPayload {
  assignee_id: string;
  note?: string;
}

export interface EscalatePayload {
  escalation_manager_id: string;
  reason: string;
}

export interface CreateSideConversationPayload {
  subject: string;
  kind: 'supplier' | 'agency';
  recipients: Array<{ email: string; name?: string }>;
  initial_message: string;
  kind_message?: MessageKind;
}

export interface AddSideMessagePayload {
  body: string;
  kind: MessageKind;
}

export interface ExportFilterParams {
  status?: string;
  intent?: string;
  region?: string;
  priority?: string;
  start_date?: string;
  end_date?: string;
}

export interface TicketComment {
  id: string; ticket_id: string; author_id?: string; author_name: string; body: string; visibility: 'internal' | 'public'; created_at: string;
}
export interface CreateTicketCommentPayload { body: string; visibility: 'internal' | 'public'; }
