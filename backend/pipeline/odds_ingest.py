"""
Vegas odds pipeline.

Fetches moneyline (h2h) and spread data from The Odds API (DraftKings primary)
for all NCAA tournament matchups.

Output: data/processed/odds_2026.json
Structure per matchup (keyed by "TeamA vs TeamB"):
{
    "team_a": "Duke",
    "team_b": "Siena",
    "moneyline_a": -2500,
    "moneyline_b": 1200,
    "spread_a": -18.5,
    "spread_b": 18.5,
    "implied_prob_a": 0.962,
    "implied_prob_b": 0.077,
    "source": "DraftKings",
    "last_updated": "2026-03-18T12:00:00Z"
}

Implied probabilities are calculated from American moneylines and may sum
to > 1.0 due to vig. A no-vig (normalized) pair is also provided.

This data is display-only — not part of the weighted prediction formula.
"""
from __future__ import annotations

import json
import os
import requests
from datetime import datetime
from pathlib import Path

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"

# The Odds API endpoint for NCAAB
ODDS_API_URL = (
    "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds/"
)

# ---------------------------------------------------------------------------
# Odds API team name → bracket team name mapping
# Only entries that differ need to be listed here.
# ---------------------------------------------------------------------------
ODDS_NAME_MAP = {
    "Duke Blue Devils":            "Duke",
    "UConn Huskies":               "Connecticut",
    "Michigan St Spartans":        "Michigan State",
    "Kansas Jayhawks":             "Kansas",
    "St. John's Red Storm":        "St. John's (NY)",
    "Louisville Cardinals":        "Louisville",
    "UCLA Bruins":                 "UCLA",
    "Ohio State Buckeyes":         "Ohio State",
    "TCU Horned Frogs":            "TCU",
    "UCF Knights":                 "UCF",
    "South Florida Bulls":         "South Florida",
    "Northern Iowa Panthers":      "Northern Iowa",
    "Cal Baptist Lancers":         "California Baptist",
    "North Dakota St Bison":       "North Dakota State",
    "Furman Paladins":             "Furman",
    "Siena Saints":                "Siena",
    "Howard Bison":                "Howard",
    "Michigan Wolverines":         "Michigan",
    "Iowa State Cyclones":         "Iowa State",
    "Virginia Cavaliers":          "Virginia",
    "Illinois Fighting Illini":    "Illinois",
    "Clemson Tigers":              "Clemson",
    "Arkansas Razorbacks":         "Arkansas",
    "Purdue Boilermakers":         "Purdue",
    "Missouri Tigers":             "Missouri",
    "Saint Mary's Gaels":          "Saint Mary's (CA)",
    "Vanderbilt Commodores":       "Vanderbilt",
    "Nebraska Cornhuskers":        "Nebraska",
    "Kennesaw St Owls":            "Kennesaw State",
    "Murray St Racers":            "Murray State",
    "Troy Trojans":                "Troy",
    "Tennessee St Tigers":         "Tennessee State",
    "Houston Cougars":             "Houston",
    "Tennessee Volunteers":        "Tennessee",
    "Alabama Crimson Tide":        "Alabama",
    "Florida Gators":              "Florida",
    "Texas A&M Aggies":            "Texas A&M",
    "North Carolina Tar Heels":    "North Carolina",
    "Wisconsin Badgers":           "Wisconsin",
    "Texas Tech Red Raiders":      "Texas Tech",
    "Kentucky Wildcats":           "Kentucky",
    "Iowa Hawkeyes":               "Iowa",
    "Georgia Bulldogs":            "Georgia",
    "Hofstra Pride":               "Hofstra",
    "McNeese Cowboys":             "McNeese",
    "High Point Panthers":         "High Point",
    "Idaho Vandals":               "Idaho",
    "Gonzaga Bulldogs":            "Gonzaga",
    "Arizona Wildcats":            "Arizona",
    "Texas Longhorns":             "Texas",
    "Villanova Wildcats":          "Villanova",
    "BYU Cougars":                 "BYU",
    "SMU Mustangs":                "SMU",
    "Nevada Wolf Pack":            "Nevada",
    "Colorado St Rams":            "Colorado State",
    "Santa Clara Broncos":         "Santa Clara",
    "Saint Joseph's Hawks":        "Saint Joseph's",
    "Saint Louis Billikens":       "Saint Louis",
    "Wright St Raiders":           "Wright State",
    "Miami Hurricanes":            "Miami (FL)",
    "Miami (OH) RedHawks":         "Miami (OH)",
    "Pennsylvania Quakers":        "Penn",
    "LIU Sharks":                  "LIU",
    "Akron Zips":                  "Akron",
    "Prairie View Panthers":       "Prairie View",
    "Queens University Royals":    "Queens (NC)",
    "California Golden Bears":     "California",
    "UIC Flames":                  "UIC",
    "Hawai'i Rainbow Warriors":    "Hawaii",
    # UMBC not in API response — may appear as:
    "UMBC Retrievers":             "UMBC",
    "NC State Wolfpack":           "NC State",
    "Utah State Aggies":           "Utah State",
    "VCU Rams":                    "VCU",
}


def _resolve_name(api_name: str) -> str:
    """Map an Odds API team name to our bracket team name."""
    return ODDS_NAME_MAP.get(api_name, api_name)


def _implied_prob(american_odds: int) -> float:
    """
    Convert American moneyline odds to implied probability.
    Negative odds (favorite): prob = |odds| / (|odds| + 100)
    Positive odds (underdog): prob = 100 / (odds + 100)
    """
    if american_odds < 0:
        return abs(american_odds) / (abs(american_odds) + 100)
    else:
        return 100 / (american_odds + 100)


