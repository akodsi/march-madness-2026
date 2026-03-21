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

export interface ChampionCheck {
  rule_id: string
  label: string
  passed: boolean | null
  value: number | null
  threshold: number
  detail: string
  points: number
  is_hard: boolean
}

export interface ChampionLikelihood {
  team: string
  score: number
  checks: ChampionCheck[]
  hard_filter_failed: boolean
  reasons: string[]
  warnings: string[]
  seed?: number
  region?: string
  raw_values: {
    torvik_overall_rank: number | null
    torvik_adjO_rank: number | null
    torvik_adjD_rank: number | null
    torvik_adjOE: number | null
    torvik_adjDE: number | null
    torvik_adjEM: number | null
    ap_rank: number | null
  }
}

export interface UpsetAlert {
  active: boolean
  underdog: string
  underdog_adjD_rank: number
  favorite: string
  favorite_adjD_rank: number | null
  seed_gap: number
  nudge_pct: number
  reason: string
}

export interface VegasDisagreement {
  level: 'agree' | 'disagree_winner' | 'disagree_confidence'
  model_prob_a: number
  vegas_prob_a: number
  diff_pct: number
  model_favors?: string
  vegas_favors?: string
  message: string
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
    // Torvik efficiency
    torvik_adjEM_a?: number | null; torvik_adjEM_b?: number | null
    torvik_adjOE_a?: number | null; torvik_adjOE_b?: number | null
    torvik_adjDE_a?: number | null; torvik_adjDE_b?: number | null
    torvik_overall_rank_a?: number | null; torvik_overall_rank_b?: number | null
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
    // Vegas odds (display only)
    moneyline_a?: number; moneyline_b?: number
    spread_a?: number; spread_b?: number
    implied_prob_a?: number; implied_prob_b?: number
    no_vig_prob_a?: number; no_vig_prob_b?: number
    odds_source?: string
  } | null
  commentary: {
    team_a: TeamCommentary
    team_b: TeamCommentary
  } | null
  champion_likelihood: {
    team_a: ChampionLikelihood
    team_b: ChampionLikelihood
  } | null
  upset_alert?: UpsetAlert | null
  vegas_disagreement?: VegasDisagreement | null
}

export type BracketData = Record<string, Matchup>

// ── Post-Tournament Analysis Types ──────────────────────────────────

export interface SignalGrade {
  signal: string
  correct: number
  total: number
  accuracy: number
  weight: number
}

export interface AnalysisRecord {
  correct: number
  total: number
  accuracy: number
}

export interface VegasGame {
  matchup_id: string
  round_name: string
  region: string
  team_a: string
  team_b: string
  seed_a: number | null
  seed_b: number | null
  model_pick: string
  model_conf: number
  vegas_pick: string | null
  vegas_conf: number | null
  actual_winner: string
  actual_score_a: number | null
  actual_score_b: number | null
  model_correct: boolean
  vegas_correct: boolean | null
}

export interface UpsetSignal {
  signal: string
  prob_a: number
  picked: string
  called_upset: boolean
  weight: number
}

export interface UpsetDetail {
  matchup_id: string
  round_name: string
  region: string
  favorite: string
  favorite_seed: number
  underdog: string
  underdog_seed: number
  actual_score_a: number | null
  actual_score_b: number | null
  model_pick: string
  model_had_upset: boolean
  model_confidence: number
  signals: UpsetSignal[]
}

export interface AnalysisData {
  signal_report_card: {
    total_games: number
    model: AnalysisRecord | null
    signals: SignalGrade[]
  }
  vegas_vs_model: {
    total_games: number
    model_record: AnalysisRecord | null
    vegas_record: AnalysisRecord | null
    games: VegasGame[]
  }
  upset_autopsy: {
    total_upsets: number
    total_games: number
    upset_rate: number
    upsets: UpsetDetail[]
  }
}

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
