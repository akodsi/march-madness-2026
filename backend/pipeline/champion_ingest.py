"""
Champion-profile data ingestion.

Fetches two data sources needed for champion-likelihood scoring:

1. **Bart Torvik efficiency ranks** — AdjOE rank, AdjDE rank, overall (AdjEM) rank
   for all D1 teams. Free, no auth required. Substitute for KenPom.
   Uses session-based request to handle Torvik's JS verification challenge.

2. **AP Poll rankings** — current week's AP Top 25 from ESPN's public rankings API.
   Free, no auth required.

Output: champion_data_2026.json keyed by bracket team name, containing:
    - torvik_overall_rank, torvik_adjO_rank, torvik_adjD_rank
    - ap_rank (null if unranked)

Cached locally for 24 hours to avoid redundant requests.
"""

import json
import time
import requests
import pandas as pd
from pathlib import Path
from io import StringIO
from datetime import datetime, timedelta

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
CACHE_DIR = Path(__file__).parent.parent / "data" / "cache"
CURRENT_YEAR = 2026

# Bart Torvik team-level rankings endpoint (returns CSV after session auth)
TORVIK_BASE_URL = "https://barttorvik.com/"
TORVIK_TEAM_RANKINGS_URL = (
    "https://barttorvik.com/trank.php"
    "?year={year}&csv=1"
)

# ESPN public rankings endpoint
ESPN_RANKINGS_URL = (
    "https://site.api.espn.com/apis/site/v2/sports/"
    "basketball/mens-college-basketball/rankings"
)

# ---------------------------------------------------------------------------
# Torvik team name → bracket team name mapping
# Torvik uses abbreviated names with periods (e.g. "Michigan St.", "Iowa St.")
# ---------------------------------------------------------------------------
TORVIK_NAME_MAP = {
    "Michigan St.":           "Michigan State",
    "Ohio St.":               "Ohio State",
    "Iowa St.":               "Iowa State",
    "Utah St.":               "Utah State",
    "North Dakota St.":       "North Dakota State",
    "Wright St.":             "Wright State",
    "Tennessee St.":          "Tennessee State",
    "Kennesaw St.":           "Kennesaw State",
    "McNeese St.":            "McNeese",
    "N.C. State":             "NC State",
    "Cal Baptist":            "California Baptist",
    "Saint Mary's":           "Saint Mary's (CA)",
    "St. John's":             "St. John's (NY)",
    "Miami FL":               "Miami (FL)",
    "Miami OH":               "Miami (OH)",
    "Queens":                 "Queens (NC)",
    "Prairie View A&M":       "Prairie View",
}

# ESPN displayName → bracket team name mapping
ESPN_NAME_MAP = {
    "BYU Cougars":                   "BYU",
    "TCU Horned Frogs":              "TCU",
    "SMU Mustangs":                  "SMU",
    "Penn Quakers":                  "Penn",
    "LIU Sharks":                    "LIU",
    "UMBC Retrievers":               "UMBC",
    "Prairie View A&M Panthers":     "Prairie View",
    "VCU Rams":                      "VCU",
    "Saint Mary's Gaels":            "Saint Mary's (CA)",
    "Miami Hurricanes":              "Miami (FL)",
    "Miami (OH) RedHawks":           "Miami (OH)",
    "St. John's Red Storm":          "St. John's (NY)",
    "Queens Royals":                 "Queens (NC)",
    "UCF Knights":                   "UCF",
    "UConn Huskies":                 "Connecticut",
    "Michigan State Spartans":       "Michigan State",
    "Ohio State Buckeyes":           "Ohio State",
    "Iowa State Cyclones":           "Iowa State",
    "North Carolina Tar Heels":      "North Carolina",
    "Texas A&M Aggies":              "Texas A&M",
    "NC State Wolfpack":             "NC State",
    "Texas Tech Red Raiders":        "Texas Tech",
}


def _cache_path(name: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}_{CURRENT_YEAR}.json"


def _is_cache_fresh(path: Path, max_age_hours: int = 24) -> bool:
    if not path.exists():
        return False
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(hours=max_age_hours)


# ---------------------------------------------------------------------------
# Torvik: fetch team-level rankings, compute ranks
# ---------------------------------------------------------------------------

