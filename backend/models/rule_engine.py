"""
Rule-based prediction engine.

For any two tournament teams, produces a win probability (0–1) for Team A
by combining four signals with explicit weights.

Weights (intentionally de-prioritizing seed history):
    SRS delta         40%  — best single predictor of team quality
    SOS               30%  — adjusts for strength of competition faced
    Seed history      15%  — historical matchup rates, down-weighted to
                             allow strong/weak seeds to show through
    Travel advantage  15%  — geographic proximity to venue

All signals are converted to a [0, 1] win probability before weighting,
then combined into a final probability and confidence label.

Weights are defined in WEIGHTS dict — easy to adjust in future iterations.
"""

import math
import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

# ---------------------------------------------------------------------------
# Weights — must sum to 1.0
# ---------------------------------------------------------------------------
WEIGHTS = {
    "srs":      0.40,   # Efficiency/quality delta
    "sos":      0.30,   # Strength of schedule delta
    "seed":     0.15,   # Historical seed matchup win rate
    "travel":   0.15,   # Geographic proximity advantage
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

# Sigmoid steepness for SRS and SOS conversions.
# At k=0.12, a 10-point SRS gap → ~75% win prob. At 20 points → ~91%.
SRS_K = 0.12
# SOS ranges tighter than SRS, so steeper curve needed.
# At k=0.18, a 10-point SOS gap → ~83% win prob.
SOS_K = 0.18


# ---------------------------------------------------------------------------
# Data loaders (cached at module level after first call)
# ---------------------------------------------------------------------------
_tournament_teams = None
_seed_history = None


def _load_teams() -> pd.DataFrame:
    global _tournament_teams
    if _tournament_teams is None:
        _tournament_teams = pd.read_csv(PROCESSED_DIR / "tournament_teams_2026.csv")
    return _tournament_teams


def _load_seed_history() -> pd.DataFrame:
    global _seed_history
    if _seed_history is None:
        _seed_history = pd.read_csv(PROCESSED_DIR / "seed_matchup_history.csv")
    return _seed_history


def get_team(name: str) -> pd.Series:
    teams = _load_teams()
    row = teams[teams["Team"] == name]
    if row.empty:
        raise ValueError(f"Team not found: '{name}'. Check tournament_teams_2026.csv.")
    return row.iloc[0]


# ---------------------------------------------------------------------------
# Individual signal → win probability converters
# ---------------------------------------------------------------------------

def _sigmoid(x: float, k: float) -> float:
    """Standard sigmoid. x > 0 means Team A is better → prob > 0.5."""
    return 1.0 / (1.0 + math.exp(-k * x))


def srs_prob(team_a: pd.Series, team_b: pd.Series) -> float:
    """Win probability based on SRS (Simple Rating System) difference."""
    a, b = team_a.get("SRS"), team_b.get("SRS")
    if pd.isna(a) or pd.isna(b):
        return 0.5
    return _sigmoid(float(a) - float(b), SRS_K)


def sos_prob(team_a: pd.Series, team_b: pd.Series) -> float:
    """
    Win probability based on Strength of Schedule difference.
    A team that dominated a harder schedule is more credible.
    """
    a, b = team_a.get("SOS"), team_b.get("SOS")
    if pd.isna(a) or pd.isna(b):
        return 0.5
    return _sigmoid(float(a) - float(b), SOS_K)


def seed_prob(team_a: pd.Series, team_b: pd.Series) -> float:
    """
    Historical win rate for this seed matchup (10-year window, 2015–2024).
    Returns Team A's historical win probability vs Team B's seed.
    Falls back to 0.5 if the matchup pair isn't in history.
    """
    seed_a = int(team_a["Seed"])
    seed_b = int(team_b["Seed"])

    if seed_a == seed_b:
        return 0.5

    history = _load_seed_history()
    fav_seed = min(seed_a, seed_b)
    und_seed = max(seed_a, seed_b)
    row = history[(history["FavSeed"] == fav_seed) & (history["UndSeed"] == und_seed)]

    if row.empty:
        return 0.5

    fav_win_rate = float(row["FavWinRate"].iloc[0])
    return fav_win_rate if seed_a < seed_b else (1.0 - fav_win_rate)


def travel_prob(team_a: pd.Series, team_b: pd.Series) -> float:
    """
    Win probability based on relative geographic proximity to the venue.
    Uses BestAdvantageScore (0–1 exponential decay by distance).
    Falls back to 0.5 if either team has no location data.
    """
    a = team_a.get("BestAdvantageScore")
    b = team_b.get("BestAdvantageScore")

    if pd.isna(a) or pd.isna(b):
        return 0.5

    a, b = float(a), float(b)
    total = a + b
    if total == 0:
        return 0.5
    return a / total


# ---------------------------------------------------------------------------
# Core prediction function
# ---------------------------------------------------------------------------

def predict(team_a_name: str, team_b_name: str) -> dict:
    """
    Calculate win probabilities for both teams in a matchup.
    Does NOT pick a winner — that's the user's job.

    Returns a dict with:
        team_a / team_b     — team names
        pct_a / pct_b       — rounded display percentages summing to 100
        prob_a / prob_b     — raw probabilities (0–1) summing to 1.0
        confidence          — how decisive the gap is: Toss-Up / Slight Edge / Clear Favorite / Heavy Favorite
        signals             — per-signal probability for Team A (1 - signal = Team B)
        weights             — the weights used
    """
    a = get_team(team_a_name)
    b = get_team(team_b_name)

    signals = {
        "srs":    srs_prob(a, b),
        "sos":    sos_prob(a, b),
        "seed":   seed_prob(a, b),
        "travel": travel_prob(a, b),
    }

    prob_a = sum(WEIGHTS[k] * v for k, v in signals.items())
    prob_b = 1.0 - prob_a

    # Round to whole percentages that sum to 100
    pct_a = round(prob_a * 100)
    pct_b = 100 - pct_a

    # Confidence label based on the larger of the two probabilities
    edge = max(prob_a, prob_b)
    if edge >= 0.80:
        label = "Heavy Favorite"
    elif edge >= 0.65:
        label = "Clear Favorite"
    elif edge >= 0.55:
        label = "Slight Edge"
    else:
        label = "Toss-Up"

    return {
        "team_a":     team_a_name,
        "team_b":     team_b_name,
        "prob_a":     round(prob_a, 4),
        "prob_b":     round(prob_b, 4),
        "pct_a":      pct_a,
        "pct_b":      pct_b,
        "confidence": label,
        "signals":    {k: round(v, 4) for k, v in signals.items()},
        "weights":    WEIGHTS,
    }


def predict_matchup_display(team_a: str, team_b: str) -> None:
    """Pretty-print a single matchup prediction."""
    r = predict(team_a, team_b)
    a_data = get_team(team_a)
    b_data = get_team(team_b)

    print(f"\n{'─'*52}")
    print(f"  ({int(a_data['Seed'])}) {team_a}  vs  ({int(b_data['Seed'])}) {team_b}")
    print(f"{'─'*52}")
    print(f"  Predicted winner : {r['winner']}")
    print(f"  Confidence       : {r['confidence_pct']}%  [{r['confidence']}]")
    print(f"\n  Signal breakdown (Team A = {team_a}):")
    for signal, prob in r["signals"].items():
        weight = WEIGHTS[signal]
        contribution = round(prob * weight * 100, 1)
        print(f"    {signal:8s}  prob={prob:.3f}  weight={int(weight*100)}%  → {contribution:4.1f}pts")
    print(f"\n  Raw win prob for {team_a}: {r['win_probability']:.1%}")


# ---------------------------------------------------------------------------
# Run all first-round matchups
# ---------------------------------------------------------------------------

def predict_first_round() -> pd.DataFrame:
    """
    Predict every first-round matchup using the bracket in tournament_teams_2026.csv.
    Excludes First Four teams (they haven't played yet).
    """
    teams = _load_teams()
    first_round = teams[~teams["IsFirstFour"]].copy()

    results = []
    seen = set()

    for _, row in first_round.iterrows():
        team_a = row["Team"]
        team_b = row["FirstRoundOpponent"]

        # Skip if opponent is also a First Four team or already processed
        pair = tuple(sorted([team_a, team_b]))
        if pair in seen:
            continue

        # Skip if opponent isn't in the dataset (First Four placeholder)
        opp_rows = teams[teams["Team"] == team_b]
        if opp_rows.empty:
            continue

        seen.add(pair)

        try:
            r = predict(team_a, team_b)
            a_data = get_team(team_a)
            b_data = get_team(team_b)
            results.append({
                "Region":         a_data["Region"],
                "SeedA":          int(a_data["Seed"]),
                "TeamA":          team_a,
                "SeedB":          int(b_data["Seed"]),
                "TeamB":          team_b,
                "PredictedWinner": r["winner"],
                "Confidence_pct":  r["confidence_pct"],
                "Confidence":      r["confidence"],
                "WinProb_A":       r["win_probability"],
                "Signal_SRS":      r["signals"]["srs"],
                "Signal_SOS":      r["signals"]["sos"],
                "Signal_Seed":     r["signals"]["seed"],
                "Signal_Travel":   r["signals"]["travel"],
            })
        except Exception as e:
            print(f"  Skipped {team_a} vs {team_b}: {e}")

    df = pd.DataFrame(results).sort_values(["Region", "SeedA"]).reset_index(drop=True)
    return df


if __name__ == "__main__":
    print("=" * 52)
    print("  2026 NCAA Tournament — First Round Predictions")
    print("  Weights: SRS=40%  SOS=30%  Seed=15%  Travel=15%")
    print("=" * 52)

    # Show a few highlighted matchups with full signal breakdown
    highlights = [
        ("Duke",     "Siena"),
        ("Michigan", "UMBC"),
        ("Gonzaga",  "Kennesaw State"),
        ("Iowa State", "Tennessee State"),
        ("Houston",  "Idaho"),
        ("Wisconsin", "High Point"),    # potential upset candidate
        ("Missouri",  "Saint Mary's (CA)"),  # close matchup
    ]
    for a, b in highlights:
        try:
            predict_matchup_display(a, b)
        except Exception as e:
            print(f"  Skipped {a} vs {b}: {e}")

    # Full first-round table
    print("\n\n" + "=" * 52)
    print("  Full First Round")
    print("=" * 52)
    df = predict_first_round()
    for region, grp in df.groupby("Region"):
        print(f"\n── {region.upper()} ──")
        for _, row in grp.iterrows():
            marker = "⚡" if row["SeedB"] < row["SeedA"] + 4 and row["PredictedWinner"] == row["TeamB"] else " "
            print(
                f"  {marker}({row['SeedA']:2d}) {row['TeamA']:22s} vs "
                f"({row['SeedB']:2d}) {row['TeamB']:22s} "
                f"→  {row['PredictedWinner']:22s}  {row['Confidence_pct']:4.1f}%  [{row['Confidence']}]"
            )

    # Save
    out = PROCESSED_DIR / "first_round_predictions_2026.csv"
    df.to_csv(out, index=False)
    print(f"\nSaved predictions → {out}")
