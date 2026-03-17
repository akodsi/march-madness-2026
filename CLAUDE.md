# March Madness Prediction Web App

## Project Goal
Build a web app that predicts March Madness tournament outcomes with confidence levels for each matchup. The user sees both teams' win percentages (e.g. 68% vs 32%) and picks winners manually. Picks cascade forward — each new matchup recalculates automatically as teams advance. Start with a rule-based system, architected to swap in a statistical or ML model later.

## Current Approach: Rule-Based
- Weighted combination of SRS, SOS, seed history, and travel advantage → both teams' win %
- User picks the winner — no auto-prediction
- Picks cascade forward through all 6 rounds
- Rules are in a swappable `WEIGHTS` dict in `models/rule_engine.py` for easy iteration

## Core Features (MVP) — all complete
- [x] Full 68-team bracket with confidence intervals on every matchup
- [x] Both teams' win % shown (e.g. Duke 99% vs Siena 1%)
- [x] Click to pick, click again to undo — cascades to all future rounds
- [x] First Four games feed correctly into Round of 64
- [x] Final Four and Championship wired between regions
- [x] Bracket state persists to JSON between sessions
- [x] Reset button to wipe all picks

## Tech Stack
- **Frontend**: Next.js 14 / React + Tailwind CSS — `frontend/`
- **Backend**: Python 3.9 + FastAPI + uvicorn — `backend/`
- **State**: File-based JSON (`data/processed/bracket_state_2026.json`)

## Running the App
```bash
# Terminal 1 — Backend (port 8000)
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (port 3000)
cd frontend && npm run dev
```
Open http://localhost:3000

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/bracket` | Full bracket state (67 matchups) |
| POST | `/bracket/{id}/pick` | Submit a pick `{"winner": "Team Name"}` |
| DELETE | `/bracket/{id}/pick` | Undo a pick, clears downstream |
| POST | `/bracket/reset` | Wipe all picks |

## Data Sources
| Source | Purpose |
|--------|---------|
| [Sports-Reference CBB](https://www.sports-reference.com/cbb) | Current season team stats (wins, SRS, SOS, pace, ORtg) |
| Built-in seed history (2015–2024) | 10-year historical seed matchup win rates |
| OpenStreetMap / Nominatim | Campus geocoding for travel distance |
| NCAA Selection Sunday 2026 | Official 68-team bracket, seedings, regions |

## Key Metrics & Weights (v1)
| Signal | Weight | What it measures |
|--------|--------|-----------------|
| SRS (efficiency) | **40%** | Overall team quality adjusted for opponent |
| SOS (schedule strength) | **30%** | How hard was their regular season |
| Seed history | **15%** | 10-year historical win rate for this seed matchup |
| Travel advantage | **15%** | Geographic proximity to game venue |

Confidence labels: Heavy Favorite (80%+) · Clear Favorite (65–79%) · Slight Edge (55–64%) · Toss-Up (<55%)

## Data Decisions
- **Historical window: 10 years (2015–2024)** — not 40. Modern basketball plays differently than the 1985–2005 era. 2020 excluded (COVID). ~603 games across 9 tournaments.
- **Seeds down-weighted to 15%** — allows genuinely strong low-seeds and weak high-seeds to show through the data.
- **No auto-winner prediction** — the app shows probabilities and lets the user decide, preserving human judgment.

## File Structure
```
backend/
├── main.py                          FastAPI app (5 endpoints)
├── models/
│   ├── rule_engine.py               Weighted probability calculator
│   └── bracket.py                   Full bracket tree with pick/cascade logic
├── pipeline/
│   ├── run_pipeline.py              Master pipeline runner
│   ├── stats_ingest.py              Sports-Reference scraper
│   ├── kaggle_ingest.py             Historical tournament data loader
│   ├── geo_ingest.py                Campus geocoding + travel distances
│   ├── normalize.py                 Metric normalization
│   └── tournament_filter.py        Filter to 68 confirmed teams
└── data/processed/                  All output CSVs + bracket JSON

frontend/
├── src/app/                         Next.js app shell
├── src/lib/
│   ├── types.ts                     TypeScript interfaces
│   ├── api.ts                       API client functions
│   └── bracketSlots.ts              Slot ordering + layout constants
└── src/components/
    ├── BracketBoard.tsx             Main bracket container + state
    ├── RegionBracket.tsx            One region's 4 rounds
    ├── MatchupCard.tsx              Individual matchup with % bars
    ├── ConnectorLines.tsx           SVG bracket connector lines
    ├── FirstFour.tsx                First Four section
    └── FinalFour.tsx                Final Four + Championship
```

## Build Order
1. ✅ Data pipeline — Sports-Reference stats, seed history, geocoding, travel distances
2. ✅ Tournament filter — 68 confirmed 2026 teams with seeds, regions, stats, travel scores
3. ✅ Rule engine — SRS 40% + SOS 30% + Seed 15% + Travel 15% → both teams' win %
4. ✅ Bracket model — 67-matchup tree, pick/cascade/undo, JSON persistence
5. ✅ FastAPI layer — 5 REST endpoints with CORS
6. ✅ Frontend — full bracket UI, confidence %, click-to-pick, live cascade
7. Post-round refresh — update predictions after each round's results (next)

## Future Model Upgrade Path
Swap `WEIGHTS` dict in `rule_engine.py` for quick re-weighting. Full model upgrade (ELO, logistic regression, ML) only requires reimplementing `predict()` — the bracket model and frontend are decoupled from prediction logic.
