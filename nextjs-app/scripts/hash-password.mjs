// Usage: npm run hash-password -- "my-password"
// Prints "salt$hash" (PBKDF2-SHA256, 600k iterations) — same format as the Streamlit app.
import { pbkdf2Sync, randomBytes } from "node:crypto";

const password = process.argv[2];
if (!password) {
  console.error('Usage: npm run hash-password -- "your-password"');
  process.exit(1);
}
const salt = randomBytes(16).toString("hex");
const hash = pbkdf2Sync(password, salt, 600_000, 32, "sha256").toString("hex");
console.log(`${salt}$${hash}`);
