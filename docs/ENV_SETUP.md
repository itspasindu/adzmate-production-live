# Production environment setup (Render + Vercel + Supabase + R2 + Upstash)

Follow this guide after implementing Phase 1 infrastructure code.  
**Stack chosen:** Supabase Postgres + Auth · Cloudflare R2 · Upstash Redis · Render API · Vercel Web.

---

## 1. Supabase (Postgres + Auth)

1. Create a project at [supabase.com](https://supabase.com).
2. **Database → Connection string → URI** (Transaction pooler, port **6543**).
   The API auto-configures asyncpg for PgBouncer (no extra env vars needed).
3. Paste into Render as `DATABASE_URL` (the API normalizes `postgresql://` → `postgresql+asyncpg://`).
4. **Project Settings → API** → copy:
   - `SUPABASE_URL` → Render + Vercel
   - `anon` key → Vercel `SUPABASE_ANON_KEY`
5. **JWT Settings** → copy legacy JWT secret → Render `SUPABASE_JWT_SECRET` (if using HS256).
6. Enable Email auth; configure redirect URLs:
   - `http://localhost:3000/**`
   - `https://adzmate-production-live-web.vercel.app/**`

Run migrations on Render Shell after first deploy:

```bash
cd apps/api  # or /opt/render/project/src/apps/api depending on layout
alembic upgrade head
python -m app.seed --force
```

---

## 2. Upstash Redis

1. Create a database at [upstash.com](https://upstash.com).
2. Copy the **Redis URL** (`rediss://...`) → Render `REDIS_URL`.
3. Used for: Meta OAuth state, future job queue / SSE scaling.

---

## 3. Cloudflare R2

1. Cloudflare Dashboard → R2 → Create bucket (e.g. `adzmate-assets`).
2. Create API token with Object Read & Write.
3. Set on Render:

| Variable | Value |
|----------|--------|
| `STORAGE_BACKEND` | `r2` |
| `R2_ACCOUNT_ID` | Cloudflare account ID |
| `R2_ACCESS_KEY_ID` | Token access key |
| `R2_SECRET_ACCESS_KEY` | Token secret |
| `R2_BUCKET` | Bucket name |
| `R2_PUBLIC_URL` | Custom domain or r2.dev public URL |

4. Enable public access or attach a custom domain for `R2_PUBLIC_URL`.

---

## 4. Token encryption

Generate a Fernet key (store only in Render secrets):

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set as `TOKEN_ENCRYPTION_KEY` on Render.

---

## 5. Render (API)

| Variable | Production value |
|----------|------------------|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Supabase pooler URI |
| `REDIS_URL` | Upstash URL |
| `AUTH_ENABLED` | `true` |
| `SUPABASE_URL` | Your project URL |
| `SUPABASE_JWT_SECRET` | JWT secret |
| `ADZMATE_ALLOW_DEMO` | `0` |
| `PUBLIC_BASE_URL` | `https://adzmate-production-live.onrender.com` |
| `WEB_APP_URL` | `https://adzmate-production-live-web.vercel.app` |
| `CORS_ORIGINS` | `["https://adzmate-production-live-web.vercel.app"]` |
| `STORAGE_BACKEND` | `r2` |
| R2_* | See section 3 |
| `TOKEN_ENCRYPTION_KEY` | Fernet key |
| `ADZMATE_USE_LLM` | `1` |
| `GEMINI_API_KEY` | Your key |

**Start command** (in Render dashboard or `render.yaml`):

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Root Directory:** `apps/api`

---

## 6. Vercel (Web)

| Variable | Value |
|----------|--------|
| `API_INTERNAL_URL` | `https://adzmate-production-live.onrender.com` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon key |

Root Directory: `apps/web`  
Disable Deployment Protection for public access (or use production domain).

---

## 7. Verify

```bash
curl https://adzmate-production-live.onrender.com/api/health
curl https://adzmate-production-live-web.vercel.app/api-proxy/health
```

Expect:

- `"environment": "production"`
- `"database": { "ok": true, "engine": "postgresql" }`
- `"storage": { "backend": "r2" }`
- `"redis": { "ok": true }`

Open Vercel app → sign up → create campaign → confirm uploads load from R2 URLs.

---

## 9. Background worker (ARQ)

When `REDIS_URL` is set, campaign pipelines and metrics sync run on the ARQ worker instead of blocking API requests.

**Local:**
```bash
npm run worker:api
```

**Render:** Blueprint includes `adzmate-worker` service (`arq app.jobs.worker.WorkerSettings`).

Cron job `sync_all_live_metrics` runs every 6 hours for published/live campaigns when `ADZMATE_USE_FIXTURE_METRICS=0`.

---

## 10. What we still need from you

Paste these when ready (never commit to git):

- [ ] Supabase `DATABASE_URL` (pooler)
- [ ] Supabase URL + anon key + JWT secret
- [ ] Upstash `REDIS_URL`
- [ ] R2 credentials + public URL
- [ ] `TOKEN_ENCRYPTION_KEY` (generated locally)
- [ ] `GEMINI_API_KEY`
- [ ] Meta `META_APP_ID` / `META_APP_SECRET` (Phase 2)
- [ ] Final Vercel production domain — `https://adzmate-production-live-web.vercel.app`

---

*See also: [PROJECT_PLAN.md](./PROJECT_PLAN.md) · [DEPLOY_RENDER.md](./DEPLOY_RENDER.md)*
