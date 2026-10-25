# Testing Report

## Automated backend tests (`backend/tests`)
Run: `cd backend && .venv\Scripts\python -m pytest -q`
Result on 2026-10-25: **40 passed** (no network access; demo mode forced in `conftest.py`).

| Area | Tests | What is verified |
|---|---|---|
| Schema enforcement | `test_schemas.py` (10) | Every model has non-null defaults; messy AI output (strings for lists, dict-shaped lists, `"87%"`, `"₹12,00,000"`, out-of-range confidence, enum variants) coerces correctly; JSON extraction from fenced / prose-wrapped replies; garbage rejected |
| AI layer | `test_ai_service.py` (6) | Success path marks `ai_generated`; image requests use the vision model with a base64 data URL; invalid JSON is repaired on retry; persistent failure falls back to demo data with the reason in `meta.notes`; 401 does not retry; disabled AI never calls the LLM |
| Functional API | `test_api.py` (24) | Health; all seven endpoints return complete contracts; planner and valuation numeric consistency (range ordering, percentages ≈ 100, SVG present); weather NO-GO on storm / GO on clear; repeated requests are stable |
| Edge cases | `test_api.py` | Empty request (422), empty file upload with description (200 fallback), non-image file (415), spoofed `image/png` content type (415), 9 MB upload (413), negative age (422), zero area (422), rain probability 150 (422), blank chat (422), unknown city (200) |

## Manual end-to-end UI checks (Vite dev server + uvicorn, demo mode)
| Flow | Result |
|---|---|
| App loads, sidebar shows "Backend online · demo mode" | Pass |
| Project Planner with defaults (30x40 ft, 2 floors, Pune) renders KPIs, materials table, cost breakdown, Gantt schedule, concept sketch | Pass |
| Weather Advisory with "Thunderstorm with heavy rain and gusty winds" → NO-GO badge, risks, precautions, mitigation, window | Pass |
| Site Safety submitted with no image and no text → inline error "Provide a site image, a description, or both." | Pass (expected 422) |
| Knowledge Chat starter question → answer, key points, references, follow-up chips | Pass |
| Browser console | No runtime errors (only the expected 422 network log) |
| Production build `npm run build` | Pass (25 modules, ~253 kB JS) |

Screenshots: `docs/screenshots/`.

## Not covered yet
- Live LLM responses were not exercised in this session (no API key configured); the live path is covered by
  mocked tests only. With a key, re-run the UI checks and confirm `meta.ai_generated` is `true`.
- No automated frontend component tests; the UI relies on null-safe accessors and a React error boundary.
