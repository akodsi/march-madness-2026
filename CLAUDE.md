# March Madness Prediction Web App

## Project Goal
Build a web app that predicts March Madness tournament outcomes with confidence levels for each matchup. The user sees both teams' win percentages (e.g. 68% vs 32%) and picks winners manually. Picks cascade forward — each new matchup recalculates automatically as teams advance. Start with a rule-based system, architected to swap in a statistical or ML model later.

## Current Approach: Rule-Based (v2)
- 6 weighted signals: SRS, SOS, momentum, seed history, travel advantage, injuries → both teams' win %
- Expert commentary from ESPN scraped and passed through for display (not part of prediction formula)
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

## Frontend Improvements (v2) — all complete
- [x] Tab navigation — no horizontal scrolling, one region per tab (First Four / East / Midwest / West / South / Final Four)
- [x] Team logos — ESPN CDN logos on every matchup card, initials fallback for unrecognized schools
- [x] Matchup detail modal — click ⓘ on any card to see full breakdown: signal bars, plain-English "case for each team", pick/undo buttons
- [x] Raw stats passed from backend — SRS, SOS, seed, record, travel distance available in every matchup for the detail modal

## Tech Stack
- **Frontend**: Next.js 14 / React + Tailwind CSS — `frontend/`
- **Backend**: Python 3.9 + FastAPI + uvicorn — `backend/`
- **State**: File-based JSON (`data/processed/bracket_state_2026.json`)
- **Logos**: ESPN CDN (`a.espncdn.com/i/teamlogos/ncaa/500/{id}.png`) with initials fallback

## Running the App
```bash
# Terminal 1 — Backend (port 8000)
cd backend && source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 — Frontend (port 3000)
cd frontend && npm run dev
```
Open http://localhost:3000

## Git Workflow
```bash
# Always work on a branch, never directly on main
git checkout -b my-feature-name
# ... make changes ...
git add -A && git commit -m "describe changes"
git push origin my-feature-name
# When ready, merge to main
git checkout main && git merge my-feature-name && git push origin main
```
Repo: https://github.com/akodsi/march-madness-2026 (private)

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/bracket` | Full bracket state (67 matchups, includes raw_stats, signals, commentary) |
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
| ESPN CDN | Team logos for all 68 tournament schools |
| ESPN Schedule API | Game-by-game results for momentum (last 10 W/L, streaks, margins) |
| ESPN Injuries API | Injury reports + player status for health scores |
| ESPN Team Summary API | Expert headlines + team context for commentary display |

## Key Metrics & Weights (v2)
| Signal | Weight | What it measures |
|--------|--------|-----------------|
| SRS (efficiency) | **30%** | Overall team quality adjusted for opponent |
| SOS (schedule strength) | **25%** | How hard was their regular season |
| Momentum | **15%** | Last 10 games W/L record + margin of victory trend |
| Seed history | **10%** | 10-year historical win rate for this seed matchup |
| Travel advantage | **10%** | Geographic proximity to game venue |
| Injuries | **10%** | Roster health — key players out reduce team's score |

**Commentary** (display only): ESPN headlines + team context shown in matchup detail modal. Not part of weighted formula.

Confidence labels: Heavy Favorite (80%+) · Clear Favorite (65–79%) · Slight Edge (55–64%) · Toss-Up (<55%)

## Data Decisions
- **Historical window: 10 years (2015–2024)** — not 40. Modern basketball plays differently than the 1985–2005 era. 2020 excluded (COVID). ~603 games across 9 tournaments.
- **Seeds down-weighted to 10%** — allows genuinely strong low-seeds and weak high-seeds to show through the data.
- **Momentum at 15%** — a team's last 10 games (W/L + margin trend) captures form heading into the tournament. A hot team on a 9-game win streak is meaningfully different from one limping in at 4-6.
- **Injuries at 10%** — missing a star player can swing a game, but injury data is noisy (status changes daily, importance is estimated). Kept at 10% to influence without dominating.
- **Commentary is display-only** — expert analysis is valuable as a sense check but too subjective to quantify in a formula. Shown in the matchup detail modal alongside signal breakdowns.
- **No auto-winner prediction** — the app shows probabilities and lets the user decide, preserving human judgment.

## File Structure
```
backend/
├── main.py                          FastAPI app (5 endpoints)
├── models/
│   ├── rule_engine.py               6-signal weighted probability calculator + commentary
│   └── bracket.py                   Full bracket tree with pick/cascade logic
├── pipeline/
│   ├── run_pipeline.py              Master pipeline runner (6 steps)
│   ├── stats_ingest.py              Sports-Reference scraper
│   ├── kaggle_ingest.py             Historical tournament data loader
│   ├── geo_ingest.py                Campus geocoding + travel distances
│   ├── normalize.py                 Metric normalization
│   ├── tournament_filter.py         Filter to 68 confirmed teams (merges all data)
│   ├── espn_ids.py                  ESPN team ID mapping for 68 teams
│   ├── momentum_ingest.py           Last-10 games, streaks, margin trends from ESPN
│   ├── injury_ingest.py             ESPN injury reports → health scores
│   ├── commentary_ingest.py         ESPN headlines + sentiment for display
│   └── torvik_ingest.py             Bart Torvik advanced stats (optional)
└── data/processed/                  All output CSVs + bracket JSON + commentary JSON

