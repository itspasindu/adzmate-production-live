# AdzMate — Campaign Auto-Pilot

**Team SUDO · IDEALIZE 2026 · AIESEC in University of Moratuwa**

Multi-agent marketing automation demo: brief → Creative / Sentiment / Strategy agents (parallel) → Signal Aggregator → manager approval → landing page deploy.

## Auth (Supabase) + workspace isolation

AdzMate uses **Supabase Auth** for identity and stores **workspaces** in the API database.

1. Create a Supabase project → enable Email auth.
2. Copy Project URL + anon key into `apps/web/.env.local` (see `.env.example`).
3. Copy JWT Secret (Settings → API → JWT Secret) into `apps/api/.env` as `SUPABASE_JWT_SECRET`.
4. Restart API + web.

Without Supabase env vars, the stack runs in **local demo mode** (user `local-demo`, seeded workspace).

Optional Supabase SQL (if you also want workspaces mirrored in Supabase): `supabase/schema.sql`.

New API endpoints:
- `GET /api/me`
- `GET|POST /api/workspaces`

All campaign/recommendation routes are scoped by `X-Workspace-Id` (or the user's default workspace).

## Account & Meta connections

Open **Account & Meta** in the sidebar (`/settings`):

1. **User** — Supabase registration/login (or local demo user).
2. **Business / company profile** — create and edit multiple companies per workspace.
3. **Meta connection** — Facebook Page, Instagram Business account, and Ad Account selection.

Without `META_APP_ID` / `META_APP_SECRET`, use **Connect demo Meta** (mock assets for the hackathon). For real OAuth:

```bash
# apps/api/.env
META_APP_ID=your-facebook-app-id
META_APP_SECRET=your-app-secret
META_OAUTH_REDIRECT_URI=http://localhost:8000/api/meta/oauth/callback
WEB_APP_URL=http://localhost:3000
```

Add the same redirect URI in the Meta app’s Facebook Login settings.

## Draft → Review → Publish + optimization

After agents finish with LAUNCH/HOLD, AdzMate auto-builds a **Meta draft**:

1. Campaign + ad set (daily budget, placements, audience)
2. Multiple ads from generated creatives
3. Workflow stays **draft** until you **Review & publish** (approve) or use Publish on the campaign page

**Audience automation** covers location, age/gender, interests, behaviors, custom, lookalike, website visitors, retargeting, and customer lists — with AI recommendations from the product description.

Once published, **Automated optimization** rules run (CPA / ROAS / CTR / CPC / no-conversion spend / frequency). Use **Simulate 1 day** / **3 days** on the campaign page to demo budget reallocation and pausing losers.

## Quick start

### 1. API

```bash
cd apps/api
pip install -r requirements.txt
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Dashboard

```bash
cd apps/web
npm install
npm run dev
```

Open http://localhost:3000

### Judging reset (only the 4 seed scenarios)

```bash
cd apps/api
# Optional: skip Gemini/images so reseed is fast and quota-safe
set ADZMATE_USE_LLM=0
set ADZMATE_USE_AI_IMAGES=0
python -m app.seed --force
```

`--force` deletes **all** campaigns (every workspace), then recreates Aurora, Pulse Buds, Cedar Desk, and TrailRun.

**Architecture one-pager for judges:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
**Demo video script (with speech):** [docs/DEMO_VIDEO_GUIDE.md](docs/DEMO_VIDEO_GUIDE.md)

Optional DistilBERT (downloads model on first use):

```bash
pip install torch transformers
set ADZMATE_USE_DISTILBERT=1
```

### AI agents (Gemini / LLM)

Agents work offline with templates/rules. To enable Gemini-powered copy, sentiment insight, strategy narrative, and decision briefs, add to `apps/api/.env`:

```bash
ADZMATE_USE_LLM=1
GEMINI_API_KEY=your-key-from-https://aistudio.google.com/apikey
LLM_MODEL=gemini-2.0-flash
```

(OpenAI still works via `OPENAI_API_KEY` if you prefer.)

Check status: `GET http://127.0.0.1:8000/api/health` → `llm_enabled: true`, `llm_provider: gemini`.

## Demo walkthrough (5–7 min)

1. Open **Campaigns** — three seeded clients appear (healthy / poor ROAS / mixed sentiment).
2. Open **Aurora Bottle Launch** — show Creative assets, sentiment score, ROAS, and `LAUNCH` decision.
3. Click **Approve & deploy landing page** — iframe preview + simulated CloudFront URL.
4. Open **Pulse Buds Rescue** — aggregator says `HALT` on low ROAS; approve halt to pause mock ads.
5. Open **Cedar Desk Mixed** — `HOLD` from soft sentiment; use judge controls.
6. On any live/awaiting campaign, trigger **Spend spike / ROAS drop** or **Negative comment flood** — Strategy emits pause recommendation; approve from campaign page or **Approvals** inbox.
7. Mention resilience: set env `FORCE_FAIL_AGENT=creative` (or edit `app/config.py` `force_fail_agent`) and re-run — pipeline continues with a warning banner.

## Architecture

```
Brief → Orchestrator → [Creative | Sentiment | Strategy] → Signal Aggregator
      → Decision (LAUNCH/HALT/HOLD) → Approval → Landing Deployer → Dashboard
```

| Layer | Demo implementation |
|---|---|
| Orchestrator | FastAPI + asyncio fan-out + SQLite |
| Creative | Product upload + soft cutout + free AI scenes (Pollinations) + LLM copy |
| Sentiment | DistilBERT / lexicon + optional LLM brand insight |
| Strategy | Mock Meta / Google / TikTok spend + ROAS + optional LLM narrative |
| Aggregator | Rule gates (LAUNCH/HALT/HOLD) + optional LLM manager brief |
| Deployer | Jinja HTML → `/previews/{id}/` + fake CloudFront URL |
| Dashboard | Next.js + SSE/polling + Supabase Auth |

## Team

| Role | Name | Email |
|---|---|---|
| Leader | Pasindu Dewviman Pushpakumara | pasindudewviman59@gmail.com |
| Member | Amasha Wijerathna | amasha.wijeratna@gmail.com |
| Member | Sandani Eshani Aramudale | sandani0320@gmail.com |

## Repo layout

```
adzmate/
  apps/api/       # FastAPI orchestrator + agents
  apps/web/       # Next.js dashboard
  fixtures/       # Mock ads + social comments
  packages/shared/
  .github/        # CI + staging deploy (GHCR → VPS SSH)
  docs/STAGING_CICD.md
```

## Staging CI/CD

Push/merge to the **`staging`** branch runs corporate CI (lint, build, secret scan, CodeQL, image scan) and deploys to the staging VPS over SSH.

See [docs/STAGING_CICD.md](docs/STAGING_CICD.md) for secrets, VPS bootstrap, and branch protection.