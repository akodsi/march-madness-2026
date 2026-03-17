'use client'
import { useState } from 'react'
import { Matchup, CONFIDENCE_PILL } from '@/lib/types'
import { CARD_H, CARD_W } from '@/lib/bracketSlots'
import { getLogoUrl, getInitials } from '@/lib/teamLogos'

interface Props {
  matchup: Matchup
  onPick: (matchupId: string, winner: string) => void
  onUnpick: (matchupId: string) => void
  onDetail: (matchup: Matchup) => void
}

function TeamLogo({ name }: { name: string }) {
  const [failed, setFailed] = useState(false)
  const url = getLogoUrl(name)

  if (!url || failed) {
    return (
      <div className="w-5 h-5 rounded-full bg-slate-600 flex items-center justify-center flex-shrink-0">
        <span className="text-[7px] font-bold text-slate-300">{getInitials(name)}</span>
      </div>
    )
  }

  return (
    <img
      src={url}
      alt={name}
      width={20}
      height={20}
      className="w-5 h-5 object-contain flex-shrink-0"
      onError={() => setFailed(true)}
    />
  )
}

export default function MatchupCard({ matchup, onPick, onUnpick, onDetail }: Props) {
  const { id, team_a, team_b, pct_a, pct_b, confidence, user_pick, raw_stats } = matchup
  const ready  = team_a !== null && team_b !== null
  const picked = user_pick !== null

  function handleClick(team: string | null) {
    if (!team || !ready) return
    if (user_pick === team) onUnpick(id)
    else onPick(id, team)
  }

  function teamRow(team: string | null, pct: number | null, isA: boolean) {
    const isWinner = picked && user_pick === team
    const isLoser  = picked && user_pick !== team
    const pctVal   = pct ?? 50

    const barColor = isWinner
      ? 'bg-amber-500'
      : pctVal >= 65 ? 'bg-emerald-600'
      : pctVal >= 55 ? 'bg-blue-600'
      : 'bg-slate-600'

    const seed    = isA ? raw_stats?.seed_a : raw_stats?.seed_b
    const streak  = isA ? raw_stats?.win_streak_a : raw_stats?.win_streak_b
    const keyOut  = isA ? raw_stats?.key_players_out_a : raw_stats?.key_players_out_b
    const hasStreak = streak !== undefined && streak !== null && Math.abs(streak) >= 3
    const hasInjury = keyOut !== undefined && keyOut.length > 0

    return (
      <button
        onClick={() => handleClick(team)}
        disabled={!ready}
        className={[
          'flex items-center gap-1.5 px-2 py-1 w-full text-left transition-all duration-200',
          'disabled:cursor-default',
          isWinner ? 'bg-amber-500/15 text-white border-l-2 border-l-amber-500 pl-1.5' : '',
          isLoser  ? 'opacity-30' : '',
          ready && !picked ? 'hover:bg-white/10 cursor-pointer' : '',
          isA ? 'rounded-t' : 'rounded-b',
        ].join(' ')}
      >
        {team ? <TeamLogo name={team} /> : <div className="w-5 h-5 flex-shrink-0" />}

        <div className="relative w-8 h-2 bg-slate-700 rounded-full flex-shrink-0">
          <div
            className={`absolute left-0 top-0 h-full rounded-full transition-all duration-300 ${barColor}`}
            style={{ width: `${pctVal}%` }}
          />
        </div>

        {seed !== undefined && seed !== null && (
          <span className="text-[9px] font-bold text-slate-500 flex-shrink-0 w-3 text-right">{seed}</span>
        )}

        <span className="flex-1 text-xs font-medium truncate leading-tight">
          {team ?? <span className="text-slate-500 italic">TBD</span>}
        </span>

        {hasStreak && streak !== undefined && (
          <span className={`text-[8px] font-bold px-0.5 rounded flex-shrink-0 leading-tight ${streak > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {streak > 0 ? `W${streak}` : `L${Math.abs(streak)}`}
          </span>
        )}
        {hasInjury && (
          <span className="text-orange-400 text-[9px] flex-shrink-0" title="Key players out">⚠</span>
        )}

        {ready && (
          <span className={`text-xs font-bold flex-shrink-0 ${isWinner ? 'text-amber-400' : 'text-slate-300'}`}>
            {pctVal}%
          </span>
        )}
        {isWinner && <span className="text-amber-400 text-xs flex-shrink-0">✓</span>}
      </button>
    )
  }

  const confPill = confidence ? CONFIDENCE_PILL[confidence] ?? 'text-slate-500' : 'text-slate-600'
  const hasPick = user_pick !== null

  return (
    <div
      style={{ width: CARD_W, height: CARD_H }}
      className={[
        'rounded flex flex-col justify-between overflow-hidden transition-all duration-200',
        'bg-slate-800/90 border',
        hasPick
          ? 'border-amber-500/40 shadow-md shadow-amber-500/10'
          : 'border-slate-700 hover:border-slate-500 hover:shadow-lg hover:shadow-blue-500/10 hover:scale-[1.02]',
      ].join(' ')}
    >
      {teamRow(team_a, pct_a, true)}

      <div className="flex items-center gap-1 px-2" style={{ height: 16 }}>
        <div className="flex-1 border-t border-slate-700" />
        {confidence && ready && (
          <span className={`text-[9px] uppercase tracking-wide leading-none whitespace-nowrap px-1.5 py-0.5 rounded-full ${confPill}`}>
            {confidence}
          </span>
        )}
        <div className="flex-1 border-t border-slate-700" />
        {ready && (
          <button
            onClick={(e) => { e.stopPropagation(); onDetail(matchup) }}
            className="text-slate-500 hover:text-blue-400 transition-colors leading-none ml-1"
            title="See breakdown"
          >
            <span className="text-[11px]">ⓘ</span>
          </button>
        )}
      </div>

      {teamRow(team_b, pct_b, false)}
    </div>
  )
}
