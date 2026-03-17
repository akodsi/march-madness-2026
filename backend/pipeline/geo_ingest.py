"""
Geographic data pipeline.

Two responsibilities:
  1. Geocode every team's campus (lat/long) using OpenStreetMap Nominatim (free, no API key).
     Results are cached in data/raw/geo/campus_coords_cache.csv so we only hit the API once.

  2. Provide tournament venue locations and compute the travel distance (miles) from each
     team's campus to each venue. This becomes a feature in the prediction engine —
     shorter distance = perceived home-field advantage.

Haversine distance formula used for all calculations (accurate to ~0.5%).
"""

import time
import math
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

RAW_DIR = Path(__file__).parent.parent / "data" / "raw" / "geo"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

CACHE_FILE = RAW_DIR / "campus_coords_cache.csv"
VENUES_FILE = RAW_DIR / "venues_2026.csv"

# ---------------------------------------------------------------------------
# Team name → full university name for geocoding
# Sports-Reference uses short names; Nominatim needs the real university name.
# ---------------------------------------------------------------------------
TEAM_NAME_MAP = {
    "Michigan":            "University of Michigan",
    "Duke":                "Duke University",
    "Arizona":             "University of Arizona",
    "Florida":             "University of Florida",
    "Iowa State":          "Iowa State University",
    "Illinois":            "University of Illinois Urbana-Champaign",
    "Houston":             "University of Houston",
    "Purdue":              "Purdue University",
    "Gonzaga":             "Gonzaga University",
    "Michigan State":      "Michigan State University",
    "Louisville":          "University of Louisville",
    "Connecticut":         "University of Connecticut",
    "Vanderbilt":          "Vanderbilt University",
    "Alabama":             "University of Alabama",
    "Arkansas":            "University of Arkansas",
    "St. John's (NY)":     "St. John's University Queens New York",
    "Tennessee":           "University of Tennessee",
    "Texas Tech":          "Texas Tech University",
    "Virginia":            "University of Virginia",
    "Nebraska":            "University of Nebraska-Lincoln",
    "Creighton":           "Creighton University",
    "Kentucky":            "University of Kentucky",
    "UCLA":                "University of California Los Angeles",
    "USC":                 "University of Southern California",
    "Oregon":              "University of Oregon",
    "Washington":          "University of Washington",
    "Kansas":              "University of Kansas",
    "Baylor":              "Baylor University",
    "Ohio State":          "Ohio State University",
    "Indiana":             "Indiana University Bloomington",
    "Wisconsin":           "University of Wisconsin-Madison",
    "North Carolina":      "University of North Carolina Chapel Hill",
    "NC State":            "North Carolina State University",
    "Wake Forest":         "Wake Forest University",
    "Syracuse":            "Syracuse University",
    "Pittsburgh":          "University of Pittsburgh",
    "Miami (FL)":          "University of Miami Coral Gables",
    "Florida State":       "Florida State University",
    "Clemson":             "Clemson University",
    "Georgia Tech":        "Georgia Institute of Technology",
    "Virginia Tech":       "Virginia Polytechnic Institute and State University",
    "Notre Dame":          "University of Notre Dame",
    "Marquette":           "Marquette University",
    "Georgetown":          "Georgetown University",
    "Providence":          "Providence College",
    "Xavier":              "Xavier University Cincinnati",
    "Villanova":           "Villanova University",
    "Seton Hall":          "Seton Hall University",
    "Butler":              "Butler University",
    "BYU":                 "Brigham Young University",
    "Utah":                "University of Utah",
    "Colorado":            "University of Colorado Boulder",
    "Arizona State":       "Arizona State University",
    "Stanford":            "Stanford University",
    "California":          "University of California Berkeley",
    "Oregon State":        "Oregon State University",
    "Washington State":    "Washington State University",
    "Utah State":          "Utah State University",
    "Nevada":              "University of Nevada Reno",
    "San Diego State":     "San Diego State University",
    "UNLV":                "University of Nevada Las Vegas",
    "Fresno State":        "California State University Fresno",
    "Boise State":         "Boise State University",
    "New Mexico":          "University of New Mexico",
    "Colorado State":      "Colorado State University",
    "Wyoming":             "University of Wyoming",
    "Air Force":           "United States Air Force Academy",
    "Memphis":             "University of Memphis",
    "Tulsa":               "University of Tulsa",
    "SMU":                 "Southern Methodist University",
    "TCU":                 "Texas Christian University",
    "Texas":               "University of Texas Austin",
    "Texas A&M":           "Texas A&M University",
    "Oklahoma":            "University of Oklahoma",
    "Oklahoma State":      "Oklahoma State University",
    "Missouri":            "University of Missouri",
    "Iowa":                "University of Iowa",
    "Minnesota":           "University of Minnesota",
    "Northwestern":        "Northwestern University",
    "Penn State":          "Pennsylvania State University",
    "Maryland":            "University of Maryland",
    "Rutgers":             "Rutgers University New Brunswick",
    "Mississippi State":   "Mississippi State University",
    "Ole Miss":            "University of Mississippi",
    "LSU":                 "Louisiana State University",
    "Auburn":              "Auburn University",
    "Georgia":             "University of Georgia",
    "South Carolina":      "University of South Carolina",
    "Mississippi":         "University of Mississippi",
    "Drake":               "Drake University",
    "Wichita State":       "Wichita State University",
    "Bradley":             "Bradley University",
    "Northern Iowa":       "University of Northern Iowa",
    "Loyola Chicago":      "Loyola University Chicago",
    "Illinois State":      "Illinois State University",
    "Indiana State":       "Indiana State University",
    "Evansville":          "University of Evansville",
    "Valparaiso":          "Valparaiso University",
    "UC Irvine":           "University of California Irvine",
    "UC Santa Barbara":    "University of California Santa Barbara",
    "UC Davis":            "University of California Davis",
    "UC Riverside":        "University of California Riverside",
    "Long Beach State":    "California State University Long Beach",
    "Cal Poly":            "California Polytechnic State University San Luis Obispo",
    "Hawaii":              "University of Hawaii at Manoa",
}


