import FormChip from './FormChip'

// Headline numbers for the season (or one competition), then the last results
function SeasonStats({ stats }) {
  if (stats.played === 0) return <p className="club-empty">No matches played yet this season.</p>

  const tiles = [
    ['Played', stats.played],
    ['Won', stats.wins],
    ['Drawn', stats.draws],
    ['Lost', stats.losses],
    ['Goals scored', stats.goalsFor],
    ['Goals conceded', stats.goalsAgainst],
    ['Clean sheets', stats.cleanSheets],
  ]

  return (
    <>
      <dl className="club-stats">
        {tiles.map(([label, value]) => (
          <div key={label} className="club-stat">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <div className="club-form-row">
        <span>Last {stats.form.length}</span>
        {stats.form.map((result, index) => (
          <FormChip key={index} result={result} />
        ))}
      </div>
    </>
  )
}

export default SeasonStats
