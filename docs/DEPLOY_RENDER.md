# Deploy AdzMate on Render

Recommended split for the hackathon:

| Piece | Host |
|-------|------|
| **API** (`apps/api`) | **Render** Web Service |
| **Web** (`apps/web`) | Vercel (or a second Render Web Service) |

## Prefer: Native Python (no Docker)

Avoids Dockerfile context issues in a monorepo.

1. **New → Web Service** → connect GitHub.
2. Settings:

| Field | Value |
|-------|--------|
| **Language** | Python 3 |
| **Root Directory** | `apps/api` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/api/health` |

3. Env vars — see below. Deploy. Seed via Shell.

---

## If you use Docker (common failure)

Your error:

```text
transferring context: 2B
"/apps/api": not found
```

means Render’s **Docker build context is wrong**.  
`apps/api/Dockerfile` expects the **repository root** as context (it `COPY apps/api` and `COPY fixtures`).

### Correct Docker settings

| Field | Value |
|-------|--------|
| **Environment** | Docker |
| **Root Directory** | *(leave empty)* |
| **Dockerfile Path** | `apps/api/Dockerfile` |
| **Docker Context** | `.` (repo root) |

Wrong (causes your error): Root Directory = `apps/api` while using that Dockerfile.

### Start command with `$PORT`

Render injects `PORT`. Override Docker CMD if needed:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

(In Render Docker services you can set **Docker Command** to that.)

---

## Environment variables

| Key | Example / notes |
|-----|-----------------|
| `PUBLIC_BASE_URL` | `https://adzmate-api.onrender.com` |
| `WEB_APP_URL` | `https://your-app.vercel.app` |
| `DATABASE_URL` | `sqlite+aiosqlite:////var/data/adzmate.db` (with disk) |
| `AUTH_ENABLED` | `true` / `false` |
| `SUPABASE_URL` | project URL |
| `SUPABASE_JWT_SECRET` | if auth on |
| `ADZMATE_USE_LLM` | `0` for stable demos |
| `ADZMATE_USE_AI_IMAGES` | `0` |
| `GEMINI_API_KEY` | optional |
| `PYTHON_VERSION` | `3.12.8` (native Python only) |

**Persistent disk** at `/var/data` (Starter+) so SQLite survives restarts. Free tier often has no disk — data resets when the instance sleeps.

---

## Seed demo data

Render → service → **Shell**:

```bash
ADZMATE_USE_LLM=0 ADZMATE_USE_AI_IMAGES=0 python -m app.seed --force
```

---

## Point the frontend at Render

Vercel env:

```text
NEXT_PUBLIC_API_URL=https://YOUR-SERVICE.onrender.com
```

Redeploy the web app.

---

## Blueprint

[`render.yaml`](../render.yaml) uses **native Python** (`rootDir: apps/api`).  
**New → Blueprint** → apply that file (do not use Docker for the blueprint service).

## Verify

- [ ] `GET …/api/health` → ok  
- [ ] Frontend can list campaigns  
- [ ] No “Cannot reach API”
