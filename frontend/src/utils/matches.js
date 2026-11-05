// Matches are shown in Algiers time, where they're played, whatever the visitor's own time zone
const timeZone = 'Africa/Algiers'

// "Sat 14 Nov, 17:00" (or "Sat 14 Nov" while the kick-off time isn't fixed yet)
export const formatKickoff = (match) =>
  new Date(match.date).toLocaleString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    ...(match.kickoffConfirmed && { hour: '2-digit', minute: '2-digit' }),
    timeZone,
  })

// "14 Nov"
export const formatMatchDay = (match) =>
  new Date(match.date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone })

// "17:00", or "TBC" while the time isn't fixed
export const formatKickoffTime = (match) =>
  match.kickoffConfirmed
    ? new Date(match.date).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone })
    : 'TBC'

// "5 Nov, 18:40": when the match data was last fetched
export const formatUpdated = (iso) =>
  new Date(iso).toLocaleString('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', timeZone })

// 2026 → "2026/27"
export const formatSeason = (season) => `${season}/${String(season + 1).slice(-2)}`

// "https://www.digiticket.dz/event/123" → "digiticket.dz", so fans see where they're going
export const ticketSite = (url) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export const RESULT_LABELS = { W: 'Win', D: 'Draw', L: 'Loss' }
