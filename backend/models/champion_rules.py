"""
Champion-likelihood scoring engine.

Evaluates each tournament team against historically-validated champion patterns
using Bart Torvik efficiency data (KenPom substitute) and AP Poll rankings.

Two types of rules:
- **Hard filters**: near-universal requirements. Failing = team is flagged as
  extremely unlikely to win it all. (100% or near-100% historical accuracy)
- **Soft scores**: point-based boosts for traits shared by most champions.
  Accumulate into a champion_likelihood_score for ranking.

Each rule is returned as a named check with pass/fail status so the frontend
can display checkmarks and Xs on individual criteria.

Historical basis: 25+ years of tournament data (2001–2025, excl. 2020 COVID).
Torvik AdjOE/AdjDE/AdjEM ranks are used as direct substitutes for KenPom —
the two systems are highly correlated (r > 0.95 for efficiency metrics).

NOTE: UConn is the known exception to many "top 6" rules. They won in 2011
and 2014 ranked ~#19 in polls but were KenPom/Torvik top-25. Teams with
elite defense + middling polls deserve extra scrutiny, not elimination.

NOTE: The "no West Coast winner since 1997" rule is a fun coincidence,
not a causal factor. Flagged as a warning, never a hard filter.
"""

import json
from pathlib import Path
from typing import Optional

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

# ---------------------------------------------------------------------------
# Champion pattern constants — easy to tune
# ---------------------------------------------------------------------------
CHAMPION_RULES = {
    # Torvik/KenPom overall efficiency rank
    "torvik_overall_rank_max": 25,       # All champions since 2001 were top 25
    "torvik_overall_rank_elite": 6,      # 19 of last 22 champions were top 6

    # Torvik/KenPom adjusted defense rank
    "torvik_adjD_rank_max": 25,          # ~100% since 2002
    "torvik_adjD_rank_elite": 7,         # 12 of last 13 champions

    # Torvik/KenPom adjusted offense rank
    "torvik_adjO_rank_max": 40,          # ~100% since 2002
    "torvik_adjO_rank_strict": 21,       # 23 of last 24 champions

    # AP Poll
    "ap_final_week_rank_max": 12,        # Only exception: 2003 Syracuse
    "ap_final_week_rank_elite": 6,       # 9 of last 10 champions

    # Tournament seed
    "seed_max": 8,                       # Lowest seed to ever win (Villanova 1985)
    "seed_practical_max": 3,             # All recent winners are 1, 2, or 3 seeds
}

# West Coast conferences — for fun-coincidence warning
WEST_COAST_CONFERENCES = {"Pac-12", "WCC", "Big West", "Mountain West", "WAC"}


# ---------------------------------------------------------------------------
# Champion data loader (cached at module level)
# ---------------------------------------------------------------------------
_champion_data: Optional[dict] = None


def _load_champion_data() -> dict:
    global _champion_data
    if _champion_data is None:
        path = PROCESSED_DIR / "champion_data_2026.json"
        if path.exists():
            with open(path) as f:
                _champion_data = json.load(f)
        else:
            _champion_data = {}
    return _champion_data


# ---------------------------------------------------------------------------
# Individual rule checks
# Each returns a dict with:
#   rule_id, label, passed (bool), value, threshold, detail, points, is_hard
# ---------------------------------------------------------------------------

