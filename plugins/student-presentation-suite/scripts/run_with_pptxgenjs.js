#!/usr/bin/env node

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const Module = require("node:module");

function npmGlobalRoot() {
  const npm = process.platform === "win32" ? "npm.cmd" : "npm";
  const result = spawnSync(npm, ["root", "-g"], { encoding: "utf8", shell: false });
  return result.status === 0 ? result.stdout.trim() : "";
}

function candidateRoots() {
  const project = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const plugin = path.resolve(__dirname, "..");
  return [
    { source: "project", root: project },
    { source: "plugin", root: plugin },
    { source: "global", root: npmGlobalRoot() },
  ].filter((item) => item.root);
}

function packageVersion(modulePath) {
  let dir = path.dirname(modulePath);
  while (dir !== path.dirname(dir)) {
    const candidate = path.join(dir, "package.json");
    if (fs.existsSync(candidate)) {
      const pkg = JSON.parse(fs.readFileSync(candidate, "utf8"));
      if (pkg.name === "pptxgenjs") {
        return pkg.version;
      }
    }
    dir = path.dirname(dir);
  }
  throw new Error("pptxgenjs package.json was not found above the resolved module");
}

function resolveRuntime() {
  for (const candidate of candidateRoots()) {
    try {
      const modulePath = require.resolve("pptxgenjs", { paths: [candidate.root] });
      return {
        ...candidate,
        modulePath,
        version: packageVersion(modulePath),
      };
    } catch (_) {
      // Continue to the next supported location.
    }
  }
  throw new Error(
    "pptxgenjs was not found. Try running:\n" +
    "  npm --prefix " + path.resolve(__dirname, "..") + " ci\n" +
    "If the issue persists, install globally: npm install -g pptxgenjs"
  );
}

const runtime = resolveRuntime();
const existing = process.env.NODE_PATH ? process.env.NODE_PATH.split(path.delimiter) : [];
const moduleRoot =
  runtime.source === "global" ? runtime.root : path.join(runtime.root, "node_modules");
// 把 scripts 目录也加入 NODE_PATH，让生成的 deck 可以 require("pptx-helpers")
const scriptsDir = __dirname;
process.env.NODE_PATH = [scriptsDir, moduleRoot, ...existing]
  .filter(Boolean)
  .join(path.delimiter);
process.env.PPTX_HELPERS_DIR = scriptsDir;
Module._initPaths();

if (process.argv[2] === "--probe") {
  process.stdout.write(JSON.stringify(runtime));
  process.exit(0);
}

const script = process.argv[2];
if (!script || !fs.existsSync(script) || !fs.statSync(script).isFile()) {
  console.error("Usage: run_with_pptxgenjs.js <deck-script.js> [args...]");
  process.exit(2);
}

const result = spawnSync(process.execPath, [path.resolve(script), ...process.argv.slice(3)], {
  stdio: "inherit",
  env: process.env,
});
process.exit(result.status === null ? 1 : result.status);
