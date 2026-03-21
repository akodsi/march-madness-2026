'use client'
import { useState, useEffect } from 'react'
import Link from 'next/link'
import { AnalysisData, SignalGrade, VegasGame, UpsetDetail } from '@/lib/types'
import { fetchAnalysis } from '@/lib/api'
import { getLogoUrl, getInitials } from '@/lib/teamLogos'

// ── Helpers ──────────────────────────────────────────────────────────

const SIGNAL_LABELS: Record<string, string> = {
  srs: 'SRS (Efficiency)',
  sos: 'Strength of Schedule',
  momentum: 'Momentum',
  seed: 'Seed History',
  travel: 'Travel Advantage',
  injuries: 'Injuries',
}

function pct(n: number): string {
  return `${Math.round(n * 100)}%`
}

function Logo({ name, size = 24 }: { name: string; size?: number }) {
  const [failed, setFailed] = useState(false)
  const url = getLogoUrl(name)
  if (!url || failed) {
    return (
      <div
        className="rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0"
        style={{ width: size, height: size }}
      >
        <span className="text-[8px] font-bold text-slate-300">{getInitials(name)}</span>
      </div>
    )
  }
  return (
    <img
      src={url} alt={name} width={size} height={size}
      className="object-contain flex-shrink-0"
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  )
}

function accuracyColor(acc: number): string {
  if (acc >= 0.75) return 'bg-emerald-500'
  if (acc >= 0.60) return 'bg-blue-500'
  if (acc >= 0.50) return 'bg-yellow-500'
  return 'bg-red-500'
}

function accuracyTextColor(acc: number): string {
  if (acc >= 0.75) return 'text-emerald-400'
  if (acc >= 0.60) return 'text-blue-400'
  if (acc >= 0.50) return 'text-yellow-400'
  return 'text-red-400'
}

// ── Signal Report Card ──────────────────────────────────────────────

