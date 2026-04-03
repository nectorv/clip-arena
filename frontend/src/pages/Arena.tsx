import { useState } from 'react'
import { API_BASE } from '../api'
import ImageUploader from '../components/ImageUploader'
import ResultPanel from '../components/ResultPanel'

interface SearchResult {
  score: number
  title: string
  price: string
  source: string
  image_url: string
}

interface Panel {
  results: SearchResult[]
  latency_ms: number
}

interface SearchResponse {
  session_id: string
  panel_a: Panel
  panel_b: Panel
}

interface VoteReveal {
  winner: string
  reveal: { panel_a: string; panel_b: string }
}

type Phase = 'idle' | 'loading' | 'voting' | 'revealed'

export default function Arena() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [searchData, setSearchData] = useState<SearchResponse | null>(null)
  const [voteData, setVoteData] = useState<VoteReveal | null>(null)

  async function handleUpload(file: File) {
    setPhase('loading')
    setError(null)
    setSearchData(null)
    setVoteData(null)

    const form = new FormData()
    form.append('file', file)

    try {
      const res = await fetch(`${API_BASE}/search`, { method: 'POST', body: form })
      if (!res.ok) throw new Error(`Search failed: ${res.status}`)
      const data: SearchResponse = await res.json()
      setSearchData(data)
      setPhase('voting')
    } catch (e) {
      setError(String(e))
      setPhase('idle')
    }
  }

  async function handleVote(panel: 'a' | 'b') {
    if (!searchData) return
    try {
      const res = await fetch(`${API_BASE}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: searchData.session_id, chosen_panel: panel }),
      })
      if (!res.ok) throw new Error(`Vote failed: ${res.status}`)
      const data: VoteReveal = await res.json()
      setVoteData(data)
      setPhase('revealed')
    } catch (e) {
      setError(String(e))
    }
  }

  function reset() {
    setPhase('idle')
    setSearchData(null)
    setVoteData(null)
    setError(null)
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-10 flex flex-col gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">CLIP Arena</h1>
        <p className="text-gray-400 text-sm">
          Upload a furniture image. Vote for the result set that best matches it. Discover which model wins.
        </p>
      </div>

      <div className="max-w-md mx-auto w-full">
        <ImageUploader onUpload={handleUpload} disabled={phase === 'loading' || phase === 'voting'} />
      </div>

      {phase === 'loading' && (
        <div className="text-center text-gray-400 animate-pulse">Running both models...</div>
      )}

      {error && (
        <div className="text-center text-red-400 text-sm">{error}</div>
      )}

      {(phase === 'voting' || phase === 'revealed') && searchData && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <ResultPanel
              label="A"
              results={searchData.panel_a.results}
              latency_ms={searchData.panel_a.latency_ms}
              revealed={voteData?.reveal.panel_a}
              winner={voteData?.winner}
              highlight={voteData?.winner === voteData?.reveal.panel_a}
            />
            <ResultPanel
              label="B"
              results={searchData.panel_b.results}
              latency_ms={searchData.panel_b.latency_ms}
              revealed={voteData?.reveal.panel_b}
              winner={voteData?.winner}
              highlight={voteData?.winner === voteData?.reveal.panel_b}
            />
          </div>

          {phase === 'voting' && (
            <div className="flex justify-center gap-4">
              <button
                onClick={() => handleVote('a')}
                className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold transition-colors"
              >
                Model A is better
              </button>
              <button
                onClick={() => handleVote('b')}
                className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-semibold transition-colors"
              >
                Model B is better
              </button>
            </div>
          )}

          {phase === 'revealed' && voteData && (
            <div className="text-center flex flex-col items-center gap-4">
              <p className="text-green-400 font-semibold text-lg">
                You preferred {voteData.winner === 'finetuned' ? 'Fine-tuned CLIP' : 'Original CLIP'}
              </p>
              <button
                onClick={reset}
                className="px-6 py-2 rounded-xl border border-gray-600 hover:border-gray-400 text-sm transition-colors"
              >
                Try another image
              </button>
            </div>
          )}
        </>
      )}
    </main>
  )
}
