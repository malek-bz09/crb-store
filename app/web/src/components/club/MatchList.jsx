import FormChip from "./FormChip";
import TeamName from "./TeamName";
import { formatKickoffTime, formatMatchDay } from "../../utils/matches";

const STATUS_NOTES = {
  postponed: "Postponed",
  cancelled: "Cancelled",
  live: "Live",
};

function MatchRow({ match, crbId, showCompetition }) {
  const hasScore = match.status === "finished" || match.status === "live";
  const postponed = match.status === "postponed";
  return (
    <li className="club-match">
      <div className="club-match-meta">
        {/* A postponed match's old date no longer means anything */}
        {postponed ? (
          <span className="club-match-tbc">Date TBC</span>
        ) : (
          <time dateTime={match.date}>{formatMatchDay(match)}</time>
        )}
        {showCompetition && <span>{match.competition.name}</span>}
      </div>
      <div className="club-match-teams">
        <TeamName team={match.home} crbId={crbId} align="end" />
        <span className="club-match-score">
          {hasScore
            ? `${match.home.goals ?? 0} – ${match.away.goals ?? 0}`
            : postponed
              ? "vs"
              : formatKickoffTime(match)}
        </span>
        <TeamName team={match.away} crbId={crbId} />
      </div>
      <div className="club-match-end">
        {match.result && <FormChip result={match.result} />}
        {STATUS_NOTES[match.status] && (
          <span className="club-match-status">
            {STATUS_NOTES[match.status]}
          </span>
        )}
        {match.ticketUrl && (
          <a
            href={match.ticketUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="club-match-ticket"
          >
            Tickets
          </a>
        )}
      </div>
    </li>
  );
}

function MatchList({ matches, crbId, showCompetition, empty }) {
  if (matches.length === 0) return <p className="club-empty">{empty}</p>;
  return (
    <ul className="club-matches">
      {matches.map((match) => (
        <MatchRow
          key={match.id}
          match={match}
          crbId={crbId}
          showCompetition={showCompetition}
        />
      ))}
    </ul>
  );
}

export default MatchList;
