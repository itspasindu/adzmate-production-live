# AdzMate — Demonstration video guide (with speech)

**Team SUDO · IDEALIZE 2026**  
**Target length:** 3:00–4:00 (ideal) · max 5:00  
**Tone:** clear, confident, honest about real vs simulated layers

Use this as a **recording checklist + spoken script**. Read the speech aloud while clicking the screen actions.

---

## Hackathon requirements this video must prove

| Requirement | Where you prove it on camera |
|-------------|------------------------------|
| Functioning **AI agent** (not a chatbot wrapper) | Orchestrator + 3 parallel agents + aggregator decision |
| **Reasoning / decision-making** | LAUNCH vs HOLD vs HALT with reasons |
| **Action-taking** | Meta draft → Publish; auto-pause on ROAS drop; timeline logs |
| **Multi-step workflow** | Brief → agents → approve → publish → optimize |
| Problem: agencies drowning in manual ops | Opening + Pulse Buds HALT + auto-pause |
| Transparency / licensing | Agents page “Real vs simulated” |

---

## Before you hit Record

### 1. Reset demo data

```bash
cd apps/api
set ADZMATE_USE_LLM=0
set ADZMATE_USE_AI_IMAGES=0
python -m app.seed --force
```

Confirm only 4 campaigns:
- Aurora Bottle Launch → LAUNCH  
- Cedar Desk Mixed → HOLD  
- TrailRun Shoes Sprint → LAUNCH  
- Pulse Buds Rescue → HALT (workspace: **Beacon Media**)

### 2. Start stack

```bash
# Terminal 1
cd apps/api
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2
cd apps/web
npm run dev
```

Open http://localhost:3000 — workspace **Local Demo**.

### 3. Browser prep
- Zoom **110–125%** so text is readable on phone/YouTube
- Close other tabs; hide Discord/Slack
- Cursor size large (optional)
- Have tabs ready: app, `docs/ARCHITECTURE.md` (optional title slide)

### 4. Pre-publish one campaign (optional speed hack)
If you want auto-pause in under 60s of video time, **before recording**:
1. Open Aurora → Approve / Publish my ads until status is **published/live**
2. Or do Publish live on camera (safer for authenticity; adds ~40s)

---

## Shot list (timeline)

| Time | Scene | On screen |
|------|-------|-----------|
| 0:00–0:25 | Hook + problem | Title card or My ads list |
| 0:25–0:55 | Architecture / agents | `/agents` Real vs simulated |
| 0:55–1:45 | Happy path LAUNCH | Aurora campaign Simple view → Publish |
| 1:45–2:20 | Multi-client HALT | Switch to Beacon → Pulse Buds |
| 2:20–2:55 | HOLD + human gate | Cedar Desk |
| 2:55–3:35 | Action: auto-pause | Live campaign → Spend spike → timeline |
| 3:35–4:00 | Close + stack | Agents page / architecture |

Trim if over 4 minutes: cut Cedar Desk (mention HOLD in one sentence on Agents page).

---

## Full spoken script

> *Italics = what to click / show. Speak at a calm pace (~140 wpm).*

### SCENE 1 — Hook (0:00–0:25)

**Show:** My ads list (Local Demo) with Aurora, Cedar, TrailRun.

**Say:**

> Hi, we’re **Team SUDO**, and this is **AdzMate** — a multi-agent marketing auto-pilot for digital agencies.
>
> Agencies manage many client campaigns at once. Managers burn hours watching spend, reading comments, and deciding whether to launch or pause ads. AdzMate turns that into an **agent workflow with a human approval gate**.

---

### SCENE 2 — Prove it’s agentic, not a chatbot (0:25–0:55)

**Show:** Sidebar → **Agents & workflows**. Scroll **Real vs simulated**. Point at demo script list.

**Say:**

> This is not a single chatbot prompt. AdzMate runs a real **orchestrator** that starts three specialist agents **in parallel**: Creative, Sentiment, and Strategy. Their signals go to a **Signal Aggregator** that decides **LAUNCH, HOLD, or HALT**.
>
> We’re transparent with judges: agent orchestration and decisions are **real**. Ad platform metrics and Meta publish IDs are **simulated fixtures** for a safe demo. LLM enrichment is optional when Gemini is available.

---

### SCENE 3 — Happy path: LAUNCH → publish (0:55–1:45)

