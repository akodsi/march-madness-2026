/**
 * ESPN CDN logo URLs for all 68 tournament teams.
 * Format: https://a.espncdn.com/i/teamlogos/ncaa/500/{id}.png
 * Falls back to initials badge in MatchupCard if image fails to load.
 */
const ESPN_IDS: Record<string, number> = {
  // ── EAST ──────────────────────────────────────────────────────────────
  'Duke':                 150,
  'Connecticut':          41,
  'Michigan State':       127,
  'Kansas':               2305,
  'St. John\'s (NY)':     2599,
  'Louisville':           97,
  'UCLA':                 26,
  'Ohio State':           194,
  'TCU':                  2628,
  'UCF':                  2116,
  'South Florida':        58,
  'Northern Iowa':        2534,
  'California Baptist':   2856,
  'North Dakota State':   2449,
  'Furman':               231,
  'Siena':                2597,
  'UMBC':                 2378,
  'Howard':               47,

  // ── MIDWEST ───────────────────────────────────────────────────────────
  'Michigan':             130,
  'Iowa State':           66,
  'Virginia':             258,
  'Alabama':              333,
  'Texas Tech':           2641,
  'Tennessee':            2633,
  'Kentucky':             96,
  'Georgia':              61,
  'Saint Louis':          139,
  'Santa Clara':          2617,
  'Miami (OH)':           193,
  'SMU':                  2567,
  'Akron':                2006,
  'Hofstra':              2171,
  'Wright State':         2750,
  'Tennessee State':      2640,

  // ── SOUTH ─────────────────────────────────────────────────────────────
  'Florida':              57,
  'Houston':              248,
  'Illinois':             356,
  'Nebraska':             158,
  'Vanderbilt':           238,
  'North Carolina':       153,
  'Miami (FL)':           2390,
  'Clemson':              228,
  'Iowa':                 2294,
  'Texas A&M':            245,
  'VCU':                  2670,
  'McNeese':              2383,
  'Troy':                 2653,
  'Queens (NC)':          2695,
  'Idaho':                70,
  'Prairie View':         2489,
  'Lehigh':               2332,

  // ── WEST ──────────────────────────────────────────────────────────────
  'Arizona':              12,
  'Purdue':               2509,
  'Gonzaga':              2250,
  'Arkansas':             8,
  'Wisconsin':            275,
  'BYU':                  252,
  'Saint Mary\'s (CA)':   2608,
  'Villanova':            222,
  'Utah State':           328,
  'Missouri':             142,
  'Texas':                251,
  'NC State':             152,
  'High Point':           2272,
  'Hawaii':               62,
  'Kennesaw State':       2310,
  'Penn':                 219,
  'LIU':                  2351,
}

export function getLogoUrl(teamName: string): string | null {
  const id = ESPN_IDS[teamName]
  return id ? `https://a.espncdn.com/i/teamlogos/ncaa/500/${id}.png` : null
}

/** Returns 1–3 character initials to use as fallback badge */
export function getInitials(teamName: string): string {
  const words = teamName.replace(/[()]/g, '').split(/\s+/)
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase()
  // Use first letter of first two meaningful words
  const meaningful = words.filter(w => !['of', 'the', 'at', 'A', '&'].includes(w))
  return meaningful.slice(0, 2).map(w => w[0]).join('').toUpperCase()
}
