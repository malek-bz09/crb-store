// A club's crest and name. CRB is shown in bold.
function TeamName({ team, crbId, align = 'start' }) {
  return (
    <span className={`club-team club-team--${align} ${team.id === crbId ? 'is-crb' : ''}`}>
      {team.logo && <img src={team.logo} alt="" width="24" height="24" loading="lazy" />}
      <span>{team.name}</span>
    </span>
  )
}

export default TeamName
