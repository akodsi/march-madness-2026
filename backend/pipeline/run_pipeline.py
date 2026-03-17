"""
Master pipeline runner.

Usage:
    python pipeline/run_pipeline.py

Steps:
    1. Fetch current season team stats from Sports-Reference
    2. Build seed matchup history from Kaggle historical data (if available)
    3. Normalize and build team profiles
    4. Geocode team campuses and compute travel distances to tournament venues
    5. Print a summary of what's ready

Kaggle data is optional for step 2 — the prediction engine will fall back to
seed-based historical averages compiled from public data if Kaggle CSVs are absent.
"""

from pathlib import Path
import sys

# Allow running from the backend/ directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stats_ingest import build_team_stats, save_processed
from pipeline.normalize import build_team_profiles, build_matchup_dataset
from pipeline.geo_ingest import geocode_teams, add_2026_venues, compute_travel_distances
from pipeline.momentum_ingest import fetch_all_momentum, save_momentum
from pipeline.injury_ingest import fetch_all_injuries, save_injuries
from pipeline.commentary_ingest import fetch_all_commentary, save_commentary
from pipeline.community_ingest import fetch_all_community, save_community
from pipeline.tournament_filter import filter_to_tournament, save_tournament_dataset

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURRENT_YEAR = 2026


def run():
    print("=" * 60)
    print("  March Madness Data Pipeline")
    print("=" * 60)

    # Step 1: Current season stats
    print("\n[1/6] Fetching current season stats...")
    stats = build_team_stats(CURRENT_YEAR)
    save_processed(stats, f"team_stats_{CURRENT_YEAR}.csv")

    # Step 2: Historical seed matchup data (requires Kaggle CSVs)
    print("\n[2/6] Building seed matchup history...")
    kaggle_dir = Path(__file__).parent.parent / "data" / "raw" / "kaggle"
    seed_file = kaggle_dir / "MNCAATourneySeeds.csv"

    if seed_file.exists():
        from pipeline.kaggle_ingest import build_seed_matchup_history, save_processed as ksp
        matchup_history = build_seed_matchup_history()
        ksp(matchup_history, "seed_matchup_history.csv")
    else:
        print(f"  Kaggle data not found at {kaggle_dir}")
        print("  → Using built-in seed matchup averages (see normalize.py)")
        _write_builtin_seed_history()

    # Step 3: Build team profiles
    print("\n[3/6] Building team profiles...")
    profiles = build_team_profiles(CURRENT_YEAR)
    save_processed(profiles, f"team_profiles_{CURRENT_YEAR}.csv")

    # Step 4: Geographic data — campus locations + travel distances to venues
    print("\n[4/6] Computing geographic travel distances...")
    import pandas as pd
    teams = pd.read_csv(PROCESSED_DIR / f"team_stats_{CURRENT_YEAR}.csv")["Team"].tolist()
    coords = geocode_teams(teams)
    venues = add_2026_venues()
    distances = compute_travel_distances(coords, venues)
    distances.to_csv(PROCESSED_DIR / f"travel_distances_{CURRENT_YEAR}.csv", index=False)
    print(f"  Saved travel_distances_{CURRENT_YEAR}.csv  ({len(distances)} rows)")

    # Step 5: Momentum data — last 10 games, streaks, margin trends
    print("\n[5/7] Fetching momentum data (last 10 games)...")
    from pipeline.tournament_filter import build_tournament_teams
    tournament_teams = build_tournament_teams()["Team"].tolist()
    momentum = fetch_all_momentum(tournament_teams, delay=0.5)
    save_momentum(momentum, CURRENT_YEAR)

    # Step 6: Injuries + Commentary
    print("\n[6/8] Fetching injuries and expert commentary...")
    injury_df, injury_details = fetch_all_injuries(tournament_teams, delay=0.5)
    save_injuries(injury_df, injury_details, CURRENT_YEAR)

    commentary = fetch_all_commentary(tournament_teams, delay=0.5)
    save_commentary(commentary, CURRENT_YEAR)

    # Step 7: Community data — Google News RSS + Reddit r/collegebasketball
    print("\n[7/8] Fetching community data (Google News + Reddit)...")
    community = fetch_all_community(tournament_teams, delay=1.5)
    save_community(community, CURRENT_YEAR)

    # Final merge — rebuild tournament_teams CSV with all new data columns
    print("\n[8/8] Merging all data into tournament_teams CSV...")
    merged = filter_to_tournament(CURRENT_YEAR)
    save_tournament_dataset(merged)

    print("\n" + "=" * 60)
    print("  Pipeline complete. Files in data/processed/:")
    for f in sorted(PROCESSED_DIR.glob("*.csv")):
        rows = sum(1 for _ in open(f)) - 1
        print(f"    {f.name:45s}  {rows} rows")
    for f in sorted(PROCESSED_DIR.glob("*.json")):
        print(f"    {f.name:45s}  (JSON)")
    print("=" * 60)


def _write_builtin_seed_history():
    """
    Hardcoded historical seed matchup win rates (2015–2024, ~603 games, 9 tournaments).
    2020 excluded (tournament cancelled due to COVID-19).
    Source: aggregated from public tournament records.

    Using a 10-year window instead of 40-year window because:
    - Modern basketball (3-point era, pace, analytics) plays differently than 1985–2005
    - 10-year rates reflect current team-building and scouting tendencies
    - Faster decision signal with less noise from outdated eras
    - Still large enough sample for first-round matchups (~36 games per seed pairing)
    """
    import pandas as pd

    # Format: FavSeed, UndSeed, FavWinRate  (FavSeed = lower number = higher seed)
    # Notable recent upsets baked in: UMBC over Virginia (2018), FDU over Purdue (2023),
    # Saint Peter's run (2022), Oral Roberts (2021), Princeton over Arizona (2023)
    records = [
        (1, 16, 0.944), (2, 15, 0.917), (3, 14, 0.861), (4, 13, 0.778),
        (5, 12, 0.611), (6, 11, 0.611), (7, 10, 0.556), (8,  9, 0.500),
        (1,  8, 0.830), (1,  9, 0.830), (2,  7, 0.750), (2, 10, 0.710),
        (3,  6, 0.700), (3, 11, 0.620), (4,  5, 0.560), (1,  4, 0.760),
        (1,  5, 0.780), (2,  3, 0.600), (1,  2, 0.550), (1,  3, 0.680),
    ]
    df = pd.DataFrame(records, columns=["FavSeed", "UndSeed", "FavWinRate"])
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DIR / "seed_matchup_history.csv", index=False)
    print(f"  Wrote built-in seed history ({len(df)} matchup pairs)")


if __name__ == "__main__":
    run()
