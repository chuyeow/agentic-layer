#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, existsSync, mkdirSync, readdirSync, renameSync, statSync, writeFileSync } from "node:fs";
import { basename, dirname, isAbsolute, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) continue;
    const key = arg.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

function run(command, args, options = {}) {
  return spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    encoding: "utf8",
    stdio: options.stdio || "pipe",
  });
}

function gitValue(args, fallback = "") {
  const result = run("git", args);
  return result.status === 0 ? result.stdout.trim() : fallback;
}

function slug(value) {
  return (value || "demo")
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "demo";
}

function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function hash(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

function currentDiffFingerprint() {
  const head = gitValue(["rev-parse", "HEAD"], "no-head");
  const ignored = /^(?:\.tmp\/verification\/|outputs\/verification\/)/;
  const status = gitValue(["status", "--short"], "")
    .split("\n")
    .filter((line) => !ignored.test(line.trim().slice(3).trim()))
    .join("\n");
  const diffNames = gitValue(["diff", "--name-only", "HEAD"], "")
    .split("\n")
    .filter((line) => line && !ignored.test(line))
    .join("\n");
  return hash([head, status, diffNames].join("\n"));
}

function ensureExampleHtml(outDir) {
  const fixture = join(outDir, "fixture.html");
  writeFileSync(fixture, `<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Verification Demo Fixture</title>
  <style>
    body { margin:0; font-family: Georgia, serif; background:#f5f1e8; color:#211f1b; }
    main { min-height:100vh; display:grid; place-items:center; padding:48px; }
    section { max-width:760px; }
    h1 { font-size:56px; margin:0 0 16px; letter-spacing:0; }
    p { font-size:22px; line-height:1.5; }
    .badge { display:inline-block; border:1px solid #211f1b; padding:6px 10px; font:14px ui-monospace, monospace; }
  </style>
</head>
<body>
  <main>
    <section>
      <span class="badge">verification fixture</span>
      <h1>Demo recording is working</h1>
      <p>This page is a local fixture used to prove the create-video-recording skill can produce a reviewer-facing video artifact.</p>
    </section>
  </main>
</body>
</html>`);
  return fixture;
}

function chromeBinary() {
  const candidates = [
    process.env.CHROME_BIN,
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ].filter(Boolean);
  return candidates.find((candidate) => existsSync(candidate));
}

function ffmpegBinary() {
  const which = run("which", ["ffmpeg"]);
  return which.status === 0 ? which.stdout.trim() : "";
}

async function recordWithPlaywright(url, outDir, durationMs) {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch {
    return null;
  }

  const videoDir = join(outDir, "playwright-video");
  mkdirSync(videoDir, { recursive: true });
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    recordVideo: { dir: videoDir, size: { width: 1280, height: 720 } },
  });
  const page = await context.newPage();
  const consoleMessages = [];
  const requestFailures = [];
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      consoleMessages.push(`${message.type()}: ${message.text()}`);
    }
  });
  page.on("requestfailed", (request) => {
    requestFailures.push(`${request.method()} ${request.url()} ${request.failure()?.errorText || ""}`);
  });
  await page.goto(url, { waitUntil: "networkidle", timeout: 45000 });
  await page.screenshot({ path: join(outDir, "screenshot.png"), fullPage: true });
  await page.waitForTimeout(durationMs);
  await context.close();
  await browser.close();

  const videos = readdirSync(videoDir)
    .filter((file) => file.endsWith(".webm"))
    .map((file) => join(videoDir, file))
    .sort((a, b) => statSync(b).mtimeMs - statSync(a).mtimeMs);
  if (!videos[0]) throw new Error("Playwright completed but no video was written.");
  const finalVideo = join(outDir, "demo.webm");
  renameSync(videos[0], finalVideo);
  return { videoPath: finalVideo, mode: "playwright", consoleMessages, requestFailures };
}

