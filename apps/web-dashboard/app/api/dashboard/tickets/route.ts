/**
 * /api/dashboard/tickets → proxies to Ticket Service GET /tickets and POST /tickets
 */
import { NextRequest, NextResponse } from "next/server";

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const upstream = new URLSearchParams();
    ["page","page_size","status","priority","ticket_type","assignee","search"].forEach(k => {
      const v = searchParams.get(k);
      if (v) upstream.set(k, v);
    });
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets?${upstream}`, {
      next: { revalidate: 0 },
    });
    if (!res.ok) return NextResponse.json({ success: false, error: "Failed to fetch tickets" }, { status: res.status });
    const data = await res.json();
    // data is already { tickets, total, page, page_size }
    return NextResponse.json({ success: true, data, ...data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const res = await fetch(`${TICKET_SERVICE_URL}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      return NextResponse.json({ success: false, error: err.detail || "Failed to create ticket" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json({ success: true, data }, { status: 201 });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message }, { status: 500 });
  }
}
