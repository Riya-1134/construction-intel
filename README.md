# AI-Powered Multimodal Construction Intelligence Platform

A full-stack decision-support system for construction professionals. A **React + Vite** frontend talks to a
**FastAPI** backend that routes every request through a single multimodal LLM layer (Groq) and enforces
**strict JSON contracts**, so the UI never crashes on partial or malformed AI output.

| Feature | Input | Output |
|---|---|---|
| Site Safety Monitoring | site image + optional text | hazards, risk level/score, PPE observed/missing, corrective actions |
| Crack Detection & Analysis | crack image + optional text | crack type, orientation, severity, causes, repairs, prevention |
| Project Planner | plot size, floors, type, quality, city | materials, INR cost breakdown, week-wise schedule, concept sketch |
| Real Estate Valuation | location, area, age, amenities | value range, price/sq ft, rent, yield, ROI, outlook |
| Daily Site Assistant | stage, activities, workforce, conditions | prioritised tasks, materials, equipment, safety checks, alerts |
| Weather-Aware Advisory | activities + weather | GO / CAUTION / NO-GO, risks, precautions, mitigation |
| Knowledge Chat | question + history | answer, key points, IS/NBC references, follow-ups |

The platform runs fully **offline in demo mode** (deterministic, thumb-rule based responses) when no API key is
configured, and switches to live multimodal AI reasoning as soon as `GROQ_API_KEY` is set.

---

## 1. Architecture

```
frontend/ (React 19 + Vite)                 backend/ (FastAPI, Python 3.9+)
┌─────────────────────────┐   JSON / multipart   ┌───────────────────────────────────────┐
│ pages/   7 feature views│ ───────────────────▶ │ routers/analysis.py   image + text     │
│ api.js   typed client   │ ◀─────────────────── │ routers/planning.py   planner/valuation│
│ components/ui.jsx       │   strict JSON        │ routers/assistants.py chat/daily/weather│
└─────────────────────────┘                      │        │                               │
                                                 │        ▼                               │
                                                 │ ai_service.run_feature()  ◀── prompts.py│
                                                 │   • builds feature prompt + metadata   │
                                                 │   • text or image+text → Groq LLM      │
                                                 │   • JSON extraction + retry-on-repair  │
                                                 │   • schemas.py validation + coercion   │
                                                 │   • demo.py / fallback() on failure    │
                                                 └───────────────────────────────────────┘
```

Key backend modules:

- `backend/app/ai_service.py` - the centralized multimodal AI interaction layer used by every feature.
- `backend/app/prompts.py` - base system prompt (construction domain, deterministic JSON) + per-feature guidelines.
- `backend/app/schemas.py` - Pydantic contracts with coercion validators and `fallback()` builders.
- `backend/app/demo.py` - deterministic demo payloads (Indian thumb rules, city rate tables).
- `backend/app/visualization.py` - server-side SVG concept sketch (elevation + plot footprint).

---

## 2. Prerequisites

- Python 3.9+ (tested on 3.14), Node.js 18+ (tested on 24), npm, Git.
- A Groq API key (free tier works) for live AI. Optional: the app runs in demo mode without one.

## 3. Setup

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env               # macOS/Linux: cp .env.example .env
```

Edit `backend/.env`:

```
GROQ_API_KEY=gsk_...                 # leave empty for demo mode
GROQ_VISION_MODEL=qwen/qwen3.8-27b          # must support image input on your key
GROQ_TEXT_MODEL=openai/gpt-oss-120b
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEMO_MODE=false
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env               # optional; defaults to http://localhost:8000
```

## 4. Run

Terminal 1 (backend):

```bash
cd backend && .venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2 (frontend):

```bash
cd frontend && npm run dev
```

Open http://localhost:5173. The sidebar shows backend status and whether AI is **live** or in **demo mode**.
Interactive API docs: http://localhost:8000/docs. Health: http://localhost:8000/api/health.

Helper scripts for Windows: `scripts/start-backend.ps1` and `scripts/start-frontend.ps1`.

