import { redirect } from "next/navigation";
import { isAdmin } from "@/lib/auth";

export const dynamic = "force-dynamic";

export default async function AdminLogin({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>;
}) {
  if (await isAdmin()) redirect("/admin");
  const { error } = await searchParams;

  return (
    <div className="login-wrap">
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Admin login</h2>
        <p className="caption">Bank of Abyssinia · Chatbot evaluation platform</p>
        {error && <div className="alert alert-error">Invalid username or password.</div>}
        <form method="post" action="/api/admin/login">
          <label className="field" htmlFor="username">Username</label>
          <input id="username" name="username" type="text" autoComplete="username" required />
          <div style={{ height: "0.9rem" }} />
          <label className="field" htmlFor="password">Password</label>
          <input id="password" name="password" type="password" autoComplete="current-password" required />
          <button type="submit" className="btn btn-primary btn-block" style={{ marginTop: "1.25rem" }}>
            Log in
          </button>
        </form>
      </div>
    </div>
  );
}