def _check_torvik_overall(rank: Optional[int]) -> list[dict]:
    """Check Torvik overall efficiency rank against champion thresholds."""
    checks = []
    if rank is None:
        checks.append({
            "rule_id": "torvik_overall_top25",
            "label": "Torvik Top 25 Overall",
            "passed": None,
            "value": None,
            "threshold": CHAMPION_RULES["torvik_overall_rank_max"],
            "detail": "No Torvik data available",
            "points": 0,
            "is_hard": True,
        })
        return checks

    # Hard filter: must be top 25
    passed_25 = rank <= CHAMPION_RULES["torvik_overall_rank_max"]
    checks.append({
        "rule_id": "torvik_overall_top25",
        "label": "Torvik Top 25 Overall",
        "passed": passed_25,
        "value": rank,
        "threshold": CHAMPION_RULES["torvik_overall_rank_max"],
        "detail": f"Rank #{rank} — all champions since 2001 were top 25" if passed_25
                  else f"Rank #{rank} — no champion has been ranked this low since 2001",
        "points": 15 if passed_25 else 0,
        "is_hard": True,
    })

    # Soft: elite tier (top 6)
    if passed_25:
        passed_6 = rank <= CHAMPION_RULES["torvik_overall_rank_elite"]
        checks.append({
            "rule_id": "torvik_overall_top6",
            "label": "Torvik Top 6 Overall",
            "passed": passed_6,
            "value": rank,
            "threshold": CHAMPION_RULES["torvik_overall_rank_elite"],
            "detail": f"Rank #{rank} — 19 of last 22 champions were top 6" if passed_6
                      else f"Rank #{rank} — outside elite tier (top 6)",
            "points": 15 if passed_6 else 0,  # additional 15 on top of the 15 above
            "is_hard": False,
        })

    return checks


def _check_torvik_defense(rank: Optional[int]) -> list[dict]:
    """Check Torvik adjusted defensive efficiency rank."""
    checks = []
    if rank is None:
        checks.append({
            "rule_id": "torvik_adjD_top25",
            "label": "Torvik Top 25 Defense",
            "passed": None,
            "value": None,
            "threshold": CHAMPION_RULES["torvik_adjD_rank_max"],
            "detail": "No Torvik data available",
            "points": 0,
            "is_hard": True,
        })
        return checks

    # Hard filter: top 25 defense
    passed_25 = rank <= CHAMPION_RULES["torvik_adjD_rank_max"]
    checks.append({
        "rule_id": "torvik_adjD_top25",
        "label": "Torvik Top 25 Defense",
        "passed": passed_25,
        "value": rank,
        "threshold": CHAMPION_RULES["torvik_adjD_rank_max"],
        "detail": f"Rank #{rank} — ~100% of champions since 2002 were top 25 defense" if passed_25
                  else f"Rank #{rank} — no champion has had defense ranked this low",
        "points": 15 if passed_25 else 0,
        "is_hard": True,
    })

    # Soft: elite defense (top 7)
    if passed_25:
        passed_7 = rank <= CHAMPION_RULES["torvik_adjD_rank_elite"]
        checks.append({
            "rule_id": "torvik_adjD_top7",
            "label": "Torvik Top 7 Defense",
            "passed": passed_7,
            "value": rank,
            "threshold": CHAMPION_RULES["torvik_adjD_rank_elite"],
            "detail": f"Rank #{rank} — 12 of last 13 champions had top 7 defense" if passed_7
                      else f"Rank #{rank} — outside elite defense tier (top 7)",
            "points": 10 if passed_7 else 0,
            "is_hard": False,
        })

    return checks


def _check_torvik_offense(rank: Optional[int]) -> list[dict]:
    """Check Torvik adjusted offensive efficiency rank."""
    checks = []
    if rank is None:
        checks.append({
            "rule_id": "torvik_adjO_top40",
            "label": "Torvik Top 40 Offense",
            "passed": None,
            "value": None,
            "threshold": CHAMPION_RULES["torvik_adjO_rank_max"],
            "detail": "No Torvik data available",
            "points": 0,
            "is_hard": True,
        })
        return checks

    # Hard filter: top 40 offense
    passed_40 = rank <= CHAMPION_RULES["torvik_adjO_rank_max"]
    checks.append({
        "rule_id": "torvik_adjO_top40",
        "label": "Torvik Top 40 Offense",
        "passed": passed_40,
        "value": rank,
        "threshold": CHAMPION_RULES["torvik_adjO_rank_max"],
        "detail": f"Rank #{rank} — ~100% of champions since 2002 were top 40 offense" if passed_40
                  else f"Rank #{rank} — no champion has had offense ranked this low",
        "points": 10 if passed_40 else 0,
        "is_hard": True,
    })

    # Soft: strict offense (top 21)
    if passed_40:
        passed_21 = rank <= CHAMPION_RULES["torvik_adjO_rank_strict"]
        checks.append({
            "rule_id": "torvik_adjO_top21",
            "label": "Torvik Top 21 Offense",
            "passed": passed_21,
            "value": rank,
            "threshold": CHAMPION_RULES["torvik_adjO_rank_strict"],
            "detail": f"Rank #{rank} — 23 of last 24 champions had top 21 offense" if passed_21
                      else f"Rank #{rank} — outside strict offense tier (top 21)",
            "points": 10 if passed_21 else 0,
            "is_hard": False,
        })

    return checks


