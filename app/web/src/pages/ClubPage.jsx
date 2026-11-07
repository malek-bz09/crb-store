import { useEffect, useState } from 'react'
import CatalogMessage from '../components/CatalogMessage'
import NextMatch from '../components/club/NextMatch'
import SeasonStats from '../components/club/SeasonStats'
import MatchList from '../components/club/MatchList'
import StandingsTable from '../components/club/StandingsTable'
import { fetchCrbOverview } from '../services/crb'
import { formatSeason, formatUpdated } from '../utils/matches'
import './ClubPage.css'

const ALL = 'all'
// Longer lists start with this many matches and a "Show all" button
const SHOWN = 8

// CRB Analytics: next match with tickets, the season's matches, the table and season numbers
function ClubPage() {
  const [state, setState] = useState({ data: null, error: null })
  const [competitionId, setCompetitionId] = useState(ALL)
  const [allUpcoming, setAllUpcoming] = useState(false)
  const [allResults, setAllResults] = useState(false)

  useEffect(() => {
    let ignore = false
    fetchCrbOverview().then(
      (data) => !ignore && setState({ data, error: null }),
      (error) => !ignore && setState({ data: null, error: error.message }),
    )
    return () => {
      ignore = true
    }
  }, [])

  const { data, error } = state
  if (!data) return <CatalogMessage error={error} loadingText="Loading match data…" />

  const crbId = data.team.id
  // null when showing every competition
  const competition = data.competitions.find((c) => c.id === competitionId) ?? null
  const inCompetition = (match) => !competition || match.competition.id === competition.id
  const upcoming = data.upcoming.filter(inCompetition)
  const results = data.results.filter(inCompetition)
  const shownUpcoming = allUpcoming ? upcoming : upcoming.slice(0, SHOWN)
  const shownResults = allResults ? results : results.slice(0, SHOWN)
  const tables = (competition ? [competition] : data.competitions).filter((c) => c.standings.length > 0)

  return (
    <div className="club">
      <header className="club-header">
        {data.team.logo && <img src={data.team.logo} alt="" width="56" height="56" />}
        <div>
          <p>Season {formatSeason(data.season)}</p>
          <h1>CRB Analytics</h1>
        </div>
      </header>

      <NextMatch match={data.nextMatch} />

      {data.competitions.length > 1 && (
        <div className="club-tabs" role="group" aria-label="Show competition">
          {[{ id: ALL, name: 'All competitions' }, ...data.competitions].map((c) => (
            <button
              key={c.id}
              type="button"
              aria-pressed={competitionId === c.id}
              onClick={() => {
                setCompetitionId(c.id)
                setAllUpcoming(false)
                setAllResults(false)
              }}
            >
              {c.name}
            </button>
          ))}
        </div>
      )}

      <section className="club-section">
        <h2>Season so far</h2>
        <SeasonStats stats={competition ? competition.stats : data.stats} />
      </section>

      <div className="club-columns">
        <section className="club-section">
          <h2>Upcoming</h2>
          <MatchList
            matches={shownUpcoming}
            crbId={crbId}
            showCompetition={!competition}
            empty="No upcoming matches scheduled."
          />
          {upcoming.length > SHOWN && (
            <button type="button" className="club-more" onClick={() => setAllUpcoming((v) => !v)}>
              {allUpcoming ? 'Show fewer' : `Show all ${upcoming.length} matches`}
            </button>
          )}
        </section>
        <section className="club-section">
          <h2>Results</h2>
          <MatchList
            matches={shownResults}
            crbId={crbId}
            showCompetition={!competition}
            empty="No results yet this season."
          />
          {results.length > SHOWN && (
            <button type="button" className="club-more" onClick={() => setAllResults((v) => !v)}>
              {allResults ? 'Show fewer' : `Show all ${results.length} results`}
            </button>
          )}
        </section>
      </div>

      <section className="club-section">
        <h2>Tables</h2>
        {data.unavailable.includes('standings') ? (
          <p className="club-empty">The table isn't available yet. Please try again later.</p>
        ) : tables.length === 0 ? (
          <p className="club-empty">No table for this competition.</p>
        ) : (
          tables.flatMap((c) =>
            c.standings.map((group) => (
              <StandingsTable key={`${c.id}-${group.name}`} title={c.name} group={group} crbId={crbId} />
            )),
          )
        )}
      </section>


      <p className="club-source">
        Match data from{' '}
        <a href="https://www.thesportsdb.com" target="_blank" rel="noopener noreferrer">
          TheSportsDB
        </a>
        {data.updatedAt && `, updated ${formatUpdated(data.updatedAt)}`}. Times are Algiers time.
      </p>
    </div>
  )
}

export default ClubPage