def _torvik_session() -> requests.Session:
    """Create a session that passes Torvik's JS verification challenge."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    })
    # Hit main page, then submit the JS test form
    session.get(TORVIK_BASE_URL, timeout=15)
    session.post(TORVIK_BASE_URL, data={"js_test_submitted": "1"}, timeout=15)
    return session


def fetch_torvik_ranks(year: int = CURRENT_YEAR) -> dict:
    """
    Fetch Torvik team-level stats for all D1 teams and compute AdjOE/AdjDE/AdjEM ranks.
    Returns dict keyed by bracket team name with rank integers and raw values.

    The Torvik trank.php CSV has no header row. Key columns:
        col 0: Team name
        col 1: AdjOE (adjusted offensive efficiency)
        col 2: AdjDE (adjusted defensive efficiency)
    """
    cache = _cache_path("torvik_ranks")
    if _is_cache_fresh(cache):
        print("  Using cached Torvik ranks")
        with open(cache) as f:
            return json.load(f)

    print(f"  Fetching Torvik team rankings for {year}...")
    session = _torvik_session()
    url = TORVIK_TEAM_RANKINGS_URL.format(year=year)
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    # Verify we got CSV, not an HTML challenge page
    if resp.text.strip().startswith("<"):
        print("  WARNING: Torvik returned HTML instead of CSV (JS challenge failed)")
        return {}

    df = pd.read_csv(StringIO(resp.text), header=None)

    # Name key columns
    df = df.rename(columns={0: "Team", 1: "AdjOE", 2: "AdjDE"})
    df["AdjEM"] = df["AdjOE"] - df["AdjDE"]

    # Compute ranks (1 = best)
    # AdjOE: higher is better → rank descending
    # AdjDE: lower is better → rank ascending
    # AdjEM: higher is better → rank descending
    df["AdjOE_Rank"] = df["AdjOE"].rank(ascending=False, method="min").astype(int)
    df["AdjDE_Rank"] = df["AdjDE"].rank(ascending=True, method="min").astype(int)
    df["AdjEM_Rank"] = df["AdjEM"].rank(ascending=False, method="min").astype(int)

    # Map Torvik team names to bracket names
    df["BracketName"] = df["Team"].map(TORVIK_NAME_MAP).fillna(df["Team"])

    result = {}
    for _, row in df.iterrows():
        name = row["BracketName"]
        result[name] = {
            "torvik_overall_rank": int(row["AdjEM_Rank"]),
            "torvik_adjO_rank": int(row["AdjOE_Rank"]),
            "torvik_adjD_rank": int(row["AdjDE_Rank"]),
            "torvik_adjOE": round(float(row["AdjOE"]), 1),
            "torvik_adjDE": round(float(row["AdjDE"]), 1),
            "torvik_adjEM": round(float(row["AdjEM"]), 1),
        }

    # Cache
    with open(cache, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Fetched Torvik ranks for {len(result)} teams")

    return result


# ---------------------------------------------------------------------------
# ESPN AP Poll
# ---------------------------------------------------------------------------

def fetch_ap_poll() -> dict:
    """
    Fetch current AP Top 25 from ESPN's public rankings API.
    Returns dict of bracket team name → AP rank (1–25).
    Teams outside top 25 are not included.
    """
    cache = _cache_path("ap_poll")
    if _is_cache_fresh(cache):
        print("  Using cached AP Poll")
        with open(cache) as f:
            return json.load(f)

    print("  Fetching AP Poll from ESPN...")
    resp = requests.get(ESPN_RANKINGS_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # Find the AP poll in the rankings list
    ap_poll = None
    for ranking in data.get("rankings", []):
        if "AP" in ranking.get("name", ""):
            ap_poll = ranking
            break

    if ap_poll is None:
        print("  WARNING: AP Poll not found in ESPN rankings response")
        return {}

    result = {}
    for entry in ap_poll.get("ranks", []):
        team_info = entry.get("team", {})
        display_name = team_info.get("displayName", "")
        location = team_info.get("location", "")
        rank = entry.get("current", entry.get("rank"))

        # Try mapping ESPN display name to bracket name
        bracket_name = ESPN_NAME_MAP.get(display_name)
        if bracket_name is None:
            # Try location (e.g. "Duke", "Michigan", "Arizona")
            bracket_name = location

        if bracket_name and rank:
            result[bracket_name] = int(rank)

    # Cache
    with open(cache, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  Fetched AP Poll: {len(result)} ranked teams")

    return result


# ---------------------------------------------------------------------------
# Combined: build champion profile data for all 68 tournament teams
# ---------------------------------------------------------------------------

def fetch_champion_data(tournament_teams: list[str], year: int = CURRENT_YEAR) -> dict:
    """
    Build champion-profile data for each tournament team.
    Merges Torvik efficiency ranks + AP Poll into a single dict per team.

    Returns dict keyed by bracket team name.
    """
    torvik = fetch_torvik_ranks(year)
    time.sleep(0.5)  # rate-limit between API calls
    ap_poll = fetch_ap_poll()

    result = {}
    for team in tournament_teams:
        tv = torvik.get(team, {})
        entry = {
            # Torvik efficiency ranks (KenPom substitute)
            "torvik_overall_rank": tv.get("torvik_overall_rank"),
            "torvik_adjO_rank": tv.get("torvik_adjO_rank"),
            "torvik_adjD_rank": tv.get("torvik_adjD_rank"),
            "torvik_adjOE": tv.get("torvik_adjOE"),
            "torvik_adjDE": tv.get("torvik_adjDE"),
            "torvik_adjEM": tv.get("torvik_adjEM"),
            # AP Poll (null if unranked)
            "ap_rank": ap_poll.get(team),
        }
        result[team] = entry

    return result


def save_champion_data(data: dict, year: int = CURRENT_YEAR):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / f"champion_data_{year}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Saved champion data for {len(data)} teams → {path}")


if __name__ == "__main__":
    from tournament_filter import build_tournament_teams

    teams = build_tournament_teams()["Team"].tolist()
    print(f"Fetching champion-profile data for {len(teams)} tournament teams...\n")

    data = fetch_champion_data(teams)
    save_champion_data(data)

    # Show summary
    have_torvik = sum(1 for v in data.values() if v.get("torvik_overall_rank"))
    have_ap = sum(1 for v in data.values() if v.get("ap_rank"))
    print(f"\nTeams with Torvik data: {have_torvik}")
    print(f"Teams with AP rank: {have_ap}")

    # Flag teams missing Torvik data
    missing = [k for k, v in data.items() if not v.get("torvik_overall_rank")]
    if missing:
        print(f"\nMissing Torvik data ({len(missing)}):")
        for t in missing:
            print(f"  - {t}")

    # Top contenders preview
    ranked = [(k, v) for k, v in data.items() if v.get("torvik_overall_rank")]
    ranked.sort(key=lambda x: x[1]["torvik_overall_rank"])
    print("\nTop 15 by Torvik overall rank:")
    for name, d in ranked[:15]:
        ap = f"AP #{d['ap_rank']}" if d.get("ap_rank") else "unranked"
        print(f"  #{d['torvik_overall_rank']:3d}  {name:25s}  O=#{d['torvik_adjO_rank']:3d}  D=#{d['torvik_adjD_rank']:3d}  {ap}")
