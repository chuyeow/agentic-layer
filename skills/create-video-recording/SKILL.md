---
name: create-video-recording
description: Create PR-ready video verification artifacts for UI, report, browser, visual, or human-reviewable changes. Use when the user asks to record a demo, create a video recording, demo this, make a verification video, produce proof for a PR, prepare the PR Verification section, or when a change is demoable before review. Also use before `gh pr create` for product-visible changes and when building verification reports that should embed or link to a demo video.
---

# Create Video Recording

Create a short reviewer-facing proof artifact: video, screenshot, manifest, and a PR-ready Verification snippet. Prefer a real browser recording; do not fake proof. If recording cannot run, report the exact blocker and fallback artifact.

## Decision

Record video when the change affects:

- UI, CSS, layout, browser flow, chart, dashboard, generated HTML, or report rendering
- visible product behavior, onboarding, checkout, booking, search, payments, or admin surfaces
- a demoable checkpoint the user should review before more work

Skip video only when the change is clearly backend-only, docs-only, tests-only, or config-only. If skipping before PR, write the reason in the Verification section.

## Workflow

1. Resolve the demo target:
   - URL, local HTML file, report file, or dev server route
   - expected behavior to prove
   - commands already run, such as lint/typecheck/tests
2. Run the recorder:

   ```bash
   node skills/create-video-recording/scripts/record_web_demo.mjs \
     --url http://127.0.0.1:3000 \
     --title "Checkout verification" \
     --scenario "Open checkout, verify payment CTA remains visible"
   ```

   For a local HTML report:

   ```bash
   node skills/create-video-recording/scripts/record_web_demo.mjs \
     --html outputs/report/index.html \
     --title "Report verification" \
     --scenario "Open report and verify charts render"
   ```

3. Read `.tmp/verification/latest-video.json`.
4. Include the generated `verificationSnippet` under the PR `## Verification` section.
5. If a richer report is needed, run:

   ```bash
   node skills/create-video-recording/scripts/build_verification_report.mjs \
     --manifest .tmp/verification/latest-video.json
   ```

6. If publishing externally for reviewers, use `publish-to-wego-hub` on the generated `index.html` and video file.

## Output Contract

The recorder writes:

- `outputs/verification/<branch>/<timestamp>/demo.webm` or `demo.mp4`
- `outputs/verification/<branch>/<timestamp>/screenshot.png`
- `outputs/verification/<branch>/<timestamp>/manifest.json`
- `outputs/verification/<branch>/<timestamp>/verification.md`
- `.tmp/verification/latest-video.json`

The manifest must include branch, commit, diff fingerprint, scenario, artifact paths, and `verificationSnippet`.

## PR Gate

The companion hook blocks `gh pr create` only when a video-requiring file changed and no fresh manifest exists for the current diff. It should not guess the demo scenario or silently generate a meaningless recording inside the hook. Run this skill first, then retry PR creation.

## Scripts

- `scripts/record_web_demo.mjs` — record or construct a real browser-derived demo artifact.
- `scripts/build_verification_report.mjs` — turn a manifest into a standalone HTML verification report.
- `scripts/check_pr_verification.mjs` — hook-safe pre-PR freshness check.

If Playwright is installed, the recorder uses Playwright video capture. Otherwise it falls back to Chrome/Brave headless screenshots stitched by `ffmpeg`. If both paths fail, stop and report the blocker.
