// Local development on the bank network only.
// The corporate proxy re-signs HTTPS traffic, which makes the Neon driver fail with
// SELF_SIGNED_CERT_IN_CHAIN. This makes Node trust the Windows certificate store
// (where the corporate root CA lives). TLS verification stays fully enabled.
// Not needed on Vercel.
import { spawn } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const nextBin = require.resolve("next/dist/bin/next");

const child = spawn(process.execPath, [nextBin, "dev", ...process.argv.slice(2)], {
  stdio: "inherit",
  env: {
    ...process.env,
    NODE_OPTIONS: `${process.env.NODE_OPTIONS ?? ""} --use-system-ca`.trim(),
  },
});
child.on("exit", (code) => process.exit(code ?? 0));
