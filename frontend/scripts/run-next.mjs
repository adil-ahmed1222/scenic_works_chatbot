import { spawn } from "child_process";
import { createRequire } from "module";
import path from "path";
import { fileURLToPath } from "url";

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const nextBin = createRequire(import.meta.url).resolve("next/dist/bin/next");
const args = process.argv.slice(2);
if (args[0] === "start" && !args.includes("--port") && process.env.PORT) {
  args.push("--port", String(process.env.PORT));
}

const child = spawn(process.execPath, [nextBin, ...args], {
  cwd: frontend,
  stdio: "inherit",
  env: {
    ...process.env,
    NODE_PATH: path.join(frontend, "node_modules"),
  },
});

child.on("exit", (code) => process.exit(code ?? 0));
