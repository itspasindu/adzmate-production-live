# AdzMate — Production Project Plan

**Team SUDO · Target: Real-world agency users**  
**Version:** 1.0 · **Horizon:** 16 weeks (4 phases)  
**Status:** Draft for execution

---

## 1. Executive summary

AdzMate is a multi-agent marketing automation platform with a working hackathon MVP: orchestrator, three parallel agents (Creative, Sentiment, Strategy), signal aggregation (LAUNCH / HOLD / HALT), human approval, Meta draft workflow, landing previews, and auto-pause logic.

**What blocks real users today:**

| Gap | Impact |
|-----|--------|
| SQLite + local file storage | Data loss on redeploy; no horizontal scaling |
| Simulated ad metrics & publish IDs | Agents cannot act on real campaigns |
| Auth optional / `local-demo` bypass | No secure multi-tenant production |
| In-memory OAuth state & SSE | Breaks with multiple API instances |
| Agent pipeline in HTTP request | Timeouts under load; poor UX |
| No automated tests | High regression risk on every change |
| No monitoring / alerting | Incidents invisible until users report |

**Production goal:** Agencies can sign up, connect a Meta ad account, run campaigns through the agent pipeline, approve recommendations, publish real ads, and receive auto-pause when performance drops — with secure workspace isolation and reliable uptime.

**Recommended MVP for launch:** Meta-only integration + Postgres + job queue + billing. Google/TikTok in v1.1.

---

## 2. Success criteria (definition of done)

Launch is complete when all of the following are true:

- [ ] User can sign up, verify email, create workspace, invite one teammate
- [ ] User connects real Meta ad account via OAuth (not demo connect)
- [ ] User creates campaign → agents run → LAUNCH/HOLD/HALT shown with reasons
- [ ] Manager approves → Meta campaign/ad set/ads created via Marketing API with real IDs
- [ ] Landing page served from CDN with HTTPS URL (not local `/previews/` only)
- [ ] Live campaign metrics pulled from Meta Insights (not fixtures)
- [ ] Auto-pause triggers real Meta API pause when ROAS drops below threshold
- [ ] All data persisted in PostgreSQL; files in object storage
- [ ] Auth required in production; no `local-demo` access
- [ ] 99%+ API uptime over 7-day staging soak; Sentry configured
- [ ] Critical path covered by automated tests (CI gate)
- [ ] Privacy policy, terms of service, and Meta app review approved

---

## 3. Team & roles (Team SUDO)

| Role | Owner | Primary focus |
|------|-------|---------------|
| **Tech lead / Backend** | Pasindu | API, integrations, job queue, DB migrations |
| **Frontend** | Amasha | Auth UX, campaign flows, error states, onboarding |
| **Integrations / QA** | Sandani | Meta app review, E2E tests, demo data, docs |

Adjust assignments as needed. Each phase ends with a **demo + checklist sign-off**.

---

## 4. Architecture target state

```
┌─────────────────────────────────────────────────────────────────┐
│  Vercel (Next.js 15)          app.adzmate.com                   │
│  Supabase Auth client · workspace switcher · campaign UI        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS + JWT
┌────────────────────────────▼────────────────────────────────────┐
│  API (Render / Fly / Railway)     api.adzmate.com               │
│  FastAPI · RBAC · rate limits · webhooks                        │
└──────┬──────────────┬──────────────┬────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
  PostgreSQL      Redis          Object storage
  (Neon/Supabase) (Upstash)      (R2 / S3)
       │              │              │
       │              └── SSE pub/sub, OAuth state, rate limit
       │
       ▼
  Worker process (ARQ / Celery)
  · agent pipeline
  · Meta insights sync
  · optimization ticks
  · token refresh

External:
  Meta Marketing API · Meta Webhooks · Gemini API · Stripe
```

---

## 5. Phase overview

| Phase | Weeks | Theme | Outcome |
|-------|-------|-------|---------|
| **0** | 1 | Stabilize demo | Production deploy seeded & documented |
| **1** | 3 | Platform foundation | Postgres, storage, Redis, auth, observability |
| **2** | 4 | Meta integration | Real OAuth, publish, insights, auto-pause |
| **3** | 3 | Async & optimization | Job queue, scheduled sync, remove demo paths |
| **4** | 3 | SaaS & launch | Billing, onboarding, legal, Meta app review, go-live |
| **5** | 2+ | Post-launch | Google/TikTok, advanced features |

**Total to public launch:** ~14 weeks (+ 2 week buffer)

