# AdzMate — Campaign Auto-Pilot

**Team SUDO · IDEALIZE 2026 · Open Category · AIESEC in University of Moratuwa**

AdzMate is a **multi-agent marketing automation platform** for digital agencies. Paste a product brief, and specialist AI agents collaborate to decide whether to **LAUNCH**, **HOLD**, or **HALT** a campaign — then a human manager approves before anything goes live.

> **Problem:** Agency managers drown in spend dashboards, comment fires, and launch/pause decisions across Meta, Google, and TikTok.  
> **Solution:** Parallel Creative, Sentiment, and Strategy agents + a Signal Aggregator produce a clear recommendation; humans stay in the loop for approval, then AdzMate drafts Meta ads, deploys a landing preview, and can auto-pause when spend or sentiment spikes.

---

## Live demo

| Layer | URL |
|-------|-----|
| **Frontend (Vercel)** | https://adzmate-production-live-w-git-90be60-pasindus-projects-8ffd4b17.vercel.app/ |
| **API (Render)** | https://adzmate-production-live.onrender.com/ |
| **API health** | https://adzmate-production-live.onrender.com/api/health |
| **API docs** | https://adzmate-production-live.onrender.com/docs |

> Tip: If the Vercel preview asks you to log in, disable **Deployment Protection** on the project, or open the production domain from the Vercel dashboard.

---

## Tech stack

Must match our IDEALIZE / Open Category proposal:

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS |
| **Auth** | Supabase Auth (email); local demo mode without keys |
| **Backend** | FastAPI, Uvicorn, Pydantic, SQLAlchemy (async) |
| **Database** | SQLite (`aiosqlite`) |
| **Realtime** | Server-Sent Events (SSE) |
| **AI / LLM** | Google Gemini (`gemini-2.0-flash`); OpenAI fallback |
| **Sentiment (optional)** | DistilBERT (`transformers` / `torch`) or lexicon fallback |
| **Creative images** | Pollinations AI scenes + product cutout; procedural fallback |
| **Landing pages** | Jinja2 HTML previews |
| **Ads / Meta** | Meta Marketing API OAuth (optional) or demo connect |
| **Hosting** | Frontend → **Vercel** · API → **Render** |
| **CI/CD** | GitHub Actions (lint, build, staging deploy) |

---

## AI agent workflow (Open Category)

This is the core of our Open Category submission: **multiple specialised agents**, a **deterministic aggregator**, and **human-in-the-loop** actions — not a single chatbot.

```
Product brief + image + budget
        │
        ▼
   Orchestrator (FastAPI)
        │
        ├──► Creative Agent     → ad copy, multi-format creatives, audience hints
        ├──► Sentiment Agent    → brand sentiment from comments (+ optional DistilBERT / LLM)
        └──► Strategy Agent     → spend / ROAS across Meta · Google · TikTok
                │  (asyncio.gather — parallel; one failure does not kill the pipeline)
                ▼
        Signal Aggregator
                │  Rule gates + optional Gemini manager brief
                ▼
        LAUNCH  |  HOLD  |  HALT   (+ confidence + reason)
                │
                ▼
        Pending recommendation → Review queue (human)
                │
        Approve ──► Landing deployer (local HTML + preview URL)
                │   Meta draft → review → publish (structure / IDs)
                │   Optimization rules armed
                ▼
        Live campaign
                │
        Demo ticks / spend spike / comment flood
                │
        auto-pause ON ──► Strategy pause applied + timeline event
```

### Decision gates

| Signal | Threshold (defaults) | Effect |
|--------|----------------------|--------|
| Creative readiness | ≥ 0.7 | Required for LAUNCH |
| Brand sentiment | ≥ 0.55 | Soft score alone → **HOLD** |
| ROAS floor | ≥ 1.5 | Below floor → **HALT** |
| All healthy | — | **LAUNCH** |

### What is real vs simulated

| Component | Status |
|-----------|--------|
| Orchestrator, 3 parallel agents, Signal Aggregator | **Real** |
| Landing page HTML deployer + preview | **Real** |
| Action timeline + auto-pause | **Real** |
| Gemini enrichment (copy, insight, brief) | **Optional** (templates if off) |
| Meta OAuth account link | **Optional** (demo connect without keys) |
| Platform metrics, comment floods, Meta publish IDs | **Simulated** fixtures |

Architecture one-pager: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Core features

1. **Publish ads wizard** — brief, product image, budget, targeting → kicks off the agent pipeline  
2. **My ads** — campaign list and detail with creative assets, scores, and decision  
3. **Review queue** — approve / reject aggregator recommendations (human-in-the-loop)  
4. **Agents & workflows** — transparency page: real vs simulated labels for judges  
5. **Meta draft → review → publish** — campaign / ad set / ads from generated creatives  
6. **Audience automation** — location, age/gender, interests, lookalikes, retargeting (+ AI hints)  
7. **Landing deploy** — Jinja preview at `/previews/{id}/` with simulated CDN URL  
8. **Optimization rules** — CPA / ROAS / CTR / CPC / frequency; simulate 1–3 day ticks  
9. **Auto-pause** — spend spike or negative comment flood can pause ads when enabled  
10. **Account & Meta** — workspaces, businesses, Meta OAuth or demo connect  
11. **Workspace isolation** — Supabase users + `X-Workspace-Id` scoping  
12. **Resilience** — `FORCE_FAIL_AGENT=creative` (etc.): pipeline continues with warnings  

