import "server-only";
import { db } from "./db";

export type Filters = {
  department?: string;
  section?: string;
  language?: string;
  status?: string;
};

export type EvaluationRecord = {
  id: number;
  department: string;
  section: string;
  language: string;
  question_id: string;
  category: string;
  question_text: string;
  actual_answer: string | null;
  status: string;
  comments: string | null;
  submitted_at: string;
};

export async function getSummary() {
  const sql = db();
  const [row] = await sql`
    SELECT
      COUNT(*)::int                                              AS total,
      COUNT(*) FILTER (WHERE status = 'Passed')::int             AS passed,
      COUNT(*) FILTER (WHERE status = 'Failed')::int             AS failed,
      COUNT(*) FILTER (WHERE status = 'Not Enough Info')::int    AS not_enough_info
    FROM evaluations`;
  return row as { total: number; passed: number; failed: number; not_enough_info: number };
}

export async function getDepartmentProgress() {
  const sql = db();
  const rows = (await sql`
    SELECT q.department,
           COUNT(DISTINCT q.id)::int            AS total_questions,
           COUNT(DISTINCT e.question_id)::int   AS evaluated_questions
    FROM questions q
    LEFT JOIN evaluations e ON e.question_id = q.id
    WHERE q.is_active = TRUE
    GROUP BY q.department
    ORDER BY q.department`) as {
    department: string;
    total_questions: number;
    evaluated_questions: number;
  }[];

  return rows.map((r) => ({
    ...r,
    remaining_questions: r.total_questions - r.evaluated_questions,
    progress: r.total_questions
      ? Math.round((r.evaluated_questions / r.total_questions) * 1000) / 10
      : 0,
  }));
}

function clean(v?: string) {
  return v && v !== "All" ? v : null;
}

export async function getEvaluationRecords(f: Filters) {
  const sql = db();
  const rows = await sql`
    SELECT e.id, q.department, q.section, q.language, q.question_id, q.category,
           q.question_text, e.actual_answer, e.status, e.comments, e.submitted_at
    FROM evaluations e
    JOIN questions q ON q.id = e.question_id
    WHERE (${clean(f.department)}::text IS NULL OR q.department = ${clean(f.department)})
      AND (${clean(f.section)}::text    IS NULL OR q.section    = ${clean(f.section)})
      AND (${clean(f.language)}::text   IS NULL OR q.language   = ${clean(f.language)})
      AND (${clean(f.status)}::text     IS NULL OR e.status     = ${clean(f.status)})
    ORDER BY e.submitted_at DESC`;
  return rows as EvaluationRecord[];
}
