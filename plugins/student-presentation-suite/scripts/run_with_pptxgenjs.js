#!/usr/bin/env node

const { spawnSync } = require('node:child_process');
const { randomUUID } = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');
const Module = require('node:module');

function npmGlobalRoot() {
  // On Windows, Node 20+ blocks direct spawn of .cmd/.bat. Use a fixed cmd.exe
  // command with no user-controlled interpolation instead of shell: true.
  const result =
    process.platform === 'win32'
      ? spawnSync(process.env.ComSpec || 'cmd.exe', ['/d', '/s', '/c', 'npm root -g'], {
          encoding: 'utf8',
        })
      : spawnSync('npm', ['root', '-g'], { encoding: 'utf8' });
  return result.status === 0 ? result.stdout.trim() : '';
}

function candidateRoots() {
  const project = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const plugin = path.resolve(__dirname, '..');
  return [
    { source: 'project', root: project },
    { source: 'plugin', root: plugin },
    { source: 'global', root: npmGlobalRoot() },
  ].filter((item) => item.root);
}

function packageVersion(modulePath) {
  let dir = path.dirname(modulePath);
  while (dir !== path.dirname(dir)) {
    const candidate = path.join(dir, 'package.json');
    if (fs.existsSync(candidate)) {
      const pkg = JSON.parse(fs.readFileSync(candidate, 'utf8'));
      if (pkg.name === 'pptxgenjs') {
        return pkg.version;
      }
    }
    dir = path.dirname(dir);
  }
  throw new Error('pptxgenjs package.json was not found above the resolved module');
}

function resolveRuntime() {
  for (const candidate of candidateRoots()) {
    try {
      const modulePath = require.resolve('pptxgenjs', { paths: [candidate.root] });
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
    `pptxgenjs was not found. Try running:\n` +
      `  npm --prefix ${path.resolve(__dirname, '..')} ci\n` +
      `If the issue persists, install globally: npm install -g pptxgenjs`,
  );
}
const runtime = resolveRuntime();
const existing = process.env.NODE_PATH ? process.env.NODE_PATH.split(path.delimiter) : [];
const moduleRoot =
  runtime.source === 'global' ? runtime.root : path.join(runtime.root, 'node_modules');
// 把 scripts 目录也加入 NODE_PATH，让生成的 deck 可以 require("pptx-helpers")
const scriptsDir = __dirname;
process.env.NODE_PATH = [scriptsDir, moduleRoot, ...existing].filter(Boolean).join(path.delimiter);
process.env.PPTX_HELPERS_DIR = scriptsDir;
Module._initPaths();

if (process.argv[2] === '--probe') {
  process.stdout.write(JSON.stringify(runtime));
  process.exit(0);
}

const outputFlag = process.argv.indexOf('--output');
const output = outputFlag >= 0 ? process.argv[outputFlag + 1] : '';
const script = outputFlag >= 0 ? process.argv[outputFlag + 2] : '';
const deckArgs = outputFlag >= 0 ? process.argv.slice(outputFlag + 3) : [];
if (!script || !fs.existsSync(script) || !fs.statSync(script).isFile()) {
  // eslint-disable-next-line no-console
  console.error(
    'Usage: run_with_pptxgenjs.js --output <new-deck.pptx> <deck-script.js> [deck-args...]',
  );
  process.exit(2);
}
if (!output || !/\.(pptx|potx)$/i.test(output)) {
  // eslint-disable-next-line no-console
  console.error('--output must name a new .pptx or .potx file');
  process.exit(2);
}
const finalOutput = path.resolve(output);
if (fs.existsSync(finalOutput)) {
  // eslint-disable-next-line no-console
  console.error(`Refusing to overwrite existing output: ${finalOutput}`);
  process.exit(2);
}
const protectedInputs = [script, ...deckArgs]
  .filter((value) => typeof value === 'string' && fs.existsSync(value))
  .map((value) => path.resolve(value).toLowerCase());
if (protectedInputs.includes(finalOutput.toLowerCase())) {
  // eslint-disable-next-line no-console
  console.error(`Output must not be the deck script or an existing input: ${finalOutput}`);
  process.exit(2);
}

fs.mkdirSync(path.dirname(finalOutput), { recursive: true });
const token = randomUUID();
const extension = path.extname(finalOutput);
const stem = path.basename(finalOutput, extension);
const generated = path.join(path.dirname(finalOutput), `.${stem}.${token}.raw${extension}`);
const normalized = path.join(path.dirname(finalOutput), `.${stem}.${token}.normalized${extension}`);
try {
  const result = spawnSync(process.execPath, [path.resolve(script), generated, ...deckArgs], {
    stdio: 'inherit',
    env: process.env,
  });
  if (result.status !== 0) {
    process.exitCode = result.status === null ? 1 : result.status;
    return;
  }
  if (!fs.existsSync(generated) || !fs.statSync(generated).isFile()) {
    // eslint-disable-next-line no-console
    console.error(`Deck script did not create the requested output: ${generated}`);
    process.exitCode = 1;
    return;
  }
  const python = process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  const normalization = spawnSync(
    python,
    [
      path.join(__dirname, 'pptx_tool.py'),
      'normalize-generated',
      generated,
      '--output',
      normalized,
    ],
    { encoding: 'utf8', env: process.env },
  );
  if (normalization.status !== 0) {
    // eslint-disable-next-line no-console
    console.error(
      (normalization.stderr || normalization.stdout || 'PPTX normalization failed').trim(),
    );
    process.exitCode = normalization.status === null ? 1 : normalization.status;
    return;
  }
  // A same-directory hard link is atomic and fails with EEXIST on every
  // supported platform; rename() would overwrite a raced-in file on POSIX.
  fs.linkSync(normalized, finalOutput);
} finally {
  for (const temporary of [generated, normalized]) {
    try {
      fs.rmSync(temporary, { force: true });
    } catch (_) {
      // Preserve the primary failure; stale dot-files are safe to remove manually.
    }
  }
}