## 5. API summary

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/api/health` | - | status, ai_enabled, models |
| POST | `/api/safety/analyze` | multipart: `image?`, `description?`, `site_type?` | `SafetyReport` |
| POST | `/api/crack/analyze` | multipart: `image?`, `description?`, `element?`, `building_age_years?` | `CrackReport` |
| POST | `/api/planner/generate` | JSON `PlanRequest` | `ProjectPlan` |
| POST | `/api/valuation/estimate` | JSON `ValuationRequest` | `ValuationReport` |
| POST | `/api/chat` | JSON `{message, history[]}` | `ChatResponse` |
| POST | `/api/daily/plan` | JSON `DailyRequest` | `DailyPlan` |
| POST | `/api/weather/advisory` | JSON `WeatherRequest` | `WeatherAdvisory` |

Full field-level contracts: [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md). Every response carries a `meta`
object (`feature`, `model`, `ai_generated`, `notes`) so the UI can label demo/fallback output.

Validation errors always return `422 {"detail": "Invalid input", "errors": [{field, message}]}`.
Images are sniffed by magic bytes (JPEG/PNG/WEBP/GIF), capped at 8 MB, and a spoofed content-type is rejected with 415.

## 6. Testing

```bash
cd backend && .venv\Scripts\python -m pytest -q
```

40 tests cover schema coercion, JSON extraction, the AI layer with a mocked LLM (success, repair-on-retry,
fallback, auth short-circuit), every endpoint, and edge cases (empty uploads, spoofed/oversized files,
out-of-range numbers, repeated-request stability). Tests never call the network. See
[docs/TESTING.md](docs/TESTING.md) for the end-to-end checklist and results.

## 7. Build and deployment

### One-click on Render (recommended)
A [render.yaml](render.yaml) blueprint deploys both halves:

| Service | Type | What it does |
|---|---|---|
| `construction-intel-api` | Python web service | `uvicorn app.main:app`, health check on `/api/health` |
| `construction-intel-web` | Static site | `npm ci && npm run build`, serves `frontend/dist` |

Steps:
1. Push this folder to a GitHub or GitLab repository (`.env` files are git-ignored and never uploaded).
2. In Render choose **New > Blueprint**, select the repo, and click **Apply**.
3. When prompted, paste your `GROQ_API_KEY`. Everything else is pre-filled: the frontend's host is injected into
   the API's `CORS_ORIGINS`, and the API's host is injected into the frontend's `VITE_API_BASE_URL` at build time.
4. Open the static site URL. The sidebar should read "Backend online · AI live".

Notes: the free plan spins the API down after 15 minutes idle, so the first request after a pause takes
20-40 seconds (the UI shows the loading state). Upgrade the API service to `starter` to avoid that. Change
`region` in `render.yaml` if you want a different data centre.

### Manual / other hosts
```bash
cd frontend && npm run build          # outputs frontend/dist (static)
```

- Serve `frontend/dist` from any static host (Vercel, Netlify, S3 + CloudFront, Nginx) with `VITE_API_BASE_URL`
  set at build time to the public backend URL (a bare host is accepted; `https://` is assumed).
- Run the backend with `uvicorn app.main:app --host 0.0.0.0 --port 8000` behind a reverse proxy, or in a
  container. Set `CORS_ORIGINS` to the frontend origin and keep `GROQ_API_KEY` in the environment, never in code.
- AWS: EC2 (t3.small is sufficient) or App Runner for the API; S3 + CloudFront for the static frontend.
- Vercel for the frontend only: import the repo, set root directory to `frontend`, framework Vite,
  and add `VITE_API_BASE_URL` pointing at the Render API.

## 8. Known limitations

- Valuation and planning figures are **indicative** (LLM reasoning plus thumb rules), not registered
  valuations or BOQs. Always verify with local contractors and engineers.
- Crack and safety analysis assist inspection; they do not replace a structural engineer or safety officer.
- The architectural visualization is a conceptual SVG sketch, not a rendered image or a drawing to scale.
- Demo mode uses fixed city rate tables for a subset of Indian cities and a default rate elsewhere.
- Live vision quality depends on photo clarity; unclear images lower confidence and may trigger fallback output.
- No authentication or persistence; the app is single-tenant and stateless by design for this phase.

## 9. Project layout

```
backend/
  app/            config, main, ai_service, prompts, schemas, demo, visualization, routers/
  tests/          pytest suite (schemas, API, AI layer)
  requirements.txt, .env.example
frontend/
  src/            App.jsx, api.js, components/ui.jsx, pages/*.jsx, index.css
  .env.example, package.json, vite.config.js
docs/             REQUIREMENTS.md, API_CONTRACTS.md, TESTING.md, screenshots/
scripts/          start-backend.ps1, start-frontend.ps1
```
