'use client'
import { BracketData } from '@/lib/types'
import { FIRST_FOUR_SLOTS } from '@/lib/bracketSlots'
import MatchupCard from './MatchupCard'

interface Props {
  bracket: BracketData
  onPick: (id: string, winner: string) => void
  onUnpick: (id: string) => void
}

const FF_LABELS: Record<string, string> = {
  FF_1: 'Midwest 16',
  FF_2: 'Midwest 11',
  FF_3: 'West 11',
  FF_4: 'South 16',
}

export default function FirstFour({ bracket, onPick, onUnpick }: Props) {
  const games = FIRST_FOUR_SLOTS.map(id => bracket[id]).filter(Boolean)

  return (
    <div className="mb-8">
      <h2 className="text-center text-xs font-semibold uppercase tracking-widest text-slate-500 mb-3">
        First Four — Dayton, OH — Mar 17–18
      </h2>
      <div className="flex justify-center gap-4 flex-wrap">
        {games.map(m => (
          <div key={m.id} className="flex flex-col items-center gap-1">
            <span className="text-[10px] text-slate-500 uppercase tracking-wide">
              {FF_LABELS[m.id] ?? m.id}
            </span>
            <MatchupCard matchup={m} onPick={onPick} onUnpick={onUnpick} />
          </div>
        ))}
      </div>
    </div>
  )
}
