import { useState } from 'react'
import { useAuth } from '../../context/auth'
import { formatKickoff, ticketSite } from '../../utils/matches'
import { useAdminData } from './useAdminData'
import './AdminPages.css'

// The ticket link for one match: a small form for admins, read-only for staff
function TicketLink({ match, canEdit, onChange }) {
  const { authFetch } = useAuth()
  const [url, setUrl] = useState(match.ticketUrl ?? '')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const path = `/admin/crb/matches/${match.id}/ticket`

  const send = async (request) => {
    setBusy(true)
    setError(null)
    try {
      await request()
      onChange()
    } catch (err) {
      setError(err.data?.fieldErrors?.url ?? err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleSave = (event) => {
    event.preventDefault()
    send(() => authFetch(path, { method: 'PUT', body: { url: url.trim() } }))
  }

  const handleRemove = () => {
    if (!window.confirm('Remove the ticket link? Fans will see "Tickets aren\'t on sale yet".')) return
    send(async () => {
      await authFetch(path, { method: 'DELETE' })
      setUrl('')
    })
  }

  if (!canEdit) {
    return match.ticketUrl ? (
      <a href={match.ticketUrl} target="_blank" rel="noopener noreferrer" className="admin-link">
        {ticketSite(match.ticketUrl)}
      </a>
    ) : (
      <span className="admin-status admin-status--muted">No link</span>
    )
  }

  return (
    <form className="admin-ticket-form" onSubmit={handleSave}>
      <input
        type="url"
        required
        value={url}
        onChange={(event) => setUrl(event.target.value)}
        placeholder="https://… (the match's Digiticket page)"
        aria-label={`Ticket link for ${match.home.name} vs ${match.away.name}`}
      />
      <button type="submit" className="admin-button" disabled={busy || url.trim() === (match.ticketUrl ?? '')}>
        Save
      </button>
      {match.ticketUrl && (
        <button type="button" className="admin-link--danger" disabled={busy} onClick={handleRemove}>
          Remove
        </button>
      )}
      {error && (
        <p className="admin-ticket-error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}

// Upcoming CRB matches and where fans buy tickets for them
function AdminMatchesPage() {
  const { user } = useAuth()
  const { data: matches, error, loading, reload } = useAdminData('/admin/crb/matches')
  const canEdit = user.role === 'admin'

  return (
    <section>
      <header className="admin-page-header">
        <div>
          <h1>Matches</h1>
          <p>
            Paste each match's Digiticket page: the shop's CRB Analytics page shows a “Buy tickets”
            button that opens it.
            {!canEdit && ' Only admins can change the links.'}
          </p>
        </div>
      </header>

      {loading && <p className="admin-message">Loading matches…</p>}
      {error && <p className="admin-alert">{error}</p>}
      {matches?.length === 0 && <p className="admin-message">No upcoming matches scheduled.</p>}

      {matches?.length > 0 && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Kick-off (Algiers)</th>
                <th>Match</th>
                <th>Competition</th>
                <th>Ticket link</th>
              </tr>
            </thead>
            <tbody>
              {matches.map((match) => (
                <tr key={match.id}>
                  <td>
                    {formatKickoff(match)}
                    {match.status !== 'upcoming' && <small>{match.statusText}</small>}
                  </td>
                  <td>
                    <strong>
                      {match.home.name} vs {match.away.name}
                    </strong>
                    {match.venue && <small>{match.venue}</small>}
                  </td>
                  <td>{match.competition.name}</td>
                  <td className="is-wrap">
                    <TicketLink match={match} canEdit={canEdit} onChange={reload} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default AdminMatchesPage
