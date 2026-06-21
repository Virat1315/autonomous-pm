/**
 * /api/dashboard/stats → proxies to Ticket Service GET /stats
 */
import { NextResponse } from "next/server";

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL || "http://localhost:3001";

export async function GET() {
  try {
    const res = await fetch(`${TICKET_SERVICE_URL}/stats`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
      next: { revalidate: 0 },
    });
    if (!res.ok) {
      return NextResponse.json({ success: false, error: "Failed to fetch stats" }, { status: res.status });
    }
    const data = await res.json();
    return NextResponse.json({ success: true, data });
  } catch (err: any) {
    return NextResponse.json({ success: false, error: err?.message || "Internal error" }, { status: 500 });
  }
}
