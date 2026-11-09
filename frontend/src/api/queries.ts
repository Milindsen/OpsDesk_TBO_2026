import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  AddSideMessagePayload,
  Agency,
  AssignPayload,
  AuthResponse,
  CreateSideConversationPayload,
  CreateTicketPayload,
  CreateTicketResponse,
  EscalatePayload,
  Theme,
  IntentSuggestion,
  PaginatedResponse,
  SideConversation,
  SideMessage,
  Ticket,
  TicketFilters,
  TicketLink,
  TimelineEvent,
  TransitionPayload,
  UpdateTicketPayload,
  User,
  TicketComment,
  CreateTicketCommentPayload,
} from './types';

// ================= AUTH =================
export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (credentials: { email: string; password?: string }) => {
      // Handles both JSON credentials and standard OAuth form if backend uses either
      const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
      return response.data;
    },
    onSuccess: (data) => {
      localStorage.setItem('opsdesk_token', data.access_token);
      localStorage.setItem('opsdesk_user', JSON.stringify(data.user));
      queryClient.setQueryData(['me'], data.user);
    },
  });
}

export function useMe() {
  return useQuery({
    queryKey: ['me'],
    queryFn: async (): Promise<User> => {
      const stored = localStorage.getItem('opsdesk_user');
      try {
        const response = await apiClient.get<User>('/me');
        localStorage.setItem('opsdesk_user', JSON.stringify(response.data));
        return response.data;
      } catch (err) {
        if (stored) {
          return JSON.parse(stored) as User;
        }
        throw err;
      }
    },
    retry: 1,
    staleTime: 5 * 60 * 1000,
  });
}

// ================= TICKETS =================
export function useTickets(filters: TicketFilters = {}) {
  return useQuery({
    queryKey: ['tickets', filters],
    queryFn: async (): Promise<PaginatedResponse<Ticket>> => {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', String(filters.status));
      if (filters.intent) params.append('intent', String(filters.intent));
      if (filters.region) params.append('region', filters.region);
      if (filters.priority) params.append('priority', String(filters.priority));
      if (filters.tboh) params.append('tboh', filters.tboh);
      if (filters.assignee_id) params.append('assignee_id', filters.assignee_id);
      if (filters.unassigned !== undefined) params.append('unassigned', String(filters.unassigned));
      if (filters.page) params.append('page', String(filters.page));
      if (filters.page_size) params.append('page_size', String(filters.page_size));
      if (filters.has_links !== undefined) params.append('has_links', String(filters.has_links));

      const response = await apiClient.get<PaginatedResponse<Ticket> | Ticket[]>('/tickets', { params });
      
      // Normalize if backend returns a plain array vs PaginatedResponse
      if (Array.isArray(response.data)) {
        return {
          items: response.data,
          total: response.data.length,
          page: 1,
          page_size: response.data.length,
        };
      }
      return response.data;
    },
    refetchInterval: 15000, // Background poll every 15s for queue freshness
  });
}

export function useTicket(id: string | undefined) {
  return useQuery({
    queryKey: ['ticket', id],
    queryFn: async (): Promise<Ticket> => {
      if (!id) throw new Error('Ticket ID is required');
      const response = await apiClient.get<Ticket>(`/tickets/${id}`);
      return response.data;
    },
    enabled: Boolean(id),
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: CreateTicketPayload): Promise<CreateTicketResponse> => {
      const response = await apiClient.post<CreateTicketResponse | Ticket>('/tickets', payload);
      // Normalize response if returns Ticket directly or CreateTicketResponse wrapper
      const data = response.data;
      if ('id' in data && !('ticket' in data)) {
        return {
          ticket: data as Ticket,
          routing_reason: (data as Ticket).routing_reason,
          assigned_agent_name: (data as Ticket).assignee_name,
        };
      }
      return data as CreateTicketResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
    },
  });
}

export function useUpdateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: UpdateTicketPayload }): Promise<Ticket> => {
      const response = await apiClient.patch<Ticket>(`/tickets/${id}`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ticket', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.id] });
    },
  });
}

export function useTransitionTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: TransitionPayload }): Promise<Ticket> => {
      const response = await apiClient.post<Ticket>(`/tickets/${id}/transition`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ticket', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.id] });
    },
  });
}

export function useAssignTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: AssignPayload }): Promise<Ticket> => {
      const response = await apiClient.post<Ticket>(`/tickets/${id}/assign`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ticket', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.id] });
    },
  });
}

export function useEscalateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, payload }: { id: string; payload: EscalatePayload }): Promise<Ticket> => {
      const response = await apiClient.post<Ticket>(`/tickets/${id}/escalate`, payload);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['ticket', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['tickets'] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.id] });
    },
  });
}