---

## 6. Phase 0 — Stabilize current demo (Week 1)

**Objective:** Judges/stakeholders can use live URLs reliably while Phase 1 starts.

| # | Task | Owner | Deliverable |
|---|------|-------|-------------|
| 0.1 | Seed Render production DB | Backend | 4 seed campaigns visible on live frontend |
| 0.2 | Set `NEXT_PUBLIC_API_URL` on Vercel; disable deployment protection | Frontend | Public demo URL works without login wall |
| 0.3 | Set Render env: `PUBLIC_BASE_URL`, `WEB_APP_URL` | Backend | CORS + redirects correct |
| 0.4 | Add `apps/web/.env.example` | Frontend | Onboarding doc matches repo |
| 0.5 | Commit & sync README | All | Clean `main` branch |
| 0.6 | Record 3–4 min demo video | All | Submission / marketing asset |

**Exit criteria:** Live demo walkthrough passes end-to-end (see `docs/DEMO_VIDEO_GUIDE.md`).

---

## 7. Phase 1 — Platform foundation (Weeks 2–4)

**Objective:** Replace demo infrastructure with production-grade persistence, auth, and ops.

### 7.1 Database (Week 2)

| # | Task | Files / notes |
|---|------|---------------|
| 1.1 | Provision PostgreSQL (Neon or Supabase) | New `DATABASE_URL` |
| 1.2 | Add Alembic; initial migration from `models.py` | `apps/api/alembic/` |
| 1.3 | Remove SQLite-only `_migrate_sqlite()` after parity | `apps/api/app/db.py` |
| 1.4 | Add `asyncpg` driver; update `requirements.txt` | Replace `aiosqlite` for prod |
| 1.5 | Run Alembic migrations on deploy | `alembic upgrade head` on Render Shell |

**Acceptance:** Fresh deploy creates schema via Alembic; seed script works on Postgres.

### 7.2 Object storage (Week 2)

| # | Task | Files / notes |
|---|------|---------------|
| 1.6 | Add storage abstraction (`StorageBackend` interface) | `apps/api/app/storage/` |
| 1.7 | Implement S3/R2 provider (boto3 or aioboto3) | Upload product images, creatives |
| 1.8 | Landing pages uploaded to bucket + public CDN URL | Replace `cloudfront_url` simulation in `deployer.py` |
| 1.9 | Migrate static mounts to signed URLs or CDN proxy | `main.py` mounts become dev-only |

**Acceptance:** New campaign image URL is HTTPS on CDN, survives API redeploy.

### 7.3 Auth & security (Week 3)

| # | Task | Files / notes |
|---|------|---------------|
| 1.10 | Enforce `AUTH_ENABLED=true` in prod/staging | `config.py`, Render env |
| 1.11 | Remove or gate `local-demo` user behind `ENV=development` | `auth.py` |
| 1.12 | Workspace invite flow (email link or Supabase invite) | New routes + UI |
| 1.13 | Encrypt `MetaConnection.access_token` at rest | `models.py` + Fernet/KMS |
| 1.14 | Restrict CORS to `WEB_APP_URL` + staging URL | Replace wildcard middleware in `main.py` |
| 1.15 | Rate limiting (slowapi + Redis) | Auth, create campaign, LLM endpoints |
| 1.16 | Add security headers middleware | HSTS, X-Frame-Options, etc. |

**Acceptance:** Unauthenticated API calls return 401; cross-origin from unknown domains blocked.

### 7.4 Redis & multi-instance prep (Week 3)

| # | Task | Files / notes |
|---|------|---------------|
| 1.17 | Provision Upstash Redis | Env: `REDIS_URL` |
| 1.18 | Move OAuth state to Redis | `meta.py` `_oauth_states` |
| 1.19 | Move SSE `EventBus` to Redis pub/sub | `events.py` |
| 1.20 | Session/cache for health-heavy reads | Optional |

**Acceptance:** Two API instances share OAuth callback and SSE events correctly.

### 7.5 Observability (Week 4)

| # | Task | Files / notes |
|---|------|---------------|
| 1.21 | Structured JSON logging with request ID | Middleware |
| 1.22 | Sentry for API + Next.js | `@sentry/nextjs`, `sentry-sdk[fastapi]` |
| 1.23 | Enhanced `/api/health` (DB, Redis, storage checks) | `routes.py` |
| 1.24 | Uptime monitor on health + web home | Better Stack / UptimeRobot |
| 1.25 | Staging/production env documented | `docs/ENV_SETUP.md` |

