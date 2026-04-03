import { useEffect, useState } from 'react'
import { API_BASE } from '../api'

interface ModelStats {
  wins: number
  win_rate: number
  avg_latency_ms: number
}

interface StatsData {
  total_votes: number
  original: ModelStats
  finetuned: ModelStats
}

export default function Stats() {
  const [data, setData] = useState<StatsData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/stats`)
      .then((r) => r.json())
      .then(setData)
      .catch((e) => setError(String(e)))
  }, [])

  if (error) return <p className="text-center text-red-400 mt-20">{error}</p>
  if (!data) return <p className="text-center text-gray-500 mt-20 animate-pulse">Loading...</p>

  const models = [
    { key: 'original', label: 'Original CLIP', stats: data.original },
    { key: 'finetuned', label: 'Fine-tuned CLIP', stats: data.finetuned },
  ]

  return (
    <main className="max-w-3xl mx-auto px-4 py-10 flex flex-col gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Leaderboard</h1>
        <p className="text-gray-400 text-sm">{data.total_votes} votes cast</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {models.map(({ label, stats }) => (
          <div key={label} className="bg-gray-900 border border-gray-800 rounded-2xl p-6 flex flex-col gap-4">
            <h2 className="font-semibold text-lg">{label}</h2>

            <div className="flex flex-col gap-3">
              <Stat label="Win rate" value={`${stats.win_rate}%`} />
              <Stat label="Wins" value={String(stats.wins)} />
              <Stat label="Avg latency" value={`${stats.avg_latency_ms} ms`} />
            </div>

            <div className="w-full bg-gray-800 rounded-full h-2 mt-1">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all"
                style={{ width: `${stats.win_rate}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </main>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-gray-400">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </div>
  )
}
