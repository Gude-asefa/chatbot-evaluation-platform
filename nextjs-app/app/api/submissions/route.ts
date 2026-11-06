import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const deviceId = req.nextUrl.searchParams.get("deviceId");
  const department = req.nextUrl.searchParams.get("department");
  if (!deviceId || !department) return NextResponse.json([]);

  const sql = db();
  const rows = await sql`
    SELECT section, language FROM submissions
    WHERE device_id = ${deviceId} AND department = ${department}`;
  return NextResponse.json(rows, { headers: { "Cache-Control": "no-store" } });
}
