import { formatKickoff, ticketSite } from '../../utils/matches'

function Crest({ team }) {
  return (
    <div className="club-next-team">
      {/* An empty circle when there's no crest, so both teams line up */}
      {team.logo ? <img src={team.logo} alt="" width="72" height="72" /> : <span className="club-next-crest" />}
      <strong>{team.name}</strong>
    </div>
  )
}

// The big card at the top: who, when, where, and the ticket button
function NextMatch({ match }) {
  if (!match) {
    return (
      <section className="club-next">
        <p className="club-next-note">No upcoming match is scheduled yet. Check back soon.</p>
      </section>
    )
  }

  const live = match.status === 'live'

  return (
    <section className="club-next" aria-labelledby="club-next-title">
      <p id="club-next-title" className="club-next-kicker">
        {live ? <span className="club-live">Live now</span> : 'Next match'} · {match.competition.name}
        {match.round && ` · ${match.round}`}
      </p>

      <div className="club-next-teams">
        <Crest team={match.home} />
        <span className="club-next-score">
          {live ? `${match.home.goals ?? 0} – ${match.away.goals ?? 0}` : 'vs'}
        </span>
        <Crest team={match.away} />
      </div>

      <p className="club-next-when">
        <time dateTime={match.date}>{formatKickoff(match)}</time>
        {match.venue && <span> · {match.venue}</span>}
      </p>

      {match.ticketUrl ? (
        <div className="club-next-tickets">
          {/* noopener: the ticket site can't control this tab */}
          <a href={match.ticketUrl} target="_blank" rel="noopener noreferrer" className="club-ticket-button">
            Buy tickets
          </a>
          <small>Opens {ticketSite(match.ticketUrl)} in a new tab</small>
        </div>
      ) : (
        <p className="club-next-note">Tickets aren't on sale yet. Check back closer to the match.</p>
      )}
    </section>
  )
}

export default NextMatch
