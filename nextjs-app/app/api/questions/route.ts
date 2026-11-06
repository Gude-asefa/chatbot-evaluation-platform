import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const department = req.nextUrl.searchParams.get("department");
  if (!department) {
    return NextResponse.json({ error: "department is required" }, { status: 400 });
  }
  const sql = db();
  // Expected answers are intentionally not sent to testers.
  const rows = await sql`
    SELECT id, question_id, section, category, language, question_text
    FROM questions
    WHERE department = ${department} AND is_active = TRUE
    ORDER BY id`;
  return NextResponse.json(rows, {
    headers: { "Cache-Control": "s-maxage=300, stale-while-revalidate=600" },
  });
}
