// Ordered slot IDs for each region's rounds, top-to-bottom within each round.
// This order controls the visual vertical stacking of matchup cards.
export const REGION_SLOTS: Record<string, Record<string, string[]>> = {
  East: {
    'Round of 64': ['E_R1_1','E_R1_2','E_R1_3','E_R1_4','E_R1_5','E_R1_6','E_R1_7','E_R1_8'],
    'Round of 32': ['E_R2_1','E_R2_2','E_R2_3','E_R2_4'],
    'Sweet 16':    ['E_R3_1','E_R3_2'],
    'Elite 8':     ['E_R4_1'],
  },
  West: {
    'Round of 64': ['W_R1_1','W_R1_2','W_R1_3','W_R1_4','W_R1_5','W_R1_6','W_R1_7','W_R1_8'],
    'Round of 32': ['W_R2_1','W_R2_2','W_R2_3','W_R2_4'],
    'Sweet 16':    ['W_R3_1','W_R3_2'],
    'Elite 8':     ['W_R4_1'],
  },
  Midwest: {
    'Round of 64': ['MW_R1_1','MW_R1_2','MW_R1_3','MW_R1_4','MW_R1_5','MW_R1_6','MW_R1_7','MW_R1_8'],
    'Round of 32': ['MW_R2_1','MW_R2_2','MW_R2_3','MW_R2_4'],
    'Sweet 16':    ['MW_R3_1','MW_R3_2'],
    'Elite 8':     ['MW_R4_1'],
  },
  South: {
    'Round of 64': ['S_R1_1','S_R1_2','S_R1_3','S_R1_4','S_R1_5','S_R1_6','S_R1_7','S_R1_8'],
    'Round of 32': ['S_R2_1','S_R2_2','S_R2_3','S_R2_4'],
    'Sweet 16':    ['S_R3_1','S_R3_2'],
    'Elite 8':     ['S_R4_1'],
  },
}

export const FIRST_FOUR_SLOTS = ['FF_1', 'FF_2', 'FF_3', 'FF_4']

// Visual layout constants (px)
export const SLOT_H   = 96   // height allocated to each R64 matchup
export const CARD_H   = 76   // actual rendered card height
export const CARD_W   = 188  // card width
export const COL_GAP  = 28   // gap between round columns (for connector lines)

// Given a round index (0=R64, 1=R32, 2=S16, 3=E8) and slot index within that round,
// return the top-left y coordinate for the card.
export function cardY(roundIdx: number, slotIdx: number): number {
  const slotSize = SLOT_H * Math.pow(2, roundIdx)
  const offset   = (slotSize - CARD_H) / 2
  return slotIdx * slotSize + offset
}

// Total region height
export const REGION_H = SLOT_H * 8  // 768px

// Column x positions (left side, ltr — R64 first)
export function colX(roundIdx: number): number {
  return roundIdx * (CARD_W + COL_GAP)
}

export const REGION_W = colX(3) + CARD_W  // 4 rounds wide

// For RTL regions (West/South), mirror the column x positions
export function colXRtl(roundIdx: number): number {
  return colX(3 - roundIdx)
}
