import "server-only";
import { createHmac, pbkdf2Sync, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

export const SESSION_COOKIE = "boa_admin_session";
const SESSION_HOURS = 8;

function safeEqual(a: string, b: string) {
  const ab = Buffer.from(a);
  const bb = Buffer.from(b);
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

/** Verifies "salt$hash" (PBKDF2-SHA256, 600k) — identical to the Python auth_service. */
export function verifyPassword(password: string, stored: string) {
  const [salt, expected] = stored.split("$");
  if (!salt || !expected) return false;
  const actual = pbkdf2Sync(password, salt, 600_000, 32, "sha256").toString("hex");
  return safeEqual(actual, expected);
}

export function checkCredentials(username: string, password: string) {
  const user = process.env.ADMIN_USERNAME;
  const hash = process.env.ADMIN_PASSWORD_HASH;
  if (!user || !hash) return false;
  // Always run the hash so timing doesn't reveal whether the username matched.
  const passwordOk = verifyPassword(password, hash);
  return safeEqual(username.trim(), user) && passwordOk;
}

function secret() {
  const s = process.env.SESSION_SECRET;
  if (!s || s.length < 32) throw new Error("SESSION_SECRET must be set (32+ characters).");
  return s;
}

function sign(value: string) {
  return createHmac("sha256", secret()).update(value).digest("hex");
}

export function createSessionToken() {
  const expires = Date.now() + SESSION_HOURS * 3600 * 1000;
  const payload = `admin.${expires}`;
  return { token: `${payload}.${sign(payload)}`, maxAge: SESSION_HOURS * 3600 };
}

export function isValidSessionToken(token: string | undefined) {
  if (!token) return false;
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  const payload = `${parts[0]}.${parts[1]}`;
  if (!safeEqual(sign(payload), parts[2])) return false;
  return Number(parts[1]) > Date.now();
}

export async function isAdmin() {
  const store = await cookies();
  return isValidSessionToken(store.get(SESSION_COOKIE)?.value);
}
