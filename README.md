# 2026 March Madness Predictor

A web app for predicting March Madness tournament outcomes with confidence-interval win probabilities. Pick your bracket manually while the app shows you the data behind every matchup.

![Next.js](https://img.shields.io/badge/Next.js-14-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green) ![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38bdf8)

---

## Features

**Bracket Prediction**
- Full 68-team bracket with win % on every matchup (e.g. Duke 68% vs Kansas 32%)
- 6-signal weighted model: team quality (SRS), schedule strength (SOS), momentum, seed history, travel advantage, injuries
- Click to pick a winner — cascades forward through all 6 rounds automatically
- Click again to undo any pick

**Matchup Detail Modal**
- Signal breakdown bars showing which team has the edge on each factor
- Momentum section: last-10 record, current streak, avg margin
- Injury report: health score, players out by name
- ESPN expert coverage + sentiment
- Google News headlines and Reddit r/collegebasketball community posts
- Champion Profile: per-rule pass/fail checks showing each team's fit against historical champion patterns

**Champion Profiles Page (`/champion`)**
- All 68 teams ranked by champion likelihood score
- Sortable table with every check column — click any header to sort
- Torvik efficiency ranks displayed as ordinal values (e.g. "5th"); AP Poll and seed checks as ✓/✗
- Hard-filter eliminations dimmed with red badge; toggle to hide them
- Historically-validated rules: top-25 Torvik overall, top-25 defense, top-40 offense, AP top-12, seed ≤ 8

**Visual Design**
- Dark slate theme, team logos from ESPN CDN, initials fallback
- Confidence pills: Heavy Favorite · Clear Favorite · Slight Edge · Toss-Up
- Streak badges (`W11` / `L3`) and injury warning icons on cards
- Tab navigation per region, Final Four mini-bracket with SVG connectors
- PDF export of the full bracket

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React, Tailwind CSS |
| Backend | Python 3.9, FastAPI, uvicorn |
| State | File-based JSON (`bracket_state_2026.json`) |
| Logos | ESPN CDN with initials fallback |

---

## Getting Started

**Prerequisites:** Node.js 18+, Python 3.9+

```bash
# Clone the repo
git clone https://github.com/akodsi/march-madness-2026.git
cd march-madness-2026
```

**Terminal 1 — Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/bracket` | Full bracket state (67 matchups) |
| `POST` | `/bracket/{id}/pick` | Submit a pick `{"winner": "Team Name"}` |
| `DELETE` | `/bracket/{id}/pick` | Undo a pick, clears downstream |
| `POST` | `/bracket/reset` | Wipe all picks |
| `GET` | `/champion-likelihood` | All 68 teams scored against champion patterns |

---

## Prediction Model

| Signal | Weight | What it measures |
|--------|--------|-----------------|
| SRS (efficiency) | **30%** | Overall team quality adjusted for opponent |
| SOS (schedule strength) | **25%** | How hard was their regular season |
| Momentum | **15%** | Last 10 games W/L + margin of victory trend |
| Seed history | **10%** | 10-year historical win rate for this seed matchup |
| Travel advantage | **10%** | Geographic proximity to game venue |
| Injuries | **10%** | Roster health — key players out reduce team's score |

Commentary, community data, and champion likelihood are **display only** — they do not affect win probabilities.

---

## Data Sources

| Source | Purpose |
|--------|---------|
| Sports-Reference CBB | Season stats (SRS, SOS, record) |
| ESPN Schedule API | Momentum — last 10 games, streaks, margins |
| ESPN Injuries API | Health scores, players out |
| ESPN Team Summary API | Expert headlines + sentiment |
| Google News RSS | Recent headlines (4 per team) |
| Reddit r/collegebasketball | Top community posts (last 30 days) |
| Bart Torvik | AdjOE/AdjDE/AdjEM efficiency ranks |
| ESPN Rankings API | AP Poll Top 25 |
| OpenStreetMap / Nominatim | Campus geocoding for travel distances |
| NCAA Selection Sunday 2026 | Official 68-team bracket and seedings |

---

## Running the Data Pipeline

```bash
cd backend && source venv/bin/activate

# Full pipeline (fetches all data and merges)
python pipeline/run_pipeline.py

# Individual steps
python pipeline/momentum_ingest.py     # Last-10 games from ESPN
python pipeline/injury_ingest.py       # ESPN injury reports
python pipeline/commentary_ingest.py   # ESPN headlines
python -m pipeline.community_ingest    # Google News + Reddit
python pipeline/champion_ingest.py     # Torvik + AP Poll
python pipeline/tournament_filter.py   # Merge into final CSV
```

Re-run before each round to refresh momentum, injuries, and commentary. Restart the backend after re-running — uvicorn caches team data in memory.
