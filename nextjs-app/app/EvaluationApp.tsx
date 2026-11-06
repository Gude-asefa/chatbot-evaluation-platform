"use client";

import { useEffect, useMemo, useState } from "react";
import {
  SECTIONS,
  languageSortKey,
  statusesFor,
  validateRow,
  type Question,
} from "@/lib/evaluation";

// Same localStorage key as the Streamlit app, so existing testers keep their device ID.
const STORAGE_KEY = "boa_chatbot_eval_device_id";

type Combo = { section: string; language: string };
type RowState = { status: string; answer: string; comment: string };
type Notice = { kind: "success" | "warning" | "error"; title?: string; lines: string[] } | null;

function getDeviceId() {
  let id: string | null = null;
  try {
    id = localStorage.getItem(STORAGE_KEY);
  } catch {}
  if (!id) {
    id = crypto?.randomUUID?.() ?? Date.now().toString(36) + Math.random().toString(36).slice(2);
    try {
      localStorage.setItem(STORAGE_KEY, id);
    } catch {}
  }
  return id;
}

const EMPTY_ROW: RowState = { status: "", answer: "", comment: "" };
const key = (c: Combo) => `${c.section}|${c.language}`;
const describe = (combos: Combo[]) => combos.map((c) => `${c.section} (${c.language})`).join(", ");

