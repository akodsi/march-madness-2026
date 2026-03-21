import sys
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent))
from models.bracket import Bracket, BRACKET_STATE_FILE
from models.champion_rules import score_all_teams
from models.analysis_engine import full_analysis

app = FastAPI(title="March Madness Predictor 2026")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_bracket: Optional[Bracket] = None


def get_bracket() -> Bracket:
    global _bracket
    if _bracket is None:
        _bracket = Bracket.load()
    return _bracket


class PickRequest(BaseModel):
    winner: str


@app.get("/bracket")
def read_bracket():
    return get_bracket().to_dict()


@app.post("/bracket/reset")
def reset_bracket():
    global _bracket
    _bracket = Bracket()
    _bracket.save()
    return _bracket.to_dict()


@app.post("/bracket/{matchup_id}/pick")
def make_pick(matchup_id: str, body: PickRequest):
    b = get_bracket()
    try:
        updated = b.pick(matchup_id, body.winner)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    b.save()
    return {"updated": updated, "bracket": b.to_dict()}


@app.delete("/bracket/{matchup_id}/pick")
def undo_pick(matchup_id: str):
    b = get_bracket()
    updated = b.unpick(matchup_id)
    b.save()
    return {"updated": updated, "bracket": b.to_dict()}


@app.get("/champion-likelihood")
def champion_likelihood():
    return score_all_teams()


@app.get("/analysis")
def analysis():
    return full_analysis(get_bracket())
