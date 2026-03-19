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

## Frontend Improvements (v3) — all complete
- [x] Streak badges on cards — `W11` / `L3` shown inline on each team row when streak ≥ 3 games
- [x] Injury warning icon — `⚠` shown on card when key players are out
- [x] Momentum section in modal — last-10 record (color-coded), current streak, avg margin per game; "No schedule data available" for small schools not in ESPN
- [x] Injury Report section in modal — health score bar (green/yellow/red), injured player count, key players out by name; hidden when all teams healthy
- [x] ESPN Coverage section in modal — sentiment indicator (↑/↓/—), team context (record + ranking), up to 2 headlines; hidden until pipeline is run
- [x] Signal bars updated — momentum and injuries now appear alongside SRS/SOS/seed/travel with correct weights

## Frontend Improvements (v4 — Visual Polish & Export) — all complete
- [x] Seed numbers — shown before team names on cards (`1 Duke`) and as circular badges in the detail modal
- [x] Card hover effects — blue glow shadow, subtle scale bump (`hover:scale-[1.02]`), smoother border transitions
- [x] Pick styling — amber border/shadow on picked cards, amber left border accent on winner row
- [x] Wider/taller % bars (32×8px) with animated width transitions
- [x] Confidence pill labels — colored background pills instead of plain text (e.g. emerald pill for "Heavy Favorite")
- [x] Tab fade transitions — fade-in + slide-up animation on tab switch
- [x] Connector lines — thicker with rounded caps/joins, highlight blue when feeder game is picked
- [x] Final Four layout — horizontal mini-bracket with SVG connectors, trophy icon, champion display below when picked
- [x] Mobile responsiveness — scrollable tab bar, responsive header text/padding, hidden scrollbar on mobile
- [x] PDF export — "Export PDF" button in header, renders full bracket (4 regions in 2×2 grid + Final Four) to landscape PDF via `jspdf` + `html2canvas`

## Frontend Improvements (v4.1 — Signal Bar Contrast) — all complete
- [x] Signal breakdown bars — dominant side color-coded by edge strength (emerald ≥75%, blue ≥60%, yellow ≥52%); weaker side darkened to `slate-800` for sharp contrast; 1px gap divider between halves

## Community Commentary (v5) — all complete
- [x] Google News RSS — up to 4 recent headlines per team from reputable outlets, with source and date; summary blurb from top 3 titles
- [x] Reddit r/collegebasketball — up to 5 top posts per team (last 30 days), sorted by upvote score; summary blurb from top 3 titles
- [x] Both sources shown in matchup detail modal as new sections (Google News · r/CollegeBasketball); hidden when no data present
- [x] Community data stored in `community_2026.json`, merged into commentary at prediction time — display only, not part of weighted formula

## Frontend Improvements (v5.1 — Community Section Polish) — all complete
- [x] Summary blurbs styled as tinted callout boxes — blue left-border accent for Google News, orange for Reddit; `italic text-slate-300` inside for visual distinction from headline items
- [x] Reddit posts — `▲` upvote icon, full `text-orange-400` (no opacity reduction), comma-formatted scores, `border-orange-500/30` left border
- [x] Google News source/date — bumped from `text-slate-600` to `text-slate-500` for readability while staying de-emphasized
- [x] Section headers — added muted sub-labels ("recent headlines" / "community posts") alongside the uppercase title

## Champion Likelihood (v6 — Backend Only) — all complete
- [x] Bart Torvik efficiency data — AdjOE, AdjDE, AdjEM ranks for all D1 teams via session-authenticated CSV (free KenPom substitute)
- [x] AP Poll Top 25 — current week's rankings from ESPN public API
- [x] Hard filters — historically-validated rules that nearly all champions pass (top-25 Torvik overall, top-25 AdjDE, seed ≤ 8)
- [x] Soft scoring — bonus points for AP top-12, top-40 AdjOE, top-15 overall, top-10 AdjDE, top-3 seed
- [x] Per-rule structured checks — each rule returns `rule_id`, `label`, `passed`, `value`, `threshold`, `detail`, `points`, `is_hard` for frontend rendering
- [x] Champion likelihood flows through bracket API (`champion_likelihood.team_a` / `team_b`) — display only, not part of weighted prediction formula
- [x] TypeScript types added (`ChampionCheck`, `ChampionLikelihood` interfaces)
- [x] Pipeline step 8/9 fetches Torvik + AP data before final merge; 24-hour JSON caching
- [x] Frontend rendering of champion checks — modal section + full comparison page

