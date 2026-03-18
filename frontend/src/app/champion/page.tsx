'use client'
import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { ChampionLikelihood, ChampionCheck } from '@/lib/types'
import { fetchChampionLikelihood } from '@/lib/api'
import { getLogoUrl, getInitials } from '@/lib/teamLogos'

function Logo({ name, size = 28 }: { name: string; size?: number }) {
  const [failed, setFailed] = useState(false)
  const url = getLogoUrl(name)

  if (!url || failed) {
    return (
      <div
        className="rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0"
        style={{ width: size, height: size }}
      >
        <span className="text-[9px] font-bold text-slate-300">{getInitials(name)}</span>
      </div>
    )
  }

  return (
    <img
      src={url}
      alt={name}
      width={size}
      height={size}
      className="object-contain flex-shrink-0"
      style={{ width: size, height: size }}
      onError={() => setFailed(true)}
    />
  )
}

function getSuffix(n: number): string {
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return s[(v - 20) % 10] || s[v] || s[0]
}

// Proximity rules show rank values; binary rules show check/x
const PROXIMITY_RULES = new Set([
  'torvik_overall_top25', 'torvik_overall_top6',
  'torvik_adjD_top25', 'torvik_adjD_top7',
  'torvik_adjO_top40', 'torvik_adjO_top21',
])

type SortKey = 'score' | 'team' | 'seed' | string