# ---------------------------------------------------------------------------
# Haversine distance (miles between two lat/lon points)
# ---------------------------------------------------------------------------
def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------
def _make_geocoder():
    geolocator = Nominatim(user_agent="march_madness_predictor_v1")
    return RateLimiter(geolocator.geocode, min_delay_seconds=1.1)


def geocode_teams(teams: list[str], force_refresh: bool = False) -> pd.DataFrame:
    """
    Geocode each team's campus. Results cached in CACHE_FILE.
    Only hits the API for teams not already in the cache.

    Returns DataFrame with columns: Team, Lat, Lon, Address, GeoStatus
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing cache
    if CACHE_FILE.exists() and not force_refresh:
        cache = pd.read_csv(CACHE_FILE)
    else:
        cache = pd.DataFrame(columns=["Team", "Lat", "Lon", "Address", "GeoStatus"])

    cached_teams = set(cache["Team"].tolist())
    to_geocode = [t for t in teams if t not in cached_teams]

    if not to_geocode:
        print(f"  All {len(teams)} teams found in cache.")
        return cache[cache["Team"].isin(teams)].reset_index(drop=True)

    print(f"  Geocoding {len(to_geocode)} teams (cached: {len(cached_teams)})...")
    geocode = _make_geocoder()
    new_rows = []

    for i, team in enumerate(to_geocode):
        query = TEAM_NAME_MAP.get(team, f"{team} University")
        try:
            loc = geocode(query)
            if loc:
                row = {
                    "Team": team,
                    "Lat": round(loc.latitude, 5),
                    "Lon": round(loc.longitude, 5),
                    "Address": loc.address[:80],
                    "GeoStatus": "ok",
                }
            else:
                # Fallback: try appending "University" if map didn't help
                loc2 = geocode(f"{team} University")
                if loc2:
                    row = {
                        "Team": team,
                        "Lat": round(loc2.latitude, 5),
                        "Lon": round(loc2.longitude, 5),
                        "Address": loc2.address[:80],
                        "GeoStatus": "fallback",
                    }
                else:
                    row = {"Team": team, "Lat": None, "Lon": None, "Address": "", "GeoStatus": "failed"}
                    print(f"    FAILED: {team}")
        except Exception as e:
            row = {"Team": team, "Lat": None, "Lon": None, "Address": str(e)[:60], "GeoStatus": "error"}
            print(f"    ERROR: {team} — {e}")

        new_rows.append(row)
        if (i + 1) % 10 == 0:
            print(f"    {i + 1}/{len(to_geocode)} done...")

    if new_rows:
        new_df = pd.DataFrame(new_rows)
        cache = pd.concat([cache, new_df], ignore_index=True)
        cache.to_csv(CACHE_FILE, index=False)
        ok = new_df[new_df["GeoStatus"] == "ok"].shape[0]
        print(f"  Geocoded {ok}/{len(new_rows)} successfully. Cache saved.")

    return cache[cache["Team"].isin(teams)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Tournament venues
# ---------------------------------------------------------------------------
def load_or_create_venues(year: int = 2026) -> pd.DataFrame:
    """
    Load venue locations for the tournament year.
    If the file doesn't exist, creates a template to fill in once the bracket drops.

    CSV format: Round, City, State, VenueName, Lat, Lon
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    venues_file = RAW_DIR / f"venues_{year}.csv"

    if venues_file.exists():
        return pd.read_csv(venues_file)

    # Template — lat/lon left blank until bracket is announced
    # First/Second round sites are typically announced weeks in advance
    template = pd.DataFrame([
        {"Round": "First/Second", "City": "TBD", "State": "TBD", "VenueName": "TBD", "Lat": None, "Lon": None},
    ])
    template.to_csv(venues_file, index=False)
    print(f"  Created venue template at {venues_file}")
    print("  Fill in city/lat/lon once the bracket is announced on Selection Sunday.")
    return template


