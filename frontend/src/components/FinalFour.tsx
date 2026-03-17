'use client'
import { BracketData, Matchup } from '@/lib/types'
import { CARD_W, CARD_H } from '@/lib/bracketSlots'
import MatchupCard from './MatchupCard'

interface Props {
  bracket: BracketData
  onPick: (id: string, winner: string) => void
  onUnpick: (id: string) => void
  onDetail: (matchup: Matchup) => void
}

export default function FinalFour({ bracket, onPick, onUnpick, onDetail }: Props) {
  const sf1   = bracket['SF_1']
  const sf2   = bracket['SF_2']
  const champ = bracket['CHAMP']

  return (
    <div className="flex flex-col items-center gap-10" style={{ width: CARD_W + 24 }}>
      {sf1 && (
        <div className="w-full">
          <div className="text-[10px] text-center text-slate-500 uppercase tracking-widest mb-2">East vs West</div>
          <MatchupCard matchup={sf1} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}

      {champ && (
        <div className="w-full">
          <div className="text-[10px] text-center text-amber-500 uppercase tracking-widest mb-2 font-bold">Championship</div>
          <MatchupCard matchup={champ} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}

      {sf2 && (
        <div className="w-full">
          <div className="text-[10px] text-center text-slate-500 uppercase tracking-widest mb-2">Midwest vs South</div>
          <MatchupCard matchup={sf2} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}
    </div>
  )
}
