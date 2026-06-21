/**
 * types.ts – Canonical TypeScript types.
 * Status and Priority enums MATCH the backend exactly (case-sensitive).
 */

// ── Canonical enums matching backend ─────────────────────────────────────────
export type TicketStatus =
  | "Open"
  | "In Progress"
  | "In Review"
  | "Done"
  | "Closed"
  | "Blocked";

export type TicketPriority = "Low" | "Medium" | "High" | "Critical";

export type TicketType =
  | "bug"
  | "feature"
  | "task"
  | "incident"
  | "code_review"
  | "epic"
  | "story"
  | "spike";

// ── Core ticket model (matches TicketResponse from ticket-service) ────────────
export interface Ticket {
  id:               number;
  ticket_id:        string;   // e.g. "APM-42"
  title:            string;
  description:      string | null;
  ticket_type:      TicketType;
  status:           TicketStatus;
  priority:         TicketPriority;
  priority_score:   number | null;
  assignee:         string | null;
  reported_by:      string | null;
  source:           string | null;
  channel:          string | null;
  slack_message_ts: string | null;
  created_at:       string;
  updated_at:       string;
}

export interface TicketCreatePayload {
  title:       string;
  description?: string;
  ticket_type?: TicketType;
  priority?:    TicketPriority;
  assignee?:    string;
  source?:      string;
}

export interface TicketUpdatePayload {
  title?:          string;
  description?:    string;
  ticket_type?:    TicketType;
  status?:         TicketStatus;
  priority?:       TicketPriority;
  priority_score?: number;
  assignee?:       string;
}

// ── List response ─────────────────────────────────────────────────────────────
export interface TicketListResponse {
  tickets:   Ticket[];
  total:     number;
  page:      number;
  page_size: number;
}

// ── Stats ─────────────────────────────────────────────────────────────────────
export interface DashboardStats {
  total_tickets:     number;
  active_tickets:    number;
  completed_tickets: number;
  blocked_tickets:   number;
  critical_tickets:  number;
  success_rate:      number;
  by_status:         Record<string, number>;
  by_priority:       Record<string, number>;
}

// ── Filter ────────────────────────────────────────────────────────────────────
export interface TicketFilter {
  status?:      TicketStatus;
  priority?:    TicketPriority;
  ticket_type?: TicketType;
  assignee?:    string;
  search?:      string;
}

// ── API response wrapper ──────────────────────────────────────────────────────
export interface ApiResponse<T> {
  success: boolean;
  data?:   T;
  error?:  string;
  total?:  number;
  page?:   number;
  page_size?: number;
}
