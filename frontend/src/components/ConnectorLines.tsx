// SVG connector lines between two adjacent rounds in the bracket.
// Draws the classic bracket "L"-shaped connectors from each pair of
// source matchup midpoints down/up to their shared parent midpoint.

import { SLOT_H, CARD_H, CARD_W, COL_GAP, REGION_H, cardY } from '@/lib/bracketSlots'
import { BracketData } from '@/lib/types'

interface Props {
  fromRound: number  // 0=R64, 1=R32, 2=S16, 3=E8
  rtl?: boolean      // West/South regions read right-to-left
  bracket?: BracketData
  slotIds?: string[] // slot IDs for the source round (to check picks)
}

export default function ConnectorLines({ fromRound, rtl = false, bracket, slotIds }: Props) {
  const toRound   = fromRound + 1
  const srcCount  = Math.pow(2, 3 - fromRound)   // e.g. fromRound=0 → 8
  const dstCount  = srcCount / 2

  const midX = COL_GAP / 2  // horizontal midpoint of the gap SVG

  const lines: { d: string; picked: boolean }[] = []

  for (let dstIdx = 0; dstIdx < dstCount; dstIdx++) {
    const srcA = dstIdx * 2
    const srcB = dstIdx * 2 + 1

    const yMidA  = cardY(fromRound, srcA) + CARD_H / 2
    const yMidB  = cardY(fromRound, srcB) + CARD_H / 2
    const yMidDst = cardY(toRound,  dstIdx) + CARD_H / 2

    // Check if these source matchups have picks
    const idA = slotIds?.[srcA]
    const idB = slotIds?.[srcB]
    const pickedA = !!(idA && bracket?.[idA]?.user_pick)
    const pickedB = !!(idB && bracket?.[idB]?.user_pick)

    if (rtl) {
      lines.push({ d: `M ${COL_GAP} ${yMidA} H ${midX} V ${yMidDst} H 0`, picked: pickedA })
      lines.push({ d: `M ${COL_GAP} ${yMidB} H ${midX} V ${yMidDst} H 0`, picked: pickedB })
    } else {
      lines.push({ d: `M 0 ${yMidA} H ${midX} V ${yMidDst} H ${COL_GAP}`, picked: pickedA })
      lines.push({ d: `M 0 ${yMidB} H ${midX} V ${yMidDst} H ${COL_GAP}`, picked: pickedB })
    }
  }

  return (
    <svg
      width={COL_GAP}
      height={REGION_H}
      className="flex-shrink-0"
      style={{ overflow: 'visible' }}
    >
      {lines.map((line, i) => (
        <path
          key={i}
          d={line.d}
          fill="none"
          stroke={line.picked ? '#60a5fa' : '#334155'}
          strokeWidth={line.picked ? 2 : 1.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          className="transition-all duration-300"
        />
      ))}
    </svg>
  )
}