**Acceptance:** Forced error appears in Sentry; health fails when DB unreachable.

### Phase 1 milestone demo

- Sign up with Supabase → create workspace → upload campaign → data in Postgres + R2
- Staging deploy auto-runs CI

---

## 8. Phase 2 — Meta integration (Weeks 5–8)

**Objective:** Replace simulated ad platform layer with real Meta Marketing API.

### 8.1 Meta Developer setup (Week 5)

| # | Task | Notes |
|---|------|-------|
| 2.1 | Create Meta Developer app (dev + prod) | Business verification may take days |
| 2.2 | Configure OAuth redirect URIs for staging + prod | `META_OAUTH_REDIRECT_URI` |
| 2.3 | Request App Review permissions | `ads_management`, `ads_read`, `pages_read_engagement`, `business_management` |
| 2.4 | Document data use for Meta review | Privacy policy required |

### 8.2 Real OAuth & account linking (Week 5)

| # | Task | Files / notes |
|---|------|---------------|
| 2.5 | Production OAuth flow end-to-end | `meta.py`, `routes_account.py` |
| 2.6 | Long-lived token exchange + refresh job | New `jobs/meta_tokens.py` |
| 2.7 | UI: connect Meta → select Page, IG, Ad Account | `settings/page.tsx` |
| 2.8 | Remove demo connect in production (`ENV=production`) | Gate `demo-connect` route |

**Acceptance:** Real ad account appears in settings; token stored encrypted.

### 8.3 Real publish pipeline (Week 6–7)

| # | Task | Files / notes |
|---|------|---------------|
| 2.9 | Implement `MetaPublisher` service (Graph API v21+) | New `integrations/meta/publisher.py` |
| 2.10 | Upload creative images to Meta Ad Library | Image hash / upload API |
| 2.11 | Create Campaign → Ad Set → Ad Creative → Ad | Replace `publish_structure()` mock |
| 2.12 | Map AdzMate objectives to Meta `OUTCOME_*` | Extend `meta_publish.py` |
| 2.13 | Store real Meta IDs on campaign record | New columns or JSON field |
| 2.14 | Pause/resume via Marketing API | Wire to auto-pause + HALT |
| 2.15 | Error handling: Meta error codes → user-friendly messages | `friendly.ts` + API |

**Acceptance:** Approved Aurora-style campaign creates visible draft/active ads in Meta Ads Manager (test account).

### 8.4 Real metrics & sentiment inputs (Week 7–8)

| # | Task | Files / notes |
|---|------|---------------|
| 2.16 | Insights sync job: spend, revenue, ROAS per ad/ad set | Replace `load_base_ads()` for connected campaigns |
| 2.17 | Add `platform_metrics` table or JSON snapshot with timestamps | Strategy agent reads live data |
| 2.18 | Meta comment fetch for connected Page/IG | Feed Sentiment agent |
| 2.19 | Webhook endpoint for ad account alerts (optional v1) | `routes/webhooks.py` |
| 2.20 | Feature flag: `USE_FIXTURE_METRICS=0` in prod | `strategy.py`, `routes.py` |

**Acceptance:** Pulse Buds scenario reproduces HALT using real low-ROAS test data (or seeded test account).

### Phase 2 milestone demo

- Connect Meta → create campaign → approve → see ad in Ads Manager
- ROAS on dashboard matches Meta Insights (within sync delay)

---

## 9. Phase 3 — Async agents & optimization (Weeks 9–11)

**Objective:** Reliable agent execution at scale; automated optimization without demo ticks.

### 9.1 Background job system (Week 9)

| # | Task | Files / notes |
|---|------|---------------|
| 3.1 | Choose queue: **ARQ** (async, Redis) recommended | `apps/api/app/worker.py` |
| 3.2 | Move `run_pipeline()` to job | `orchestrator.py` |
| 3.3 | Campaign status: `processing` → SSE progress events | Frontend polling/SSE |
| 3.4 | Retry policy for transient LLM / Meta failures | Exponential backoff, max 3 |
| 3.5 | Separate worker dyno/process on Render | `render.yaml` or Procfile |

**Acceptance:** Creating campaign returns immediately; UI shows agent progress via SSE.

### 9.2 LLM production hardening (Week 9)

| # | Task | Notes |
|---|------|-------|
| 3.6 | Gemini primary with OpenAI fallback | Already partially wired in `config.py` |
| 3.7 | Per-workspace daily token budget | Prevent runaway costs |
| 3.8 | Timeout caps on creative/image generation | 60s max per agent |
| 3.9 | Cache LLM responses for identical brief hash | Redis |

