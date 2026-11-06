# Chatbot Evaluation Platform — Next.js (Vercel)

Next.js version of the Streamlit chatbot pilot-testing app. It uses the **same Neon Postgres
database and tables**, so existing questions, evaluations and submission locks carry over.

| Page | URL | Who |
|---|---|---|
| Tester evaluation form | `/` | Share this link with testers |
| Admin dashboard (+ Excel export) | `/admin` | Admins only (login required) |

## Deploy to Vercel

1. **Push to GitHub.** Commit the `nextjs-app/` folder to the existing repository
   (`.env.local` is git-ignored and is never committed).
2. **Import the project** at <https://vercel.com/new> → pick the GitHub repository.
3. **Set Root Directory to `nextjs-app`.** Framework preset: Next.js (auto-detected).
4. **Add environment variables** (Project → Settings → Environment Variables):

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | Neon **pooled** connection string, `postgresql://…-pooler…/neondb?sslmode=require` |
   | `ADMIN_USERNAME` | Admin username |
   | `ADMIN_PASSWORD_HASH` | Output of `npm run hash-password -- "<password>"` (the hash from the Streamlit `.env` also works) |
   | `SESSION_SECRET` | 64-character random hex: `node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"` |

5. **Deploy.** Vercel gives you a URL like `https://<project>.vercel.app` to share.
   Testers use the root URL and admins use `/admin`.

> Tip: In Vercel → Settings → Functions, set the region close to the Neon database
> (currently `us-west-2` → Vercel `pdx1`/`sfo1`) to reduce query latency.

## Run locally

```bash
cd nextjs-app
npm install
cp .env.example .env.local   # then fill in the values
npm run dev                  # http://localhost:3000
```

**On the bank network** use `npm run dev:corp` instead. The corporate proxy re-signs HTTPS
traffic, so Node rejects the Neon connection with `SELF_SIGNED_CERT_IN_CHAIN`. `dev:corp`
makes Node trust the Windows certificate store; TLS verification stays enabled. Vercel
does not need this.

## How it works

- **Device lock:** each browser gets a random UUID in `localStorage` (same key as the
  Streamlit app). The `submissions` table's unique constraint allows one submission per
  device × department × section × language. The submission lock and the evaluations are
  written in a single transaction.
- **Validation** (shared by browser and server, in `lib/evaluation.ts`): every question needs a
  status. Failed / Not Enough Info need the actual response. Not Enough Info needs a comment.
  Action questions only allow Passed / Failed.
- **Admin auth:** PBKDF2-SHA256 password hash (same format as the Python app), plus an
  HMAC-signed, `HttpOnly`, `SameSite=Strict` cookie that expires after 8 hours.
- **Expected answers are never sent to the browser.**

## Project layout

```
app/
  page.tsx, EvaluationApp.tsx     tester form (client component)
  admin/page.tsx                  dashboard (server-rendered)
  admin/login/page.tsx            admin login
  api/departments|questions|submissions|evaluations   public API
  api/admin/login|logout|export   admin API (export = .xlsx)
lib/  db.ts (Neon), auth.ts, dashboard.ts, evaluation.ts (shared rules)
db/schema.sql                     reference schema for a fresh database
scripts/hash-password.mjs         generate ADMIN_PASSWORD_HASH
```

## Security notes (review before sharing widely)

- The tester page has **no login**, the same as the Streamlit app. Anyone with the link can
  submit evaluations. The device lock stops repeat submissions but not deliberate abuse
  (for example, private windows or cleared storage). If the link will be shared beyond
  trusted staff, consider adding Vercel Deployment Protection, a shared access code, or SSO.
- The app is public on the internet once deployed. Confirm with IT Security / Compliance
  that hosting this data (test questions and chatbot responses, no customer data) on
  Vercel + Neon (US region) is acceptable under Bank policy.
- Rotate the Neon database password if it has ever been shared or committed, and store it
  only in Vercel's encrypted environment variables.
