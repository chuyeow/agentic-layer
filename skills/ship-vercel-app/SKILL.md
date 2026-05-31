---
name: ship-vercel-app
description: Deploy a local web app idea from this Mac to production using a new GitHub repository and Vercel GitOps. Use when the user asks to ship, launch, deploy, productionize, or publish a local app/site from ~/code or another local folder, especially with GitHub, Vercel, custom domains, Cloudflare DNS, or "from this Mac mini to production".
---

# Ship Vercel App

## Operating Rules

- Treat deployment as code plus live infrastructure: inspect, change, verify, then report exact URLs.
- Prefer existing local patterns. If no app exists, scaffold the smallest production-viable app.
- Keep the functional core separate from the imperative shell when implementing app logic.
- Use CLI as the primary path: `rg`, `git`, `gh`, `npm`, `vercel`, `wrangler`, `dig`, `curl`, and browser verification.
- Create new GitHub repos as private by default unless the user explicitly asks for public.
- Use real GitHub Markdown links, e.g. `[pay.chuyeow.wtf](https://pay.chuyeow.wtf)`, not bare URLs.
- Never print API tokens. Read tokens from files at runtime if needed.
- Stop before destructive DNS or git changes unless the user explicitly approves.

## Workflow

1. Orient.
   - Confirm repo path with `pwd`, `git status --short --branch`, `rg --files`.
   - Read `README`, package files, framework config, and local instructions.
   - If the app idea is not implemented yet, build it first with focused tests and browser QA.

2. Harden locally.
   - Install dependencies only when needed.
   - Run the handoff gate that exists for the project: usually `npm test`, `npm run build`, `npm audit --audit-level=high`, plus lint/typecheck if configured.
   - For frontend apps, run the dev server and verify the real UI in a browser at desktop and mobile sizes. Check console errors and obvious layout overflow.

3. Prepare GitHub.
   - Create the repo with `gh repo create <owner>/<repo> --private --source . --remote origin --push` unless the user asked for public.
   - If SSH fails, use the user's documented SSH helper or switch to HTTPS after confirming auth.

4. Create Vercel project.
   - Use installed `vercel` when present; otherwise use `npx -y vercel@latest`.
   - Log in with `vercel login` if needed.
   - Link/import the project, then connect GitHub with `vercel git connect`.
   - Set framework/build/output settings explicitly when Vercel guesses wrong.
   - Push to the production branch to trigger the GitOps deployment.

5. Add domain.
   - Add the custom domain to Vercel, then inspect the required DNS record. Do not assume the record shape.
   - For Cloudflare-managed DNS, prefer DNS-only records for Vercel verification.
   - Wrangler OAuth may not expose DNS edit scope. If DNS writes are needed, use a scoped Cloudflare API token with `Zone:Zone:Read` and `Zone:DNS:Edit`, read from `/Users/chuyeow/.config/cloudflare/dns-token` when present.
   - Before writing DNS, list existing records for the hostname. Create/update one matching record only. If CNAME/NS conflicts or multiple A records exist, stop and ask.
   - Verify the custom domain end to end: Vercel alias, public DNS, HTTP, HTTPS, and browser sanity check.

6. Verify production.
   - Check Vercel deployment status until `READY`.
   - Verify alias attachment with `vercel alias ls`.
   - Verify DNS with `dig +short <host>`.
   - Verify HTTP and HTTPS with `curl -I`; if HTTP works but HTTPS fails, run `vercel certs issue <host>` and recheck HTTPS.
   - Open the production URL in a browser and sanity-check the app.

7. Close out.
   - Report the GitHub repo, Vercel project/deployment, production URL, custom domain, DNS record, commit SHA, and checks run.
   - Mention anything intentionally left manual, time-dependent, or blocked.