function SignalReportCard({ data }: { data: AnalysisData['signal_report_card'] }) {
  if (data.total_games === 0) {
    return <EmptyState message="No completed games yet. Results will appear once games are entered." />
  }

  return (
    <section>
      <h2 className="text-lg font-bold mb-4">Signal Report Card</h2>
      <p className="text-sm text-slate-400 mb-4">
        How accurate was each signal as a standalone predictor across {data.total_games} completed games?
      </p>

      {/* Model overall */}
      {data.model && (
        <div className="mb-4 p-3 rounded-lg bg-slate-800/80 border border-slate-700">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">Combined Model</span>
            <span className={`text-sm font-bold ${accuracyTextColor(data.model.accuracy)}`}>
              {data.model.correct}/{data.model.total} ({pct(data.model.accuracy)})
            </span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-3">
            <div
              className={`h-3 rounded-full ${accuracyColor(data.model.accuracy)} transition-all`}
              style={{ width: pct(data.model.accuracy) }}
            />
          </div>
        </div>
      )}

      {/* Per-signal bars */}
      <div className="space-y-3">
        {data.signals.map((s) => (
          <div key={s.signal} className="p-3 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{SIGNAL_LABELS[s.signal] || s.signal}</span>
                <span className="text-xs text-slate-500">({Math.round(s.weight * 100)}% weight)</span>
              </div>
              <span className={`text-sm font-bold ${accuracyTextColor(s.accuracy)}`}>
                {s.correct}/{s.total} ({pct(s.accuracy)})
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className={`h-2 rounded-full ${accuracyColor(s.accuracy)} transition-all`}
                style={{ width: pct(s.accuracy) }}
              />
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── Vegas vs Model ──────────────────────────────────────────────────

function VegasVsModel({ data }: { data: AnalysisData['vegas_vs_model'] }) {
  if (data.total_games === 0) {
    return <EmptyState message="No completed games yet." />
  }

  const modelRec = data.model_record
  const vegasRec = data.vegas_record

  return (
    <section>
      <h2 className="text-lg font-bold mb-4">Vegas vs. Model</h2>
      <p className="text-sm text-slate-400 mb-4">
        Head-to-head comparison across {data.total_games} completed games. Disagreement games shown first.
      </p>

      {/* Big numbers */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {modelRec && (
          <div className="p-4 rounded-lg bg-slate-800/80 border border-blue-500/30 text-center">
            <div className="text-2xl font-bold text-blue-400">{modelRec.correct}/{modelRec.total}</div>
            <div className="text-xs text-slate-400 mt-1">Model ({pct(modelRec.accuracy)})</div>
          </div>
        )}
        {vegasRec && (
          <div className="p-4 rounded-lg bg-slate-800/80 border border-amber-500/30 text-center">
            <div className="text-2xl font-bold text-amber-400">{vegasRec.correct}/{vegasRec.total}</div>
            <div className="text-xs text-slate-400 mt-1">Vegas ({pct(vegasRec.accuracy)})</div>
          </div>
        )}
      </div>

      {/* Game-by-game table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-xs text-slate-500 uppercase border-b border-slate-700">
              <th className="text-left py-2 px-2">Matchup</th>
              <th className="text-center py-2 px-2">Model Pick</th>
              <th className="text-center py-2 px-2">Vegas Pick</th>
              <th className="text-center py-2 px-2">Actual</th>
              <th className="text-center py-2 px-2">Score</th>
            </tr>
          </thead>
          <tbody>
            {data.games.map((g) => {
              const bothRight = g.model_correct && g.vegas_correct
              const bothWrong = !g.model_correct && g.vegas_correct === false
              const modelOnly = g.model_correct && !g.vegas_correct
              const vegasOnly = !g.model_correct && g.vegas_correct
              let rowBg = ''
              if (modelOnly) rowBg = 'bg-blue-500/10'
              else if (vegasOnly) rowBg = 'bg-amber-500/10'
              else if (bothWrong) rowBg = 'bg-red-500/10'

              return (
                <tr key={g.matchup_id} className={`border-b border-slate-800 ${rowBg}`}>
                  <td className="py-2 px-2">
                    <div className="flex items-center gap-1.5">
                      <Logo name={g.team_a} size={20} />
                      <span className="text-xs text-slate-500">{g.seed_a}</span>
                      <span className="text-slate-400 mx-1">vs</span>
                      <span className="text-xs text-slate-500">{g.seed_b}</span>
                      <Logo name={g.team_b} size={20} />
                    </div>
                  </td>
                  <td className="text-center py-2 px-2">
                    <span className={g.model_correct ? 'text-emerald-400' : 'text-red-400'}>
                      {g.model_pick}
                    </span>
                    <span className="text-xs text-slate-500 ml-1">({pct(g.model_conf)})</span>
                  </td>
                  <td className="text-center py-2 px-2">
                    {g.vegas_pick ? (
                      <>
                        <span className={g.vegas_correct ? 'text-emerald-400' : 'text-red-400'}>
                          {g.vegas_pick}
                        </span>
                        <span className="text-xs text-slate-500 ml-1">({pct(g.vegas_conf!)})</span>
                      </>
                    ) : (
                      <span className="text-slate-600">N/A</span>
                    )}
                  </td>
                  <td className="text-center py-2 px-2 font-medium">{g.actual_winner}</td>
                  <td className="text-center py-2 px-2 text-xs text-slate-500">
                    {g.actual_score_a != null && g.actual_score_b != null
                      ? `${g.actual_score_a}–${g.actual_score_b}`
                      : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="flex gap-4 mt-3 text-xs text-slate-500">
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-blue-500/30" /> Model right, Vegas wrong</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-amber-500/30" /> Vegas right, Model wrong</span>
        <span className="flex items-center gap-1"><span className="w-3 h-3 rounded bg-red-500/30" /> Both wrong</span>
      </div>
    </section>
  )
}

// ── Upset Autopsy ───────────────────────────────────────────────────

function UpsetAutopsy({ data }: { data: AnalysisData['upset_autopsy'] }) {
  if (data.total_games === 0) {
    return <EmptyState message="No completed games yet." />
  }
  if (data.total_upsets === 0) {
    return (
      <section>
        <h2 className="text-lg font-bold mb-4">Upset Autopsy</h2>
        <p className="text-sm text-slate-400">No upsets in {data.total_games} completed games. Chalk city.</p>
      </section>
    )
  }

  return (
    <section>
      <h2 className="text-lg font-bold mb-4">Upset Autopsy</h2>
      <p className="text-sm text-slate-400 mb-4">
        {data.total_upsets} upset{data.total_upsets > 1 ? 's' : ''} in {data.total_games} games
        ({pct(data.upset_rate)} upset rate). Biggest surprises first.
      </p>

      <div className="space-y-4">
        {data.upsets.map((u) => (
          <div key={u.matchup_id} className="p-4 rounded-lg bg-slate-800/60 border border-slate-700">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Logo name={u.underdog} size={28} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{u.underdog}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">
                      {u.underdog_seed} seed
                    </span>
                    <span className="text-slate-500">over</span>
                    <span className="text-slate-300">{u.favorite}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">
                      {u.favorite_seed} seed
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    {u.region} &middot; {u.round_name}
                    {u.actual_score_a != null && u.actual_score_b != null && (
                      <> &middot; {u.actual_score_a}–{u.actual_score_b}</>
                    )}
                  </div>
                </div>
              </div>
              <div className={`text-xs px-2 py-1 rounded font-medium ${
                u.model_had_upset
                  ? 'bg-emerald-500/20 text-emerald-400'
                  : 'bg-red-500/20 text-red-400'
              }`}>
                {u.model_had_upset ? 'Called It' : 'Missed'}
              </div>
            </div>

            {/* Signal breakdown */}
            <div className="text-xs text-slate-500 mb-2">
              Model confidence: {pct(u.model_confidence)} on {u.model_pick}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
              {u.signals.map((s) => (
                <div
                  key={s.signal}
                  className={`flex items-center justify-between px-2.5 py-1.5 rounded text-xs border ${
                    s.called_upset
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400'
                      : 'border-red-500/30 bg-red-500/10 text-red-400'
                  }`}
                >
                  <span>{SIGNAL_LABELS[s.signal] || s.signal}</span>
                  <span className="font-medium">{s.called_upset ? 'Saw it' : 'Missed'}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}

// ── Empty State ─────────────────────────────────────────────────────

function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-12 text-slate-500">
      <p>{message}</p>
    </div>
  )
}

// ── Main Dashboard ──────────────────────────────────────────────────

type TabId = 'signals' | 'vegas' | 'upsets'
const TABS: { id: TabId; label: string }[] = [
  { id: 'signals', label: 'Signal Report Card' },
  { id: 'vegas',   label: 'Vegas vs. Model' },
  { id: 'upsets',  label: 'Upset Autopsy' },
]

export default function AnalysisDashboard() {
  const [data, setData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<TabId>('signals')

  useEffect(() => {
    fetchAnalysis()
      .then(setData)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <div className="text-slate-400">Loading analysis...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-900 text-white flex items-center justify-center">
        <div className="text-red-400">Error: {error}</div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <h1 className="text-base sm:text-lg font-bold tracking-tight">Post-Tournament Analysis</h1>
            <p className="text-xs text-slate-500">Model performance after Round of 64</p>
          </div>
          <Link
            href="/"
            className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors"
          >
            Back to Bracket
          </Link>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-3 overflow-x-auto scrollbar-hide">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-600 text-white'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </header>

      {/* Tab content */}
      <div className="px-4 sm:px-6 py-6 max-w-4xl mx-auto">
        <div className="animate-fade-in">
          {activeTab === 'signals' && <SignalReportCard data={data.signal_report_card} />}
          {activeTab === 'vegas' && <VegasVsModel data={data.vegas_vs_model} />}
          {activeTab === 'upsets' && <UpsetAutopsy data={data.upset_autopsy} />}
        </div>
      </div>
    </div>
  )
}