**Show:** My ads → open **Aurora Bottle Launch**. Stay on **Simple** view. Scroll creatives + “What the agents did” timeline. Click **Publish my ads** / approve if pending. Open landing preview if shown.

**Say:**

> Here’s a healthy product launch — **Aurora Bottle**. The Creative Agent built ad copy and creatives from the product brief. Sentiment and Strategy scored brand tone and ROAS. The Aggregator decided **LAUNCH**.
>
> Nothing goes live without a human. We approve, AdzMate builds a **Meta-style draft** — campaign, ad set, ads — then we **publish**. A landing page preview is deployed locally so the client can see the offer.
>
> The **action timeline** records every agent step for auditability — critical for agencies that need trust.

---

### SCENE 4 — HALT when performance is bad (1:45–2:20)

**Show:** Workspace switcher → **Beacon Media (client)** → open **Pulse Buds Rescue**. Show decision **HALT**, low ROAS / strategy message.

**Say:**

> Agencies don’t have one client — they have many workspaces. Here’s **Beacon Media**.
>
> **Pulse Buds** is burning budget with weak return. Strategy recommends pause; the Aggregator decides **HALT**. AdzMate protects spend instead of blindly launching.

---

### SCENE 5 — HOLD needs a human call (2:20–2:55)

**Show:** Switch back to **Local Demo** → **Cedar Desk Mixed** → decision **HOLD**.

**Say:**

> When creatives look fine but social sentiment is mixed, AdzMate chooses **HOLD** — escalate to a manager instead of auto-publishing risky ads. That’s human-in-the-loop by design.

*(If short on time: skip this scene; say one line about HOLD while pointing at Cedar on the list.)*

---

### SCENE 6 — Mid-flight action: auto-pause (2:55–3:35)

**Show:** A **published/live** campaign (Aurora or TrailRun). Confirm **Auto-pause on ROAS drop** is ON. Click **Spend spike / ROAS drop**. Show status pause/halt and timeline entry `auto_paused`. Optional: Run 1 day optimization.

**Say:**

> After publish, agents keep watching. With **auto-pause** enabled, a spend spike or ROAS collapse **pauses ads immediately** and logs the action.
>
> That’s action-taking — not just advice in a chat window. Optimization rules can also shift budget toward winning ads over simulated days.

---

### SCENE 7 — Close (3:35–4:00)

**Show:** `/agents` or architecture one-pager briefly. End on AdzMate logo / My ads.

**Say:**

> AdzMate: **orchestrated multi-agent reasoning**, clear **LAUNCH / HOLD / HALT** decisions, **human approval**, publish workflow, and **auto-pause** when performance drops.
>
> Built for IDEALIZE 2026 by **Team SUDO**. Thank you.

---

## Shorter 2:30 version (if time-capped)

1. Hook (15s)  
2. Agents page real vs mock (25s)  
3. Aurora LAUNCH + Publish (50s)  
4. Pulse Buds HALT (25s)  
5. Spend spike auto-pause (25s)  
6. Close (10s)

---

## Recording tips

- **One take per scene**, then edit — easier than one perfect take  
- If an API call is slow, keep talking: “Agents are finishing in parallel…”  
- If Gemini 429 appears, ignore it — templates still complete the pipeline  
- Never claim Meta Ads are live production unless OAuth + real API is configured  
- Prefer **Simple** view for most of the video; open **Technical** once for signals/aggregator if judges expect depth  
- Add soft background music at −20 dB or none; speech must stay clear  
- Export **1080p**, filename: `AdzMate_TeamSUDO_IDEALIZE2026_Demo.mp4`

---

## On-screen title cards (optional)

| Card | Text |
|------|------|
| Open | AdzMate — Multi-Agent Marketing Auto-Pilot · Team SUDO |
| Mid | Real agents · Simulated ad metrics · Human approval |
| End | IDEALIZE 2026 · Docs: ARCHITECTURE.md |

---

## Checklist mapped to speech lines

- [ ] Stated the **agency ops problem**  
- [ ] Said **orchestrator + 3 parallel agents + aggregator**  
- [ ] Showed **LAUNCH** (Aurora)  
- [ ] Showed **HALT** (Pulse Buds)  
- [ ] Mentioned or showed **HOLD** (Cedar)  
- [ ] Showed **human approve / publish**  
- [ ] Showed **timeline** or agent status  
- [ ] Showed **auto-pause** action  
- [ ] Said what is **real vs simulated**  

If every box is checked, the video meets the agentic + problem-statement judging story.
