import { redirect } from "next/navigation";
import { isAdmin } from "@/lib/auth";
import { getDepartmentProgress, getEvaluationRecords, getSummary, type Filters } from "@/lib/dashboard";

export const dynamic = "force-dynamic";

const STATUS_COLORS: Record<string, string> = {
  Passed: "#F1AB15",
  Failed: "#111111",
  "Not Enough Info": "#9CA3AF",
};

function Donut({ data }: { data: { label: string; value: number }[] }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  const r = 70;
  const c = 2 * Math.PI * r;
  let offset = 0;
  return (
    <div style={{ textAlign: "center" }}>
      <svg viewBox="0 0 200 200" width="220" height="220" role="img" aria-label="Donut chart of evaluation results by status">
        <circle cx="100" cy="100" r={r} fill="none" stroke="#f0ede6" strokeWidth="34" />
        {data.map((d) => {
          const len = (d.value / total) * c;
          const el = (
            <circle
              key={d.label}
              cx="100" cy="100" r={r} fill="none"
              stroke={STATUS_COLORS[d.label]} strokeWidth="34"
              strokeDasharray={`${len} ${c - len}`} strokeDashoffset={-offset}
              transform="rotate(-90 100 100)"
            >
              <title>{`${d.label}: ${d.value}`}</title>
            </circle>
          );
          offset += len;
          return el;
        })}
        <text x="100" y="96" textAnchor="middle" fontSize="26" fontWeight="700">{total}</text>
        <text x="100" y="118" textAnchor="middle" fontSize="12" fill="#6b6b6b">evaluations</text>
      </svg>
      <div className="legend">
        {data.map((d) => (
          <span key={d.label}>
            <span className="swatch" style={{ background: STATUS_COLORS[d.label] }} />
            {d.label} ({total ? Math.round((d.value / total) * 100) : 0}%)
          </span>
        ))}
      </div>
    </div>
  );
}

export default async function AdminDashboard({
  searchParams,
}: {
  searchParams: Promise<Filters>;
}) {
  if (!(await isAdmin())) redirect("/admin/login");

  const filters = await searchParams;
  const [summary, departments, records] = await Promise.all([
    getSummary(),
    getDepartmentProgress(),
    getEvaluationRecords(filters),
  ]);

  const passRate = summary.total ? `${Math.round((summary.passed / summary.total) * 100)}%` : "—";
  const exportQuery = new URLSearchParams(
    Object.entries(filters).filter(([, v]) => typeof v === "string" && v && v !== "All") as [string, string][],
  ).toString();

  const select = (name: keyof Filters, label: string, options: string[]) => (
    <div>
      <label className="field" htmlFor={name}>{label}</label>
      <select id={name} name={name} defaultValue={filters[name] ?? "All"}>
        {["All", ...options].map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </div>
  );

  return (
    <>
      <div className="head-row">
        <div>
          <h1>Chatbot evaluation dashboard</h1>
          <p className="caption">Monitor pilot testing results across all departments.</p>
        </div>
        <form method="post" action="/api/admin/logout">
          <button className="btn" type="submit">Log out</button>
        </form>
      </div>

      <div className="row" style={{ marginBottom: "1rem" }}>
        {[
          ["Total evaluations", summary.total],
          ["Pass rate", passRate],
          ["Passed", summary.passed],
          ["Failed", summary.failed],
          ["Not enough info", summary.not_enough_info],
        ].map(([label, value]) => (
          <div className="metric" key={label as string}>
            <div className="label">{label}</div>
            <div className="value">{value}</div>
          </div>
        ))}
      </div>

      <div className="row">
        <div className="card" style={{ flex: "1 1 320px" }}>
          <h3>Result distribution</h3>
          {summary.total > 0 ? (
            <Donut
              data={[
                { label: "Passed", value: summary.passed },
                { label: "Failed", value: summary.failed },
                { label: "Not Enough Info", value: summary.not_enough_info },
              ]}
            />
          ) : (
            <p className="caption">No evaluations have been submitted yet.</p>
          )}
        </div>

        <div className="card" style={{ flex: "2 1 480px" }}>
          <h3>Completion by department</h3>
          {departments.length ? (
            <div className="bars">
              {departments.map((d) => (
                <div className="bar-row" key={d.department}>
                  <span>{d.department}</span>
                  <div className="bar-track" title={`${d.evaluated_questions} of ${d.total_questions} questions evaluated`}>
                    <div className="bar-fill" style={{ width: `${Math.min(d.progress, 100)}%` }} />
                  </div>
                  <b>{Math.round(d.progress)}%</b>
                </div>
              ))}
            </div>
          ) : (
            <p className="caption">No department data available.</p>
          )}
        </div>
      </div>

      {departments.length > 0 && (
        <div className="card">
          <h3>Department progress</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Department</th><th>Total questions</th><th>Evaluated</th><th>Remaining</th><th>Completion</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((d) => (
                  <tr key={d.department}>
                    <td>{d.department}</td>
                    <td>{d.total_questions}</td>
                    <td>{d.evaluated_questions}</td>
                    <td>{d.remaining_questions}</td>
                    <td>{Math.round(d.progress)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <h2>Evaluation records</h2>
      <p className="caption">Review submitted chatbot evaluations and employee feedback.</p>

      <form className="card filters" method="get">
        {select("department", "Department", departments.map((d) => d.department))}
        {select("section", "Section", ["Information", "Action"])}
        {select("language", "Language", ["Amharic", "English"])}
        {select("status", "Evaluation status", ["Passed", "Failed", "Not Enough Info"])}
        <button className="btn btn-primary" type="submit">Apply filters</button>
      </form>

      {records.length ? (
        <>
          <div className="head-row" style={{ marginBottom: "0.5rem" }}>
            <span className="caption" style={{ margin: 0 }}>Found {records.length} evaluation records.</span>
            <a className="btn btn-primary" href={`/api/admin/export${exportQuery ? `?${exportQuery}` : ""}`}>
              Download evaluations as Excel
            </a>
          </div>
          <div className="table-wrap" style={{ maxHeight: "70vh" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Department</th><th>Section</th><th>Language</th><th>Question ID</th><th>Category</th>
                  <th>Question</th><th>Actual chatbot response</th><th>Status</th><th>Employee comment</th><th>Submitted at</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id}>
                    <td>{r.department}</td>
                    <td>{r.section}</td>
                    <td>{r.language}</td>
                    <td><b>{r.question_id}</b></td>
                    <td>{r.category}</td>
                    <td className="wide">{r.question_text}</td>
                    <td className="wide">{r.actual_answer}</td>
                    <td><span className={`badge badge-${r.status.replace(/\s/g, "")}`}>{r.status}</span></td>
                    <td className="wide">{r.comments}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      {new Date(r.submitted_at).toLocaleString("sv-SE", {
                        timeZone: "Africa/Addis_Ababa",
                        dateStyle: "short",
                        timeStyle: "short",
                      })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <div className="alert alert-info">No evaluation records match the selected filters.</div>
      )}
    </>
  );
}
