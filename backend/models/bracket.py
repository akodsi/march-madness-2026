"""
Bracket model.

Represents the full 68-team 2026 NCAA Tournament as a tree of matchups.
Each matchup shows both teams' win percentages. The user picks winners —
picks cascade forward so the next matchup is calculated as soon as both
teams are known.

Structure:
    First Four  (4 games)  → feeds into Round of 64
    Round of 64 (32 games) → Round of 32 (16) → Sweet 16 (8)
    → Elite 8 (4) → Final Four (2) → Championship (1)

Each matchup slot is identified by a string ID, e.g.:
    "FF_1"          — First Four game 1
    "E_R1_1"        — East region, Round 1, slot 1  (1 vs 16)
    "E_R2_1"        — East region, Round 2, slot 1
    "E_R3_1"        — East Sweet 16, slot 1
    "E_R4_1"        — East Elite 8
    "S4_1"          — Final Four game 1  (East winner vs West winner)
    "CHAMP"         — Championship
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
BRACKET_STATE_FILE = PROCESSED_DIR / "bracket_state_2026.json"
RESULTS_FILE = PROCESSED_DIR / "results_2026.json"


@dataclass
class Matchup:
    id: str
    round_name: str         # "First Four" | "Round of 64" | etc.
    region: str             # "East" | "West" | "Midwest" | "South" | "National"
    team_a: Optional[str]   # None = TBD (waiting on a prior pick)
    team_b: Optional[str]
    prob_a: Optional[float] # None = not yet calculable
    prob_b: Optional[float]
    pct_a:  Optional[int]   # display percentage e.g. 68
    pct_b:  Optional[int]   # display percentage e.g. 32
    confidence: Optional[str]
    user_pick: Optional[str]          # team name the user chose
    winner_slot: Optional[str]        # matchup_id this winner feeds into
    winner_slot_position: Optional[str]  # "a" or "b" in the next matchup
    signals: Optional[dict] = field(default=None)
    raw_stats: Optional[dict] = field(default=None)
    commentary: Optional[dict] = field(default=None)
    champion_likelihood: Optional[dict] = field(default=None)
    actual_winner: Optional[str] = field(default=None)
    actual_score_a: Optional[int] = field(default=None)
    actual_score_b: Optional[int] = field(default=None)

    def is_ready(self) -> bool:
        """Both teams are known — probabilities can be calculated."""
        return self.team_a is not None and self.team_b is not None

    def is_decided(self) -> bool:
        """User has made a pick."""
        return self.user_pick is not None

    def display(self) -> str:
        a = self.team_a or "TBD"
        b = self.team_b or "TBD"
        if self.is_ready() and self.prob_a is not None:
            pa, pb = self.pct_a, self.pct_b
            pick_marker_a = " ✓" if self.user_pick == self.team_a else ""
            pick_marker_b = " ✓" if self.user_pick == self.team_b else ""
            return (
                f"[{self.id}]  {a} {pa}% vs {pb}% {b}"
                f"{pick_marker_a or pick_marker_b}  [{self.confidence}]"
            )
        return f"[{self.id}]  {a} vs {b}  [TBD]"


class Bracket:
    """
    Full tournament bracket. Holds all matchup slots and manages
    pick propagation.
    """

    def __init__(self):
        self.matchups: dict[str, Matchup] = {}
        self._build()

    # -----------------------------------------------------------------------
    # Construction
    # -----------------------------------------------------------------------

    def _add(self, id, round_name, region, team_a, team_b, winner_slot, winner_pos):
        self.matchups[id] = Matchup(
            id=id,
            round_name=round_name,
            region=region,
            team_a=team_a,
            team_b=team_b,
            prob_a=None, prob_b=None, pct_a=None, pct_b=None,
            confidence=None,
            user_pick=None,
            winner_slot=winner_slot,
            winner_slot_position=winner_pos,
            signals=None,
        )

    def _build(self):
        """
        Construct all matchup slots from the 2026 bracket.
        Teams that come from First Four games start as None.
        """
        A = self._add

        # ── FIRST FOUR ──────────────────────────────────────────────────────
        # FF winners feed into their respective R1 slots
        A("FF_1", "First Four", "Midwest",  "UMBC",        "Howard",       "MW_R1_1", "a")
        A("FF_2", "First Four", "Midwest",  "Miami (OH)",  "SMU",          "MW_R1_6", "a")
        A("FF_3", "First Four", "West",     "Texas",       "NC State",     "W_R1_6",  "a")
        A("FF_4", "First Four", "South",    "Prairie View","Lehigh",       "S_R1_1",  "b")

        # ── EAST REGION ─────────────────────────────────────────────────────
        #   R1 slot → R2 slot → R3 (S16) → R4 (E8)
        A("E_R1_1", "Round of 64", "East", "Duke",              "Siena",             "E_R2_1", "a")
        A("E_R1_2", "Round of 64", "East", "Ohio State",        "TCU",               "E_R2_1", "b")
        A("E_R1_3", "Round of 64", "East", "St. John's (NY)",   "Northern Iowa",     "E_R2_2", "a")
        A("E_R1_4", "Round of 64", "East", "Kansas",            "California Baptist","E_R2_2", "b")
        A("E_R1_5", "Round of 64", "East", "Louisville",        "South Florida",     "E_R2_3", "a")
        A("E_R1_6", "Round of 64", "East", "Michigan State",    "North Dakota State","E_R2_3", "b")
        A("E_R1_7", "Round of 64", "East", "UCLA",              "UCF",               "E_R2_4", "a")
        A("E_R1_8", "Round of 64", "East", "Connecticut",       "Furman",            "E_R2_4", "b")

        A("E_R2_1", "Round of 32", "East", None, None, "E_R3_1", "a")
        A("E_R2_2", "Round of 32", "East", None, None, "E_R3_1", "b")
        A("E_R2_3", "Round of 32", "East", None, None, "E_R3_2", "a")
        A("E_R2_4", "Round of 32", "East", None, None, "E_R3_2", "b")

        A("E_R3_1", "Sweet 16",    "East", None, None, "E_R4_1", "a")
        A("E_R3_2", "Sweet 16",    "East", None, None, "E_R4_1", "b")
        A("E_R4_1", "Elite 8",     "East", None, None, "SF_1",   "a")

        # ── WEST REGION ─────────────────────────────────────────────────────
        A("W_R1_1", "Round of 64", "West", "Arizona",          "LIU",               "W_R2_1", "a")
        A("W_R1_2", "Round of 64", "West", "Villanova",        "Utah State",        "W_R2_1", "b")
        A("W_R1_3", "Round of 64", "West", "Wisconsin",        "High Point",        "W_R2_2", "a")
        A("W_R1_4", "Round of 64", "West", "Arkansas",         "Hawaii",           "W_R2_2", "b")
        A("W_R1_5", "Round of 64", "West", None,               "BYU",               "W_R2_3", "a")  # FF_3 winner vs BYU
        A("W_R1_6", "Round of 64", "West", "Gonzaga",          "Kennesaw State",    "W_R2_3", "b")
        A("W_R1_7", "Round of 64", "West", "Saint Mary's (CA)","Texas A&M",         "W_R2_4", "a")
        A("W_R1_8", "Round of 64", "West", "Purdue",           "Queens (NC)",       "W_R2_4", "b")

        A("W_R2_1", "Round of 32", "West", None, None, "W_R3_1", "a")
        A("W_R2_2", "Round of 32", "West", None, None, "W_R3_1", "b")
        A("W_R2_3", "Round of 32", "West", None, None, "W_R3_2", "a")
        A("W_R2_4", "Round of 32", "West", None, None, "W_R3_2", "b")

        A("W_R3_1", "Sweet 16",    "West", None, None, "W_R4_1", "a")
        A("W_R3_2", "Sweet 16",    "West", None, None, "W_R4_1", "b")
        A("W_R4_1", "Elite 8",     "West", None, None, "SF_1",   "b")

        # ── MIDWEST REGION ──────────────────────────────────────────────────
        A("MW_R1_1", "Round of 64", "Midwest", None,         "Michigan",      "MW_R2_1", "a")  # FF_1 winner vs Michigan
        A("MW_R1_2", "Round of 64", "Midwest", "Georgia",    "Saint Louis",   "MW_R2_1", "b")
        A("MW_R1_3", "Round of 64", "Midwest", "Texas Tech",  "Akron",        "MW_R2_2", "a")
        A("MW_R1_4", "Round of 64", "Midwest", "Alabama",     "Hofstra",      "MW_R2_2", "b")
        A("MW_R1_5", "Round of 64", "Midwest", "Tennessee",   None,           "MW_R2_3", "a")  # Tennessee vs FF_2 winner
        A("MW_R1_6", "Round of 64", "Midwest", "Virginia",    "Wright State", "MW_R2_3", "b")
        A("MW_R1_7", "Round of 64", "Midwest", "Kentucky",    "Santa Clara",  "MW_R2_4", "a")
        A("MW_R1_8", "Round of 64", "Midwest", "Iowa State",  "Tennessee State","MW_R2_4","b")

        A("MW_R2_1", "Round of 32", "Midwest", None, None, "MW_R3_1", "a")
        A("MW_R2_2", "Round of 32", "Midwest", None, None, "MW_R3_1", "b")
        A("MW_R2_3", "Round of 32", "Midwest", None, None, "MW_R3_2", "a")
        A("MW_R2_4", "Round of 32", "Midwest", None, None, "MW_R3_2", "b")

        A("MW_R3_1", "Sweet 16",    "Midwest", None, None, "MW_R4_1", "a")
        A("MW_R3_2", "Sweet 16",    "Midwest", None, None, "MW_R4_1", "b")
        A("MW_R4_1", "Elite 8",     "Midwest", None, None, "SF_2",    "a")

        # ── SOUTH REGION ────────────────────────────────────────────────────
        A("S_R1_1",  "Round of 64", "South", "Florida",       None,           "S_R2_1", "a")  # Florida vs FF_4 winner
        A("S_R1_2",  "Round of 64", "South", "Clemson",       "Iowa",         "S_R2_1", "b")
        A("S_R1_3",  "Round of 64", "South", "Vanderbilt",    "McNeese",      "S_R2_2", "a")
        A("S_R1_4",  "Round of 64", "South", "Nebraska",      "Troy",         "S_R2_2", "b")
        A("S_R1_5",  "Round of 64", "South", "North Carolina","VCU",          "S_R2_3", "a")
        A("S_R1_6",  "Round of 64", "South", "Illinois",      "Penn",         "S_R2_3", "b")
        A("S_R1_7",  "Round of 64", "South", "Miami (FL)",    "Missouri",     "S_R2_4", "a")
        A("S_R1_8",  "Round of 64", "South", "Houston",       "Idaho",        "S_R2_4", "b")

        A("S_R2_1",  "Round of 32", "South", None, None, "S_R3_1", "a")
        A("S_R2_2",  "Round of 32", "South", None, None, "S_R3_1", "b")
        A("S_R2_3",  "Round of 32", "South", None, None, "S_R3_2", "a")
        A("S_R2_4",  "Round of 32", "South", None, None, "S_R3_2", "b")

        A("S_R3_1",  "Sweet 16",    "South", None, None, "S_R4_1", "a")
        A("S_R3_2",  "Sweet 16",    "South", None, None, "S_R4_1", "b")
        A("S_R4_1",  "Elite 8",     "South", None, None, "SF_2",   "b")

        # ── NATIONAL ────────────────────────────────────────────────────────
        A("SF_1",    "Final Four",   "National", None, None, "CHAMP", "a")   # East vs West
        A("SF_2",    "Final Four",   "National", None, None, "CHAMP", "b")   # Midwest vs South
        A("CHAMP",   "Championship", "National", None, None, None,    None)

        # Wire First Four winners into their R1 slots
        # FF_3 (Texas/NC State) → W_R1_5 team_a (vs BYU team_b)
        self.matchups["FF_3"].winner_slot = "W_R1_5"
        self.matchups["FF_3"].winner_slot_position = "a"

        # FF_1 (UMBC/Howard) → MW_R1_1 team_a (vs Michigan team_b)
        self.matchups["MW_R1_1"].team_b = "Michigan"
        self.matchups["FF_1"].winner_slot = "MW_R1_1"
        self.matchups["FF_1"].winner_slot_position = "a"

        # FF_2 (Miami OH/SMU) → MW_R1_5 team_b (vs Tennessee team_a)
        self.matchups["FF_2"].winner_slot = "MW_R1_5"
        self.matchups["FF_2"].winner_slot_position = "b"

        # FF_4 (Prairie View/Lehigh) → S_R1_1 team_b (vs Florida team_a)
        self.matchups["FF_4"].winner_slot = "S_R1_1"
        self.matchups["FF_4"].winner_slot_position = "b"

        # Calculate probabilities for all matchups that already have both teams
        self._recalculate_all()

    # -----------------------------------------------------------------------
    # Probability calculation
    # -----------------------------------------------------------------------

    def _calc(self, matchup_id: str):
        """Calculate and store probabilities for a matchup if both teams are known."""
        import sys, pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
        from models.rule_engine import predict
        m = self.matchups[matchup_id]
        if not m.is_ready():
            return
        try:
            result = predict(m.team_a, m.team_b)
            m.prob_a      = result["prob_a"]
            m.prob_b      = result["prob_b"]
            m.pct_a       = result["pct_a"]
            m.pct_b       = result["pct_b"]
            m.confidence  = result["confidence"]
            m.signals     = result["signals"]
            m.raw_stats   = result["raw_stats"]
            m.commentary  = result.get("commentary")
            m.champion_likelihood = result.get("champion_likelihood")
        except Exception as e:
            # Team not in dataset (e.g. small school) — fall back to seed-based 50/50
            m.prob_a = 0.5
            m.prob_b = 0.5
            m.pct_a  = 50
            m.pct_b  = 50
            m.confidence = "Toss-Up"

    def _recalculate_all(self):
        for mid in self.matchups:
            self._calc(mid)

    # -----------------------------------------------------------------------
    # User picks + cascade
    # -----------------------------------------------------------------------

    def pick(self, matchup_id: str, winner: str) -> list[str]:
        """
        Record the user's pick for a matchup and cascade forward.

        - Sets user_pick on the matchup
        - Advances the winner into the appropriate slot of the next matchup
        - Recalculates probabilities for the next matchup if both teams are now known
        - Continues cascading if the next matchup was already decided

        Returns a list of matchup IDs that were updated (for the API to push
        targeted updates to the frontend).
        """
        m = self.matchups.get(matchup_id)
        if m is None:
            raise ValueError(f"Unknown matchup: {matchup_id}")
        if winner not in (m.team_a, m.team_b):
            raise ValueError(f"'{winner}' is not a team in matchup {matchup_id}")

        m.user_pick = winner
        updated = [matchup_id]

        # Cascade winner into the next matchup
        if m.winner_slot:
            updated += self._advance(winner, m.winner_slot, m.winner_slot_position)

        return updated

    def _advance(self, team: str, slot_id: str, position: str) -> list[str]:
        """
        Place `team` into `position` ('a' or 'b') of matchup `slot_id`.
        Recalculate probabilities. If that matchup already has a pick,
        cascade further.
        """
        next_m = self.matchups[slot_id]
        if position == "a":
            next_m.team_a = team
        else:
            next_m.team_b = team

        # Reset probabilities — teams may have changed
        next_m.prob_a = next_m.prob_b = None
        next_m.pct_a = next_m.pct_b = None
        next_m.confidence = None

        self._calc(slot_id)
        updated = [slot_id]

        # If the user had already picked this matchup (e.g. bracket re-entry),
        # re-validate their pick is still a valid team, then re-cascade.
        if next_m.user_pick and next_m.winner_slot:
            if next_m.user_pick not in (next_m.team_a, next_m.team_b):
                # Their previous pick is no longer in this matchup — clear it
                next_m.user_pick = None
            else:
                updated += self._advance(
                    next_m.user_pick, next_m.winner_slot, next_m.winner_slot_position
                )

        return updated

    def unpick(self, matchup_id: str) -> list[str]:
        """
        Clear a user's pick and all downstream consequences.
        The downstream matchup slots revert to TBD.
        """
        m = self.matchups.get(matchup_id)
        if m is None or m.user_pick is None:
            return []

        m.user_pick = None
        updated = [matchup_id]

        if m.winner_slot:
            updated += self._clear_downstream(m.winner_slot, m.winner_slot_position)

        return updated

    def _clear_downstream(self, slot_id: str, position: str) -> list[str]:
        m = self.matchups[slot_id]
        if position == "a":
            m.team_a = None
        else:
            m.team_b = None

        m.prob_a = m.prob_b = None
        m.pct_a = m.pct_b = None
        m.confidence = None
        updated = [slot_id]

        if m.user_pick and m.winner_slot:
            updated += self._clear_downstream(m.winner_slot, m.winner_slot_position)
            m.user_pick = None

        return updated

    # -----------------------------------------------------------------------
    # Serialisation (for API / persistence)
    # -----------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {mid: asdict(m) for mid, m in self.matchups.items()}

    def save(self, path: Path = BRACKET_STATE_FILE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path = BRACKET_STATE_FILE) -> "Bracket":
        b = cls.__new__(cls)
        b.matchups = {}
        b._build()  # build fresh first to get structure
        if path.exists():
            with open(path) as f:
                saved = json.load(f)
            for mid, data in saved.items():
                if mid in b.matchups:
                    m = b.matchups[mid]
                    m.user_pick = data.get("user_pick")
                    # Re-cascade all picks in order to restore state
            # Replay picks in round order
            round_order = [
                "First Four", "Round of 64", "Round of 32",
                "Sweet 16", "Elite 8", "Final Four", "Championship"
            ]
            for round_name in round_order:
                for mid, data in saved.items():
                    if data.get("round_name") == round_name and data.get("user_pick"):
                        try:
                            b.pick(mid, data["user_pick"])
                        except Exception:
                            pass
        # Merge actual results if available
        if RESULTS_FILE.exists():
            with open(RESULTS_FILE) as f:
                results = json.load(f)
            for mid, res in results.items():
                if mid in b.matchups and res.get("winner"):
                    b.matchups[mid].actual_winner = res["winner"]
                    b.matchups[mid].actual_score_a = res.get("score_a")
                    b.matchups[mid].actual_score_b = res.get("score_b")
        return b

    # -----------------------------------------------------------------------
    # Display helpers
    # -----------------------------------------------------------------------

    def print_round(self, round_name: str):
        print(f"\n{'─'*65}")
        print(f"  {round_name.upper()}")
        print(f"{'─'*65}")
        for region in ["East", "West", "Midwest", "South", "National"]:
            slots = [
                m for m in self.matchups.values()
                if m.round_name == round_name and m.region == region
            ]
            if not slots:
                continue
            if round_name not in ("Final Four", "Championship"):
                print(f"  [{region}]")
            for m in slots:
                print(f"    {m.display()}")

    def print_bracket(self):
        for rnd in ["First Four", "Round of 64", "Round of 32",
                    "Sweet 16", "Elite 8", "Final Four", "Championship"]:
            self.print_round(rnd)


# ───────────────────────────────────────────────────────────────────────────
# Quick demo
# ───────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    b = Bracket()

    print("=" * 65)
    print("  2026 NCAA Tournament Bracket — Confidence Intervals")
    print("  Pick the winner in each matchup. Cascades automatically.")
    print("=" * 65)

    b.print_round("First Four")
    b.print_round("Round of 64")

    print("\n\n── Simulating user picks (First Four) ──")
    b.pick("FF_1", "UMBC")           # upset pick
    b.pick("FF_2", "Miami (OH)")
    b.pick("FF_3", "Texas")
    b.pick("FF_4", "Prairie View")

    print("After First Four picks, Round of 64 updates:")
    b.print_round("Round of 64")

    print("\n── Simulating a few Round of 64 picks ──")
    updated = b.pick("E_R1_1", "Duke")
    updated += b.pick("E_R1_2", "Ohio State")
    print(f"Updated matchup slots: {updated}")
    print()
    b.print_round("Round of 32")

    b.save()
    print(f"\nBracket state saved → {BRACKET_STATE_FILE}")
