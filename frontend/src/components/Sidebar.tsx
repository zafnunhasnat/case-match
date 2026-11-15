type SidebarProps = {
  currentPage: string
  onNavigate: (page: string) => void
}

function Sidebar({ currentPage, onNavigate }: SidebarProps) {
  return (
    <aside className="min-h-screen w-64 shrink-0 border-r border-slate-800 bg-slate-900 p-6">
      <h1 className="mb-10 text-2xl font-bold text-blue-400">
        CaseMatch
      </h1>

      <nav className="space-y-4">
        <button
          onClick={() => onNavigate('dashboard')}
          className={`w-full rounded-lg p-3 text-left ${
            currentPage === 'dashboard'
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
          }`}
        >
          Dashboard
        </button>

        <button
          onClick={() => onNavigate('search')}
          className={`w-full rounded-lg p-3 text-left ${
            currentPage === 'search'
              ? 'bg-slate-800 text-white'
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
          }`}
        >
          Search Cases
        </button>

        <div className="p-3 text-slate-500">
          Review Queue
        </div>
      </nav>
    </aside>
  )
}

export default Sidebar
