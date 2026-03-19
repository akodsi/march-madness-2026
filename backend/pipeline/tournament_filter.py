"""
Filters all pipeline data down to only the 68 confirmed 2026 NCAA Tournament teams.
Adds seed, region, and first-round matchup info to each team's profile.

Bracket source: NCAA Selection Sunday, March 15 2026.
First Four games: March 17-18 in Dayton, OH.
First Round:      March 19-20.
"""

import pandas as pd
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CURRENT_YEAR = 2026

# ---------------------------------------------------------------------------
# Full 2026 bracket — all 68 teams
# Format: (Region, Seed, Team, FirstRoundOpponent, IsFirstFour)
#
# First Four teams are listed as individual entries.
# Their bracket slot opponent is the winner of the matching First Four game.
# ---------------------------------------------------------------------------
BRACKET_2026 = [
    # ── EAST REGION (No. 1 overall seed: Duke) ──────────────────────────────
    ("East",  1, "Duke",                "Siena",              False),
    ("East", 16, "Siena",              "Duke",                False),
    ("East",  2, "Connecticut",        "Furman",              False),
    ("East", 15, "Furman",             "Connecticut",         False),
    ("East",  3, "Michigan State",     "North Dakota State",  False),
    ("East", 14, "North Dakota State", "Michigan State",      False),
    ("East",  4, "Kansas",             "California Baptist",  False),
    ("East", 13, "California Baptist", "Kansas",              False),
    ("East",  5, "St. John's (NY)",    "Northern Iowa",       False),
    ("East", 12, "Northern Iowa",      "St. John's (NY)",     False),
    ("East",  6, "Louisville",         "South Florida",       False),
    ("East", 11, "South Florida",      "Louisville",          False),
    ("East",  7, "UCLA",               "UCF",                 False),
    ("East", 10, "UCF",                "UCLA",                False),
    ("East",  8, "Ohio State",         "TCU",                 False),
    ("East",  9, "TCU",                "Ohio State",          False),

    # ── WEST REGION (No. 1 seed: Arizona) ────────────────────────────────────
    ("West",  1, "Arizona",            "LIU",                 False),
    ("West", 16, "LIU",                "Arizona",             False),
    ("West",  2, "Purdue",             "Queens (NC)",         False),
    ("West", 15, "Queens (NC)",        "Purdue",              False),
    ("West",  3, "Gonzaga",            "Kennesaw State",      False),
    ("West", 14, "Kennesaw State",     "Gonzaga",             False),
    ("West",  4, "Arkansas",           "Hawaii",             False),
    ("West", 13, "Hawaii",            "Arkansas",            False),
    ("West",  5, "Wisconsin",          "High Point",          False),
    ("West", 12, "High Point",         "Wisconsin",           False),
    ("West",  6, "BYU",                "Texas",               False),  # Texas won First Four
    ("West", 11, "Texas",              "BYU",                 False),  # First Four winner
    ("West", 11, "NC State",           "Texas",               True),   # First Four loser
    ("West",  7, "Saint Mary's (CA)",  "Texas A&M",           False),
    ("West", 10, "Texas A&M",          "Saint Mary's (CA)",   False),
    ("West",  8, "Villanova",          "Utah State",          False),
    ("West",  9, "Utah State",         "Villanova",           False),

    # ── MIDWEST REGION (No. 1 seed: Michigan) ────────────────────────────────
    ("Midwest",  1, "Michigan",         "UMBC",               False),  # UMBC won First Four
    ("Midwest", 16, "UMBC",             "Michigan",           False),  # First Four winner
    ("Midwest", 16, "Howard",           "UMBC",               True),   # First Four loser
    ("Midwest",  2, "Iowa State",       "Tennessee State",    False),
    ("Midwest", 15, "Tennessee State",  "Iowa State",         False),
    ("Midwest",  3, "Virginia",         "Wright State",       False),
    ("Midwest", 14, "Wright State",     "Virginia",           False),
    ("Midwest",  4, "Alabama",          "Hofstra",            False),
    ("Midwest", 13, "Hofstra",          "Alabama",            False),
    ("Midwest",  5, "Texas Tech",       "Akron",              False),
    ("Midwest", 12, "Akron",            "Texas Tech",         False),
    ("Midwest",  6, "Tennessee",        "Miami (OH)",         False),  # Miami OH won First Four
    ("Midwest", 11, "Miami (OH)",       "Tennessee",          False),  # First Four winner
    ("Midwest", 11, "SMU",              "Miami (OH)",         True),   # First Four loser
    ("Midwest",  7, "Kentucky",         "Santa Clara",        False),
    ("Midwest", 10, "Santa Clara",      "Kentucky",           False),
    ("Midwest",  8, "Georgia",          "Saint Louis",        False),
    ("Midwest",  9, "Saint Louis",      "Georgia",            False),

    # ── SOUTH REGION (No. 1 seed: Florida) ───────────────────────────────────
    ("South",  1, "Florida",           "Prairie View",        False),  # Prairie View won First Four
    ("South", 16, "Prairie View",      "Florida",             False),  # First Four winner
    ("South", 16, "Lehigh",            "Prairie View",        True),   # First Four loser
    ("South",  2, "Houston",           "Idaho",               False),
    ("South", 15, "Idaho",             "Houston",             False),
    ("South",  3, "Illinois",          "Penn",                False),
    ("South", 14, "Penn",              "Illinois",            False),
    ("South",  4, "Nebraska",          "Troy",                False),
    ("South", 13, "Troy",              "Nebraska",            False),
    ("South",  5, "Vanderbilt",        "McNeese",             False),
    ("South", 12, "McNeese",           "Vanderbilt",          False),
    ("South",  6, "North Carolina",    "VCU",                 False),
    ("South", 11, "VCU",               "North Carolina",      False),
    ("South",  7, "Miami (FL)",        "Missouri",            False),
    ("South", 10, "Missouri",          "Miami (FL)",          False),
    ("South",  8, "Clemson",           "Iowa",                False),
    ("South",  9, "Iowa",              "Clemson",             False),
]

