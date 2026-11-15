import { useState } from 'react'
import { mockCases } from '../data/mockCases'

type DashboardProps = {
    onNavigateToSearch: (query?: string) => void
    recentSearches: string[]
}

function Dashboard({ onNavigateToSearch, recentSearches }: DashboardProps){
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <div className="min-h-screen bg-slate-950 text-white">


      {/* Main dashboard */}
      <main className="flex-1 p-10">
        <h2 className="text-3xl font-bold">
          Dashboard
        </h2>

        <p className="mt-2 text-slate-400">
          Search and explore historical clinical cases.
        </p>

        {/* Search bar */}
        <div className="mt-10 rounded-xl border border-slate-700 bg-slate-900 p-6">
          <h3 className="mb-4 text-xl font-semibold">
            Find Similar Cases
          </h3>

          <input
            type="text"
            placeholder="Describe a clinical case or enter keywords..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 p-4 text-white outline-none focus:border-blue-400"
          />

          <button
            onClick={() => onNavigateToSearch(searchQuery)}
            className="mt-4 rounded-lg bg-blue-600 px-6 py-3 font-semibold hover:bg-blue-700"
          >
            Search Cases
          </button>
        </div>

        {/* Dashboard cards */}
        <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
                <h3 className="text-slate-400">Recent Searches</h3>

                <p className="mt-3 text-2xl font-bold">
                    {recentSearches.length}
                </p>

                {recentSearches.length === 0 ? (
                    <p className="mt-2 text-sm text-slate-500">
                        No recent searches yet
                    </p>
                ) : (
                    <div className="mt-4 space-y-2">
                        {recentSearches.map((search) => (
                            <button
                              key={search}
                              onClick={() => onNavigateToSearch(search)}
                              className="block w-full rounded-lg bg-slate-800 p-2 text-left text-sm text-blue-300 hover:bg-slate-700"
                            >
                                {search}
                            </button>
                        ))}
                    </div>
                )}
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
                <h3 className="text-slate-400">Available Cases</h3>
                <p className="mt-3 text-2xl font-bold">
                    {mockCases.length}
                </p>
                <p className="mt-2 text-sm text-slate-500">
                    Mock cases for testing
                </p>
            </div>

            <div className="rounded-xl border border-slate-700 bg-slate-900 p-6">
                <h3 className="text-slate-400">Review Queue</h3>
                <p className="mt-3 text-2xl font-bold">0</p>
                <p className="mt-2 text-sm text-slate-500">
                    Review queue not connected yet
                </p>
            </div>
        </div>

      </main>
    </div>
  )
}

export default Dashboard
