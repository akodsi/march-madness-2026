'use client'
import { BracketData } from '@/lib/types'
import { CARD_H, REGION_H, cardY } from '@/lib/bracketSlots'
import MatchupCard from './MatchupCard'

interface Props {
  bracket: BracketData
  onPick: (id: string, winner: string) => void
  onUnpick: (id: string) => void
}

// The Final Four sits between the two halves (East/West top, Midwest/South bottom).
// SF_1 is vertically centered in the top half (REGION_H), SF_2 in the bottom half.
// Championship sits between them.
export default function FinalFour({ bracket, onPick, onUnpick }: Props) {
  const sf1   = bracket['SF_1']
  const sf2   = bracket['SF_2']
  const champ = bracket['CHAMP']

  const totalH = REGION_H * 2
  // E8 card midpoint in each half
  const e8Mid  = cardY(3, 0) + CARD_H / 2          // ~384 within a region
  const sf1Y   = e8Mid - CARD_H / 2                 // top half
  const champY = REGION_H - CARD_H / 2              // center between halves
  const sf2Y   = REGION_H + e8Mid - CARD_H / 2      // bottom half

  return (
    <div className="relative flex-shrink-0" style={{ width: 200, height: totalH }}>
      <div className="absolute -top-6 left-0 right-0 text-center text-[10px] font-semibold uppercase tracking-widest text-slate-500">
        Final Four / Champ
      </div>

      {sf1 && (
        <div className="absolute" style={{ top: sf1Y, left: 6, right: 6 }}>
          <div className="text-[9px] text-center text-slate-500 uppercase mb-1">East vs West</div>
          <MatchupCard matchup={sf1} onPick={onPick} onUnpick={onUnpick} />
        </div>
      )}

      {champ && (
        <div className="absolute" style={{ top: champY, left: 6, right: 6 }}>
          <div className="text-[9px] text-center text-amber-500 uppercase mb-1 font-bold">Championship</div>
          <MatchupCard matchup={champ} onPick={onPick} onUnpick={onUnpick} />
        </div>
      )}

      {sf2 && (
        <div className="absolute" style={{ top: sf2Y, left: 6, right: 6 }}>
          <div className="text-[9px] text-center text-slate-500 uppercase mb-1">Midwest vs South</div>
          <MatchupCard matchup={sf2} onPick={onPick} onUnpick={onUnpick} />
        </div>
      )}
    </div>
  )
}
