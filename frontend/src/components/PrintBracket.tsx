'use client'
import { BracketData } from '@/lib/types'
import { REGION_SLOTS, FIRST_FOUR_SLOTS, CARD_W } from '@/lib/bracketSlots'

/**
 * Compact printable bracket for PDF export.
 * Renders all regions + Final Four in a single flat layout
 * using simple HTML tables — no absolute positioning.
 */

const REGIONS: { name: string; key: string }[] = [
  { name: 'East', key: 'East' },
  { name: 'West', key: 'West' },
  { name: 'Midwest', key: 'Midwest' },
  { name: 'South', key: 'South' },
]

const ROUNDS = ['Round of 64', 'Round of 32', 'Sweet 16', 'Elite 8']

function TeamCell({ bracket, matchupId, team }: { bracket: BracketData; matchupId: string; team: 'a' | 'b' }) {
  const m = bracket[matchupId]
  if (!m) return <span className="text-slate-600 text-[9px]">—</span>

  const name = team === 'a' ? m.team_a : m.team_b
  const pct  = team === 'a' ? m.pct_a : m.pct_b
  const seed = team === 'a' ? m.raw_stats?.seed_a : m.raw_stats?.seed_b
  const isPicked = m.user_pick === name

  if (!name) return <span className="text-slate-600 text-[9px] italic">TBD</span>

  return (
    <span className={`text-[9px] leading-tight ${isPicked ? 'text-amber-400 font-bold' : 'text-slate-300'}`}>
      {seed !== undefined && seed !== null && (
        <span className="text-slate-500 mr-0.5">{seed}</span>
      )}
      {name}
      {pct !== null && <span className="text-slate-500 ml-1">{pct}%</span>}
      {isPicked && <span className="ml-0.5">✓</span>}
    </span>
  )
}

export default function PrintBracket({ bracket }: { bracket: BracketData }) {
  const sf1   = bracket['SF_1']
  const sf2   = bracket['SF_2']
  const champ = bracket['CHAMP']

  return (
    <div className="bg-slate-900 text-white p-6" style={{ width: 1100 }}>
      {/* Title */}
      <div className="text-center mb-4">
        <h1 className="text-lg font-bold tracking-tight">2026 March Madness Bracket</h1>
        <p className="text-[10px] text-slate-400">
          Exported {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}
        </p>
      </div>

      {/* Regions in 2×2 grid */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {REGIONS.map(({ name, key }) => {
          const slots = REGION_SLOTS[key]
          return (
            <div key={key} className="bg-slate-800/60 rounded-lg p-3">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2 text-center">{name}</h2>
              <div className="flex gap-2">
                {ROUNDS.map(round => {
                  const ids = slots[round] ?? []
                  return (
                    <div key={round} className="flex-1">
                      <div className="text-[7px] text-slate-600 uppercase tracking-wide mb-1 text-center truncate">{round}</div>
                      <div className="space-y-1">
                        {ids.map(id => (
                          <div key={id} className="bg-slate-800 rounded px-1.5 py-0.5 border border-slate-700">
                            <div className="border-b border-slate-700/50 pb-0.5 mb-0.5">
                              <TeamCell bracket={bracket} matchupId={id} team="a" />
                            </div>
                            <TeamCell bracket={bracket} matchupId={id} team="b" />
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>

      {/* Final Four + Championship */}
      <div className="bg-slate-800/60 rounded-lg p-3">
        <h2 className="text-xs font-bold uppercase tracking-widest text-amber-500 mb-2 text-center">Final Four & Championship</h2>
        <div className="flex items-center justify-center gap-6">
          {/* SF1 */}
          {sf1 && (
            <div className="bg-slate-800 rounded px-2 py-1 border border-slate-700 w-40">
              <div className="text-[7px] text-slate-500 uppercase text-center mb-1">East vs West</div>
              <div className="border-b border-slate-700/50 pb-0.5 mb-0.5">
                <TeamCell bracket={bracket} matchupId="SF_1" team="a" />
              </div>
              <TeamCell bracket={bracket} matchupId="SF_1" team="b" />
            </div>
          )}

          {/* Arrow */}
          <span className="text-slate-600 text-xs">→</span>

          {/* Championship */}
          {champ && (
            <div className="bg-slate-800 rounded px-2 py-1 border border-amber-500/30 w-44">
              <div className="text-[7px] text-amber-500 uppercase text-center mb-1 font-bold">🏆 Championship</div>
              <div className="border-b border-slate-700/50 pb-0.5 mb-0.5">
                <TeamCell bracket={bracket} matchupId="CHAMP" team="a" />
              </div>
              <TeamCell bracket={bracket} matchupId="CHAMP" team="b" />
              {champ.user_pick && (
                <div className="text-center mt-1 text-[10px] font-bold text-amber-400">
                  Champion: {champ.user_pick}
                </div>
              )}
            </div>
          )}

          {/* Arrow */}
          <span className="text-slate-600 text-xs">←</span>

          {/* SF2 */}
          {sf2 && (
            <div className="bg-slate-800 rounded px-2 py-1 border border-slate-700 w-40">
              <div className="text-[7px] text-slate-500 uppercase text-center mb-1">Midwest vs South</div>
              <div className="border-b border-slate-700/50 pb-0.5 mb-0.5">
                <TeamCell bracket={bracket} matchupId="SF_2" team="a" />
              </div>
              <TeamCell bracket={bracket} matchupId="SF_2" team="b" />
            </div>
          )}
        </div>
      </div>

      {/* Pick summary */}
      <div className="text-center mt-3 text-[9px] text-slate-500">
        {Object.values(bracket).filter(m => m.user_pick).length} / 67 picks made
      </div>
    </div>
  )
}
