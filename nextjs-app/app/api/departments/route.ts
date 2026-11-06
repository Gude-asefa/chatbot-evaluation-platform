import { NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET() {
  const sql = db();
  const rows = await sql`
    SELECT DISTINCT department FROM questions
    WHERE is_active = TRUE ORDER BY department`;
  return NextResponse.json(
    rows.map((r) => r.department as string),
    { headers: { "Cache-Control": "s-maxage=300, stale-while-revalidate=600" } },
  );
}