# Sports-Reference team name → bracket team name (for matching)
TEAM_NAME_ALIASES = {
    "Connecticut":        "Connecticut",
    "St. John's (NY)":    "St. John's (NY)",
    "Northern Iowa":      "Northern Iowa",
    "California Baptist": "California Baptist",
    "Ohio State":         "Ohio State",
    "North Dakota State": "North Dakota State",
    "UCF":                "UCF",
    "South Florida":      "South Florida",
    "LIU":                "LIU",
    "Kennesaw State":     "Kennesaw State",
    "Utah State":         "Utah State",
    "High Point":         "High Point",
    "Saint Mary's (CA)":  "Saint Mary's (CA)",
    "Wright State":       "Wright State",
    "Tennessee State":    "Tennessee State",
    "Santa Clara":        "Santa Clara",
    "Saint Louis":        "Saint Louis",
    "Prairie View":       "Prairie View",
    "Queens (NC)":        "Queens (NC)",
    "Miami (OH)":         "Miami (OH)",
    "Miami (FL)":         "Miami (FL)",
    "Texas A&M":          "Texas A&M",
}


# Sports-Reference uses different names for some programs
SPORTSREF_NAME_MAP = {
    "BYU":              "Brigham Young",
    "TCU":              "Texas Christian",
    "SMU":              "Southern Methodist",
    "Penn":             "Pennsylvania",
    "LIU":              "Long Island University",
    "UMBC":             "Maryland-Baltimore County",
    "Prairie View":     "Prairie View A&M",
    "VCU":              "Virginia Commonwealth",
    "Saint Mary's (CA)": "Saint Mary's",
}


def build_tournament_teams() -> pd.DataFrame:
    """
    Returns a DataFrame of all 68 tournament teams with seed, region,
    first-round opponent, and First Four flag.
    """
    df = pd.DataFrame(BRACKET_2026, columns=[
        "Region", "Seed", "Team", "FirstRoundOpponent", "IsFirstFour"
    ])
    return df


def filter_to_tournament(year: int = CURRENT_YEAR) -> pd.DataFrame:
    """
    Merge tournament bracket info with full team stats, travel distances,
    momentum data, and injury reports — returning only the 68 tournament teams.
    """
    bracket = build_tournament_teams()
    stats = pd.read_csv(PROCESSED_DIR / f"team_stats_{year}.csv")

    # Normalize stats team names to match bracket names
    reverse_map = {v: k for k, v in SPORTSREF_NAME_MAP.items()}
    stats["Team"] = stats["Team"].replace(reverse_map)

    # Merge on Team name — use bracket as the left table to preserve all 68
    merged = bracket.merge(stats, on="Team", how="left")

    # Pull in travel distances for the teams' likely venues by region
    dist_path = PROCESSED_DIR / f"travel_distances_{year}.csv"
    if dist_path.exists():
        distances = pd.read_csv(dist_path)
        # Keep only First/Second Round distances (most relevant for early games)
        fr = distances[distances["Round"] == "First/Second"].copy()
        # For each team, find the row with minimum distance
        idx_min = fr.groupby("Team")["DistanceMiles"].idxmin()
        nearest = fr.loc[idx_min, ["Team", "DistanceMiles", "AdvantageScore", "City"]].rename(columns={
            "DistanceMiles": "NearestVenueMiles",
            "AdvantageScore": "BestAdvantageScore",
            "City": "NearestVenueCity",
        })
        first_round_dist = nearest.reset_index(drop=True)
        merged = merged.merge(first_round_dist, on="Team", how="left")

    # Pull in momentum data (last 10 games, streaks)
    momentum_path = PROCESSED_DIR / f"momentum_{year}.csv"
    if momentum_path.exists():
        momentum = pd.read_csv(momentum_path)
        merged = merged.merge(momentum, on="Team", how="left")

    # Pull in injury / health score data
    injury_path = PROCESSED_DIR / f"injuries_{year}.csv"
    if injury_path.exists():
        injuries = pd.read_csv(injury_path)
        merged = merged.merge(injuries, on="Team", how="left")

    return merged.sort_values(["Region", "Seed"]).reset_index(drop=True)


def save_tournament_dataset(df: pd.DataFrame):
    path = PROCESSED_DIR / f"tournament_teams_{CURRENT_YEAR}.csv"
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} tournament teams → {path}")


if __name__ == "__main__":
    print("Building 2026 tournament team dataset...\n")
    df = filter_to_tournament(CURRENT_YEAR)
    save_tournament_dataset(df)

    # Summary by region
    for region in ["East", "West", "Midwest", "South"]:
        r = df[df["Region"] == region][["Seed", "Team", "Wins", "Losses", "SRS", "BestAdvantageScore", "IsFirstFour"]]
        print(f"\n── {region.upper()} ──")
        print(r.to_string(index=False))

    print(f"\nTotal teams: {len(df)}")
    print(f"First Four teams: {df['IsFirstFour'].sum()}")
    print(f"Teams with stats data: {df['Wins'].notna().sum()}")
    print(f"Teams with travel data: {df['BestAdvantageScore'].notna().sum()}")
