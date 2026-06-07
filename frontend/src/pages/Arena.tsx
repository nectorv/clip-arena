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

const SAMPLE_IMAGES = [
  'Capture.JPG',
  ...[1,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41].map(n => `Capture${n}.JPG`),
]

export default function Arena() {
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<string | null>(null)
  const [searchData, setSearchData] = useState<SearchResponse | null>(null)
  const [voteData, setVoteData] = useState<VoteReveal | null>(null)
  const [samplePreview, setSamplePreview] = useState<string | null>(null)

  async function handleSampleSelect(filename: string) {
    const url = `/samples/${filename}`
    setSamplePreview(url)
    try {
      const res = await fetch(url)
      const blob = await res.blob()
      const file = new File([blob], filename, { type: blob.type })
      handleUpload(file)
    } catch {
      setError('Failed to load sample image')
    }
  }

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
    setSamplePreview(null)
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-10 flex flex-col gap-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">CLIP Arena</h1>
        <p className="text-gray-400 text-sm">
          Upload a furniture image. Vote for the result set that best matches it. Discover which model wins — original or fine-tuned CLIP.
        </p>
      </div>

      <div className="max-w-md mx-auto w-full">
        <ImageUploader
          onUpload={handleUpload}
          disabled={phase === 'loading' || phase === 'voting'}
          previewOverride={samplePreview}
        />
      </div>

      {phase === 'idle' && (
        <div className="max-w-2xl mx-auto w-full">
          <p className="text-xs text-gray-500 uppercase tracking-widest mb-3 text-center">
            — or pick a sample —
          </p>
          <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-gray-700">
            {SAMPLE_IMAGES.map((filename) => (
              <button
                key={filename}
                onClick={() => handleSampleSelect(filename)}
                className="flex-shrink-0 w-20 h-20 rounded-lg overflow-hidden border-2 border-transparent hover:border-indigo-500 transition-colors focus:outline-none focus:border-indigo-400"
              >
                <img
                  src={`/samples/${filename}`}
                  alt={filename}
                  className="w-full h-full object-cover"
                />
              </button>
            ))}
          </div>
        </div>
      )}

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
