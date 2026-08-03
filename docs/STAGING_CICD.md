# Staging CI/CD (GitHub Actions → GHCR → VPS over SSH)

This repo ships a corporate-style staging pipeline:

| Workflow | Trigger | What it does |
|---|---|---|
| `.github/workflows/ci.yml` | PRs + pushes to `staging`/`main` | Install lockfiles, lint, typecheck, build, secret scan, CodeQL, Hadolint, dependency audits |
| `.github/workflows/deploy-staging.yml` | Push to **`staging`** (or manual) | Run CI → build/push images to GHCR → Trivy + SBOM → SSH deploy → smoke tests |

## Architecture

```text
developer → PR → CI gates → merge to staging
staging push → build images → GHCR → SSH/VPS docker compose → smoke checks
```

## One-time GitHub setup

### 1. Create Environment `staging`

Repo → **Settings → Environments → New environment** → name: `staging`

Recommended protection:

- Required reviewers (1+)
- Deployment branches: only `staging`

### 2. Environment / repository secrets

Add these under the `staging` environment (preferred) or repo secrets:

| Secret | Example | Purpose |
|---|---|---|
| `STAGING_HOST` | `203.0.113.10` | VPS hostname or IP |
| `STAGING_USER` | `deploy` | SSH user (docker group) |
| `STAGING_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Private key (full PEM) |
| `STAGING_SSH_PORT` | `22` | Optional (default 22) |
| `STAGING_DEPLOY_PATH` | `/home/deploy/adzmate` | **Absolute** deploy directory on the VPS |
| `STAGING_WEB_URL` | `http://203.0.113.10:3000` | Public web URL (smoke + env URL) |
| `STAGING_API_URL` | `http://203.0.113.10:8000` | Public API URL (smoke + Next build arg) |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxx.supabase.co` | Baked into web image |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJ...` | Baked into web image |
| `GHCR_PULL_TOKEN` | PAT with `read:packages` | Optional long-lived pull token for private GHCR |
| `GHCR_PULL_USER` | `your-github-username` | Optional; defaults to the workflow actor |

App runtime secrets (Gemini, Meta, JWT, etc.) live on the VPS in `.env.staging`, not necessarily in GitHub.

### 3. Branch protection for `staging`

Require status checks:

- `Web — install, lint, typecheck, build`
- `API — install, lint, dependency check`
- `Secret scan (Gitleaks)`
- `CodeQL SAST`
- `Dockerfile lint (Hadolint)`

Require PRs, dismiss stale reviews, optionally require CODEOWNERS.

> Update `.github/CODEOWNERS` with your real GitHub usernames.

### 4. Package permissions

Actions already use `packages: write` with `GITHUB_TOKEN` to push `ghcr.io/<owner>/adzmate-api` and `adzmate-web`.

If the VPS cannot pull private packages, create a fine-grained PAT (`read:packages`) and change the deploy step to use `secrets.GHCR_PULL_TOKEN` instead of `GITHUB_TOKEN`.

## One-time VPS setup

1. Install Docker Engine + Compose plugin.
2. Create a non-root user in the `docker` group (e.g. `deploy`).
3. Add the matching public SSH key for `STAGING_SSH_KEY`.
4. Copy staging files:

```bash
mkdir -p ~/adzmate/scripts
# from your laptop / CI artifact:
scp docker-compose.staging.yml .env.staging.example deploy@HOST:~/adzmate/
scp scripts/deploy-staging.sh scripts/bootstrap-staging-vps.sh deploy@HOST:~/adzmate/scripts/
ssh deploy@HOST 'cp ~/adzmate/.env.staging.example ~/adzmate/.env.staging && chmod 600 ~/adzmate/.env.staging'
```

5. Edit `~/adzmate/.env.staging` with real Supabase/JWT/CORS/public URLs.
6. Run `bash ~/adzmate/scripts/bootstrap-staging-vps.sh`.

Open firewall ports **3000** (web) and **8000** (api), or put Nginx/Caddy in front with TLS and only expose 443.

## Day-to-day flow

1. Open a PR into `staging` → CI must be green.
2. Merge → `Deploy Staging` runs automatically.
3. Confirm smoke job + open `STAGING_WEB_URL`.

Manual redeploy: **Actions → Deploy Staging → Run workflow**.

## Local image build (optional)

```bash
docker build -f apps/api/Dockerfile -t adzmate-api:local .
docker build -f apps/web/Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  --build-arg API_INTERNAL_URL=http://api:8000 \
  -t adzmate-web:local .
```

## Notes

- `NEXT_PUBLIC_*` values are compile-time for Next.js — changing Supabase URL requires a new web image build.
- Gitleaks org license may be required for some private org repos; personal/public usually works.
- CodeQL SARIF upload needs GitHub Advanced Security on private org repos; public repos are fine.
- Trivy fails the deploy on unfixed CRITICAL/HIGH findings — tighten or waive deliberately, do not silence casually.
