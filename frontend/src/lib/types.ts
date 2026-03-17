export interface Headline {
  title: string
  summary: string
  source: string
  date: string
}

export interface RedditPost {
  title: string
  score: number
  date: string
}

export interface TeamCommentary {
  headlines: Headline[]
  team_context: string
  sentiment: 'positive' | 'neutral' | 'negative'
  google_news?: Headline[]
  google_news_summary?: string
  reddit_posts?: RedditPost[]
  reddit_summary?: string
}

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
    // Momentum
    last10_wins_a?: number; last10_wins_b?: number
    last10_losses_a?: number; last10_losses_b?: number
    win_streak_a?: number; win_streak_b?: number
    last10_margin_a?: number; last10_margin_b?: number
    momentum_score_a?: number; momentum_score_b?: number
    // Injuries
    health_score_a?: number; health_score_b?: number
    injured_count_a?: number; injured_count_b?: number
    key_players_out_a?: string[]; key_players_out_b?: string[]
  } | null
  commentary: {
    team_a: TeamCommentary
    team_b: TeamCommentary
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

export const CONFIDENCE_PILL: Record<string, string> = {
  'Heavy Favorite': 'text-emerald-400 bg-emerald-400/10',
  'Clear Favorite':  'text-blue-400 bg-blue-400/10',
  'Slight Edge':     'text-yellow-400 bg-yellow-400/10',
  'Toss-Up':         'text-slate-400 bg-slate-400/10',
}
