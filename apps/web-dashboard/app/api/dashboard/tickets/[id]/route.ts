/**
 * /api/dashboard/tickets/[id] → GET, PUT, DELETE
 */
import { NextRequest, NextResponse } from "next/server";

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

export async function GET(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets/${params.id}`, { next: { revalidate: 0 } });
    if (!res.ok) return NextResponse.json({ success: false, error: "Ticket not found" }, { status: res.status });
    return NextResponse.json({ success: true, data: await res.json() });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json();
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets/${params.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json({ success: false, error: err.detail || "Update failed" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data: await res.json() });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}

export async function DELETE(_req: NextRequest, { params }: { params: { id: string } }) {
  try {
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets/${params.id}`, { method: "DELETE" });
    if (!res.ok) return NextResponse.json({ success: false, error: "Delete failed" }, { status: res.status });
    return NextResponse.json({ success: true, data: { deleted: true } });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}
