// Everything brand-specific lives here: the navbar, footer, admin and index.html
// (title, favicon, theme colour, via vite.config.js) all read from this file
export const brand = {
  shortName: 'CRB Store',
  clubName: 'Chabab Riadhi Belouizdad',
  mark: '/algeria_cr-belouizdad.football-logos.cc.svg',
  // TODO: the club's real contact details. Empty ones are hidden in the footer
  email: '',
  phone: '', // as displayed, e.g. '+213 21 00 00 00'
  phoneHref: '', // e.g. 'tel:+21321000000'
  city: 'Belouizdad, Algiers',
  // Browser UI colour on mobile; keep in sync with --accent in index.css
  themeColor: '#c8102e',
}
