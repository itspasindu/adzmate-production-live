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

## If you use Docker

`apps/api/Dockerfile` expects **build context = `apps/api`** (not the monorepo root).

### Correct Docker settings

| Field | Value |
|-------|--------|
| **Environment** | Docker |
| **Root Directory** | `apps/api` |
| **Dockerfile Path** | `Dockerfile` |
| **Docker Context** | `.` *(blank or `.` only)* |

### Start command with `$PORT`

Render injects `PORT`. Set **Docker Command** to:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Common failure (`transferring context: 2B`)

```text
transferring context: 2B
"/apps/api/requirements.txt": not found
```

Means the Docker context directory is empty or wrong. Typical mistakes:

| Wrong | Why it breaks |
|-------|----------------|
| Root Directory empty + Dockerfile still `COPY`s as if context were `apps/api` | paths missing (older Dockerfile) |
| Root Directory = `apps/api` **and** Docker Context = `apps/api` | context becomes `apps/api/apps/api` → **2B / not found** |
| Dockerfile Path = `apps/api/Dockerfile` with Root Directory = `apps/api` | path becomes `apps/api/apps/api/Dockerfile` |

Fix: Root Directory `apps/api`, Dockerfile Path `Dockerfile`, Docker Context `.`

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
