import "server-only";
import { neon, type NeonQueryFunction } from "@neondatabase/serverless";

let client: NeonQueryFunction<false, false> | null = null;

/** Neon HTTP client — stateless, ideal for Vercel serverless functions. */
export function db() {
  if (client) return client;

  const raw = process.env.DATABASE_URL;
  if (!raw) throw new Error("DATABASE_URL is not configured.");

  // Accept the Python/SQLAlchemy form too ("postgresql+psycopg://...").
  const url = raw.replace(/^postgres(ql)?\+[a-z0-9]+:\/\//i, "postgresql://");
  client = neon(url);
  return client;
}

export function isUniqueViolation(error: unknown) {
  return (
    typeof error === "object" &&
    error !== null &&
    "code" in error &&
    (error as { code?: string }).code === "23505"
  );
}
