// Shared by the browser form and the API so both apply identical rules.

export const SECTIONS = ["Information", "Action"] as const;
export type Section = (typeof SECTIONS)[number];

export const ALL_STATUSES = ["Passed", "Failed", "Not Enough Info"] as const;
export type Status = (typeof ALL_STATUSES)[number];

export type Question = {
  id: number;
  question_id: string;
  section: string;
  category: string;
  language: string;
  question_text: string;
};

export type EvaluationInput = {
  question_id: number; // questions.id (primary key)
  status: string;
  actual_answer?: string | null;
  comments?: string | null;
};

export function statusesFor(section: string): readonly Status[] {
  const s = section.trim().toLowerCase();
  if (s === "information") return ALL_STATUSES;
  if (s === "action") return ["Passed", "Failed"];
  return [];
}

export function languageSortKey(language: string) {
  const l = language.toLowerCase();
  return l === "amharic" ? 0 : l === "english" ? 1 : 2;
}

/** Returns an error message, or null when the row is valid. */
export function validateRow(
  code: string,
  section: string,
  status: string,
  actualAnswer: string,
  comment: string,
): string | null {
  if (!status) return `${code}: Please select a status.`;
  if (!statusesFor(section).includes(status as Status))
    return `${code}: Invalid status '${status}'.`;
  if ((status === "Failed" || status === "Not Enough Info") && !actualAnswer.trim())
    return `${code}: Actual chatbot response is required.`;
  if (status === "Not Enough Info" && !comment.trim())
    return `${code}: Please explain what information is missing or what should be improved.`;
  return null;
}

export const MAX_TEXT = 5000;
