import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import Arena from './pages/Arena'
import Stats from './pages/Stats'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-950 text-gray-100">
        <nav className="border-b border-gray-800 px-6 py-4 flex items-center gap-8">
          <span className="font-bold text-lg tracking-tight">CLIP Arena</span>
          <Link to="/" className="text-sm text-gray-400 hover:text-white transition-colors">
            Arena
          </Link>
          <Link to="/stats" className="text-sm text-gray-400 hover:text-white transition-colors">
            Stats
          </Link>
        </nav>
        <Routes>
          <Route path="/" element={<Arena />} />
          <Route path="/stats" element={<Stats />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
