'use client'
import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { BracketData, Matchup } from '@/lib/types'
import { fetchBracket, makePick, undoPick, resetBracket } from '@/lib/api'
import RegionBracket from './RegionBracket'
import FinalFour from './FinalFour'
import FirstFour from './FirstFour'
import MatchupDetail from './MatchupDetail'
import PrintBracket from './PrintBracket'

type Tab = 'first-four' | 'east' | 'midwest' | 'west' | 'south' | 'final-four'

const TABS: { id: Tab; label: string }[] = [
  { id: 'first-four',  label: 'First Four' },
  { id: 'east',        label: 'East' },
  { id: 'midwest',     label: 'Midwest' },
  { id: 'west',        label: 'West' },
  { id: 'south',       label: 'South' },
  { id: 'final-four',  label: 'Final Four' },
]

export default function BracketBoard() {
  const [bracket, setBracket]             = useState<BracketData | null>(null)
  const [loading, setLoading]             = useState(true)
  const [error, setError]                 = useState<string | null>(null)
  const [activeTab, setActiveTab]         = useState<Tab>('east')
  const [detailMatchup, setDetailMatchup] = useState<Matchup | null>(null)
  const [exporting, setExporting]         = useState(false)
  const printRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchBracket()
      .then(setBracket)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handlePick = useCallback(async (id: string, winner: string) => {
    if (!bracket) return
    try {
      const { bracket: updated } = await makePick(id, winner)
      setBracket(updated)
      if (detailMatchup?.id === id) setDetailMatchup(updated[id])
    } catch (e: any) { setError(e.message) }
  }, [bracket, detailMatchup])

  const handleUnpick = useCallback(async (id: string) => {
    if (!bracket) return
    try {
      const { bracket: updated } = await undoPick(id)
      setBracket(updated)
      if (detailMatchup?.id === id) setDetailMatchup(updated[id])
    } catch (e: any) { setError(e.message) }
  }, [bracket, detailMatchup])

  const handleReset = async () => {
    if (!confirm('Reset all picks?')) return
    const fresh = await resetBracket()
    setBracket(fresh)
    setDetailMatchup(null)
  }

  const handleExport = async () => {
    if (!printRef.current || exporting) return
    setExporting(true)
    try {
      const { exportBracketPdf } = await import('@/lib/exportPdf')
      await exportBracketPdf(printRef.current)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setExporting(false)
    }
  }

  if (loading) return (
    <div className="flex items-center justify-center h-screen text-slate-400">Loading bracket…</div>
  )
  if (error) return (
    <div className="flex items-center justify-center h-screen text-red-400">Error: {error}</div>
  )
  if (!bracket) return null

  const pickedCount = Object.values(bracket).filter(m => m.user_pick).length

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <h1 className="text-base sm:text-lg font-bold tracking-tight">2026 March Madness</h1>
            <p className="text-[10px] sm:text-xs text-slate-400 truncate">
              {pickedCount} / 67 picks · tap a team to pick · tap ⓘ for breakdown
            </p>
          </div>
          <div className="flex items-center gap-2 sm:gap-4 flex-shrink-0">
            <div className="hidden lg:flex items-center gap-3 text-[10px] text-slate-400">
              <span className="text-emerald-400">■</span> Heavy Favorite
              <span className="text-blue-400">■</span> Clear Favorite
              <span className="text-yellow-400">■</span> Slight Edge
              <span className="text-slate-400">■</span> Toss-Up
            </div>
            <Link
              href="/champion"
              className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors"
            >
              Champion Profiles
            </Link>
            <button
              onClick={handleExport}
              disabled={exporting}
              className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors disabled:opacity-50"
            >
              {exporting ? 'Exporting…' : 'Export PDF'}
            </button>
            <button
              onClick={handleReset}
              className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors"
            >
              Reset
            </button>
          </div>
        </div>

        {/* Tabs — scrollable on mobile */}
        <div className="flex gap-1 mt-3 overflow-x-auto scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={[
                'px-3 sm:px-4 py-1.5 rounded text-xs font-semibold uppercase tracking-wide transition-colors whitespace-nowrap flex-shrink-0',
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Tab content */}
      <div className="px-4 sm:px-6 py-6 sm:py-8 overflow-x-auto">
        <div key={activeTab} className="animate-fade-in">
        {activeTab === 'first-four' && (
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-6">
              Play-in games — winners advance to Round of 64
            </p>
            <FirstFour
              bracket={bracket}
              onPick={handlePick}
              onUnpick={handleUnpick}
              onDetail={setDetailMatchup}
            />
          </div>
        )}

        {activeTab === 'east' && (
          <RegionBracket region="East" direction="ltr" bracket={bracket}
            onPick={handlePick} onUnpick={handleUnpick} onDetail={setDetailMatchup} />
        )}
        {activeTab === 'midwest' && (
          <RegionBracket region="Midwest" direction="ltr" bracket={bracket}
            onPick={handlePick} onUnpick={handleUnpick} onDetail={setDetailMatchup} />
        )}
        {activeTab === 'west' && (
          <RegionBracket region="West" direction="ltr" bracket={bracket}
            onPick={handlePick} onUnpick={handleUnpick} onDetail={setDetailMatchup} />
        )}
        {activeTab === 'south' && (
          <RegionBracket region="South" direction="ltr" bracket={bracket}
            onPick={handlePick} onUnpick={handleUnpick} onDetail={setDetailMatchup} />
        )}

        {activeTab === 'final-four' && (
          <div className="flex flex-col items-center gap-8 py-8">
            <p className="text-xs text-slate-500 uppercase tracking-widest">
              Final Four · Championship
            </p>
            <FinalFour bracket={bracket} onPick={handlePick} onUnpick={handleUnpick} onDetail={setDetailMatchup} />
          </div>
        )}
        </div>
      </div>

      {/* Matchup detail modal */}
      {detailMatchup && (
        <MatchupDetail
          matchup={detailMatchup}
          onPick={handlePick}
          onUnpick={handleUnpick}
          onClose={() => setDetailMatchup(null)}
        />
      )}

      {/* Hidden printable bracket for PDF export */}
      <div className="fixed left-[-9999px] top-0" aria-hidden="true">
        <div ref={printRef}>
          <PrintBracket bracket={bracket} />
        </div>
      </div>
    </div>
  )
}
