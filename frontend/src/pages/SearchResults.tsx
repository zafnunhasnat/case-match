import { useEffect, useState } from 'react'
import { searchCases } from '../api/cases'
import type { SearchResult } from '../api/cases'

type SearchResultsProps = {
    initialQuery: string
}

function SearchResults({ initialQuery }: SearchResultsProps) {
    const [searchQuery, setSearchQuery] = useState(initialQuery)
    const [submittedQuery, setSubmittedQuery] = useState(initialQuery)

    const [rankedCases, setRankedCases] = useState<SearchResult[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState('')

    const query = submittedQuery.toLowerCase().trim()
    useEffect(() => {
        let cancelled = false

        async function loadCases() {
            setIsLoading(true)
            setError('')

            try {
                const results = await searchCases(submittedQuery)

                if(!cancelled) {
                    setRankedCases(results)
                }
            } catch {
                if (!cancelled) {
                    setError('Unable to load cases, please try again.')
                    setRankedCases([])
                }
            } finally {
                if (!cancelled) {
                    setIsLoading(false)
                }
            }
        }
        loadCases()
        return() => {
            cancelled = true
        }
    }, [submittedQuery])
            
  return (
    <div className="min-h-screen bg-slate-950 px-4 py-6 text-white sm:px-6 sm:py-8 lg:px-10 lg:py-10">
      <h1 className="text-2xl font-bold sm:text-3xl">
        Search Cases
      </h1>

      <p className="mt-2 text-slate-400">
        Explore similar historical clinical cases.
      </p>

      <form
        onSubmit={(e) => {
            e.preventDefault()
            setSubmittedQuery(searchQuery)
        }}
        className="mt-8 flex flex-col gap-4 sm:flex-row"
        >
            <input
                type="text"
                placeholder="Enter symptoms or clinical keywords..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                aria-label="Search clinical cases"
                className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 p-4 outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-400/30"
            />

            <button
                type="submit"
                className="rounded-lg bg-blue-600 px-6 py-3 font-medium hover:bg-blue-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
                >
                    Search
            </button>     
        </form> 

      <h2 className="mt-10 text-xl font-semibold">Search Results</h2>
      {isLoading && (
        <p className="mt-4 text-blue-400">Searching cases...</p>
      )}
      {error && (
        <p role="alert" className="mt-4 text-red-400">{error}</p>
      )}
      <p className="mt-2 text-sm text-slate-400">
        {rankedCases.length} cases found
      </p>

      {!isLoading && !error && rankedCases.length === 0 && (
        <p className="mt-6 text-slate-400">
            No matching cases found. Please try different keywords or symptoms.
        </p>
      )}

      <div className="mt-6 space-y-4">
        {!isLoading && !error && rankedCases.map((caseItem) => (
            <div
                key={caseItem.id}
                className="rounded-xl border border-slate-700 bg-slate-900 p-4 transition-all hover:border-blue-500 hover:shadow-lg hover:shadow-blue-950/30 sm:p-6"
            >
                {/* Case number and keyword score */}
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm font-medium text-slate-400">
                        Case #{caseItem.id}
                    </span>

                    {query !== '' && (
                        <span className="rounded-full border border-green-800 bg-green-950 px-3 py-1 text-sm font-medium text-green-400">
                            Keyword Match: {caseItem.score}/6
                        </span>
                    )}
                </div>

                {/* Case title */}
                <h3 className="mt-4 text-xl font-semibold text-blue-400">
                    {caseItem.title}
                </h3>

                {/* Patient Information */}
                <p className="mt-2 text-sm text-slate-400">
                    Patient Age: {caseItem.age}
                </p>

                {/* Case Summary */}
                <p className="mt-4 leading-relaxed text-slate-300">
                    {caseItem.summary}
                </p>

                {/* Symptoms */}
                <div className="mt-4 flex flex-wrap gap-2">
                    {caseItem.symptoms.map((symptom) => (
                        <span
                            key={symptom}
                            className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-sm text-blue-300"
                            >
                                {symptom}

            
                            </span>
                    ))}
                </div>

                {/* Case action */}
                <div className="mt-6 border-t border-slate-800 pt-4">
                    <button
                        type="button"
                        disabled
                        title="Case viewer coming soon"
                        className="cursor-not-allowed rounded-lg bg-slate-700 px-5 py-2 text-sm font-medium text-slate-400"
                    >
                        View Case (Coming Soon)
                    </button>
                </div>
            </div>

        ))}
      </div>
    </div>
  );
}

export default SearchResults;
