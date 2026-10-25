# Requirement Specification

## 1. Purpose
Provide site engineers, contractors, structural engineers and project managers with AI-driven, structured
decision support across planning, execution and monitoring, using text, images and structured project data.

## 2. Problem areas addressed
| Lifecycle stage | Pain point | Platform feature |
|---|---|---|
| Execution / monitoring | Manual safety supervision, missed PPE gaps | Site Safety Monitoring |
| Monitoring / maintenance | Late identification of structural cracks | Crack Detection & Analysis |
| Planning | Manual, slow material and cost estimation | Project Planner |
| Feasibility | No quick, contextual property valuation | Real Estate Valuation |
| Execution | Ad-hoc daily coordination | Daily Site Assistant |
| Execution | Weather-related accidents and delays | Weather-Aware Advisory |
| All stages | Dependence on manual reference material | Knowledge Chat |

## 3. Functional requirements

### FR-1 Site Safety Monitoring
- Accept a site image (JPEG/PNG/WEBP/GIF, max 8 MB) and/or text description and optional site type.
- Identify hazards, worker positioning risks, PPE observed/missing, scaffolding and environmental risks.
- Return risk level (low/medium/high/critical), 0-100 score, recommended PPE, corrective actions, guidelines.
- Produce a valid report even when the image is unclear, partial, or absent (text-only reasoning).

### FR-2 Crack Detection
- Accept a crack image and/or description, optional element type and building age.
- Classify type (hairline, vertical, diagonal, stepped, structural...), orientation, severity (minor/moderate/severe).
- Estimate width, list probable causes, flag structural concern, give repair and preventive measures and an
  inspection priority with a confidence value.

### FR-3 Project Planner
- Accept plot length/width (ft), floors, construction type, quality grade, city, free-text requirements.
- Return built-up area, total cost and cost per sq ft in INR, material quantities (cement, sand, aggregate, steel,
  bricks), category-wise cost breakdown with percentages, week-wise phase schedule, assumptions.
- Return a conceptual architectural visualization: description, style, floor-plan notes and an SVG sketch.

### FR-4 Real Estate Valuation
- Accept city, locality, property type, area, bedrooms, age, floor, furnishing, amenities, landmarks.
- Return value range and midpoint, price per sq ft, monthly rent range, rental yield, appreciation, 5-year ROI,
  outlook, value drivers, risk factors, confidence. All monetary values numeric INR.
- Work with partial inputs (only city and area are mandatory).

### FR-5 Knowledge Chat
- Accept a question with up to 20 prior turns; return a concise answer, key points, references, follow-ups,
  and a disclaimer. Redirect off-domain questions politely.

### FR-6 Daily Site Assistant
- Accept project stage, planned activities, workforce, site conditions, weather, date.
- Return a day summary, prioritised tasks with crew and hours, materials, equipment, safety checks, risk alerts,
  end-of-day checklist.

### FR-7 Weather-Aware Advisory
- Accept planned activities, weather description, optional temperature, wind, rain probability, location.
- Return GO / CAUTION / NO-GO, confidence, rationale, risks, affected activities, precautions, mitigation,
  recommended window.

### FR-8 Centralized AI layer
- Single request handler for text-only and image+text requests, with feature identifiers in every prompt.
- JSON-mode generation, robust JSON extraction, one repair retry, then deterministic fallback.

## 4. Non-functional requirements
| ID | Requirement | How it is met |
|---|---|---|
| NFR-1 | Frontend never crashes on AI output | Pydantic coercion + `fallback()`; UI uses safe list/number accessors; React error boundary |
| NFR-2 | Machine-readable outputs | Every endpoint has a fixed schema; `meta` labels AI vs demo output |
| NFR-3 | Modularity | Routers per domain, one AI service, prompts/schemas/demo separated |
| NFR-4 | Maintainability | Adding a feature = schema + prompt guideline + router + page |
| NFR-5 | Security | API key only via environment; CORS allow-list; image magic-byte sniffing and size cap; SVG rendered inert |
| NFR-6 | Reproducibility | Pinned-minimum `requirements.txt`, `.env.example`, launch scripts, tests without network |
| NFR-7 | Usability | Loading states, inline validation errors, demo/offline status indicator, mobile layout |

## 5. Data flow
1. User submits a form (JSON) or multipart upload from a React page.
2. FastAPI validates the request body (422 with field errors on failure).
3. Router builds a feature-specific user message and calls `run_feature()`.
4. AI service selects vision or text model, sends system + user (+ image) messages in JSON mode.
5. Response JSON is extracted, validated and coerced into the feature schema; on failure a repair retry is sent,
   then demo/fallback data is used.
6. Router applies numeric consistency guards (e.g. derive cost per sq ft) and returns the contract.
7. React renders using null-safe accessors and labels the result's provenance from `meta`.
