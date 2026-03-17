'use client'
import { useState, useEffect, useCallback } from 'react'
import { BracketData } from '@/lib/types'
import { fetchBracket, makePick, undoPick, resetBracket } from '@/lib/api'
import { REGION_H, REGION_W, COL_GAP } from '@/lib/bracketSlots'
import RegionBracket from './RegionBracket'
import FinalFour from './FinalFour'
import FirstFour from './FirstFour'

export default function BracketBoard() {
  const [bracket, setBracket] = useState<BracketData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)

  useEffect(() => {
    fetchBracket()
      .then(setBracket)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handlePick = useCallback(async (id: string, winner: string) => {
    if (!bracket) return
    // Optimistic update — will be overwritten by server response
    try {
      const { bracket: updated } = await makePick(id, winner)
      setBracket(updated)
    } catch (e: any) {
      setError(e.message)
    }
  }, [bracket])

  const handleUnpick = useCallback(async (id: string) => {
    if (!bracket) return
    try {
      const { bracket: updated } = await undoPick(id)
      setBracket(updated)
    } catch (e: any) {
      setError(e.message)
    }
  }, [bracket])

  const handleReset = async () => {
    if (!confirm('Reset all picks?')) return
    const fresh = await resetBracket()
    setBracket(fresh)
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen text-slate-400">
      Loading bracket…
    </div>
  )

  if (error) return (
    <div className="flex items-center justify-center h-screen text-red-400">
      Error: {error}
    </div>
  )

  if (!bracket) return null

  const pickedCount = Object.values(bracket).filter(m => m.user_pick).length

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold tracking-tight">2026 March Madness</h1>
          <p className="text-xs text-slate-400">
            {pickedCount} / 67 picks made · Click a team to pick, click again to undo
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Legend */}
          <div className="hidden md:flex items-center gap-3 text-[10px] text-slate-400">
            <span className="text-emerald-400">■</span> Heavy Favorite
            <span className="text-blue-400">■</span> Clear Favorite
            <span className="text-yellow-400">■</span> Slight Edge
            <span className="text-slate-400">■</span> Toss-Up
          </div>
          <button
            onClick={handleReset}
            className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors"
          >
            Reset
          </button>
        </div>
      </header>

      {/* First Four */}
      <div className="px-6 pt-6">
        <FirstFour bracket={bracket} onPick={handlePick} onUnpick={handleUnpick} />
      </div>

      {/* Main bracket — horizontally scrollable */}
      <div className="overflow-x-auto px-6 pb-12">
        <div
          className="relative mx-auto"
          style={{
            width:  REGION_W * 2 + 200 + COL_GAP * 2,
            height: REGION_H * 2 + 32,   // +32 for region labels
            paddingTop: 32,
          }}
        >
          {/* TOP HALF: East (ltr) | Final Four | West (rtl) */}
          <div className="absolute flex items-start" style={{ top: 32, left: 0 }}>
            <RegionBracket
              region="East" direction="ltr"
              bracket={bracket} onPick={handlePick} onUnpick={handleUnpick}
            />
          </div>

          <div className="absolute flex items-start" style={{ top: 32, left: REGION_W + COL_GAP }}>
            <FinalFour bracket={bracket} onPick={handlePick} onUnpick={handleUnpick} />
          </div>

          <div className="absolute flex items-start" style={{ top: 32, left: REGION_W + COL_GAP + 200 + COL_GAP }}>
            <RegionBracket
              region="West" direction="rtl"
              bracket={bracket} onPick={handlePick} onUnpick={handleUnpick}
            />
          </div>

          {/* BOTTOM HALF: Midwest (ltr) | (Final Four continues) | South (rtl) */}
          <div className="absolute flex items-start" style={{ top: 32 + REGION_H, left: 0 }}>
            <RegionBracket
              region="Midwest" direction="ltr"
              bracket={bracket} onPick={handlePick} onUnpick={handleUnpick}
            />
          </div>

          <div className="absolute flex items-start" style={{ top: 32 + REGION_H, left: REGION_W + COL_GAP + 200 + COL_GAP }}>
            <RegionBracket
              region="South" direction="rtl"
              bracket={bracket} onPick={handlePick} onUnpick={handleUnpick}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
