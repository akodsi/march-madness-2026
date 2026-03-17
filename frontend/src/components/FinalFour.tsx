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

  const GAP = 32
  const CONNECTOR_W = 40

  // Total width: SF1 + connector + CHAMP + connector + SF2
  const totalW = CARD_W * 3 + CONNECTOR_W * 2
  // Height: tallest of the semis stacked area vs championship
  const semiSpacing = CARD_H + GAP
  const totalH = Math.max(semiSpacing * 2 + CARD_H, CARD_H) + 60 // extra for trophy

  // Positions
  const sf1X = 0
  const sf1Y = 20
  const sf2X = CARD_W * 2 + CONNECTOR_W * 2
  const sf2Y = 20
  const champX = CARD_W + CONNECTOR_W
  const champY = sf1Y + CARD_H / 2 + GAP / 2

  // SVG connector midpoints
  const leftMidY  = sf1Y + CARD_H / 2
  const rightMidY = sf2Y + CARD_H / 2
  const champMidY = champY + CARD_H / 2

  return (
    <div className="relative" style={{ width: totalW, height: totalH }}>
      {/* Trophy icon above championship */}
      <div
        className="absolute flex flex-col items-center"
        style={{ left: champX, top: sf1Y - 16, width: CARD_W }}
      >
        <span className="text-2xl" role="img" aria-label="trophy">🏆</span>
      </div>

      {/* Labels */}
      <div
        className="absolute text-[10px] text-slate-500 uppercase tracking-widest text-center"
        style={{ left: sf1X, top: 0, width: CARD_W }}
      >
        East vs West
      </div>
      <div
        className="absolute text-[10px] text-amber-500 uppercase tracking-widest text-center font-bold"
        style={{ left: champX, top: champY - 16, width: CARD_W }}
      >
        Championship
      </div>
      <div
        className="absolute text-[10px] text-slate-500 uppercase tracking-widest text-center"
        style={{ left: sf2X, top: 0, width: CARD_W }}
      >
        Midwest vs South
      </div>

      {/* Left connector: SF1 → Championship */}
      <svg
        className="absolute"
        style={{ left: CARD_W, top: 0, overflow: 'visible' }}
        width={CONNECTOR_W}
        height={totalH}
      >
        <path
          d={`M 0 ${leftMidY} H ${CONNECTOR_W / 2} V ${champMidY} H ${CONNECTOR_W}`}
          fill="none"
          stroke={sf1?.user_pick ? '#60a5fa' : '#334155'}
          strokeWidth={sf1?.user_pick ? 2 : 1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />
      </svg>

      {/* Right connector: SF2 → Championship */}
      <svg
        className="absolute"
        style={{ left: CARD_W * 2 + CONNECTOR_W, top: 0, overflow: 'visible' }}
        width={CONNECTOR_W}
        height={totalH}
      >
        <path
          d={`M ${CONNECTOR_W} ${rightMidY} H ${CONNECTOR_W / 2} V ${champMidY} H 0`}
          fill="none"
          stroke={sf2?.user_pick ? '#60a5fa' : '#334155'}
          strokeWidth={sf2?.user_pick ? 2 : 1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />
      </svg>

      {/* SF1 card */}
      {sf1 && (
        <div className="absolute" style={{ left: sf1X, top: sf1Y }}>
          <MatchupCard matchup={sf1} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}

      {/* Championship card */}
      {champ && (
        <div className="absolute" style={{ left: champX, top: champY }}>
          <MatchupCard matchup={champ} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}

      {/* SF2 card */}
      {sf2 && (
        <div className="absolute" style={{ left: sf2X, top: sf2Y }}>
          <MatchupCard matchup={sf2} onPick={onPick} onUnpick={onUnpick} onDetail={onDetail} />
        </div>
      )}

      {/* Champion display */}
      {champ?.user_pick && (
        <div
          className="absolute flex flex-col items-center gap-1 animate-fade-in"
          style={{ left: champX, top: champY + CARD_H + 16, width: CARD_W }}
        >
          <div className="text-[10px] uppercase tracking-widest text-amber-500 font-bold">Champion</div>
          <div className="text-sm font-black text-amber-400">{champ.user_pick}</div>
        </div>
      )}
    </div>
  )
}
