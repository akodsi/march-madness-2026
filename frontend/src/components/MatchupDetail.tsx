'use client'
import { useState } from 'react'
import { Matchup, RedditPost, ChampionLikelihood, ChampionCheck } from '@/lib/types'
import { getLogoUrl, getInitials } from '@/lib/teamLogos'

interface Props {
  matchup: Matchup
  onPick: (id: string, winner: string) => void
  onUnpick: (id: string) => void
  onClose: () => void
}

function Logo({ name, size = 48 }: { name: string; size?: number }) {
  const [failed, setFailed] = useState(false)
  const url = getLogoUrl(name)

  if (!url || failed) {
    return (
      <div
        className="rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0"
        style={{ width: size, height: size }}
      >
        <span className="text-sm font-bold text-slate-300">{getInitials(name)}</span>
      </div>
    )
  }

  return (
    <img
      src={url}
      alt={name}
      width={size}
      height={size}
      className="object-contain flex-shrink-0"
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  )
}

/** Ordinal suffix for rank numbers (1st, 2nd, 3rd, 4th…) */
function getSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}

/** Convert a signal probability (0–1) to a descriptive edge string */
function signalEdge(prob: number): { edge: string; color: string } {
  if (prob >= 0.75) return { edge: 'Strong advantage', color: 'text-emerald-400' }
  if (prob >= 0.60) return { edge: 'Clear advantage', color: 'text-blue-400' }
  if (prob >= 0.52) return { edge: 'Slight edge', color: 'text-yellow-400' }
  if (prob <= 0.25) return { edge: 'Strong disadvantage', color: 'text-red-400' }
  if (prob <= 0.40) return { edge: 'Clear disadvantage', color: 'text-red-400' }
  if (prob <= 0.48) return { edge: 'Slight disadvantage', color: 'text-orange-400' }
  return { edge: 'Even', color: 'text-slate-400' }
}

