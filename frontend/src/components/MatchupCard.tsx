'use client'
import { Matchup, CONFIDENCE_COLORS } from '@/lib/types'
import { CARD_H, CARD_W } from '@/lib/bracketSlots'

interface Props {
  matchup: Matchup
  onPick: (matchupId: string, winner: string) => void
  onUnpick: (matchupId: string) => void
}

export default function MatchupCard({ matchup, onPick, onUnpick }: Props) {
  const { id, team_a, team_b, pct_a, pct_b, confidence, user_pick } = matchup
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
      : pctVal >= 65
      ? 'bg-emerald-600'
      : pctVal >= 55
      ? 'bg-blue-600'
      : 'bg-slate-600'

    return (
      <button
        onClick={() => handleClick(team)}
        disabled={!ready}
        className={[
          'flex items-center gap-2 px-2 py-1 w-full text-left transition-all',
          'disabled:cursor-default',
          isWinner ? 'bg-amber-500/20 text-white' : '',
          isLoser  ? 'opacity-30' : '',
          ready && !picked ? 'hover:bg-white/10 cursor-pointer' : '',
          isA ? 'rounded-t' : 'rounded-b',
        ].join(' ')}
      >
        {/* Win % bar */}
        <div className="relative w-8 h-2 bg-slate-700 rounded-full flex-shrink-0">
          <div
            className={`absolute left-0 top-0 h-full rounded-full ${barColor}`}
            style={{ width: `${pctVal}%` }}
          />
        </div>
        {/* Team name */}
        <span className="flex-1 text-xs font-medium truncate leading-tight">
          {team ?? <span className="text-slate-500 italic">TBD</span>}
        </span>
        {/* Percentage */}
        {ready && (
          <span className={`text-xs font-bold flex-shrink-0 ${isWinner ? 'text-amber-400' : 'text-slate-300'}`}>
            {pctVal}%
          </span>
        )}
        {/* Checkmark */}
        {isWinner && <span className="text-amber-400 text-xs flex-shrink-0">✓</span>}
      </button>
    )
  }

  const confColor = confidence ? CONFIDENCE_COLORS[confidence] ?? 'text-slate-500' : 'text-slate-600'

  return (
    <div
      style={{ width: CARD_W, height: CARD_H }}
      className="bg-slate-800 border border-slate-700 rounded flex flex-col justify-between overflow-hidden"
    >
      {/* Top team */}
      {teamRow(team_a, pct_a, true)}
      {/* Divider + confidence label */}
      <div className={`flex items-center gap-1 px-2 ${confColor}`} style={{ height: 14 }}>
        <div className="flex-1 border-t border-slate-700" />
        {confidence && ready && (
          <span className="text-[9px] uppercase tracking-wide leading-none whitespace-nowrap">
            {confidence}
          </span>
        )}
        <div className="flex-1 border-t border-slate-700" />
      </div>
      {/* Bottom team */}
      {teamRow(team_b, pct_b, false)}
    </div>
  )
}
