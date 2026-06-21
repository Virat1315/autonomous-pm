/**
 * api.ts – Client-side API utilities.
 * All calls go through Next.js /api/dashboard/* proxy routes.
 */
import type {
  Ticket, TicketCreatePayload, TicketUpdatePayload,
  TicketFilter, DashboardStats, ApiResponse, TicketListResponse,
} from "./types";

const BASE = "/api/dashboard";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
    const json = await res.json();
    if (!res.ok) return { success: false, error: json.error || res.statusText };
    return json;
  } catch (err: any) {
    return { success: false, error: err?.message || "Network error" };
  }
}

export async function getStats(): Promise<ApiResponse<DashboardStats>> {
  return request<DashboardStats>("/stats");
}

export async function getTickets(
  page = 1,
  pageSize = 20,
  filters: TicketFilter = {}
): Promise<ApiResponse<TicketListResponse>> {
  const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
  if (filters.status)      params.set("status",      filters.status);
  if (filters.priority)    params.set("priority",     filters.priority);
  if (filters.ticket_type) params.set("ticket_type",  filters.ticket_type);
  if (filters.assignee)    params.set("assignee",     filters.assignee);
  if (filters.search)      params.set("search",       filters.search);
  return request<TicketListResponse>(`/tickets?${params}`);
}

export async function getTicket(id: string): Promise<ApiResponse<Ticket>> {
  return request<Ticket>(`/tickets/${id}`);
}

export async function createTicket(
  payload: TicketCreatePayload
): Promise<ApiResponse<Ticket>> {
  return request<Ticket>("/tickets", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateTicket(
  id: string,
  payload: TicketUpdatePayload
): Promise<ApiResponse<Ticket>> {
  return request<Ticket>(`/tickets/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deleteTicket(id: string): Promise<ApiResponse<{ deleted: boolean }>> {
  return request<{ deleted: boolean }>(`/tickets/${id}`, { method: "DELETE" });
}

export async function assignTicket(
  id: string,
  assignee: string
): Promise<ApiResponse<Ticket>> {
  return request<Ticket>(`/tickets/${id}/assign`, {
    method: "POST",
    body: JSON.stringify({ assignee }),
  });
}
