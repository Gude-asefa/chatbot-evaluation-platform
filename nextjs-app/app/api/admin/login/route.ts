import { NextRequest, NextResponse } from "next/server";
import { checkCredentials, createSessionToken, SESSION_COOKIE } from "@/lib/auth";

export async function POST(req: NextRequest) {
  const form = await req.formData();
  const username = String(form.get("username") ?? "");
  const password = String(form.get("password") ?? "");

  if (!checkCredentials(username, password)) {
    return NextResponse.redirect(new URL("/admin/login?error=1", req.url), 303);
  }

  const { token, maxAge } = createSessionToken();
  const res = NextResponse.redirect(new URL("/admin", req.url), 303);
  res.cookies.set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "strict",
    path: "/",
    maxAge,
  });
  return res;
}