frontend/
├── src/app/                         Next.js app shell
├── src/lib/
│   ├── types.ts                     TypeScript interfaces (Matchup with raw_stats)
│   ├── api.ts                       API client functions
│   ├── bracketSlots.ts              Slot ordering + layout constants
│   └── teamLogos.ts                 ESPN logo URL mapping for 68 teams
└── src/components/
    ├── BracketBoard.tsx             Tab navigation + state manager
    ├── RegionBracket.tsx            One region's 4 rounds
    ├── MatchupCard.tsx              Team logos + % bars + ⓘ info button
    ├── MatchupDetail.tsx            Full breakdown modal (signals, case for each team)
    ├── ConnectorLines.tsx           SVG bracket connector lines
    ├── FirstFour.tsx                First Four section
    └── FinalFour.tsx                Final Four + Championship
```

## Build Order
1. ✅ Data pipeline — Sports-Reference stats, seed history, geocoding, travel distances
2. ✅ Tournament filter — 68 confirmed 2026 teams with seeds, regions, stats, travel scores
3. ✅ Rule engine — 6 weighted signals → both teams' win %
4. ✅ Bracket model — 67-matchup tree, pick/cascade/undo, JSON persistence
5. ✅ FastAPI layer — 5 REST endpoints with CORS
6. ✅ Frontend — full bracket UI, confidence %, click-to-pick, live cascade
7. ✅ Frontend v2 — tab navigation, team logos, matchup detail modal with signal breakdown
8. ✅ Backend v2 — momentum (ESPN schedule), injuries (ESPN API), expert commentary
9. Post-round refresh — update predictions after each round's results (next)
10. Frontend v3 — display momentum, injuries, and commentary in matchup detail modal

## Running the Pipeline
```bash
cd backend && source venv/bin/activate

# Full pipeline (6 steps — stats, seeds, profiles, travel, momentum, injuries+commentary)
python pipeline/run_pipeline.py

# Individual new steps
python pipeline/momentum_ingest.py     # Last-10 games from ESPN
python pipeline/injury_ingest.py       # ESPN injury reports
python pipeline/commentary_ingest.py   # ESPN headlines + sentiment
```
Re-run before each round to pick up updated momentum, fresh injury reports, and latest commentary.

## Future Model Upgrade Path
Swap `WEIGHTS` dict in `rule_engine.py` for quick re-weighting. Full model upgrade (ELO, logistic regression, ML) only requires reimplementing `predict()` — the bracket model and frontend are decoupled from prediction logic. The 6-signal architecture makes it easy to add or remove signals without touching the bracket or frontend.
