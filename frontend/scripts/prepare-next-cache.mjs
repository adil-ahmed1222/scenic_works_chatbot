/**
 * OneDrive Files On-Demand turns Next.js cache files into cloud placeholders.
 * Next.js then crashes with EINVAL on readlink.
 *
 * distDir stays a relative folder (.next-local) so Next.js accepts it.
 * That folder is a junction to %LOCALAPPDATA%, so file contents are not on OneDrive.
 */
import { existsSync, mkdirSync, readlinkSync, rmSync } from "fs";
import { spawnSync } from "child_process";
import os from "os";
import path from "path";
import { fileURLToPath } from "url";

const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const cacheDir = path.join(
  process.env.LOCALAPPDATA || path.join(os.homedir(), "AppData", "Local"),
  "scenic-works-chat-widget",
  "next-cache"
);
const localLink = path.join(frontend, ".next-local");

function removeDir(target) {
  if (!existsSync(target)) return;
  try {
    rmSync(target, { recursive: true, force: true });
  } catch {
    spawnSync("cmd.exe", ["/c", `rmdir /s /q "${target}"`], { stdio: "ignore" });
  }
}

function unlinkOrRemove(target) {
  spawnSync("cmd.exe", ["/c", `rmdir "${target}"`], { stdio: "ignore" });
  removeDir(target);
}

function junctionTarget(dir) {
  try {
    return path.resolve(readlinkSync(dir));
  } catch {
    return null;
  }
}

if (process.platform !== "win32" || process.env.VERCEL) {
  process.exit(0);
}

for (const name of [".next", ".next.nosync"]) {
  unlinkOrRemove(path.join(frontend, name));
}

mkdirSync(cacheDir, { recursive: true });

const nmLink = path.join(cacheDir, "node_modules");
const nmReal = path.join(frontend, "node_modules");
if (junctionTarget(nmLink) !== path.resolve(nmReal)) {
  unlinkOrRemove(nmLink);
  spawnSync("cmd.exe", ["/c", `mklink /J "${nmLink}" "${nmReal}"`], {
    stdio: "ignore",
  });
}

if (junctionTarget(localLink) !== path.resolve(cacheDir)) {
  unlinkOrRemove(localLink);
  const linked = spawnSync(
    "cmd.exe",
    ["/c", `mklink /J "${localLink}" "${cacheDir}"`],
    { encoding: "utf8" }
  );
  if (linked.status !== 0) {
    mkdirSync(localLink, { recursive: true });
  }
}