export default function ChampionPage() {
  const [teams, setTeams] = useState<ChampionLikelihood[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('score')
  const [sortAsc, setSortAsc] = useState(false)
  const [showEliminated, setShowEliminated] = useState(true)

  useEffect(() => {
    fetchChampionLikelihood()
      .then(setTeams)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  // Collect all unique check rule_ids for column headers
  const checkColumns = useMemo(() => {
    if (teams.length === 0) return []
    const first = teams[0]
    return first.checks.map((c: ChampionCheck) => ({
      rule_id: c.rule_id,
      label: c.label,
      is_hard: c.is_hard,
    }))
  }, [teams])

  const sorted = useMemo(() => {
    const list = showEliminated ? [...teams] : teams.filter(t => !t.hard_filter_failed)
    list.sort((a, b) => {
      let cmp = 0
      if (sortKey === 'score') cmp = a.score - b.score
      else if (sortKey === 'team') cmp = a.team.localeCompare(b.team)
      else if (sortKey === 'seed') cmp = (a.seed ?? 99) - (b.seed ?? 99)
      else {
        // Sort by a specific check's value or pass status
        const aCheck = a.checks.find((c: ChampionCheck) => c.rule_id === sortKey)
        const bCheck = b.checks.find((c: ChampionCheck) => c.rule_id === sortKey)
        const aVal = aCheck?.value ?? (aCheck?.passed ? 0 : 999)
        const bVal = bCheck?.value ?? (bCheck?.passed ? 0 : 999)
        cmp = (aVal as number) - (bVal as number)
      }
      return sortAsc ? cmp : -cmp
    })
    return list
  }, [teams, sortKey, sortAsc, showEliminated])

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortAsc(!sortAsc)
    } else {
      setSortKey(key)
      setSortAsc(key === 'team' || key === 'seed')
    }
  }

  const sortArrow = (key: SortKey) =>
    sortKey === key ? (sortAsc ? ' ↑' : ' ↓') : ''

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-slate-900 text-slate-400">Loading champion data...</div>
  )
  if (error) return (
    <div className="flex items-center justify-center h-screen bg-slate-900 text-red-400">Error: {error}</div>
  )

  const contenders = teams.filter(t => !t.hard_filter_failed).length
  const eliminated = teams.filter(t => t.hard_filter_failed).length

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-slate-900/95 backdrop-blur border-b border-slate-800 px-4 sm:px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <h1 className="text-base sm:text-lg font-bold tracking-tight">Champion Profiles</h1>
            <p className="text-[10px] sm:text-xs text-slate-400">
              {contenders} contenders · {eliminated} eliminated by hard filters · display only, not part of predictions
            </p>
          </div>
          <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
            <label className="flex items-center gap-1.5 text-[10px] text-slate-400 cursor-pointer">
              <input
                type="checkbox"
                checked={showEliminated}
                onChange={e => setShowEliminated(e.target.checked)}
                className="rounded border-slate-600 bg-slate-800 text-blue-600 focus:ring-blue-500 focus:ring-offset-0 w-3 h-3"
              />
              Show eliminated
            </label>
            <Link
              href="/"
              className="text-xs text-slate-400 hover:text-white border border-slate-700 hover:border-slate-500 rounded px-3 py-1 transition-colors"
            >
              Back to Bracket
            </Link>
          </div>
        </div>
      </header>

      {/* Table */}
      <div className="px-4 sm:px-6 py-4 overflow-x-auto">
        <table className="w-full text-[10px] sm:text-xs border-collapse min-w-[800px]">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="text-left py-2 px-2 text-slate-500 uppercase tracking-widest font-semibold w-8">#</th>
              <th
                className="text-left py-2 px-2 text-slate-500 uppercase tracking-widest font-semibold cursor-pointer hover:text-white transition-colors"
                onClick={() => handleSort('team')}
              >
                Team{sortArrow('team')}
              </th>
              <th
                className="text-center py-2 px-2 text-slate-500 uppercase tracking-widest font-semibold cursor-pointer hover:text-white transition-colors w-12"
                onClick={() => handleSort('seed')}
              >
                Seed{sortArrow('seed')}
              </th>
              <th
                className="text-center py-2 px-2 text-slate-500 uppercase tracking-widest font-semibold cursor-pointer hover:text-white transition-colors w-16"
                onClick={() => handleSort('score')}
              >
                Score{sortArrow('score')}
              </th>
              {checkColumns.map(col => (
                <th
                  key={col.rule_id}
                  className={`text-center py-2 px-1.5 uppercase tracking-widest font-semibold cursor-pointer hover:text-white transition-colors whitespace-nowrap ${
                    col.is_hard ? 'text-slate-400' : 'text-slate-500'
                  }`}
                  onClick={() => handleSort(col.rule_id)}
                  title={col.is_hard ? `${col.label} (hard filter)` : col.label}
                >
                  {col.label.replace('Torvik ', '').replace('AP Poll ', 'AP ')}{col.is_hard ? '*' : ''}{sortArrow(col.rule_id)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((team, i) => {
              const dimmed = team.hard_filter_failed
              return (
                <tr
                  key={team.team}
                  className={`border-b border-slate-800/50 transition-colors ${
                    dimmed ? 'opacity-40' : 'hover:bg-slate-800/40'
                  }`}
                >
                  <td className="py-2 px-2 text-slate-600 font-mono">{i + 1}</td>
                  <td className="py-2 px-2">
                    <div className="flex items-center gap-2">
                      <Logo name={team.team} size={24} />
                      <div className="min-w-0">
                        <span className="font-semibold text-white truncate block">{team.team}</span>
                        {team.region && <span className="text-[9px] text-slate-500">{team.region}</span>}
                      </div>
                      {dimmed && (
                        <span className="text-[8px] font-bold text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded flex-shrink-0">
                          ELIMINATED
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className="text-[10px] font-bold text-slate-400 bg-slate-700 rounded-full w-5 h-5 inline-flex items-center justify-center">
                      {team.seed}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className={`font-bold ${
                      team.score >= 60 ? 'text-emerald-400' : team.score >= 30 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {team.score}
                    </span>
                  </td>
                  {checkColumns.map(col => {
                    const check = team.checks.find((c: ChampionCheck) => c.rule_id === col.rule_id)
                    if (!check) return <td key={col.rule_id} className="py-2 px-1.5 text-center text-slate-600">—</td>

                    const isProximity = PROXIMITY_RULES.has(check.rule_id)
                    const isHardFail = check.is_hard && check.passed === false

                    return (
                      <td
                        key={col.rule_id}
                        className={`py-2 px-1.5 text-center ${isHardFail ? 'bg-red-500/5' : ''}`}
                        title={check.detail}
                      >
                        {isProximity && check.value !== null ? (
                          <span className={`font-bold ${
                            check.passed === true ? 'text-emerald-400' : isHardFail ? 'text-red-400 font-extrabold' : 'text-red-400/70'
                          }`}>
                            {check.value}{getSuffix(check.value)}
                          </span>
                        ) : (
                          <span className={
                            check.passed === true ? 'text-emerald-400' : check.passed === false ? (isHardFail ? 'text-red-400 font-extrabold' : 'text-red-400/70') : 'text-slate-600'
                          }>
                            {check.passed === true ? '✓' : check.passed === false ? '✗' : '—'}
                          </span>
                        )}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>
        </table>

        {/* Legend */}
        <div className="mt-4 flex flex-wrap gap-4 text-[10px] text-slate-500">
          <span><span className="text-emerald-400">green</span> = passes check</span>
          <span><span className="text-red-400">red</span> = fails check</span>
          <span>* = hard filter (eliminates team)</span>
          <span className="italic">Hover any cell for details</span>
        </div>
      </div>
    </div>
  )
}