def _check_ap_poll(ap_rank: Optional[int]) -> list[dict]:
    """Check AP Poll ranking against champion thresholds."""
    checks = []

    if ap_rank is None:
        checks.append({
            "rule_id": "ap_top12",
            "label": "AP Poll Top 12",
            "passed": False,
            "value": None,
            "threshold": CHAMPION_RULES["ap_final_week_rank_max"],
            "detail": "Unranked in AP Poll — only 2003 Syracuse won unranked (and they were #10)",
            "points": 0,
            "is_hard": False,  # soft — there are edge cases
        })
        return checks

    # Top 12
    passed_12 = ap_rank <= CHAMPION_RULES["ap_final_week_rank_max"]
    checks.append({
        "rule_id": "ap_top12",
        "label": "AP Poll Top 12",
        "passed": passed_12,
        "value": ap_rank,
        "threshold": CHAMPION_RULES["ap_final_week_rank_max"],
        "detail": f"AP #{ap_rank} — only 2003 Syracuse broke this rule" if passed_12
                  else f"AP #{ap_rank} — outside top 12, only 2003 Syracuse won from here",
        "points": 10 if passed_12 else 0,
        "is_hard": False,
    })

    # Elite: top 6
    if passed_12:
        passed_6 = ap_rank <= CHAMPION_RULES["ap_final_week_rank_elite"]
        checks.append({
            "rule_id": "ap_top6",
            "label": "AP Poll Top 6",
            "passed": passed_6,
            "value": ap_rank,
            "threshold": CHAMPION_RULES["ap_final_week_rank_elite"],
            "detail": f"AP #{ap_rank} — 9 of last 10 champions were top 6" if passed_6
                      else f"AP #{ap_rank} — outside elite AP tier (top 6)",
            "points": 10 if passed_6 else 0,
            "is_hard": False,
        })

    return checks


def _check_seed(seed: int) -> list[dict]:
    """Check tournament seed against champion thresholds."""
    checks = []

    # Hard filter: seed ≤ 8
    passed_8 = seed <= CHAMPION_RULES["seed_max"]
    checks.append({
        "rule_id": "seed_top8",
        "label": "Seed 8 or Better",
        "passed": passed_8,
        "value": seed,
        "threshold": CHAMPION_RULES["seed_max"],
        "detail": f"#{seed} seed — lowest champion ever was 8-seed (Villanova 1985)" if passed_8
                  else f"#{seed} seed — no team seeded this low has ever won the tournament",
        "points": 0,  # points come from the tiers below
        "is_hard": True,
    })

    # Soft: practical ≤ 3
    if passed_8:
        passed_3 = seed <= CHAMPION_RULES["seed_practical_max"]
        seed_points = {1: 20, 2: 12, 3: 8}.get(seed, 3)
        checks.append({
            "rule_id": "seed_top3",
            "label": "Seed 3 or Better",
            "passed": passed_3,
            "value": seed,
            "threshold": CHAMPION_RULES["seed_practical_max"],
            "detail": f"#{seed} seed — {'26 of 40 modern champions were 1-seeds' if seed == 1 else 'all recent winners were 1, 2, or 3 seeds'}" if passed_3
                      else f"#{seed} seed — rare for seeds 4+ to win it all",
            "points": seed_points,
            "is_hard": False,
        })

    return checks