### 9.3 Scheduled optimization (Week 10)

| # | Task | Files / notes |
|---|------|---------------|
| 3.10 | Cron: sync metrics every 15–30 min for live campaigns | Worker schedule |
| 3.11 | Cron: run `optimization.py` rules on live data | Budget shift, pause weak ads |
| 3.12 | Auto-pause calls Meta pause API (not mock) | `orchestrator.py`, `optimization.py` |
| 3.13 | Remove or hide `demo-tick` in production UI | `campaigns/[id]/page.tsx` |
| 3.14 | Email/notification on auto-pause (optional) | Resend / SendGrid |

**Acceptance:** Live campaign auto-pauses within one sync cycle after ROAS breach; timeline shows real action.

### 9.4 Testing (Week 11)

| # | Task | Target |
|---|------|--------|
| 3.15 | Unit tests: aggregator, strategy rules, optimization | 80% on core logic |
| 3.16 | Integration tests: auth + workspace scoping | pytest + httpx |
| 3.17 | Meta API contract tests (mocked responses) | pytest-httpx / VCR |
| 3.18 | Playwright E2E: signup → create → approve flow | `apps/web/e2e/` |
| 3.19 | Run pytest locally before release | `npm run test:api` |

**Acceptance:** CI green on every PR; staging smoke passes post-deploy.

### Phase 3 milestone demo

- 5 concurrent campaign creates complete without timeout
- Auto-pause fires on staging with real Meta test account

---

## 10. Phase 4 — SaaS, legal & launch (Weeks 12–14)

**Objective:** Paying customers can onboard safely; public launch.

### 10.1 Billing & plans (Week 12)

| # | Task | Notes |
|---|------|-------|
| 4.1 | Stripe integration: subscription per workspace | Starter / Pro tiers |
| 4.2 | Usage limits: campaigns/month, connected ad accounts | Middleware check |
| 4.3 | Billing UI in Account settings | `settings/page.tsx` |
| 4.4 | Webhook: subscription status → feature flags | Stripe → API |

**Suggested tiers:**

| Plan | Price | Limits |
|------|-------|--------|
| Starter | $49/mo | 1 workspace, 5 campaigns/mo, 1 Meta account |
| Pro | $149/mo | 3 workspaces, 30 campaigns/mo, 3 Meta accounts |
| Agency | Custom | Unlimited + priority support |

### 10.2 Onboarding & UX polish (Week 12–13)

| # | Task | Notes |
|---|------|-------|
| 4.5 | First-run wizard: connect Meta → first campaign | New `/onboarding` route |
| 4.6 | Empty states, loading skeletons, error boundaries | All main pages |
| 4.7 | Remove "simulated" labels where features are now real | `agents/page.tsx` |
| 4.8 | Mobile-responsive pass on campaign detail | QA |
| 4.9 | Help docs / FAQ (in-app links) | `docs/` or Notion |

### 10.3 Legal & compliance (Week 13)

| # | Task | Notes |
|---|------|-------|
| 4.10 | Privacy policy (data collected, Meta, LLM) | Public URL |
| 4.11 | Terms of service | Public URL |
| 4.12 | Cookie consent if using analytics | Vercel Analytics optional |
| 4.13 | Data export + workspace deletion API | GDPR baseline |
| 4.14 | Meta App Review submission | Allow 1–2 weeks review time |

### 10.4 Production launch (Week 14)

| # | Task | Notes |
|---|------|-------|
| 4.15 | Production environment (separate from staging) | Render + Vercel prod |
| 4.16 | DNS: `app.adzmate.com`, `api.adzmate.com` | Custom domains |
| 4.17 | Production deploy workflow with manual approval | GitHub Environment |
| 4.18 | Runbook: incident response, rollback, on-call | `docs/RUNBOOK.md` |
| 4.19 | Launch checklist sign-off | Section 12 below |
| 4.20 | Soft launch: 3–5 beta agencies | Feedback loop |

**Acceptance:** Paying beta user completes full flow without team assistance.

---

## 11. Phase 5 — Post-launch (Weeks 15+)

| Priority | Feature | Notes |
|----------|---------|-------|
| P1 | Google Ads API | Same pattern as Meta integration |
| P1 | TikTok Marketing API | Strategy agent already references platform |
| P2 | Team permissions UI | RBAC exists in API; expose in settings |
| P2 | Webhook notifications (Slack/email) | HALT / auto-pause alerts |
| P2 | Creative A/B test automation | Extend optimization rules |
| P3 | White-label for agencies | Custom domain per workspace |
| P3 | API for partners | Public REST API + keys |

