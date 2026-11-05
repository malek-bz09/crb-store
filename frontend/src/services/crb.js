import { apiFetch } from './api'

// Everything the CRB page shows: next match, fixtures, results, tables, top players
export const fetchCrbOverview = () => apiFetch('/crb')
