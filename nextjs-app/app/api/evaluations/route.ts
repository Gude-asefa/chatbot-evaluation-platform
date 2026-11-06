import { NextRequest, NextResponse } from "next/server";
import { db, isUniqueViolation } from "@/lib/db";
import { MAX_TEXT, validateRow, type EvaluationInput } from "@/lib/evaluation";

export const dynamic = "force-dynamic";

type Body = {
  deviceId?: string;
  department?: string;
  section?: string;
  language?: string;
  records?: EvaluationInput[];
};

const str = (v: unknown) => (typeof v === "string" ? v.trim() : "");

export async function POST(req: NextRequest) {
  let body: Body;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const deviceId = str(body.deviceId);
  const department = str(body.department);
  const section = str(body.section);
  const language = str(body.language);
  const records = Array.isArray(body.records) ? body.records : [];

  if (!deviceId || deviceId.length > 100 || !department || !section || !language) {
    return NextResponse.json({ error: "Missing submission details." }, { status: 400 });
  }

  const sql = db();

  // The full question set for this department/section/language must be answered.
  const questions = (await sql`
    SELECT id, question_id, section FROM questions
    WHERE department = ${department} AND section = ${section}
      AND language = ${language} AND is_active = TRUE`) as {
    id: number;
    question_id: string;
    section: string;
  }[];

  if (questions.length === 0) {
    return NextResponse.json({ error: "No questions found for this selection." }, { status: 400 });
  }

  const byId = new Map(records.map((r) => [Number(r.question_id), r]));
  const errors: string[] = [];
  const rows: { qid: number; answer: string | null; status: string; comment: string | null }[] = [];

  for (const q of questions) {
    const r = byId.get(q.id);
    const status = str(r?.status);
    const answer = str(r?.actual_answer).slice(0, MAX_TEXT);
    const comment = str(r?.comments).slice(0, MAX_TEXT);
    const err = validateRow(q.question_id, q.section, status, answer, comment);
    if (err) errors.push(err);
    else rows.push({ qid: q.id, answer: answer || null, status, comment: comment || null });
  }

  if (errors.length) {
    return NextResponse.json({ error: "Validation failed.", details: errors }, { status: 422 });
  }

  try {
    // One transaction: the submission lock and the evaluations succeed or fail together.
    await sql.transaction([
      sql`INSERT INTO submissions (device_id, department, section, language)
          VALUES (${deviceId}, ${department}, ${section}, ${language})`,
      sql`INSERT INTO evaluations (question_id, actual_answer, status, comments, session_id)
          SELECT qid, answer, status, comment, ${deviceId}
          FROM unnest(
            ${rows.map((r) => r.qid)}::int[],
            ${rows.map((r) => r.answer)}::text[],
            ${rows.map((r) => r.status)}::text[],
            ${rows.map((r) => r.comment)}::text[]
          ) AS t(qid, answer, status, comment)`,
    ]);
  } catch (error) {
    if (isUniqueViolation(error)) {
      return NextResponse.json(
        { error: "already_submitted" },
        { status: 409 },
      );
    }
    console.error("Failed to save evaluations", error);
    return NextResponse.json({ error: "Unable to save evaluations." }, { status: 500 });
  }

  return NextResponse.json({ saved: rows.length });
}