function recordWithChromeFfmpeg(url, outDir, durationMs) {
  const chrome = chromeBinary();
  const ffmpeg = ffmpegBinary();
  if (!chrome || !ffmpeg) {
    throw new Error(`Missing recorder dependencies: chrome=${chrome || "not found"} ffmpeg=${ffmpeg || "not found"}`);
  }

  const framesDir = join(outDir, "frames");
  mkdirSync(framesDir, { recursive: true });
  const frameCount = Math.max(3, Math.min(8, Math.ceil(durationMs / 1500)));
  for (let i = 0; i < frameCount; i += 1) {
    const frame = join(framesDir, `frame-${String(i + 1).padStart(3, "0")}.png`);
    const budget = String(1000 + i * 500);
    const result = run(chrome, [
      "--headless=new",
      "--disable-gpu",
      "--hide-scrollbars",
      "--no-first-run",
      "--no-default-browser-check",
      "--window-size=1280,720",
      `--virtual-time-budget=${budget}`,
      `--screenshot=${frame}`,
      url,
    ]);
    if (result.status !== 0 || !existsSync(frame)) {
      throw new Error(`Chrome screenshot failed: ${result.stderr || result.stdout}`);
    }
  }

  const screenshotPath = join(outDir, "screenshot.png");
  copyFileSync(join(framesDir, "frame-001.png"), screenshotPath);
  const videoPath = join(outDir, "demo.mp4");
  const ffmpegResult = run(ffmpeg, [
    "-y",
    "-framerate",
    "1",
    "-i",
    join(framesDir, "frame-%03d.png"),
    "-vf",
    "fps=12,format=yuv420p",
    "-movflags",
    "+faststart",
    videoPath,
  ]);
  if (ffmpegResult.status !== 0 || !existsSync(videoPath)) {
    throw new Error(`ffmpeg video encode failed: ${ffmpegResult.stderr || ffmpegResult.stdout}`);
  }
  return { videoPath, mode: "chrome-ffmpeg", consoleMessages: [], requestFailures: [] };
}

function rel(path) {
  return path.startsWith(process.cwd()) ? path.slice(process.cwd().length + 1) : path;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const title = args.title || "Video verification";
  const scenario = args.scenario || "Open the target and verify the changed surface renders.";
  const branch = slug(gitValue(["rev-parse", "--abbrev-ref", "HEAD"], "unknown-branch"));
  const commit = gitValue(["rev-parse", "HEAD"], "unknown");
  const outDir = resolve(args["output-dir"] || join("outputs", "verification", branch, timestamp()));
  mkdirSync(outDir, { recursive: true });

  let target = args.url;
  if (args.html) {
    const htmlPath = isAbsolute(args.html) ? args.html : resolve(args.html);
    if (!existsSync(htmlPath)) throw new Error(`HTML target not found: ${htmlPath}`);
    target = pathToFileURL(htmlPath).href;
  }
  if (args.example) {
    target = pathToFileURL(ensureExampleHtml(outDir)).href;
  }
  if (!target) {
    throw new Error("Provide --url, --html, or --example.");
  }

  const durationMs = Number(args.duration || 6000);
  let result = await recordWithPlaywright(target, outDir, durationMs);
  if (!result) {
    result = recordWithChromeFfmpeg(target, outDir, durationMs);
  }

  const videoRel = rel(result.videoPath);
  const screenshotRel = rel(join(outDir, "screenshot.png"));
  const snippet = `## Verification

- [x] Demo recording: ${videoRel}
- [x] Screenshot: ${screenshotRel}
- [x] Covered: ${scenario}
- [ ] Not covered: Automated checks not supplied to recorder
`;

  const manifest = {
    title,
    scenario,
    target,
    branch,
    commit,
    diffFingerprint: currentDiffFingerprint(),
    createdAt: new Date().toISOString(),
    mode: result.mode,
    videoPath: videoRel,
    screenshotPath: screenshotRel,
    outputDir: rel(outDir),
    consoleMessages: result.consoleMessages,
    requestFailures: result.requestFailures,
    verificationSnippet: snippet,
  };

  const manifestPath = join(outDir, "manifest.json");
  const verificationPath = join(outDir, "verification.md");
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`);
  writeFileSync(verificationPath, snippet);
  mkdirSync(".tmp/verification", { recursive: true });
  writeFileSync(".tmp/verification/latest-video.json", `${JSON.stringify({ ...manifest, manifestPath: rel(manifestPath) }, null, 2)}\n`);
  console.log(JSON.stringify({ manifestPath: rel(manifestPath), videoPath: videoRel, mode: result.mode }, null, 2));
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
