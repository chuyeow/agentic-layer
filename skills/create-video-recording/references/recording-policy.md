# Recording Policy

## Good Proof

- Show the actual changed surface, not a generic landing page.
- Keep recordings short: usually 10-30 seconds.
- Include the assertion in the scenario text.
- Capture console and network failures when Playwright is available.
- Prefer local/staging data; avoid production writes.

## Required Verification Snippet

Use this shape in PR descriptions:

```md
## Verification

- [x] Automated checks: `<command>`
- [x] Demo recording: <path-or-url>
- [x] Covered: <scenario>
- [ ] Not covered: <gap, if any>
```

## Skip Rule

If a visible change has no video, the PR must say why. Acceptable reasons:

- browser automation unavailable in the current environment
- no runnable UI/report target exists
- reviewer explicitly accepted screenshot-only proof

Do not mark video verification complete without an artifact.
