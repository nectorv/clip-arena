interface Result {
  score: number
  title: string
  price: string
  source: string
  image_url: string
}

interface Props {
  label: string
  results: Result[]
  latency_ms: number
  revealed?: string  // 'original' | 'finetuned' | undefined
  winner?: string    // which model won
  highlight?: boolean
}

const MODEL_LABELS: Record<string, string> = {
  original: 'Original CLIP',
  finetuned: 'Fine-tuned CLIP',
}

export default function ResultPanel({ label, results, latency_ms, revealed, winner, highlight }: Props) {
  return (
    <div className={`flex flex-col gap-4 rounded-2xl border p-4 transition-all
      ${highlight ? 'border-green-500 bg-green-950/20' : 'border-gray-800 bg-gray-900'}`}>
      <div className="flex items-center justify-between">
        <span className="font-semibold text-lg">
          {revealed ? (
            <span>
              {MODEL_LABELS[revealed]}
              {winner === revealed && (
                <span className="ml-2 text-xs bg-green-600 text-white px-2 py-0.5 rounded-full">Winner</span>
              )}
            </span>
          ) : (
            <span className="text-gray-300">Model {label}</span>
          )}
        </span>
        <span className="text-xs text-gray-500">{latency_ms} ms</span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {results.map((r, i) => (
          <div key={i} className="bg-gray-800 rounded-xl overflow-hidden flex flex-col">
            {r.image_url ? (
              <img
                src={r.image_url}
                alt={r.title}
                className="w-full h-36 object-cover"
                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
              />
            ) : (
              <div className="w-full h-36 bg-gray-700 flex items-center justify-center text-gray-500 text-xs">
                No image
              </div>
            )}
            <div className="p-2 flex flex-col gap-0.5">
              <p className="text-xs font-medium line-clamp-2 text-gray-200">{r.title}</p>
              <p className="text-xs text-gray-400">{r.price}</p>
              <p className="text-xs text-indigo-400 font-mono">score {r.score.toFixed(3)}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
