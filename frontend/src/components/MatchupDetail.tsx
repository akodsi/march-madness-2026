'use client'
import { useState } from 'react'
import { Matchup } from '@/lib/types'
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
  teamName: string,
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

  return bullets
}

const SIGNAL_LABELS: Record<string, string> = {
  srs:    'Team Quality (SRS)',
  sos:    'Schedule Strength',
  seed:   'Seed History',
  travel: 'Travel Advantage',
}

const WEIGHTS: Record<string, number> = {
  srs: 40, sos: 30, seed: 15, travel: 15,
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
                <p className="text-sm font-bold text-center text-white leading-tight">{name ?? 'TBD'}</p>
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
                const probB = 1 - probA
                const pctA  = Math.round(probA * 100)
                const pctB  = 100 - pctA
                const { edge: edgeA, color: colorA } = signalEdge(probA)
                const weight = WEIGHTS[key] ?? 0

                return (
                  <div key={key}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-slate-400">{SIGNAL_LABELS[key] ?? key}</span>
                      <span className="text-[10px] text-slate-600">{weight}% weight</span>
                    </div>
                    <div className="flex h-4 rounded overflow-hidden text-[9px] font-bold">
                      <div
                        className={`flex items-center justify-center bg-slate-700 transition-all ${pctA > pctB ? 'text-white' : 'text-slate-400'}`}
                        style={{ width: `${pctA}%` }}
                      >
                        {pctA > 20 ? `${pctA}%` : ''}
                      </div>
                      <div
                        className={`flex items-center justify-center bg-slate-600 transition-all ${pctB > pctA ? 'text-white' : 'text-slate-400'}`}
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

        {/* Case for each team */}
        {signals && raw_stats && ready && team_a && team_b && (
          <div className="grid grid-cols-2 gap-4 px-6 py-4">
            {[
              { name: team_a, isA: true },
              { name: team_b, isA: false },
            ].map(({ name, isA }) => {
              const bullets = buildCase(name, isA, signals, raw_stats)
              const winPct  = isA ? pct_a : pct_b
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
