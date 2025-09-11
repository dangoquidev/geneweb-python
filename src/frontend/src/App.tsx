import { useEffect, useState } from 'react'

type DatabaseInfo = {
  base_name: string
  persons: number
  families: number
  path: string
  version: string
}

export default function App() {
  const [databases, setDatabases] = useState<string[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [info, setInfo] = useState<DatabaseInfo | null>(null)
  const [q, setQ] = useState('')
  const [results, setResults] = useState<any[]>([])

  useEffect(() => {
    fetch('/api/databases').then(r => r.json()).then(d => setDatabases(d.databases || []))
  }, [])

  useEffect(() => {
    if (!selected) return
    fetch(`/api/${selected}/info`).then(r => r.json()).then(setInfo)
  }, [selected])

  const onSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selected || !q) return
    const r = await fetch(`/api/${selected}/search?q=${encodeURIComponent(q)}`)
    const d = await r.json()
    setResults(d.results || [])
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
          <div className="text-xl font-semibold">GenEWeb</div>
          <div className="text-sm opacity-70">Dark UI (React + Vite + Tailwind)</div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <section className="mb-6">
          <h2 className="text-lg font-medium mb-2">Databases</h2>
          <div className="flex flex-wrap gap-2">
            {databases.map((db) => (
              <button
                key={db}
                className={`px-3 py-1.5 rounded-md border ${selected === db ? 'bg-primary text-primary-foreground' : 'bg-card text-card-foreground border-border'}`}
                onClick={() => { setSelected(db); setResults([]); setQ('') }}
              >{db}</button>
            ))}
            {databases.length === 0 && <div className="text-muted-foreground text-sm">No databases found</div>}
          </div>
        </section>

        {selected && (
          <section className="grid md:grid-cols-3 gap-6">
            <div className="md:col-span-1 space-y-4">
              <div className="rounded-lg border border-border p-4 bg-card">
                <h3 className="font-medium mb-2">{selected}</h3>
                {info ? (
                  <ul className="text-sm space-y-1">
                    <li><span className="opacity-70">Persons:</span> {info.persons.toLocaleString()}</li>
                    <li><span className="opacity-70">Families:</span> {info.families.toLocaleString()}</li>
                    <li className="truncate"><span className="opacity-70">Path:</span> {info.path}</li>
                    <li><span className="opacity-70">Version:</span> {info.version}</li>
                  </ul>
                ) : (
                  <div className="text-sm opacity-70">Loading…</div>
                )}
              </div>

              <form onSubmit={onSearch} className="rounded-lg border border-border p-4 bg-card space-y-3">
                <div className="text-sm font-medium">Search</div>
                <input
                  className="w-full rounded-md bg-background border border-input px-3 py-2 outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Name to search…"
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                />
                <button className="w-full rounded-md px-3 py-2 bg-primary text-primary-foreground">Search</button>
              </form>
            </div>

            <div className="md:col-span-2">
              <div className="text-sm font-medium mb-2">Results</div>
              <div className="space-y-3">
                {results.map(p => (
                  <div key={p.id} className="rounded-lg border border-border p-4 bg-card">
                    <div className="flex items-center justify-between">
                      <div className="font-medium">{p.first_name} {p.surname}</div>
                      <div className="text-xs opacity-70">ID: {p.id}</div>
                    </div>
                    <div className="text-sm opacity-80">
                      {p.birth_date && <span className="mr-3">🎂 {p.birth_date}</span>}
                      {p.death_date && <span>✝ {p.death_date}</span>}
                    </div>
                    {p.occupation && <div className="text-sm opacity-90 mt-1">{p.occupation}</div>}
                  </div>
                ))}
                {results.length === 0 && <div className="text-sm text-muted-foreground">No results</div>}
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