# ---------------------------------------------------------------------------
# Main scoring function
# ---------------------------------------------------------------------------

def score_champion_likelihood(team_name: str, seed: int) -> dict:
    """
    Evaluate a single team against all champion-pattern rules.

    Args:
        team_name: bracket team name (must match champion_data keys)
        seed: tournament seed (1–16)

    Returns dict with:
        team, score, checks (list of individual rule results),
        hard_filter_failed (bool), reasons (list), warnings (list)
    """
    champ_data = _load_champion_data()
    team_data = champ_data.get(team_name, {})

    torvik_overall = team_data.get("torvik_overall_rank")
    torvik_adjO = team_data.get("torvik_adjO_rank")
    torvik_adjD = team_data.get("torvik_adjD_rank")
    ap_rank = team_data.get("ap_rank")

    # Run all checks
    checks = []
    checks.extend(_check_torvik_overall(torvik_overall))
    checks.extend(_check_torvik_defense(torvik_adjD))
    checks.extend(_check_torvik_offense(torvik_adjO))
    checks.extend(_check_ap_poll(ap_rank))
    checks.extend(_check_seed(seed))

    # Aggregate
    score = sum(c["points"] for c in checks)
    hard_filter_failed = any(c["is_hard"] and c["passed"] is False for c in checks)
    reasons = [c["detail"] for c in checks if c["passed"] is True]
    warnings = [c["detail"] for c in checks if c["passed"] is False]

    # Include raw Torvik values for frontend display
    raw_values = {
        "torvik_overall_rank": torvik_overall,
        "torvik_adjO_rank": torvik_adjO,
        "torvik_adjD_rank": torvik_adjD,
        "torvik_adjOE": team_data.get("torvik_adjOE"),
        "torvik_adjDE": team_data.get("torvik_adjDE"),
        "torvik_adjEM": team_data.get("torvik_adjEM"),
        "ap_rank": ap_rank,
    }

    return {
        "team": team_name,
        "score": score,
        "checks": checks,
        "hard_filter_failed": hard_filter_failed,
        "reasons": reasons,
        "warnings": warnings,
        "raw_values": raw_values,
    }


# ---------------------------------------------------------------------------
# Convenience: score all tournament teams
# ---------------------------------------------------------------------------

def score_all_teams() -> list[dict]:
    """Score all 68 tournament teams and return sorted by champion likelihood."""
    from models.rule_engine import _load_teams
    teams = _load_teams()

    results = []
    for _, row in teams.iterrows():
        name = row["Team"]
        seed = int(row["Seed"])
        result = score_champion_likelihood(name, seed)
        results.append(result)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


if __name__ == "__main__":
    results = score_all_teams()

    print("=" * 70)
    print("  CHAMPION LIKELIHOOD RANKINGS")
    print("=" * 70)

    for i, r in enumerate(results[:20], 1):
        status = "ELIMINATED" if r["hard_filter_failed"] else ""
        print(f"\n{i:2d}. {r['team']:25s}  Score: {r['score']:3d}  {status}")
        for c in r["checks"]:
            icon = "✅" if c["passed"] else ("❌" if c["passed"] is False else "—")
            print(f"    {icon} {c['label']:30s}  {c['detail']}")

    eliminated = [r for r in results if r["hard_filter_failed"]]
    if eliminated:
        print(f"\n{'─' * 70}")
        print(f"ELIMINATED BY HARD FILTERS: {len(eliminated)} teams")
        for r in eliminated:
            fails = [c["label"] for c in r["checks"] if c["is_hard"] and c["passed"] is False]
            print(f"  ❌ {r['team']:25s}  Failed: {', '.join(fails)}")
