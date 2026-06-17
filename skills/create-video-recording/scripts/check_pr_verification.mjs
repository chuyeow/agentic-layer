#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

function run(command, args) {
  return spawnSync(command, args, { encoding: "utf8", stdio: "pipe" });
}

function git(args, fallback = "") {
  const result = run("git", args);
  return result.status === 0 ? result.stdout.trim() : fallback;
}

function hash(value) {
  return createHash("sha256").update(value).digest("hex").slice(0, 16);
}

function currentDiffFingerprint() {
  const head = git(["rev-parse", "HEAD"], "no-head");
  const ignored = /^(?:\.tmp\/verification\/|outputs\/verification\/)/;
  const status = git(["status", "--short"], "")
    .split("\n")
    .filter((line) => !ignored.test(line.trim().slice(3).trim()))
    .join("\n");
  const diffNames = git(["diff", "--name-only", "HEAD"], "")
    .split("\n")
    .filter((line) => line && !ignored.test(line))
    .join("\n");
  return hash([head, status, diffNames].join("\n"));
}

function changedFiles() {
  const ignored = /^(?:\.tmp\/verification\/|outputs\/verification\/)/;
  const status = git(["status", "--short"], "");
  return status
    .split("\n")
    .map((line) => line.trim().slice(3).trim())
    .filter((line) => line && !ignored.test(line));
}

function requiresVideo(files) {
  const visible = /\.(tsx|jsx|vue|svelte|css|scss|sass|less|html|htm|svg|png|jpg|jpeg|webp)$/i;
  const report = /(^|\/)(app|pages|components|views|screens|ui|reports|outputs|docs\/agentic-engineering)\//i;
  return files.some((file) => visible.test(file) || (report.test(file) && /\.(md|html)$/i.test(file)));
}

function deny(reason) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: reason,
    },
  }));
}

function allowWithContext(message) {
  console.log(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      additionalContext: message,
    },
  }));
}

let input = {};
try {
  const raw = await new Promise((resolveRead) => {
    let data = "";
    process.stdin.on("data", (chunk) => { data += chunk; });
    process.stdin.on("end", () => resolveRead(data));
  });
  input = raw.trim() ? JSON.parse(raw) : {};
} catch {
  input = {};
}

const command = input.tool_input?.command || process.argv.slice(2).join(" ");
if (!/\bgh\s+pr\s+create\b/.test(command)) {
  process.exit(0);
}

const files = changedFiles();
if (!requiresVideo(files)) {
  allowWithContext("No video verification required: no visible UI/report files detected in git status.");
  process.exit(0);
}

const manifestPath = resolve(".tmp/verification/latest-video.json");
if (!existsSync(manifestPath)) {
  deny(`Video verification required before PR.

Run:
  node skills/create-video-recording/scripts/record_web_demo.mjs --url <demo-url> --title "<title>" --scenario "<what this proves>"

Then include the generated Verification snippet in the PR body.`);
  process.exit(0);
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const videoPath = manifest.videoPath ? resolve(manifest.videoPath) : "";
if (manifest.diffFingerprint !== currentDiffFingerprint()) {
  deny(`Video verification is stale for the current diff.

Last recording: ${manifest.createdAt || "unknown"}
Run create-video-recording again, then retry gh pr create.`);
  process.exit(0);
}
if (!videoPath || !existsSync(videoPath)) {
  deny(`Video manifest exists but video file is missing: ${manifest.videoPath || "(none)"}`);
  process.exit(0);
}

allowWithContext(`Fresh video verification found. Use this in the PR body:\n\n${manifest.verificationSnippet || ""}`);