function buildCase(
  _teamName: string,
  isA: boolean,
  signals: Record<string, number>,
  raw: NonNullable<Matchup['raw_stats']>
): string[] {
  const bullets: string[] = []

  const srs    = isA ? signals.srs    : 1 - signals.srs
  const sos    = isA ? signals.sos    : 1 - signals.sos
  const seed   = isA ? signals.seed   : 1 - signals.seed
  const travel = isA ? signals.travel : 1 - signals.travel

  const srsVal    = isA ? raw.srs_a : raw.srs_b
  const sosVal    = isA ? raw.sos_a : raw.sos_b
  const seedVal   = isA ? raw.seed_a : raw.seed_b
  const distVal   = isA ? raw.distance_a : raw.distance_b
  const wins      = isA ? raw.wins_a : raw.wins_b
  const losses    = isA ? raw.losses_a : raw.losses_b

  // Record
  bullets.push(`Season record: ${wins}–${losses}`)

  // SRS
  if (srs >= 0.55) {
    bullets.push(`Stronger overall team quality — SRS of ${srsVal > 0 ? '+' : ''}${srsVal} (higher is better)`)
  } else if (srs <= 0.45) {
    bullets.push(`Lower overall team quality — SRS of ${srsVal} vs opponent's higher rating`)
  } else {
    bullets.push(`Similar team quality to opponent — SRS of ${srsVal > 0 ? '+' : ''}${srsVal}`)
  }

  // SOS
  if (sos >= 0.55) {
    bullets.push(`Faced a tougher schedule — SOS of ${sosVal > 0 ? '+' : ''}${sosVal}, battle-tested`)
  } else if (sos <= 0.45) {
    bullets.push(`Easier schedule this season — SOS of ${sosVal}, may face tougher competition here`)
  } else {
    bullets.push(`Similar schedule difficulty — SOS of ${sosVal > 0 ? '+' : ''}${sosVal}`)
  }

  // Seed history
  const otherSeed = isA ? raw.seed_b : raw.seed_a
  if (seed >= 0.60) {
    bullets.push(`Historical edge: as a ${seedVal}-seed vs ${otherSeed}-seed, wins ~${Math.round(seed * 100)}% historically`)
  } else if (seed <= 0.40) {
    bullets.push(`Historical underdog: as a ${seedVal}-seed vs ${otherSeed}-seed, wins ~${Math.round(seed * 100)}% historically`)
  } else {
    bullets.push(`Roughly even historically vs ${otherSeed}-seeds (~${Math.round(seed * 100)}% win rate)`)
  }

  // Travel
  if (distVal !== undefined && distVal !== null) {
    if (travel >= 0.60) {
      bullets.push(`Closer to the venue — only ${distVal} miles away, near-home advantage`)
    } else if (travel <= 0.40) {
      bullets.push(`Long travel — ${distVal} miles to nearest venue, opponent plays closer`)
    } else {
      bullets.push(`Similar travel distance — ${distVal} miles to nearest venue`)
    }
  }

  // Momentum
  const last10Wins   = isA ? raw.last10_wins_a   : raw.last10_wins_b
  const last10Losses = isA ? raw.last10_losses_a : raw.last10_losses_b
  const streak       = isA ? raw.win_streak_a    : raw.win_streak_b
  const margin       = isA ? raw.last10_margin_a : raw.last10_margin_b
  const momentumSig  = signals.momentum !== undefined ? (isA ? signals.momentum : 1 - signals.momentum) : undefined

  if (last10Wins !== undefined && last10Losses !== undefined) {
    const marginStr = margin !== undefined ? `, avg margin ${margin > 0 ? '+' : ''}${margin.toFixed(1)} ppg` : ''
    if (momentumSig !== undefined && momentumSig >= 0.55) {
      bullets.push(`Hot team — ${last10Wins}-${last10Losses} in last 10${marginStr}`)
    } else if (momentumSig !== undefined && momentumSig <= 0.45) {
      bullets.push(`Cold stretch — ${last10Wins}-${last10Losses} in last 10${marginStr}`)
    } else {
      bullets.push(`Last 10 games: ${last10Wins}-${last10Losses}${marginStr}`)
    }
  }
  if (streak !== undefined && Math.abs(streak) >= 3) {
    bullets.push(`On a ${streak > 0 ? `${streak}-game win` : `${Math.abs(streak)}-game losing`} streak`)
  }

  // Injuries
  const healthScore = isA ? raw.health_score_a : raw.health_score_b
  const keyOut      = isA ? raw.key_players_out_a : raw.key_players_out_b
  if (healthScore !== undefined) {
    const healthPct = Math.round(healthScore * 100)
    if (healthPct >= 90) {
      bullets.push(`Healthy roster heading into the tournament`)
    } else if (keyOut && keyOut.length > 0) {
      bullets.push(`Injury concerns: ${keyOut.join(', ')} out (health ${healthPct}%)`)
    } else if (healthPct < 70) {
      bullets.push(`Significant injuries — roster health at ${healthPct}%`)
    }
  }

  return bullets
}

const SIGNAL_LABELS: Record<string, string> = {
  srs:      'Team Quality (SRS)',
  sos:      'Schedule Strength',
  seed:     'Seed History',
  travel:   'Travel Advantage',
  momentum: 'Momentum',
  injuries: 'Injury Impact',
}

const WEIGHTS: Record<string, number> = {
  srs: 30, sos: 25, seed: 10, travel: 10, momentum: 15, injuries: 10,
}