def _normalize_probs(prob_a: float, prob_b: float) -> tuple[float, float]:
    """
    Remove vig by normalizing implied probabilities to sum to 1.0.
    Raw implied probs from bookmakers typically sum to ~1.05–1.10 due to vig.
    """
    total = prob_a + prob_b
    if total == 0:
        return 0.5, 0.5
    return prob_a / total, prob_b / total


def fetch_odds(api_key: str = None) -> list[dict]:
    """
    Fetch current NCAAB odds from The Odds API.
    Uses DraftKings as the primary bookmaker.
    Returns the raw API response as a list of game dicts.
    """
    if api_key is None:
        api_key = os.environ.get("ODDS_API_KEY", "")
    if not api_key:
        print("  WARNING: No ODDS_API_KEY set. Skipping odds fetch.")
        return []

    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h,spreads",
        "bookmakers": "draftkings",
        "oddsFormat": "american",
    }

    print("  Fetching NCAAB odds from The Odds API (DraftKings)...")
    resp = requests.get(ODDS_API_URL, params=params, timeout=30)
    resp.raise_for_status()

    # Log remaining API quota
    remaining = resp.headers.get("x-requests-remaining", "?")
    print(f"  API requests remaining this month: {remaining}")

    games = resp.json()
    print(f"  Received odds for {len(games)} games")
    return games


def parse_odds(games: list[dict]) -> dict:
    """
    Parse raw API response into matchup-level odds dict.
    Returns dict keyed by "TeamA vs TeamB" (bracket names, alphabetical).
    Non-tournament games (NIT, etc.) are filtered out using the bracket roster.
    """
    # Load tournament team roster for filtering
    bracket_teams = set()
    bracket_path = PROCESSED_DIR / "bracket_state_2026.json"
    if bracket_path.exists():
        with open(bracket_path) as f:
            bracket = json.load(f)
        for m in bracket.values():
            if m.get("team_a"):
                bracket_teams.add(m["team_a"])
            if m.get("team_b"):
                bracket_teams.add(m["team_b"])

    result = {}
    skipped = 0

    for game in games:
        home_api = game.get("home_team", "")
        away_api = game.get("away_team", "")
        home = _resolve_name(home_api)
        away = _resolve_name(away_api)

        # Filter out non-tournament games (NIT, etc.)
        if bracket_teams and home not in bracket_teams and away not in bracket_teams:
            skipped += 1
            continue

        # Sort alphabetically for consistent keying
        team_a, team_b = sorted([home, away])

        # Extract DraftKings markets
        moneyline_a = None
        moneyline_b = None
        spread_a = None
        spread_b = None
        last_update = None

        for bookmaker in game.get("bookmakers", []):
            if bookmaker.get("key") != "draftkings":
                continue
            last_update = bookmaker.get("last_update")

            for market in bookmaker.get("markets", []):
                for outcome in market.get("outcomes", []):
                    name = _resolve_name(outcome["name"])
                    price = outcome["price"]

                    if market["key"] == "h2h":
                        if name == team_a:
                            moneyline_a = price
                        elif name == team_b:
                            moneyline_b = price

                    elif market["key"] == "spreads":
                        point = outcome.get("point", 0)
                        if name == team_a:
                            spread_a = point
                        elif name == team_b:
                            spread_b = point

        # Calculate implied probabilities from moneylines
        implied_prob_a = None
        implied_prob_b = None
        nv_prob_a = None
        nv_prob_b = None

        if moneyline_a is not None and moneyline_b is not None:
            implied_prob_a = round(_implied_prob(moneyline_a), 4)
            implied_prob_b = round(_implied_prob(moneyline_b), 4)
            nv_a, nv_b = _normalize_probs(implied_prob_a, implied_prob_b)
            nv_prob_a = round(nv_a, 4)
            nv_prob_b = round(nv_b, 4)

        key = f"{team_a} vs {team_b}"
        result[key] = {
            "team_a": team_a,
            "team_b": team_b,
            "moneyline_a": moneyline_a,
            "moneyline_b": moneyline_b,
            "spread_a": spread_a,
            "spread_b": spread_b,
            "implied_prob_a": implied_prob_a,
            "implied_prob_b": implied_prob_b,
            "no_vig_prob_a": nv_prob_a,
            "no_vig_prob_b": nv_prob_b,
            "source": "DraftKings",
            "last_updated": last_update,
        }

    if skipped:
        print(f"  Skipped {skipped} non-tournament games (NIT, etc.)")

    return result


def fetch_all_odds(api_key: str = None) -> dict:
    """Fetch and parse all available NCAAB odds."""
    games = fetch_odds(api_key)
    if not games:
        return {}
    return parse_odds(games)


def save_odds(data: dict, year: int = 2026):
    """Save odds data to JSON."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"odds_{year}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved odds for {len(data)} matchups → {path}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

    data = fetch_all_odds()
    if data:
        save_odds(data)

        # Summary
        has_ml = sum(1 for v in data.values() if v["moneyline_a"] is not None)
        has_spread = sum(1 for v in data.values() if v["spread_a"] is not None)
        print(f"\n  Matchups with moneylines: {has_ml}")
        print(f"  Matchups with spreads:    {has_spread}")

        # Preview
        print("\nSample odds:")
        for key, v in list(data.items())[:5]:
            ml = f"ML: {v['moneyline_a']}/{v['moneyline_b']}" if v["moneyline_a"] else "ML: n/a"
            sp = f"Spread: {v['spread_a']}/{v['spread_b']}" if v["spread_a"] else "Spread: n/a"
            nv = ""
            if v["no_vig_prob_a"]:
                nv = f"  No-vig: {v['no_vig_prob_a']:.1%} / {v['no_vig_prob_b']:.1%}"
            print(f"  {key}: {ml}  {sp}{nv}")
    else:
        print("No odds data retrieved.")