---

## Seed scenarios (for judges)

After `python -m app.seed --force`:

| Campaign | Workspace | Scenario | Expected decision |
|----------|-----------|----------|-------------------|
| Aurora Bottle Launch | Local Demo | Healthy | **LAUNCH** |
| Cedar Desk Mixed | Local Demo | Soft sentiment | **HOLD** |
| TrailRun Shoes Sprint | Local Demo | Healthy | **LAUNCH** |
| Pulse Buds Rescue | Beacon Media | Poor ROAS | **HALT** |

---

## Setup instructions

### Prerequisites

- Node.js 20+ and npm  
- Python 3.12+  
- (Optional) Supabase project, Gemini API key, Meta developer app  

### 1. Clone and install

```bash
git clone https://github.com/itspasindu/adzmate-production-live.git
cd adzmate-production-live
```

### 2. API (`apps/api`)

```bash
cd apps/api
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env
```

Edit `apps/api/.env` (minimum for local demo — leave Supabase empty):

```bash
PUBLIC_BASE_URL=http://localhost:8000
ADZMATE_USE_LLM=0
ADZMATE_USE_AI_IMAGES=0
```

Optional Gemini:

```bash
ADZMATE_USE_LLM=1
GEMINI_API_KEY=your-key
LLM_MODEL=gemini-2.0-flash
```

Seed and run:

```bash
python -m app.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API: http://127.0.0.1:8000  
- Docs: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/api/health  

### 3. Web (`apps/web`)

```bash
cd apps/web
npm install
copy .env.example .env.local   # or: cp .env.example .env.local
```

`apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
# Optional Supabase (omit for local demo mode — no login gate)
# NEXT_PUBLIC_SUPABASE_URL=
# NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

```bash
npm run dev
```

Open http://localhost:3000

### Root shortcuts

From the repo root:

```bash
npm run dev:api
npm run seed
npm run dev:web
```

### Judging reset (clean 4 seed campaigns)

```bash
cd apps/api
# Windows
set ADZMATE_USE_LLM=0
set ADZMATE_USE_AI_IMAGES=0
python -m app.seed --force

# macOS / Linux
# ADZMATE_USE_LLM=0 ADZMATE_USE_AI_IMAGES=0 python -m app.seed --force
```

`--force` deletes **all** campaigns, then recreates Aurora, Cedar Desk, TrailRun, and Pulse Buds.

### Auth notes

| Mode | Behaviour |
|------|-----------|
| **Local demo** (no Supabase env) | User `local-demo` / `demo@local.dev` — no login gate |
| **Supabase on** | Email signup/login via `/signup` and `/login` |

API auth needs `AUTH_ENABLED=true` plus `SUPABASE_URL` / `SUPABASE_JWT_SECRET`. Web needs `NEXT_PUBLIC_SUPABASE_*`.

---

## Demo walkthrough (5–7 min)

1. Open **Agents & workflows** — show real vs simulated layers.  
2. **Aurora Bottle Launch** — creatives, sentiment, ROAS, **LAUNCH** → Approve → Publish.  
3. **Pulse Buds Rescue** (Beacon Media) — aggregator **HALT** on low ROAS.  
4. **Cedar Desk Mixed** — **HOLD** from soft sentiment.  
5. On a live campaign: enable auto-pause → **Spend spike** or **Negative comment flood** → timeline shows pause.  
6. Optional: `FORCE_FAIL_AGENT=creative` and re-run — pipeline continues with a warning.

Full script (with speech cues): [docs/DEMO_VIDEO_GUIDE.md](docs/DEMO_VIDEO_GUIDE.md)

---

## Deploy

| Piece | Host | Notes |
|-------|------|--------|
| API | [Render](https://render.com) | Native Python or Docker — see [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) |
| Web | [Vercel](https://vercel.com) | Root Directory `apps/web`; set `NEXT_PUBLIC_API_URL` to the Render URL |

Render env (typical): `PUBLIC_BASE_URL`, `WEB_APP_URL`, optional Supabase / Gemini keys.  
Vercel env: `NEXT_PUBLIC_API_URL=https://your-api.onrender.com`

Staging CI/CD (GHCR → VPS): [docs/STAGING_CICD.md](docs/STAGING_CICD.md)

---

## Repository layout

```
adzmate/
  apps/
    api/                 # FastAPI — orchestrator, agents, Meta, optimization
      app/agents/        # creative · sentiment · strategy
      app/services/      # orchestrator · aggregator · deployer · meta · llm
      fixtures/          # Seed ads + comments (also under /fixtures)
    web/                 # Next.js dashboard
  fixtures/              # Shared mock metrics & social comments
  docs/                  # Architecture, demo guide, deploy, staging
  supabase/schema.sql    # Optional Supabase SQL
  render.yaml            # Render blueprint for the API
  .github/workflows/     # CI + staging deploy
```

---

## Team SUDO

| Role | Name | Email |
|------|------|-------|
| Leader | Pasindu Dewviman Pushpakumara | pasindudewviman59@gmail.com |
| Member | Amasha Wijerathna | amasha.wijeratna@gmail.com |
| Member | Sandani Eshani Aramudale | sandani0320@gmail.com |

**Event:** IDEALIZE 2026 · Open Category · AIESEC in University of Moratuwa
