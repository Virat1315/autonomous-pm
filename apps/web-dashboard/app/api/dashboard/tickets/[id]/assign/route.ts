/**
 * /api/dashboard/tickets/[id]/assign → POST /tickets/{id}/assign
 */
import { NextRequest, NextResponse } from "next/server";

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

export async function POST(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const body = await request.json();
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets/${params.id}/assign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json({ success: false, error: err.detail || "Assign failed" }, { status: res.status });
    }
    return NextResponse.json({ success: true, data: await res.json() });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}
