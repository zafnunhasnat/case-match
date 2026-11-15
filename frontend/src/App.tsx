import { useState } from 'react'
import Dashboard from './pages/Dashboard'
import SearchResults from './pages/SearchResults'
import Sidebar from './components/Sidebar'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [searchQuery, setSearchQuery] = useState('')
  const [recentSearches, setRecentSearches] = useState<string[]>([])
  const [sidebarOpen, setSidebarOpen] = useState(false)

  function navigateToSearch(query = '') {
    const trimmedQuery = query.trim()

    if (trimmedQuery !== ''){
      setRecentSearches((previousSearches) => [
        trimmedQuery,
        ...previousSearches.filter(
          (search) => search.toLowerCase() !== trimmedQuery.toLowerCase()
        ),
      ].slice(0,5))
    }

    setSearchQuery(trimmedQuery)
    setCurrentPage('search')
  }
  


  function navigateToPage(page: string){
    if(page === 'search'){
      navigateToSearch()
    } else {
      setCurrentPage('dashboard')
    }
    setSidebarOpen(false)
  }


  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Mobile header */}
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 p-4 md:hidden">
        <span className="text-xl font-bold text-blue-400">
          CaseMatch
        </span>

        <button
          type="button"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          aria-label={sidebarOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={sidebarOpen}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm"
        >
          {sidebarOpen ? 'Close' : 'Menu'}
        </button>
      </div>

      <div className="relative flex min-h screen">
        {/* Sidebar */}
        <div
          className={`${
            sidebarOpen ? 'block' : 'hidden'
          } absolute left-0 top-0 z-20 md:static md:block`}
        >
          <Sidebar
            currentPage={currentPage}
            onNavigate={navigateToPage}
          />
        </div>

        {/* Main page */}
        <main className="min-w-0 flex-1">
          {currentPage === 'dashboard' ? (
            <Dashboard
              onNavigateToSearch={navigateToSearch}
              recentSearches={recentSearches}
            />
          ) : (
            <SearchResults initialQuery={searchQuery} />
          )}
        </main>
      </div>
    </div>
  )
}

export default App