export default function EvaluationApp() {
  const [deviceId, setDeviceId] = useState<string | null>(null);
  const [departments, setDepartments] = useState<string[] | null>(null);
  const [department, setDepartment] = useState("");
  const [questions, setQuestions] = useState<Question[] | null>(null);
  const [submitted, setSubmitted] = useState<Set<string>>(new Set());
  const [section, setSection] = useState("");
  const [language, setLanguage] = useState("");
  const [rows, setRows] = useState<Record<number, RowState>>({});
  const [errorIds, setErrorIds] = useState<Set<number>>(new Set());
  const [notice, setNotice] = useState<Notice>(null);
  const [saving, setSaving] = useState(false);
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    setDeviceId(getDeviceId());
    fetch("/api/departments")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setDepartments)
      .catch(() => setLoadError("Unable to load departments. Please refresh the page."));
  }, []);

  useEffect(() => {
    setQuestions(null);
    setSection("");
    setLanguage("");
    setNotice(null);
    if (!department || !deviceId) return;

    const q = encodeURIComponent(department);
    Promise.all([
      fetch(`/api/questions?department=${q}`).then((r) => r.json()),
      fetch(`/api/submissions?department=${q}&deviceId=${encodeURIComponent(deviceId)}`).then((r) =>
        r.json(),
      ),
    ])
      .then(([qs, subs]: [Question[], Combo[]]) => {
        setQuestions(qs);
        setSubmitted(new Set(subs.map(key)));
      })
      .catch(() => setLoadError("Unable to load questions. Please refresh the page."));
  }, [department, deviceId]);

  const sections = useMemo(() => {
    const out: Record<string, Question[]> = {};
    for (const name of SECTIONS) {
      const qs = (questions ?? []).filter((q) => q.section.trim().toLowerCase() === name.toLowerCase());
      if (qs.length) out[name] = qs;
    }
    return out;
  }, [questions]);

  const languagesBySection = useMemo(() => {
    const out: Record<string, string[]> = {};
    for (const [name, qs] of Object.entries(sections)) {
      out[name] = [...new Set(qs.map((q) => q.language.trim()))].sort(
        (a, b) => languageSortKey(a) - languageSortKey(b),
      );
    }
    return out;
  }, [sections]);

  const allCombos = useMemo(
    () =>
      Object.entries(languagesBySection).flatMap(([s, langs]) =>
        langs.map((l) => ({ section: s, language: l })),
      ),
    [languagesBySection],
  );
  const remaining = allCombos.filter((c) => !submitted.has(key(c)));

  const filtered = useMemo(
    () => (section && language ? (sections[section] ?? []).filter((q) => q.language.trim() === language) : []),
    [sections, section, language],
  );

  function chooseSection(s: string) {
    setSection(s);
    setLanguage("");
    setNotice(null);
  }

  function chooseLanguage(l: string) {
    setLanguage(l);
    setNotice(null);
    setErrorIds(new Set());
  }

  function updateRow(id: number, patch: Partial<RowState>) {
    setRows((prev) => ({
      ...prev,
      [id]: { ...EMPTY_ROW, ...prev[id], ...patch },
    }));
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!deviceId) return;

    const errors: string[] = [];
    const bad = new Set<number>();
    for (const q of filtered) {
      const r = rows[q.id] ?? { status: "", answer: "", comment: "" };
      const err = validateRow(q.question_id, q.section, r.status, r.answer, r.comment);
      if (err) {
        errors.push(err);
        bad.add(q.id);
      }
    }
    setErrorIds(bad);
    if (errors.length) {
      setNotice({ kind: "error", title: "Please correct the following issues before submitting", lines: errors });
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }

    setSaving(true);
    setNotice(null);
    const combo = { section, language };
    const remainingAfter = remaining.filter((c) => key(c) !== key(combo));

    try {
      const res = await fetch("/api/evaluations", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          deviceId,
          department,
          section,
          language,
          records: filtered.map((q) => ({
            question_id: q.id,
            status: rows[q.id]?.status,
            actual_answer: rows[q.id]?.answer,
            comments: rows[q.id]?.comment,
          })),
        }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok) {
        setSubmitted((prev) => new Set(prev).add(key(combo)));
        setRows((prev) => {
          const next = { ...prev };
          for (const q of filtered) delete next[q.id];
          return next;
        });
        setNotice({
          kind: "success",
          title: `Successfully submitted ${data.saved} ${section} — ${language} evaluations.`,
          lines: [
            remainingAfter.length
              ? `Next, please complete: ${describe(remainingAfter)}.`
              : "You have completed every set for this department.",
          ],
        });
        setLanguage("");
      } else if (res.status === 409) {
        setSubmitted((prev) => new Set(prev).add(key(combo)));
        setNotice({
          kind: "warning",
          title: "Already submitted",
          lines: [`You have already submitted an evaluation for ${section} — ${language} from this device.`],
        });
      } else {
        setNotice({
          kind: "error",
          title: data.error ?? "Unable to save evaluations.",
          lines: data.details ?? [],
        });
      }
    } catch {
      setNotice({ kind: "error", title: "Network error — your answers are still here. Please try again.", lines: [] });
    } finally {
      setSaving(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  if (loadError) return <div className="alert alert-error">{loadError}</div>;
  if (!deviceId || !departments) return <p className="caption">Preparing your testing session…</p>;

  const doneCount = allCombos.length - remaining.length;
  const alreadyDone = section && language && submitted.has(key({ section, language }));

  return (
    <>
      <div className="card">
        <label className="field" htmlFor="department">Select your department</label>
        <select id="department" value={department} onChange={(e) => setDepartment(e.target.value)}>
          <option value="" disabled>Choose your department</option>
          {departments.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
      </div>

      {notice && (
        <div className={`alert alert-${notice.kind}`} role="status">
          {notice.title && <div className="alert-title">{notice.title}</div>}
          {notice.lines.length > 0 &&
            (notice.kind === "error" ? (
              <ul>{notice.lines.map((l) => <li key={l}>{l}</li>)}</ul>
            ) : (
              notice.lines.map((l) => <div key={l}>{l}</div>)
            ))}
        </div>
      )}

      {!department && <div className="alert alert-info">Select your department to continue.</div>}

      {department && !questions && <p className="caption">Loading questions…</p>}

      {department && questions && allCombos.length === 0 && (
        <div className="alert alert-warning">No questions are assigned to this department yet.</div>
      )}

      {department && questions && allCombos.length > 0 && (
        <>
          <h2>{department} department</h2>
          <div className="progress-label">
            {doneCount} of {allCombos.length} section/language sets submitted
          </div>
          <div className="progress" aria-hidden>
            <span style={{ width: `${(doneCount / allCombos.length) * 100}%` }} />
          </div>
          {remaining.length === 0 && (
            <div className="alert alert-success">
              You have submitted every section for this department. Thank you!
            </div>
          )}

          <div className="card" style={{ marginTop: "1rem" }}>
            <h3>Select testing section</h3>
            <div className="segmented">
              {Object.entries(sections).map(([name, qs]) => {
                const done = languagesBySection[name].every((l) => submitted.has(key({ section: name, language: l })));
                return (
                  <button key={name} type="button" aria-pressed={section === name} onClick={() => chooseSection(name)}>
                    {name} ({qs.length} questions) {done && <span className="check">✓</span>}
                  </button>
                );
              })}
            </div>

            {!section && <p className="caption" style={{ marginTop: "0.75rem" }}>Choose Information or Action to continue.</p>}

            {section && (
              <>
                <h3 style={{ marginTop: "1.25rem" }}>{section} questions</h3>
                <div className="segmented">
                  {languagesBySection[section].map((l) => {
                    const done = submitted.has(key({ section, language: l }));
                    return (
                      <button key={l} type="button" aria-pressed={language === l} onClick={() => chooseLanguage(l)}>
                        {done ? <><span className="check">✓</span> {l} — submitted</> : l}
                      </button>
                    );
                  })}
                </div>
                {!language && <p className="caption" style={{ marginTop: "0.75rem" }}>Choose Amharic or English to load the questions.</p>}
              </>
            )}
          </div>

          {alreadyDone && (
            <div className="alert alert-warning">
              <div className="alert-title">Already submitted</div>
              You have already submitted an evaluation for <b>{section} — {language}</b> from this device.
              <div>
                {remaining.length
                  ? `Please continue with the remaining sets: ${describe(remaining)}.`
                  : "All sets for this department are complete."}
              </div>
            </div>
          )}

          {section && language && !alreadyDone && (
            <form onSubmit={submit} noValidate>
              <h2>
                {section} · {language} ({filtered.length} questions)
              </h2>
              <p className="caption">
                An actual response is required for Failed and Not Enough Info; a comment is required for
                Not Enough Info. Each section/language can be submitted once per device.
              </p>

              <table className="eval-table">
                <thead>
                  <tr>
                    <th style={{ width: "9%" }}>Question ID</th>
                    <th style={{ width: "11%" }}>Category</th>
                    <th style={{ width: "27%" }}>Question</th>
                    <th style={{ width: "21%" }}>Actual response</th>
                    <th style={{ width: "13%" }}>Status</th>
                    <th style={{ width: "19%" }}>Comment</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((q) => {
                    const r = rows[q.id] ?? { status: "", answer: "", comment: "" };
                    return (
                      <tr key={q.id} className={errorIds.has(q.id) ? "row-error" : undefined}>
                        <td className="qid" data-label="Question ID">{q.question_id}</td>
                        <td className="category" data-label="Category">{q.category}</td>
                        <td className="qtext" data-label="Question">{q.question_text}</td>
                        <td data-label="Actual response">
                          <textarea
                            aria-label={`Actual response for ${q.question_id}`}
                            placeholder="Enter chatbot response"
                            maxLength={5000}
                            value={r.answer}
                            onChange={(e) => updateRow(q.id, { answer: e.target.value })}
                          />
                        </td>
                        <td data-label="Status">
                          <select
                            aria-label={`Status for ${q.question_id}`}
                            value={r.status}
                            onChange={(e) => updateRow(q.id, { status: e.target.value })}
                          >
                            <option value="">Select status</option>
                            {statusesFor(q.section).map((s) => (
                              <option key={s} value={s}>{s}</option>
                            ))}
                          </select>
                        </td>
                        <td data-label="Comment">
                          <textarea
                            aria-label={`Comment for ${q.question_id}`}
                            placeholder="If Not Enough Info, what should be improved?"
                            maxLength={5000}
                            value={r.comment}
                            onChange={(e) => updateRow(q.id, { comment: e.target.value })}
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: "1rem" }} disabled={saving}>
                {saving ? "Submitting…" : `Submit ${section} — ${language} evaluations`}
              </button>
            </form>
          )}
        </>
      )}
    </>
  );
}