def add_2026_venues() -> pd.DataFrame:
    """
    2026 NCAA Tournament venue locations.
    First/Second Round sites — fill in once officially announced.
    Sweet 16 / Elite 8 / Final Four sites tend to be announced a year in advance.
    """
    venues = [
        # Round,           City,               State, VenueName,                          Lat,      Lon
        ("First/Second",  "Lexington",         "KY",  "Rupp Arena",                       38.0492, -84.4997),
        ("First/Second",  "Indianapolis",      "IN",  "Gainbridge Fieldhouse",            39.7640, -86.1555),
        ("First/Second",  "Charlotte",         "NC",  "Spectrum Center",                  35.2251, -80.8393),
        ("First/Second",  "Albany",            "NY",  "MVP Arena",                        42.6526, -73.7562),
        ("First/Second",  "Providence",        "RI",  "Amica Mutual Pavilion",            41.8225, -71.4128),
        ("First/Second",  "Wichita",           "KS",  "INTRUST Bank Arena",               37.6872, -97.3301),
        ("First/Second",  "Cleveland",         "OH",  "Rocket Mortgage FieldHouse",       41.4965, -81.6882),
        ("First/Second",  "Spokane",           "WA",  "Spokane Arena",                    47.6651, -117.4243),
        ("Sweet 16/Elite 8", "Los Angeles",    "CA",  "Crypto.com Arena",                 34.0430, -118.2673),
        ("Sweet 16/Elite 8", "Dallas",         "TX",  "American Airlines Center",         32.7905, -96.8103),
        ("Sweet 16/Elite 8", "Newark",         "NJ",  "Prudential Center",                40.7334, -74.1713),
        ("Sweet 16/Elite 8", "Detroit",        "MI",  "Little Caesars Arena",             42.3410, -83.0554),
        ("Final Four",    "San Antonio",       "TX",  "Alamodome",                        29.4189, -98.4808),
    ]
    df = pd.DataFrame(venues, columns=["Round", "City", "State", "VenueName", "Lat", "Lon"])
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_DIR / "venues_2026.csv", index=False)
    print(f"  Saved {len(df)} venue locations.")
    return df


# ---------------------------------------------------------------------------
# Distance computation
# ---------------------------------------------------------------------------
def compute_travel_distances(
    team_coords: pd.DataFrame,
    venues: pd.DataFrame,
) -> pd.DataFrame:
    """
    For every (team, venue) combination, compute the distance in miles
    from the team's campus to the venue.

    Returns a DataFrame with columns:
        Team, VenueName, City, State, Round, DistanceMiles, AdvantageScore

    AdvantageScore (0–1):
        1.0 = within 50 miles  (strong home advantage)
        0.0 = 2000+ miles away (pure away)
        Smooth decay in between using an exponential curve.
    """
    rows = []
    coords = team_coords[team_coords["GeoStatus"].isin(["ok", "fallback"])]

    for _, venue in venues.iterrows():
        if pd.isna(venue["Lat"]):
            continue
        for _, team in coords.iterrows():
            dist = haversine_miles(team["Lat"], team["Lon"], venue["Lat"], venue["Lon"])
            # Exponential decay: full advantage at 0 mi, half at ~300 mi, ~0 at 2000+ mi
            advantage = math.exp(-dist / 600)
            rows.append({
                "Team":           team["Team"],
                "VenueName":      venue["VenueName"],
                "City":           venue["City"],
                "State":          venue["State"],
                "Round":          venue["Round"],
                "DistanceMiles":  round(dist, 1),
                "AdvantageScore": round(advantage, 4),
            })

    return pd.DataFrame(rows).sort_values(["VenueName", "DistanceMiles"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Load teams
    stats = pd.read_csv(PROCESSED_DIR / "team_stats_2026.csv")
    teams = stats["Team"].tolist()

    print("Step 1: Geocoding team campuses...")
    coords = geocode_teams(teams)
    ok = coords[coords["GeoStatus"].isin(["ok", "fallback"])]
    print(f"  {len(ok)}/{len(teams)} teams located.\n")

    print("Step 2: Loading tournament venues...")
    venues = add_2026_venues()

    print("\nStep 3: Computing travel distances...")
    distances = compute_travel_distances(coords, venues)

    out_path = PROCESSED_DIR / "travel_distances_2026.csv"
    distances.to_csv(out_path, index=False)
    print(f"  Saved {len(distances)} rows → {out_path}")

    # Show a few interesting examples
    print("\nClosest teams to each First/Second Round site:")
    first_round = distances[distances["Round"] == "First/Second"]
    for venue_name, group in first_round.groupby("VenueName"):
        closest = group.nsmallest(3, "DistanceMiles")[["Team", "DistanceMiles", "AdvantageScore"]]
        print(f"\n  {venue_name}:")
        for _, row in closest.iterrows():
            print(f"    {row['Team']:25s}  {row['DistanceMiles']:>6.0f} mi  advantage={row['AdvantageScore']:.3f}")
