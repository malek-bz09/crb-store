// Small wrapper around fetch() for our backend. Every error becomes an ApiError
// whose message can be shown to the user as-is.
export class ApiError extends Error {
  constructor(status, message, data = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status // 0 means the server couldn't be reached
    this.data = data
  }
}

// Every backend route lives under /api/v1 (see backend/app/main.py)
const API_PREFIX = '/api/v1'

export async function apiFetch(path, { method = 'GET', body, token, headers: extraHeaders } = {}) {
  // FormData (file uploads) is sent as-is; the browser sets its Content-Type
  const isForm = body instanceof FormData
  const headers = { ...extraHeaders }
  if (body !== undefined && !isForm) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${API_PREFIX}${path}`, {
      method,
      headers,
      body: body === undefined || isForm ? body : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check your connection and try again.')
  }

  // 204 No Content has no body; other bodies may not be JSON if something broke
  const data = response.status === 204 ? null : await response.json().catch(() => null)

  if (!response.ok) {
    const detail = data?.detail
    const message = detail?.message ?? 'Something went wrong. Please try again.'
    throw new ApiError(response.status, message, detail)
  }
  return data
}

// The backend returns long lists one page at a time ({items, pages, ...}).
// This fetches every page and returns all the items in one array: the first page
// says how many there are, then the rest are fetched at the same time.
export async function fetchAllPages(fetcher, path) {
  const separator = path.includes('?') ? '&' : '?'
  const pageUrl = (page) => `${path}${separator}page=${page}&size=100`
  const first = await fetcher(pageUrl(1))
  const rest = await Promise.all(
    Array.from({ length: first.pages - 1 }, (_, i) => fetcher(pageUrl(i + 2))),
  )
  // Something added or deleted between requests shifts the pages, which can repeat an item
  const byId = new Map()
  for (const item of [first, ...rest].flatMap((data) => data.items)) byId.set(item.id, item)
  return [...byId.values()]
}
