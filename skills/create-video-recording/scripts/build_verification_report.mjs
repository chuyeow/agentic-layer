#!/usr/bin/env node
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    if (!argv[i].startsWith("--")) continue;
    args[argv[i].slice(2)] = argv[i + 1];
    i += 1;
  }
  return args;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function mediaTag(manifest, outDir) {
  const video = manifest.videoPath || "";
  const screenshot = manifest.screenshotPath || "";
  const videoName = video.split("/").pop();
  const screenshotName = screenshot.split("/").pop();
  if (videoName && existsSync(join(outDir, videoName))) {
    return `<video controls src="${escapeHtml(videoName)}"></video>`;
  }
  if (screenshotName && existsSync(join(outDir, screenshotName))) {
    return `<img alt="Verification screenshot" src="${escapeHtml(screenshotName)}">`;
  }
  return "<p>No media artifact found.</p>";
}

const args = parseArgs(process.argv.slice(2));
const manifestPath = resolve(args.manifest || ".tmp/verification/latest-video.json");
if (!existsSync(manifestPath)) {
  console.error(`Manifest not found: ${manifestPath}`);
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const outDir = resolve(dirname(manifestPath));
const actualOutDir = manifest.outputDir ? resolve(manifest.outputDir) : outDir;
const scriptDir = dirname(fileURLToPath(import.meta.url));
const templatePath = resolve(scriptDir, "..", "assets", "report-template.html");
const template = readFileSync(templatePath, "utf8");
const html = template
  .replaceAll("{{TITLE}}", escapeHtml(manifest.title || "Video verification"))
  .replaceAll("{{META}}", escapeHtml(`${manifest.branch || "unknown"} · ${manifest.commit || "unknown"} · ${manifest.createdAt || ""}`))
  .replaceAll("{{MEDIA}}", mediaTag(manifest, actualOutDir))
  .replaceAll("{{SCENARIO}}", escapeHtml(manifest.scenario || ""))
  .replaceAll("{{SNIPPET}}", escapeHtml(manifest.verificationSnippet || ""));

const reportPath = join(actualOutDir, "index.html");
writeFileSync(reportPath, html);
console.log(reportPath);