## Champion Likelihood Frontend (v6.1) — all complete
- [x] Champion Profile section in matchup detail modal — side-by-side grid per team, fraction header ("5/8 checks passed") color-coded, proximity rules show ordinal rank values (e.g. "5th"), binary rules show ✓/✗, hard filter failures get red "ELIMINATED" banner
- [x] Champion Comparison page (`/champion` route) — sortable table of all 68 teams with logo, seed, score, and every check column; click any column header to sort; eliminated teams dimmed with toggle; legend at bottom
- [x] New backend endpoint `GET /champion-likelihood` — returns all 68 teams scored and sorted by champion likelihood
- [x] "Champion Profiles" button in bracket header linking to `/champion`; "Back to Bracket" link on champion page

## Vegas Odds (v7 — Backend Only) — all complete
- [x] DraftKings moneyline + spread for all Round of 64 matchups via The Odds API (free tier, 500 req/month)
- [x] Implied win probability from American moneylines (raw with vig + no-vig normalized)
- [x] NIT/non-tournament games filtered out automatically using bracket roster
- [x] Odds flow through bracket API (`raw_stats.moneyline_a/b`, `spread_a/b`, `no_vig_prob_a/b`) — display only, not part of weighted prediction formula
- [x] TypeScript types added for all odds fields in `raw_stats`
- [x] Pipeline step 9/10 fetches odds before final merge; API key stored in `.env`
- [x] Bracket matchup corrections: Missouri ↔ Texas A&M (South/West swap), Penn ↔ Queens NC (South/West swap) — verified against DraftKings lines

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
| GET | `/bracket` | Full bracket state (67 matchups, includes raw_stats, signals, commentary, champion_likelihood, vegas odds) |
| POST | `/bracket/{id}/pick` | Submit a pick `{"winner": "Team Name"}` |
| DELETE | `/bracket/{id}/pick` | Undo a pick, clears downstream |
| POST | `/bracket/reset` | Wipe all picks |
| GET | `/champion-likelihood` | All 68 teams scored against champion patterns, sorted by score |

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
| Google News RSS | Recent headlines from reputable outlets (4 per team) |
| Reddit r/collegebasketball | Top community posts per team (last 30 days, sorted by score) |
| [Bart Torvik](https://barttorvik.com) | Team-level AdjOE/AdjDE/AdjEM efficiency ranks (free KenPom substitute) |
| ESPN Rankings API | AP Poll Top 25 for champion-pattern scoring |
| [The Odds API](https://the-odds-api.com/) | DraftKings moneyline + spread for tournament matchups (free tier) |

## Key Metrics & Weights (v2)
| Signal | Weight | What it measures |
|--------|--------|-----------------|
| SRS (efficiency) | **30%** | Overall team quality adjusted for opponent |
| SOS (schedule strength) | **25%** | How hard was their regular season |
| Momentum | **15%** | Last 10 games W/L record + margin of victory trend |
| Seed history | **10%** | 10-year historical win rate for this seed matchup |
| Travel advantage | **10%** | Geographic proximity to game venue |
| Injuries | **10%** | Roster health — key players out reduce team's score |

**Commentary** (display only): ESPN headlines + team context, Google News headlines, and Reddit r/collegebasketball posts shown in matchup detail modal. Not part of weighted formula.

**Champion Likelihood** (display only): Torvik efficiency ranks + AP Poll scored against historically-validated champion patterns. Hard filters (top-25 overall, top-25 defense, seed ≤ 8) plus soft score bonuses. Per-rule pass/fail checks available in API for frontend rendering.

**Vegas Odds** (display only): DraftKings moneyline + spread per matchup. Implied win % (no-vig normalized) shown alongside model predictions for comparison. Not part of weighted formula — Vegas lines already incorporate the same signals the model uses, so blending would double-count.

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
├── main.py                          FastAPI app (6 endpoints)
├── models/
│   ├── rule_engine.py               6-signal weighted probability calculator + commentary + champion likelihood + vegas odds
│   ├── champion_rules.py            Champion-pattern scoring (hard filters + soft score from Torvik/AP data)
│   └── bracket.py                   Full bracket tree with pick/cascade logic
├── pipeline/
│   ├── run_pipeline.py              Master pipeline runner (10 steps — ends with tournament_filter merge)
│   ├── stats_ingest.py              Sports-Reference scraper
│   ├── kaggle_ingest.py             Historical tournament data loader
│   ├── geo_ingest.py                Campus geocoding + travel distances
│   ├── normalize.py                 Metric normalization
│   ├── tournament_filter.py         Filter to 68 confirmed teams (merges all data)
│   ├── espn_ids.py                  ESPN team ID mapping for 68 teams
│   ├── momentum_ingest.py           Last-10 games, streaks, margin trends from ESPN
│   ├── injury_ingest.py             ESPN injury reports → health scores
│   ├── commentary_ingest.py         ESPN headlines + sentiment for display
│   ├── community_ingest.py          Google News RSS + Reddit posts → community_2026.json
│   ├── champion_ingest.py           Bart Torvik efficiency ranks + ESPN AP Poll → champion_data_2026.json
│   ├── odds_ingest.py               DraftKings moneyline + spread via The Odds API → odds_2026.json
│   └── torvik_ingest.py             Bart Torvik advanced stats (optional)
└── data/processed/                  All output CSVs + bracket JSON + commentary JSON

frontend/
├── src/app/                         Next.js app shell (/ bracket, /champion comparison)
│   └── champion/page.tsx            Champion Profiles full-page sortable table
├── src/lib/
│   ├── types.ts                     TypeScript interfaces (Matchup, raw_stats, Headline, RedditPost, TeamCommentary, ChampionCheck, ChampionLikelihood)
│   ├── api.ts                       API client functions
│   ├── bracketSlots.ts              Slot ordering + layout constants
│   ├── teamLogos.ts                 ESPN logo URL mapping for 68 teams
│   └── exportPdf.ts                 PDF export via html2canvas + jsPDF
└── src/components/
    ├── BracketBoard.tsx             Tab navigation + state manager + export button + champion profiles link
    ├── RegionBracket.tsx            One region's 4 rounds
    ├── MatchupCard.tsx              Seeds + logos + % bars + streak badge + injury icon + ⓘ button
    ├── MatchupDetail.tsx            Full breakdown modal (signals, momentum, injuries, ESPN/Google News/Reddit commentary, champion profile, case for each team)
    ├── ConnectorLines.tsx           SVG bracket connector lines (with pick-aware highlighting)
    ├── FirstFour.tsx                First Four section
    ├── FinalFour.tsx                Final Four mini-bracket with connectors + trophy
    └── PrintBracket.tsx             Compact full-bracket layout for PDF export
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
9. ✅ Frontend v3 — streak badges, injury icons on cards; momentum/injury/commentary sections in modal
10. ✅ Frontend v4 — visual polish (hover effects, transitions, seed display, confidence pills), layout improvements (Final Four mini-bracket, mobile responsiveness), PDF export
11. ✅ Community commentary (v5) — Google News RSS + Reddit r/collegebasketball sections in matchup detail modal
12. ✅ Frontend v5.1 — polished Google News and Reddit sections (callout blurbs, Reddit orange accent, readable source/date)
13. ✅ Champion likelihood (v6) — Torvik efficiency + AP Poll → per-rule champion-pattern scoring (backend only, frontend deferred)
14. ✅ Champion likelihood frontend (v6.1) — modal section + `/champion` comparison page + new API endpoint
15. ✅ Vegas odds (v7) — DraftKings moneyline + spread via The Odds API (backend only, frontend deferred)
16. Vegas odds frontend (v7.1) — odds section in matchup detail modal + card indicators (next)
17. Post-round refresh — update predictions after each round's results

## Running the Pipeline
```bash
cd backend && source venv/bin/activate

# Full pipeline (10 steps — stats, seeds, profiles, travel, momentum, injuries+commentary, community, champion, odds, merge)
python pipeline/run_pipeline.py

# Individual steps
python pipeline/momentum_ingest.py     # Last-10 games from ESPN
python pipeline/injury_ingest.py       # ESPN injury reports
python pipeline/commentary_ingest.py   # ESPN headlines + sentiment
python -m pipeline.community_ingest    # Google News RSS + Reddit posts
python pipeline/champion_ingest.py     # Bart Torvik ranks + AP Poll
python pipeline/odds_ingest.py         # DraftKings moneyline + spread (requires ODDS_API_KEY in .env)
python pipeline/tournament_filter.py   # Merge all data into tournament_teams CSV (run after any ingest)
```
Re-run before each round to pick up updated momentum, fresh injury reports, and latest commentary.
**Important:** Always restart the backend after re-running the pipeline — uvicorn caches team data in memory.

## Future Model Upgrade Path
Swap `WEIGHTS` dict in `rule_engine.py` for quick re-weighting. Full model upgrade (ELO, logistic regression, ML) only requires reimplementing `predict()` — the bracket model and frontend are decoupled from prediction logic. The 6-signal architecture makes it easy to add or remove signals without touching the bracket or frontend.
