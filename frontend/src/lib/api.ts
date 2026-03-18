import { BracketData, ChampionLikelihood } from './types'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? 'Request failed')
  }
  return res.json()
}

export const fetchBracket = (): Promise<BracketData> =>
  request('/bracket')

export const makePick = (matchupId: string, winner: string): Promise<{ updated: string[]; bracket: BracketData }> =>
  request(`/bracket/${matchupId}/pick`, {
    method: 'POST',
    body: JSON.stringify({ winner }),
  })

export const undoPick = (matchupId: string): Promise<{ updated: string[]; bracket: BracketData }> =>
  request(`/bracket/${matchupId}/pick`, { method: 'DELETE' })

export const resetBracket = (): Promise<BracketData> =>
  request('/bracket/reset', { method: 'POST' })

export const fetchChampionLikelihood = (): Promise<ChampionLikelihood[]> =>
  request('/champion-likelihood')
