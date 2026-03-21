"""
Post-tournament analysis engine.

Computes three views from completed matchups + actual results:
1. Signal Report Card — per-signal accuracy across completed games
2. Vegas vs Model — head-to-head comparison of model vs Vegas implied picks
3. Upset Autopsy — deep dive into every upset with per-signal breakdown
"""

from __future__ import annotations
from models.bracket import Bracket, RESULTS_FILE
from models.rule_engine import WEIGHTS
import json


def _load_results() -> dict:
    if not RESULTS_FILE.exists():
        return {}
    with open(RESULTS_FILE) as f:
        raw = json.load(f)
    return {mid: r for mid, r in raw.items()
            if isinstance(r, dict) and r.get("winner")}


def _completed_matchups(bracket: Bracket) -> list:
    """Return matchups that have actual results and valid signals."""
    results = _load_results()
    out = []
    for mid, res in results.items():
        m = bracket.matchups.get(mid)
        if m and m.signals and m.team_a and m.team_b:
            out.append((m, res))
    return out


def signal_report_card(bracket: Bracket) -> dict:
    """Grade each signal + the combined model on completed games."""
    completed = _completed_matchups(bracket)
    if not completed:
        return {"total_games": 0, "signals": [], "model": None}

    signal_names = list(WEIGHTS.keys())
    counts = {s: {"correct": 0, "total": 0, "weight": WEIGHTS[s]} for s in signal_names}
    model_correct = 0

    for m, res in completed:
        actual = res["winner"]
        # Combined model pick
        model_pick = m.team_a if m.prob_a > m.prob_b else m.team_b
        if model_pick == actual:
            model_correct += 1
        # Per-signal picks
        for sig in signal_names:
            prob_a = m.signals.get(sig)
            if prob_a is None:
                continue
            sig_pick = m.team_a if prob_a > 0.5 else m.team_b
            counts[sig]["total"] += 1
            if sig_pick == actual:
                counts[sig]["correct"] += 1

    total = len(completed)
    signals = []
    for sig in signal_names:
        c = counts[sig]
        signals.append({
            "signal": sig,
            "correct": c["correct"],
            "total": c["total"],
            "accuracy": round(c["correct"] / c["total"], 4) if c["total"] else 0,
            "weight": c["weight"],
        })
    signals.sort(key=lambda s: s["accuracy"], reverse=True)

    return {
        "total_games": total,
        "model": {
            "correct": model_correct,
            "total": total,
            "accuracy": round(model_correct / total, 4) if total else 0,
        },
        "signals": signals,
    }


def vegas_vs_model(bracket: Bracket) -> dict:
    """Head-to-head: model accuracy vs Vegas implied accuracy."""
    completed = _completed_matchups(bracket)
    if not completed:
        return {"total_games": 0, "model_record": None, "vegas_record": None, "games": []}

    games = []
    model_correct = 0
    vegas_correct = 0
    vegas_total = 0

    for m, res in completed:
        actual = res["winner"]
        model_pick = m.team_a if m.prob_a > m.prob_b else m.team_b
        model_right = model_pick == actual
        if model_right:
            model_correct += 1

        # Vegas pick from no-vig probabilities
        stats = m.raw_stats or {}
        no_vig_a = stats.get("no_vig_prob_a")
        no_vig_b = stats.get("no_vig_prob_b")

        vegas_pick = None
        vegas_conf = None
        vegas_right = None
        if no_vig_a is not None and no_vig_b is not None:
            vegas_pick = m.team_a if no_vig_a > no_vig_b else m.team_b
            vegas_conf = round(max(no_vig_a, no_vig_b), 4)
            vegas_right = vegas_pick == actual
            vegas_total += 1
            if vegas_right:
                vegas_correct += 1

        games.append({
            "matchup_id": m.id,
            "round_name": m.round_name,
            "region": m.region,
            "team_a": m.team_a,
            "team_b": m.team_b,
            "seed_a": stats.get("seed_a"),
            "seed_b": stats.get("seed_b"),
            "model_pick": model_pick,
            "model_conf": round(max(m.prob_a, m.prob_b), 4),
            "vegas_pick": vegas_pick,
            "vegas_conf": vegas_conf,
            "actual_winner": actual,
            "actual_score_a": res.get("score_a"),
            "actual_score_b": res.get("score_b"),
            "model_correct": model_right,
            "vegas_correct": vegas_right,
        })

    # Sort by disagreement games first (most interesting), then by confidence gap
    games.sort(key=lambda g: (
        g["model_correct"] == g["vegas_correct"],  # disagreements first
        -abs((g["model_conf"] or 0) - (g["vegas_conf"] or 0)),
    ))

    total = len(completed)
    return {
        "total_games": total,
        "model_record": {"correct": model_correct, "total": total,
                         "accuracy": round(model_correct / total, 4) if total else 0},
        "vegas_record": {"correct": vegas_correct, "total": vegas_total,
                         "accuracy": round(vegas_correct / vegas_total, 4) if vegas_total else 0},
        "games": games,
    }


def upset_autopsy(bracket: Bracket) -> dict:
    """Analyze every upset — which signals saw it coming, which missed."""
    completed = _completed_matchups(bracket)
    if not completed:
        return {"total_upsets": 0, "total_games": 0, "upsets": []}

    upsets = []
    for m, res in completed:
        stats = m.raw_stats or {}
        seed_a = stats.get("seed_a", 8)
        seed_b = stats.get("seed_b", 8)
        actual = res["winner"]

        # Determine favorite (lower seed number = higher seed)
        if seed_a == seed_b:
            continue  # same seed, can't be an upset
        if seed_a < seed_b:
            favorite, underdog = m.team_a, m.team_b
            fav_seed, dog_seed = seed_a, seed_b
        else:
            favorite, underdog = m.team_b, m.team_a
            fav_seed, dog_seed = seed_b, seed_a

        if actual == favorite:
            continue  # no upset

        # Upset occurred — analyze each signal
        signal_breakdown = []
        for sig, prob_a in m.signals.items():
            sig_pick = m.team_a if prob_a > 0.5 else m.team_b
            # Did this signal pick the underdog (the actual winner)?
            called_upset = sig_pick == underdog
            signal_breakdown.append({
                "signal": sig,
                "prob_a": round(prob_a, 4),
                "picked": sig_pick,
                "called_upset": called_upset,
                "weight": WEIGHTS.get(sig, 0),
            })

        model_pick = m.team_a if m.prob_a > m.prob_b else m.team_b
        upsets.append({
            "matchup_id": m.id,
            "round_name": m.round_name,
            "region": m.region,
            "favorite": favorite,
            "favorite_seed": fav_seed,
            "underdog": underdog,
            "underdog_seed": dog_seed,
            "actual_score_a": res.get("score_a"),
            "actual_score_b": res.get("score_b"),
            "model_pick": model_pick,
            "model_had_upset": model_pick == underdog,
            "model_confidence": round(max(m.prob_a, m.prob_b), 4),
            "signals": signal_breakdown,
        })

    # Biggest surprises first (model was most confident in the favorite)
    upsets.sort(key=lambda u: u["model_confidence"], reverse=True)

    return {
        "total_upsets": len(upsets),
        "total_games": len(completed),
        "upset_rate": round(len(upsets) / len(completed), 4) if completed else 0,
        "upsets": upsets,
    }


def full_analysis(bracket: Bracket) -> dict:
    """Return all three analysis sections in one payload."""
    return {
        "signal_report_card": signal_report_card(bracket),
        "vegas_vs_model": vegas_vs_model(bracket),
        "upset_autopsy": upset_autopsy(bracket),
    }