export function useUnassignTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: string): Promise<Ticket> => (await apiClient.post<Ticket>(`/tickets/${id}/unassign`)).data,
    onSuccess: (_, id) => { queryClient.invalidateQueries({ queryKey: ['ticket', id] }); queryClient.invalidateQueries({ queryKey: ['tickets'] }); queryClient.invalidateQueries({ queryKey: ['timeline', id] }); },
  });
}

export function useTicketComments(ticketId: string | undefined) {
  return useQuery({ queryKey: ['ticketComments', ticketId], queryFn: async (): Promise<TicketComment[]> => {
    if (!ticketId) return []; return (await apiClient.get<TicketComment[]>(`/tickets/${ticketId}/comments`)).data;
  }, enabled: Boolean(ticketId) });
}

export function useAddTicketComment() {
  const queryClient = useQueryClient();
  return useMutation({ mutationFn: async ({ ticketId, payload }: { ticketId: string; payload: CreateTicketCommentPayload }): Promise<TicketComment> =>
    (await apiClient.post<TicketComment>(`/tickets/${ticketId}/comments`, payload)).data,
    onSuccess: (_, v) => { queryClient.invalidateQueries({ queryKey: ['ticketComments', v.ticketId] }); queryClient.invalidateQueries({ queryKey: ['timeline', v.ticketId] }); }
  });
}

// ================= LINKS =================
export function useTicketLinks(ticketId: string | undefined) {
  return useQuery({
    queryKey: ['ticketLinks', ticketId],
    queryFn: async (): Promise<TicketLink[]> => {
      if (!ticketId) return [];
      const response = await apiClient.get<TicketLink[]>(`/tickets/${ticketId}/links`);
      return response.data;
    },
    enabled: Boolean(ticketId),
  });
}

// ================= TIMELINE =================
export function useTimeline(ticketId: string | undefined) {
  return useQuery({
    queryKey: ['timeline', ticketId],
    queryFn: async (): Promise<TimelineEvent[]> => {
      if (!ticketId) return [];
      const response = await apiClient.get<TimelineEvent[]>(`/tickets/${ticketId}/timeline`);
      return response.data;
    },
    enabled: Boolean(ticketId),
  });
}

// ================= SIDE CONVERSATIONS =================
export function useSideConversations(ticketId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ['sideConversations', ticketId],
    queryFn: async (): Promise<SideConversation[]> => {
      if (!ticketId) return [];
      const response = await apiClient.get<SideConversation[]>(`/tickets/${ticketId}/side-conversations`);
      return response.data;
    },
    enabled: Boolean(ticketId) && enabled,
  });
}

export function useCreateSideConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      ticketId,
      payload,
    }: {
      ticketId: string;
      payload: CreateSideConversationPayload;
    }): Promise<SideConversation> => {
      const response = await apiClient.post<SideConversation>(
        `/tickets/${ticketId}/side-conversations`,
        payload
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sideConversations', variables.ticketId] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.ticketId] });
    },
  });
}

export function useAddMessage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      conversationId,
      payload,
    }: {
      ticketId: string;
      conversationId: string;
      payload: AddSideMessagePayload;
    }): Promise<SideMessage> => {
      const response = await apiClient.post<SideMessage>(
        `/side-conversations/${conversationId}/messages`,
        payload
      );
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sideConversations', variables.ticketId] });
      queryClient.invalidateQueries({ queryKey: ['timeline', variables.ticketId] });
    },
  });
}

// ================= INTENT =================
export function useSuggestIntent() {
  return useMutation({
    mutationFn: async (payload: { title: string; description: string }): Promise<IntentSuggestion[]> => {
      const response = await apiClient.post<IntentSuggestion[]>('/intent/suggest', payload);
      return response.data;
    },
  });
}

// ================= INSIGHTS =================
export function useInsights(since?: string) {
  return useQuery({
    queryKey: ['insights', since],
    queryFn: async (): Promise<Theme[]> => {
      const params = since ? { since } : {};
      const response = await apiClient.get<Theme[]>('/insights/themes', { params });
      return response.data;
    },
  });
}

// ================= AGENCIES & USERS =================
export function useAgencies() {
  return useQuery({
    queryKey: ['agencies'],
    queryFn: async (): Promise<Agency[]> => {
      const response = await apiClient.get<Agency[]>('/agencies');
      return response.data;
    },
    staleTime: 10 * 60 * 1000,
  });
}

export function useUsers(role?: string, enabled = true) {
  return useQuery({
    queryKey: ['users', role],
    queryFn: async (): Promise<User[]> => {
      const params = role ? { role } : {};
      const response = await apiClient.get<User[]>('/users', { params });
      return response.data;
    },
    staleTime: 5 * 60 * 1000,
    enabled,
  });
}
