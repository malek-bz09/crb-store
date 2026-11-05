import TeamName from './TeamName'

// One league table (or one group of a group stage), CRB's row highlighted
function StandingsTable({ title, group, crbId }) {
  return (
    <div className="club-table-wrap">
      <table className="club-table">
        <caption>
          {group.name && group.name !== title ? `${title} · ${group.name}` : title}
          {group.topOnly && <small> · top {group.rows.length}</small>}
        </caption>
        <thead>
          <tr>
            <th scope="col" className="is-number">#</th>
            <th scope="col">Team</th>
            <th scope="col" className="is-number" title="Played">P</th>
            <th scope="col" className="is-number" title="Won">W</th>
            <th scope="col" className="is-number" title="Drawn">D</th>
            <th scope="col" className="is-number" title="Lost">L</th>
            <th scope="col" className="is-number club-table-extra" title="Goals for and against">Goals</th>
            <th scope="col" className="is-number" title="Goal difference">GD</th>
            <th scope="col" className="is-number" title="Points">Pts</th>
          </tr>
        </thead>
        <tbody>
          {group.rows.map((row) => (
            <tr key={row.team.id} className={row.isCrb ? 'is-crb' : undefined} title={row.description ?? undefined}>
              <td className="is-number">{row.rank}</td>
              <td>
                <TeamName team={row.team} crbId={crbId} />
              </td>
              <td className="is-number">{row.played}</td>
              <td className="is-number">{row.wins}</td>
              <td className="is-number">{row.draws}</td>
              <td className="is-number">{row.losses}</td>
              <td className="is-number club-table-extra">
                {row.goalsFor}:{row.goalsAgainst}
              </td>
              <td className="is-number">{row.goalDiff > 0 ? `+${row.goalDiff}` : row.goalDiff}</td>
              <td className="is-number">
                <strong>{row.points}</strong>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default StandingsTable
