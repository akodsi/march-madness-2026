'use client'
import { BracketData, Region, Direction } from '@/lib/types'
import {
  REGION_SLOTS, CARD_W, CARD_H, COL_GAP, REGION_H, cardY,
} from '@/lib/bracketSlots'
import MatchupCard from './MatchupCard'
import ConnectorLines from './ConnectorLines'

interface Props {
  region: Region
  direction: Direction
  bracket: BracketData
  onPick: (id: string, winner: string) => void
  onUnpick: (id: string) => void
}

const ROUNDS_LTR = ['Round of 64', 'Round of 32', 'Sweet 16', 'Elite 8']

export default function RegionBracket({ region, direction, bracket, onPick, onUnpick }: Props) {
  const rounds = direction === 'ltr' ? ROUNDS_LTR : [...ROUNDS_LTR].reverse()
  const slots  = REGION_SLOTS[region]

  // For RTL, the round index used for vertical positioning is mirrored
  function posRoundIdx(displayIdx: number) {
    return direction === 'ltr' ? displayIdx : 3 - displayIdx
  }

  return (
    <div className="relative flex-shrink-0" style={{ width: CARD_W * 4 + COL_GAP * 3, height: REGION_H }}>
      {/* Region label */}
      <div
        className="absolute -top-6 left-0 right-0 text-center text-xs font-semibold uppercase tracking-widest text-slate-500"
      >
        {region}
      </div>

      {/* Columns */}
      <div className="flex h-full">
        {rounds.map((roundName, displayIdx) => {
          const slotIds    = slots[roundName] ?? []
          const posIdx     = posRoundIdx(displayIdx)
          const isLastCol  = displayIdx === rounds.length - 1

          return (
            <div key={roundName} className="flex items-start">
              {/* Connector lines to the LEFT of this column (except first) */}
              {displayIdx > 0 && (
                <ConnectorLines
                  fromRound={direction === 'ltr' ? posIdx - 1 : posIdx}
                  rtl={direction === 'rtl'}
                />
              )}

              {/* Round column */}
              <div
                className="relative flex-shrink-0"
                style={{ width: CARD_W, height: REGION_H }}
              >
                {slotIds.map((id, slotIdx) => {
                  const m = bracket[id]
                  if (!m) return null
                  return (
                    <div
                      key={id}
                      className="absolute"
                      style={{ top: cardY(posIdx, slotIdx), left: 0 }}
                    >
                      <MatchupCard matchup={m} onPick={onPick} onUnpick={onUnpick} />
                    </div>
                  )
                })}
              </div>

              {/* Connector lines to the RIGHT of Elite 8 column (feeds Final Four) */}
              {isLastCol && (
                <svg width={COL_GAP} height={REGION_H} className="flex-shrink-0">
                  {/* Single line from E8 midpoint to the edge */}
                  <line
                    x1={direction === 'ltr' ? 0 : COL_GAP}
                    y1={cardY(3, 0) + CARD_H / 2}
                    x2={direction === 'ltr' ? COL_GAP : 0}
                    y2={cardY(3, 0) + CARD_H / 2}
                    stroke="#334155"
                    strokeWidth={1.5}
                  />
                </svg>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
