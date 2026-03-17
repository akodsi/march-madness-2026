// SVG connector lines between two adjacent rounds in the bracket.
// Draws the classic bracket "L"-shaped connectors from each pair of
// source matchup midpoints down/up to their shared parent midpoint.

import { SLOT_H, CARD_H, CARD_W, COL_GAP, REGION_H, cardY } from '@/lib/bracketSlots'

interface Props {
  fromRound: number  // 0=R64, 1=R32, 2=S16, 3=E8
  rtl?: boolean      // West/South regions read right-to-left
}

export default function ConnectorLines({ fromRound, rtl = false }: Props) {
  const toRound   = fromRound + 1
  const srcCount  = Math.pow(2, 3 - fromRound)   // e.g. fromRound=0 → 8
  const dstCount  = srcCount / 2

  const midX = COL_GAP / 2  // horizontal midpoint of the gap SVG

  const paths: string[] = []

  for (let dstIdx = 0; dstIdx < dstCount; dstIdx++) {
    const srcA = dstIdx * 2
    const srcB = dstIdx * 2 + 1

    const yMidA  = cardY(fromRound, srcA) + CARD_H / 2
    const yMidB  = cardY(fromRound, srcB) + CARD_H / 2
    const yMidDst = cardY(toRound,  dstIdx) + CARD_H / 2

    if (rtl) {
      // Lines go from right edge of card (x=COL_GAP) to left (x=0)
      paths.push(`M ${COL_GAP} ${yMidA} H ${midX} V ${yMidDst} H 0`)
      paths.push(`M ${COL_GAP} ${yMidB} H ${midX} V ${yMidDst} H 0`)
    } else {
      // Lines go from left (x=0) to right (x=COL_GAP)
      paths.push(`M 0 ${yMidA} H ${midX} V ${yMidDst} H ${COL_GAP}`)
      paths.push(`M 0 ${yMidB} H ${midX} V ${yMidDst} H ${COL_GAP}`)
    }
  }

  return (
    <svg
      width={COL_GAP}
      height={REGION_H}
      className="flex-shrink-0"
      style={{ overflow: 'visible' }}
    >
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="#334155" strokeWidth={1.5} />
      ))}
    </svg>
  )
}
