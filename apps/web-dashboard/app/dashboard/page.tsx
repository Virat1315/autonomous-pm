'use client';

import { useState, useEffect, useCallback } from 'react';
import type { Ticket, DashboardStats, TicketFilter, TicketListResponse, TicketStatus, TicketPriority } from '@/lib/types';
import { getStats, getTickets, createTicket, updateTicket, deleteTicket } from '@/lib/api';
import { 
  Plus, Search, RefreshCw, LayoutGrid, List,
  AlertTriangle, CheckCircle2, Clock, XCircle, ChevronLeft, ChevronRight, Loader2
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_COLORS: Record<TicketStatus, string> = {
  'Open':        'bg-blue-900/50 text-blue-300 border border-blue-700/50',
  'In Progress': 'bg-yellow-900/50 text-yellow-300 border border-yellow-700/50',
  'In Review':   'bg-purple-900/50 text-purple-300 border border-purple-700/50',
  'Done':        'bg-green-900/50 text-green-300 border border-green-700/50',
  'Closed':      'bg-gray-800 text-gray-400 border border-gray-700',
  'Blocked':     'bg-red-900/50 text-red-300 border border-red-700/50',
};

const PRIORITY_COLORS: Record<TicketPriority, string> = {
  'Low':      'text-gray-400',
  'Medium':   'text-blue-400',
  'High':     'text-orange-400',
  'Critical': 'text-red-400 font-semibold',
};

const PRIORITY_DOT: Record<TicketPriority, string> = {
  'Low':      'bg-gray-500',
  'Medium':   'bg-blue-500',
  'High':     'bg-orange-500',
  'Critical': 'bg-red-500',
};

const KANBAN_COLS: { status: TicketStatus; label: string; color: string }[] = [
  { status: 'Open',        label: 'Open',        color: 'border-blue-700' },
  { status: 'In Progress', label: 'In Progress', color: 'border-yellow-700' },
  { status: 'In Review',   label: 'In Review',   color: 'border-purple-700' },
  { status: 'Blocked',     label: 'Blocked',     color: 'border-red-700' },
  { status: 'Done',        label: 'Done',        color: 'border-green-700' },
];

function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[status]}`}>
      {status}
    </span>
  );
}

function PriorityDot({ priority }: { priority: TicketPriority }) {
  return <span className={`inline-block w-2 h-2 rounded-full ${PRIORITY_DOT[priority]}`} />;
}

// ── Create/Edit Modal ─────────────────────────────────────────────────────────
function TicketModal({
  ticket,
  onClose,
  onSave,
}: {
  ticket: Ticket | null;
  onClose: () => void;
  onSave: (data: any) => Promise<void>;
}) {
  const [form, setForm] = useState({
    title:       ticket?.title       || '',
    description: ticket?.description || '',
    ticket_type: ticket?.ticket_type || 'task',
    priority:    ticket?.priority    || 'Medium',
    assignee:    ticket?.assignee    || '',
    status:      ticket?.status      || 'Open',
  });
  const [saving, setSaving] = useState(false);

  const set = (k: string, v: string) => setForm(f => ({ ...f, [k]: v }));

  const save = async () => {
    if (!form.title.trim()) return;
    setSaving(true);
    try { await onSave(form); } finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-lg shadow-2xl">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <h2 className="text-lg font-semibold">{ticket ? 'Edit Ticket' : 'New Ticket'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">×</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Title *</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              value={form.title}
              onChange={e => set('title', e.target.value)}
              placeholder="Brief description of the issue"
            />
          </div>
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Description</label>
            <textarea
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 resize-none"
              rows={3}
              value={form.description}
              onChange={e => set('description', e.target.value)}
              placeholder="More details…"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Type</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
                value={form.ticket_type} onChange={e => set('ticket_type', e.target.value)}>
                {['task','bug','feature','incident','code_review','epic','story','spike'].map(t =>
                  <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Priority</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
                value={form.priority} onChange={e => set('priority', e.target.value)}>
                {['Low','Medium','High','Critical'].map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
          </div>
          {ticket && (
            <div>
              <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Status</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none"
                value={form.status} onChange={e => set('status', e.target.value)}>
                {['Open','In Progress','In Review','Done','Closed','Blocked'].map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          )}
          <div>
            <label className="text-xs text-gray-400 uppercase tracking-wider mb-1 block">Assignee</label>
            <input
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              value={form.assignee}
              onChange={e => set('assignee', e.target.value)}
              placeholder="username or email"
            />
          </div>
        </div>
        <div className="px-6 pb-6 flex justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-400 hover:text-white">Cancel</button>
          <button
            onClick={save}
            disabled={saving || !form.title.trim()}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {saving && <Loader2 className="w-3 h-3 animate-spin" />}
            {ticket ? 'Save changes' : 'Create ticket'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Ticket Detail Panel ───────────────────────────────────────────────────────
function TicketDetail({ ticket, onClose, onUpdated, onDeleted }: {
  ticket: Ticket;
  onClose: () => void;
  onUpdated: (t: Ticket) => void;
  onDeleted: (id: string) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleSave = async (data: any) => {
    const res = await updateTicket(ticket.ticket_id, data);
    if (res.success && res.data) { onUpdated(res.data); setEditing(false); }
  };

  const handleDelete = async () => {
    if (!confirm(`Delete ${ticket.ticket_id}?`)) return;
    setDeleting(true);
    const res = await deleteTicket(ticket.ticket_id);
    if (res.success) onDeleted(ticket.ticket_id);
    setDeleting(false);
  };

  return (
    <>
      {editing && <TicketModal ticket={ticket} onClose={() => setEditing(false)} onSave={handleSave} />}
      <div className="fixed inset-y-0 right-0 z-40 w-full max-w-md bg-gray-900 border-l border-gray-700 shadow-2xl flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div>
            <span className="text-xs font-mono text-blue-400">{ticket.ticket_id}</span>
            <p className="text-sm text-gray-400">{ticket.ticket_type}</p>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => setEditing(true)}
              className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 rounded-lg border border-gray-700 transition-colors">
              Edit
            </button>
            <button onClick={handleDelete} disabled={deleting}
              className="text-xs px-3 py-1.5 bg-red-900/40 hover:bg-red-900/60 text-red-400 rounded-lg border border-red-800/50 transition-colors">
              {deleting ? '…' : 'Delete'}
            </button>
            <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none ml-1">×</button>
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-5 scrollbar-thin">
          <h2 className="text-base font-semibold leading-snug">{ticket.title}</h2>
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={ticket.status} />
            <span className={`text-xs px-2 py-0.5 ${PRIORITY_COLORS[ticket.priority]}`}>
              <PriorityDot priority={ticket.priority} /> {ticket.priority}
            </span>
          </div>
          {ticket.description && (
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Description</p>
              <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">{ticket.description}</p>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Assignee</p>
              <p className="text-gray-200">{ticket.assignee || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Reporter</p>
              <p className="text-gray-200">{ticket.reported_by || '—'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Source</p>
              <p className="text-gray-200">{ticket.source || '—'}</p>
            </div>
            {ticket.priority_score && (
              <div>
                <p className="text-xs text-gray-500 mb-0.5">Priority score</p>
                <p className="text-gray-200">{ticket.priority_score}/100</p>
              </div>
            )}
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Created</p>
              <p className="text-gray-200 text-xs">{formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-0.5">Updated</p>
              <p className="text-gray-200 text-xs">{formatDistanceToNow(new Date(ticket.updated_at), { addSuffix: true })}</p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

// ── Stat Card ─────────────────────────────────────────────────────────────────
function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: any; color: string;
}) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-start gap-4">
      <div className={`p-2 rounded-lg ${color}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-xs text-gray-400 mt-0.5">{label}</p>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [stats,     setStats]     = useState<DashboardStats | null>(null);
  const [tickets,   setTickets]   = useState<Ticket[]>([]);
  const [total,     setTotal]     = useState(0);
  const [page,      setPage]      = useState(1);
  const [filters,   setFilters]   = useState<TicketFilter>({});
  const [search,    setSearch]    = useState('');
  const [view,      setView]      = useState<'list' | 'kanban'>('list');
  const [loading,   setLoading]   = useState(true);
  const [selected,  setSelected]  = useState<Ticket | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const PAGE_SIZE = 20;

  const loadStats = useCallback(async () => {
    const res = await getStats();
    if (res.success && res.data) setStats(res.data);
  }, []);

  const loadTickets = useCallback(async () => {
    setLoading(true);
    setError(null);
    const f = { ...filters, search: search || undefined };
    const res = await getTickets(page, PAGE_SIZE, f);
    if (res.success && res.data) {
      setTickets(res.data.tickets);
      setTotal(res.data.total);
    } else {
      setError(res.error || 'Failed to load tickets');
    }
    setLoading(false);
  }, [page, filters, search]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadTickets(); }, [loadTickets]);

  const handleCreate = async (data: any) => {
    const res = await createTicket(data);
    if (res.success) { setShowCreate(false); loadTickets(); loadStats(); }
  };

  const handleUpdated = (updated: Ticket) => {
    setTickets(ts => ts.map(t => t.ticket_id === updated.ticket_id ? updated : t));
    setSelected(updated);
    loadStats();
  };

  const handleDeleted = (id: string) => {
    setTickets(ts => ts.filter(t => t.ticket_id !== id));
    setSelected(null);
    loadStats();
  };

  const applyFilter = (key: keyof TicketFilter, val: string) => {
    setFilters(f => ({ ...f, [key]: val || undefined }));
    setPage(1);
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="sticky top-0 z-30 bg-gray-950/90 backdrop-blur border-b border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center text-xs font-bold">A</div>
            <span className="font-semibold text-sm">Autonomous PM</span>
          </div>
          <div className="flex-1 max-w-md relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-500" />
            <input
              className="w-full bg-gray-900 border border-gray-700 rounded-lg pl-9 pr-3 py-1.5 text-sm focus:outline-none focus:border-blue-500 placeholder:text-gray-600"
              placeholder="Search tickets…"
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { loadTickets(); loadStats(); }}
              className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition-colors">
              <RefreshCw className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition-colors">
              <Plus className="w-4 h-4" /> New ticket
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <StatCard label="Total"     value={stats.total_tickets}     icon={List}           color="bg-gray-800 text-gray-300" />
            <StatCard label="Active"    value={stats.active_tickets}    icon={Clock}          color="bg-yellow-900/40 text-yellow-400" />
            <StatCard label="Completed" value={stats.completed_tickets} icon={CheckCircle2}   color="bg-green-900/40 text-green-400" />
            <StatCard label="Blocked"   value={stats.blocked_tickets}   icon={AlertTriangle}  color="bg-red-900/40 text-red-400" />
          </div>
        )}

        {/* Toolbar */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          <select
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none"
            value={filters.status || ''}
            onChange={e => applyFilter('status', e.target.value)}>
            <option value="">All statuses</option>
            {['Open','In Progress','In Review','Done','Closed','Blocked'].map(s => <option key={s}>{s}</option>)}
          </select>
          <select
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none"
            value={filters.priority || ''}
            onChange={e => applyFilter('priority', e.target.value)}>
            <option value="">All priorities</option>
            {['Low','Medium','High','Critical'].map(p => <option key={p}>{p}</option>)}
          </select>
          <select
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-1.5 text-sm focus:outline-none"
            value={filters.ticket_type || ''}
            onChange={e => applyFilter('ticket_type', e.target.value)}>
            <option value="">All types</option>
            {['task','bug','feature','incident','code_review'].map(t => <option key={t}>{t}</option>)}
          </select>
          <div className="ml-auto flex items-center gap-1 bg-gray-900 border border-gray-700 rounded-lg p-1">
            <button onClick={() => setView('list')}
              className={`p-1.5 rounded ${view === 'list' ? 'bg-gray-700' : 'hover:bg-gray-800'} transition-colors`}>
              <List className="w-4 h-4" />
            </button>
            <button onClick={() => setView('kanban')}
              className={`p-1.5 rounded ${view === 'kanban' ? 'bg-gray-700' : 'hover:bg-gray-800'} transition-colors`}>
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 mb-4 p-3 bg-red-900/30 border border-red-800/50 rounded-lg text-red-300 text-sm">
            <XCircle className="w-4 h-4 flex-shrink-0" />
            {error} — is the Ticket Service running?
          </div>
        )}

        {/* List View */}
        {view === 'list' && (
          <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center py-16 text-gray-500">
                <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
              </div>
            ) : tickets.length === 0 ? (
              <div className="text-center py-16 text-gray-500">
                <p className="mb-3">No tickets found</p>
                <button onClick={() => setShowCreate(true)}
                  className="text-blue-400 hover:text-blue-300 text-sm">
                  Create the first ticket →
                </button>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                    <th className="text-left px-4 py-3">ID</th>
                    <th className="text-left px-4 py-3">Title</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3">Priority</th>
                    <th className="text-left px-4 py-3">Assignee</th>
                    <th className="text-left px-4 py-3">Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {tickets.map(t => (
                    <tr key={t.ticket_id}
                      onClick={() => setSelected(t)}
                      className="border-b border-gray-800/50 hover:bg-gray-800/40 cursor-pointer transition-colors">
                      <td className="px-4 py-3 font-mono text-xs text-blue-400">{t.ticket_id}</td>
                      <td className="px-4 py-3">
                        <p className="font-medium truncate max-w-xs">{t.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{t.ticket_type}</p>
                      </td>
                      <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                      <td className="px-4 py-3">
                        <span className={`flex items-center gap-1.5 text-xs ${PRIORITY_COLORS[t.priority]}`}>
                          <PriorityDot priority={t.priority} />{t.priority}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300">{t.assignee || <span className="text-gray-600">—</span>}</td>
                      <td className="px-4 py-3 text-gray-500 text-xs">
                        {formatDistanceToNow(new Date(t.updated_at), { addSuffix: true })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}

        {/* Kanban View */}
        {view === 'kanban' && (
          <div className="flex gap-4 overflow-x-auto pb-4">
            {KANBAN_COLS.map(col => {
              const colTickets = tickets.filter(t => t.status === col.status);
              return (
                <div key={col.status} className={`flex-shrink-0 w-64 bg-gray-900 border border-gray-800 rounded-xl overflow-hidden`}>
                  <div className={`px-4 py-3 border-b-2 ${col.color} flex items-center justify-between`}>
                    <span className="text-sm font-medium">{col.label}</span>
                    <span className="text-xs bg-gray-800 text-gray-400 rounded-full px-2 py-0.5">{colTickets.length}</span>
                  </div>
                  <div className="p-3 space-y-2 min-h-32">
                    {colTickets.map(t => (
                      <div key={t.ticket_id}
                        onClick={() => setSelected(t)}
                        className="bg-gray-800 hover:bg-gray-750 border border-gray-700 rounded-lg p-3 cursor-pointer transition-colors">
                        <p className="text-xs font-mono text-blue-400 mb-1">{t.ticket_id}</p>
                        <p className="text-sm leading-snug line-clamp-2">{t.title}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <PriorityDot priority={t.priority} />
                          <span className="text-xs text-gray-500">{t.priority}</span>
                          {t.assignee && <span className="text-xs text-gray-500 ml-auto truncate">{t.assignee}</span>}
                        </div>
                      </div>
                    ))}
                    {colTickets.length === 0 && (
                      <p className="text-xs text-gray-600 text-center py-4">Empty</p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 text-sm text-gray-400">
            <span>{total} tickets · Page {page} of {totalPages}</span>
            <div className="flex items-center gap-1">
              <button disabled={page === 1} onClick={() => setPage(p => p - 1)}
                className="p-1.5 rounded hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}
                className="p-1.5 rounded hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Modals & panels */}
      {showCreate && (
        <TicketModal ticket={null} onClose={() => setShowCreate(false)} onSave={handleCreate} />
      )}
      {selected && (
        <TicketDetail
          ticket={selected}
          onClose={() => setSelected(null)}
          onUpdated={handleUpdated}
          onDeleted={handleDeleted}
        />
      )}
    </div>
  );
}