export default function MatchupDetail({ matchup, onPick, onUnpick, onClose }: Props) {
  const { id, team_a, team_b, pct_a, pct_b, confidence, user_pick, signals, raw_stats, round_name, region } = matchup

  const ready = team_a !== null && team_b !== null

  function handlePick(team: string) {
    if (user_pick === team) onUnpick(id)
    else onPick(id, team)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-3 border-b border-slate-800">
          <div>
            <p className="text-[10px] uppercase tracking-widest text-slate-500">{region} · {round_name}</p>
            <h2 className="text-base font-bold text-white mt-0.5">Matchup Breakdown</h2>
          </div>
          <button
            onClick={onClose}
            className="text-slate-500 hover:text-white text-xl leading-none transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Team headers with win % */}
        <div className="grid grid-cols-2 gap-4 px-6 py-5 border-b border-slate-800">
          {[
            { name: team_a, pct: pct_a, isA: true },
            { name: team_b, pct: pct_b, isA: false },
          ].map(({ name, pct, isA }) => {
            const isPicked = user_pick === name
            const isLoser  = user_pick !== null && user_pick !== name
            const seed = isA ? raw_stats?.seed_a : raw_stats?.seed_b
            return (
              <div
                key={name ?? (isA ? 'tbd-a' : 'tbd-b')}
                className={[
                  'flex flex-col items-center gap-2 p-4 rounded-lg border transition-all',
                  isPicked ? 'bg-amber-500/10 border-amber-500/50' : 'bg-slate-800 border-slate-700',
                  isLoser  ? 'opacity-40' : '',
                ].join(' ')}
              >
                {name && <Logo name={name} size={52} />}
                <div className="flex items-center gap-1.5">
                  {seed !== undefined && seed !== null && (
                    <span className="text-[10px] font-bold text-slate-500 bg-slate-700 rounded-full w-5 h-5 flex items-center justify-center flex-shrink-0">{seed}</span>
                  )}
                  <p className="text-sm font-bold text-center text-white leading-tight">{name ?? 'TBD'}</p>
                </div>
                {pct !== null && (
                  <div className="text-2xl font-black" style={{ color: isPicked ? '#f59e0b' : '#e2e8f0' }}>
                    {pct}%
                  </div>
                )}
                {confidence && ready && (
                  <span className="text-[10px] uppercase tracking-wide text-slate-400">{confidence}</span>
                )}
                {ready && name && (
                  <button
                    onClick={() => handlePick(name)}
                    className={[
                      'mt-1 px-4 py-1.5 rounded text-xs font-semibold uppercase tracking-wide transition-colors',
                      isPicked
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/40'
                        : 'bg-blue-600 hover:bg-blue-500 text-white',
                    ].join(' ')}
                  >
                    {isPicked ? 'Undo pick' : 'Pick this team'}
                  </button>
                )}
              </div>
            )
          })}
        </div>

        {/* Signal bar breakdown */}
        {signals && ready && (
          <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">Signal Breakdown</h3>
            <div className="space-y-2.5">
              {Object.entries(signals).map(([key, probA]) => {
                const pctA  = Math.round(probA * 100)
                const pctB  = 100 - pctA
                const { edge: edgeA, color: colorA } = signalEdge(probA)
                const weight = WEIGHTS[key] ?? 0

                const dominantColor = (pct: number) =>
                  pct >= 75 ? 'bg-emerald-600' : pct >= 60 ? 'bg-blue-600' : pct >= 52 ? 'bg-yellow-500' : 'bg-slate-600'
                const barColorA = pctA >= pctB ? dominantColor(pctA) : 'bg-slate-800'
                const barColorB = pctB >  pctA ? dominantColor(pctB) : 'bg-slate-800'

                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">{SIGNAL_LABELS[key] ?? key}</span>
                      <span className="text-[10px] text-slate-600">{weight}% weight</span>
                    </div>
                    <div className="flex h-4 rounded overflow-hidden text-[9px] font-bold gap-px bg-slate-900">
                      <div
                        className={`flex items-center justify-center transition-all ${barColorA} ${pctA > pctB ? 'text-white' : 'text-slate-500'}`}
                        style={{ width: `${pctA}%` }}
                      >
                        {pctA > 20 ? `${pctA}%` : ''}
                      </div>
                      <div
                        className={`flex items-center justify-center transition-all ${barColorB} ${pctB > pctA ? 'text-white' : 'text-slate-500'}`}
                        style={{ width: `${pctB}%` }}
                      >
                        {pctB > 20 ? `${pctB}%` : ''}
                      </div>
                    </div>
                    <div className="flex justify-between text-[10px] mt-0.5">
                      <span className={colorA}>{edgeA}</span>
                      <span className="text-slate-500">{team_a?.split(' ')[0]} ← → {team_b?.split(' ')[0]}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Momentum section — only render when pipeline has been run (at least 1 tracked game) */}
        {raw_stats && ready && ((raw_stats.last10_wins_a ?? 0) + (raw_stats.last10_losses_a ?? 0) > 0) && (
          <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">Momentum (Last 10 Games)</h3>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, isA: true },
                { name: team_b, isA: false },
              ] as const).map(({ name, isA }) => {
                const wins   = isA ? raw_stats.last10_wins_a   : raw_stats.last10_wins_b
                const losses = isA ? raw_stats.last10_losses_a : raw_stats.last10_losses_b
                const streak = isA ? raw_stats.win_streak_a    : raw_stats.win_streak_b
                const margin = isA ? raw_stats.last10_margin_a : raw_stats.last10_margin_b
                const isPicked = user_pick === name
                const hasData = (wins ?? 0) + (losses ?? 0) > 0
                const winsNum = wins ?? 0
                return (
                  <div key={isA ? 'mom-a' : 'mom-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <p className="text-xs font-semibold text-white mb-2 truncate">{name}</p>
                    {!hasData ? (
                      <p className="text-xs text-slate-500 italic">No schedule data available</p>
                    ) : (
                      <div className="space-y-1.5 text-xs">
                        <div className="flex justify-between">
                          <span className="text-slate-400">Last 10</span>
                          <span className={`font-bold ${winsNum >= 7 ? 'text-emerald-400' : winsNum >= 5 ? 'text-yellow-400' : 'text-red-400'}`}>
                            {wins}–{losses}
                          </span>
                        </div>
                        {streak !== undefined && streak !== 0 && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">Streak</span>
                            <span className={`font-bold ${streak > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {streak > 0 ? `W${streak}` : `L${Math.abs(streak)}`}
                            </span>
                          </div>
                        )}
                        {margin !== undefined && margin !== 0 && (
                          <div className="flex justify-between">
                            <span className="text-slate-400">Avg Margin</span>
                            <span className={`font-bold ${margin > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {margin > 0 ? '+' : ''}{margin.toFixed(1)} ppg
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Injuries section — only render when pipeline has been run (any team not at default 100%) or has injuries */}
        {raw_stats && ready && ((raw_stats.health_score_a ?? 1) < 1 || (raw_stats.health_score_b ?? 1) < 1 || (raw_stats.injured_count_a ?? 0) > 0 || (raw_stats.injured_count_b ?? 0) > 0) && (
          <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">Injury Report</h3>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, isA: true },
                { name: team_b, isA: false },
              ] as const).map(({ name, isA }) => {
                const health  = isA ? raw_stats.health_score_a  : raw_stats.health_score_b
                const count   = isA ? raw_stats.injured_count_a : raw_stats.injured_count_b
                const keyOut  = isA ? raw_stats.key_players_out_a : raw_stats.key_players_out_b
                const healthPct = Math.round((health ?? 1) * 100)
                const healthColor = healthPct >= 90 ? 'bg-emerald-500' : healthPct >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                const isPicked = user_pick === name
                return (
                  <div key={isA ? 'inj-a' : 'inj-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <p className="text-xs font-semibold text-white mb-2 truncate">{name}</p>
                    <div className="space-y-1.5 text-xs">
                      <div>
                        <div className="flex justify-between mb-1">
                          <span className="text-slate-400">Health Score</span>
                          <span className="font-bold text-white">{healthPct}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div className={`h-full rounded-full ${healthColor}`} style={{ width: `${healthPct}%` }} />
                        </div>
                      </div>
                      {count !== undefined && count > 0 ? (
                        <div className="flex justify-between">
                          <span className="text-slate-400">Injured</span>
                          <span className="font-bold text-orange-400">{count} player{count !== 1 ? 's' : ''}</span>
                        </div>
                      ) : (
                        <p className="text-emerald-400">No significant injuries</p>
                      )}
                      {keyOut && keyOut.length > 0 && (
                        <div>
                          <span className="text-slate-400 block mb-0.5">Key players out:</span>
                          <span className="text-red-400 leading-snug">{keyOut.join(', ')}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Commentary section — only render when pipeline has populated actual content */}
        {matchup.commentary && ready && (matchup.commentary.team_a?.team_context || matchup.commentary.team_b?.team_context || matchup.commentary.team_a?.headlines?.length || matchup.commentary.team_b?.headlines?.length) && (
          <div className="px-6 py-4 border-b border-slate-800">
            <h3 className="text-xs uppercase tracking-widest text-slate-500 mb-3">ESPN Coverage</h3>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, data: matchup.commentary.team_a, isA: true },
                { name: team_b, data: matchup.commentary.team_b, isA: false },
              ] as const).map(({ name, data, isA }) => {
                if (!data) return null
                const isPicked = user_pick === name
                const sentimentColor = data.sentiment === 'positive' ? 'text-emerald-400' : data.sentiment === 'negative' ? 'text-red-400' : 'text-slate-400'
                const sentimentLabel = data.sentiment === 'positive' ? '↑ Positive' : data.sentiment === 'negative' ? '↓ Negative' : '— Neutral'
                return (
                  <div key={isA ? 'com-a' : 'com-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <div className="flex items-center justify-between mb-1.5">
                      <p className="text-xs font-semibold text-white truncate">{name}</p>
                      <span className={`text-[10px] font-bold flex-shrink-0 ml-1 ${sentimentColor}`}>{sentimentLabel}</span>
                    </div>
                    {data.team_context && (
                      <p className="text-[10px] text-slate-400 mb-2">{data.team_context}</p>
                    )}
                    {data.headlines && data.headlines.length > 0 && (
                      <div className="space-y-2">
                        {data.headlines.slice(0, 2).map((h, i) => (
                          <div key={i} className="border-l-2 border-slate-600 pl-2">
                            <p className="text-[10px] font-medium text-slate-300 leading-snug">{h.title}</p>
                            {h.summary && <p className="text-[9px] text-slate-500 mt-0.5 leading-snug">{h.summary}</p>}
                            <p className="text-[9px] text-slate-600 mt-0.5">{h.source} · {h.date}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Google News section */}
        {matchup.commentary && ready && (
          (matchup.commentary.team_a?.google_news?.length || matchup.commentary.team_b?.google_news?.length ||
           matchup.commentary.team_a?.google_news_summary || matchup.commentary.team_b?.google_news_summary)
        ) && (
          <div className="px-6 py-4 border-b border-slate-800">
            <div className="flex items-baseline gap-2 mb-3">
              <h3 className="text-xs uppercase tracking-widest text-slate-500">Google News</h3>
              <span className="text-[9px] text-slate-600 normal-case tracking-normal">recent headlines</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, data: matchup.commentary.team_a, isA: true },
                { name: team_b, data: matchup.commentary.team_b, isA: false },
              ] as const).map(({ name, data, isA }) => {
                if (!data) return null
                const isPicked = user_pick === name
                const hasContent = (data.google_news?.length ?? 0) > 0 || !!data.google_news_summary
                return (
                  <div key={isA ? 'gn-a' : 'gn-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <p className="text-xs font-semibold text-white mb-2 truncate">{name}</p>
                    {!hasContent ? (
                      <p className="text-xs text-slate-500 italic">No recent news found</p>
                    ) : (
                      <div className="space-y-2">
                        {data.google_news_summary && (
                          <div className="border-l-2 border-blue-500/40 bg-blue-500/5 rounded-r px-2 py-1.5">
                            <p className="text-[10px] text-slate-300 leading-snug italic">{data.google_news_summary}</p>
                          </div>
                        )}
                        {data.google_news && data.google_news.length > 0 && (
                          <div className="space-y-2">
                            {data.google_news.slice(0, 2).map((h, i) => (
                              <div key={i} className="border-l-2 border-slate-600 pl-2">
                                <p className="text-[10px] font-medium text-slate-300 leading-snug">{h.title}</p>
                                <p className="text-[9px] text-slate-500 mt-0.5">{h.source} · {h.date}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Reddit r/collegebasketball section */}
        {matchup.commentary && ready && (
          (matchup.commentary.team_a?.reddit_posts?.length || matchup.commentary.team_b?.reddit_posts?.length ||
           matchup.commentary.team_a?.reddit_summary || matchup.commentary.team_b?.reddit_summary)
        ) && (
          <div className="px-6 py-4 border-b border-slate-800">
            <div className="flex items-baseline gap-2 mb-3">
              <h3 className="text-xs uppercase tracking-widest text-slate-500">r/CollegeBasketball</h3>
              <span className="text-[9px] text-slate-600 normal-case tracking-normal">community posts</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, data: matchup.commentary.team_a, isA: true },
                { name: team_b, data: matchup.commentary.team_b, isA: false },
              ] as const).map(({ name, data, isA }) => {
                if (!data) return null
                const isPicked = user_pick === name
                const posts: RedditPost[] = data.reddit_posts ?? []
                const hasContent = posts.length > 0 || !!data.reddit_summary
                return (
                  <div key={isA ? 'rd-a' : 'rd-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <p className="text-xs font-semibold text-white mb-2 truncate">{name}</p>
                    {!hasContent ? (
                      <p className="text-xs text-slate-500 italic">No recent posts found</p>
                    ) : (
                      <div className="space-y-2">
                        {data.reddit_summary && (
                          <div className="border-l-2 border-orange-500/40 bg-orange-500/5 rounded-r px-2 py-1.5">
                            <p className="text-[10px] text-slate-300 leading-snug italic">{data.reddit_summary}</p>
                          </div>
                        )}
                        {posts.length > 0 && (
                          <div className="space-y-1.5">
                            {posts.slice(0, 3).map((p, i) => (
                              <div key={i} className="border-l-2 border-orange-500/30 pl-2">
                                <p className="text-[10px] font-medium text-slate-300 leading-snug">{p.title}</p>
                                <p className="text-[9px] text-orange-400 mt-0.5">▲ {p.score.toLocaleString()} · {p.date}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Champion Profile section */}
        {matchup.champion_likelihood && ready && team_a && team_b && (
          <div className="px-6 py-4 border-b border-slate-800">
            <div className="flex items-baseline gap-2 mb-3">
              <h3 className="text-xs uppercase tracking-widest text-slate-500">Champion Profile</h3>
              <span className="text-[9px] text-slate-600 normal-case tracking-normal">historically-validated patterns</span>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {([
                { name: team_a, data: matchup.champion_likelihood.team_a, isA: true },
                { name: team_b, data: matchup.champion_likelihood.team_b, isA: false },
              ] as const).map(({ name, data, isA }) => {
                if (!data) return null
                const isPicked = user_pick === name
                const totalChecks = data.checks.length
                const passedChecks = data.checks.filter((c: ChampionCheck) => c.passed === true).length
                const fractionColor = data.hard_filter_failed
                  ? 'text-red-400'
                  : passedChecks >= totalChecks * 0.6
                    ? 'text-emerald-400'
                    : 'text-yellow-400'

                // Proximity rules show rank values; binary rules show ✓/✗
                const PROXIMITY_RULES = new Set([
                  'torvik_overall_top25', 'torvik_overall_top6',
                  'torvik_adjD_top25', 'torvik_adjD_top7',
                  'torvik_adjO_top40', 'torvik_adjO_top21',
                ])

                return (
                  <div key={isA ? 'champ-a' : 'champ-b'} className={`rounded-lg p-3 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs font-semibold text-white truncate">{name}</p>
                      <span className={`text-xs font-bold ${fractionColor}`}>
                        {passedChecks}/{totalChecks}
                      </span>
                    </div>

                    {data.hard_filter_failed && (
                      <div className="bg-red-500/10 border border-red-500/30 rounded px-2 py-1.5 mb-2">
                        <p className="text-[10px] font-bold text-red-400">ELIMINATED — No champion has ever failed these checks</p>
                      </div>
                    )}

                    <div className="space-y-1">
                      {data.checks.map((check: ChampionCheck) => {
                        const isProximity = PROXIMITY_RULES.has(check.rule_id)
                        const passed = check.passed
                        const isHardFail = check.is_hard && passed === false

                        return (
                          <div
                            key={check.rule_id}
                            className={`flex items-center justify-between gap-2 text-[10px] py-0.5 ${isHardFail ? 'bg-red-500/5 -mx-1 px-1 rounded' : ''}`}
                            title={check.detail}
                          >
                            <span className={`truncate ${isHardFail ? 'text-red-400 font-semibold' : 'text-slate-400'}`}>
                              {check.label}
                            </span>
                            {isProximity && check.value !== null ? (
                              <span className={`font-bold flex-shrink-0 ${
                                passed === true ? 'text-emerald-400' : passed === false ? (isHardFail ? 'text-red-400' : 'text-red-400/70') : 'text-slate-500'
                              }`}>
                                {check.value}{check.value !== null ? getSuffix(check.value) : ''}
                              </span>
                            ) : (
                              <span className={`flex-shrink-0 ${
                                passed === true ? 'text-emerald-400' : passed === false ? (isHardFail ? 'text-red-400' : 'text-red-400/70') : 'text-slate-500'
                              }`}>
                                {passed === true ? '✓' : passed === false ? '✗' : '—'}
                              </span>
                            )}
                          </div>
                        )
                      })}
                    </div>

                    <div className="mt-2 pt-2 border-t border-slate-700/50 flex items-center justify-between">
                      <span className="text-[10px] text-slate-500">Score</span>
                      <span className={`text-xs font-bold ${data.score >= 60 ? 'text-emerald-400' : data.score >= 30 ? 'text-yellow-400' : 'text-red-400'}`}>
                        {data.score}
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Case for each team */}
        {signals && raw_stats && ready && team_a && team_b && (
          <div className="grid grid-cols-2 gap-4 px-6 py-4">
            {[
              { name: team_a, isA: true },
              { name: team_b, isA: false },
            ].map(({ name, isA }) => {
              const bullets = buildCase(name, isA, signals, raw_stats)
              const isPicked = user_pick === name

              return (
                <div key={name} className={`rounded-lg p-4 ${isPicked ? 'bg-amber-500/5 border border-amber-500/20' : 'bg-slate-800/60'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Logo name={name} size={24} />
                    <p className="text-sm font-bold text-white">The case for {name}</p>
                  </div>
                  <ul className="space-y-1.5">
                    {bullets.map((b, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-xs text-slate-300 leading-snug">
                        <span className="text-slate-500 mt-0.5 flex-shrink-0">•</span>
                        {b}
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        )}

        {!ready && (
          <div className="px-6 py-8 text-center text-slate-500 text-sm">
            Waiting on earlier picks before this matchup is set.
          </div>
        )}
      </div>
    </div>
  )
}
