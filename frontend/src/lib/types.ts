export interface Matchup {
  id: string
  round_name: string
  region: string
  team_a: string | null
  team_b: string | null
  prob_a: number | null
  prob_b: number | null
  pct_a: number | null
  pct_b: number | null
  confidence: string | null
  user_pick: string | null
  winner_slot: string | null
  winner_slot_position: string | null
  signals: Record<string, number> | null
  raw_stats: {
    srs_a: number; srs_b: number
    sos_a: number; sos_b: number
    seed_a: number; seed_b: number
    wins_a: number; wins_b: number
    losses_a: number; losses_b: number
    distance_a: number; distance_b: number
  } | null
}

export type BracketData = Record<string, Matchup>

export type Region = 'East' | 'West' | 'Midwest' | 'South'
export type Direction = 'ltr' | 'rtl'

export const ROUND_ORDER = [
  'First Four',
  'Round of 64',
  'Round of 32',
  'Sweet 16',
  'Elite 8',
  'Final Four',
  'Championship',
]

export const CONFIDENCE_COLORS: Record<string, string> = {
  'Heavy Favorite': 'text-emerald-400',
  'Clear Favorite':  'text-blue-400',
  'Slight Edge':     'text-yellow-400',
  'Toss-Up':         'text-slate-400',
}