---

## 12. Launch checklist

### Infrastructure
- [ ] PostgreSQL with automated backups
- [ ] Redis provisioned
- [ ] Object storage + CDN
- [ ] Worker process running
- [ ] Custom domains + SSL
- [ ] Staging mirrors production topology

### Security
- [ ] Auth required; no demo bypass
- [ ] Meta tokens encrypted
- [ ] CORS restricted
- [ ] Rate limits active
- [ ] Secrets not in git (Gitleaks CI passing)
- [ ] Dependency audit clean (high/critical)

### Product
- [ ] Meta OAuth + publish + insights + pause
- [ ] Agent pipeline async with progress UI
- [ ] Auto-pause on real metrics
- [ ] Billing live
- [ ] Onboarding wizard
- [ ] Privacy policy + ToS published

### Quality
- [ ] Unit + integration tests in CI
- [ ] E2E smoke on staging deploy
- [ ] Sentry receiving errors
- [ ] Uptime monitor configured
- [ ] Runbook written

### Business
- [ ] Meta App Review approved
- [ ] 3+ beta users onboarded successfully
- [ ] Support email / channel defined

---

## 13. Risk register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Meta App Review delayed | High | Blocks launch | Submit Week 5; use test users during review |
| LLM cost overrun | Medium | High bills | Per-workspace budgets; template fallback |
| Render free tier sleep / data loss | High (if unchanged) | Outages | Paid plan + Postgres + R2 before launch |
| Token expiry breaks campaigns | Medium | Silent failures | Daily refresh job + alert on expiry |
| Scope creep (Google/TikTok before Meta stable) | High | Delay | Meta-only MVP; document v1.1 roadmap |
| Single developer bottleneck | Medium | Schedule slip | Parallel: Frontend Phase 1 while Backend Phase 2 |

---

## 14. Budget estimate (monthly, post-launch)

| Service | Cost (USD/mo) |
|---------|---------------|
| Render API + Worker (Starter+) | $14–50 |
| Vercel Pro | $20 |
| Neon / Supabase Postgres | $25 |
| Upstash Redis | $0–10 |
| Cloudflare R2 + CDN | $5–20 |
| Sentry | $0–26 |
| Stripe | 2.9% + 30¢ per transaction |
| Gemini API | $50–300 (usage) |
| Domain | ~$1 |
| **Estimated fixed infra** | **~$100–150/mo** + variable LLM |

---

## 15. Key files to modify (reference)

| Area | Current file | Change |
|------|--------------|--------|
| DB | `apps/api/app/db.py` | Alembic; Postgres |
| Auth | `apps/api/app/auth.py` | Remove prod demo bypass |
| Meta OAuth | `apps/api/app/services/meta.py` | Redis state; token encryption |
| Publish | `apps/api/app/services/meta_publish.py` | Real Graph API |
| Metrics | `apps/api/app/agents/strategy.py` | Live insights, not fixtures |
| Pipeline | `apps/api/app/services/orchestrator.py` | Queue job |
| Events | `apps/api/app/events.py` | Redis pub/sub |
| Storage | `apps/api/app/services/deployer.py` | CDN upload |
| CORS | `apps/api/app/main.py` | Allowlist middleware |
| Frontend | `apps/web/src/app/settings/page.tsx` | Meta connect UX |
| Tests | `apps/api/tests/` | `npm run test:api` |

---

## 16. Weekly cadence (recommended)

| Day | Activity |
|-----|----------|
| Monday | Sprint planning; pick tasks from current phase |
| Wed | Mid-week demo (internal, 15 min) |
| Friday | Merge to `staging`; verify smoke tests |
| End of phase | Milestone demo + update this doc |

---

## 17. Immediate next actions (this week)

1. **Pasindu:** Provision Neon Postgres; spike Alembic migration locally  
2. **Amasha:** Add `apps/web/.env.example`; fix production Vercel env + seed Render DB  
3. **Sandani:** Create Meta Developer app; draft privacy policy outline  
4. **All:** Review this plan; adjust timeline to exam/hackathon constraints  

---

## 18. Document history

| Date | Version | Change |
|------|---------|--------|
| 2026-08-29 | 1.0 | Initial production project plan |

---

*See also: [ENV_SETUP.md](./ENV_SETUP.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)*
