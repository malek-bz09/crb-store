import { useEffect, useRef } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import './Navbar.css'
import { categories } from '../data/products'
import { useCart } from '../context/cart'
import { brand } from '../data/brand'
import { wilayas } from '../data/wilayas'

function Navbar() {
  const { count } = useCart()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const query = searchParams.get('q') ?? ''
  const announcementRef = useRef(null)
  const headerRef = useRef(null)

  // Publish the real heights as CSS variables (--announcement-h, --header-h), so
  // sticky panels and the hero adjust when the navbar wraps onto more rows
  useEffect(() => {
    const root = document.documentElement.style
    const observer = new ResizeObserver(() => {
      root.setProperty('--announcement-h', `${announcementRef.current.offsetHeight}px`)
      root.setProperty('--header-h', `${headerRef.current.offsetHeight}px`)
    })
    observer.observe(announcementRef.current)
    observer.observe(headerRef.current)
    return () => observer.disconnect()
  }, [])

  const handleSearch = (event) => {
    event.preventDefault()
    const q = new FormData(event.currentTarget).get('q').trim()
    if (q) navigate(`/search?q=${encodeURIComponent(q)}`)
  }

  return (
    <>
      {/* Outside the sticky header, so it scrolls away instead of taking space on every screen */}
      <p ref={announcementRef} className="navbar-announcement">
        Cash on delivery to all {wilayas.length} wilayas
      </p>

      <header ref={headerRef} className="navbar">
        <div className="navbar-inner">
          <Link to="/" className="navbar-logo">
            <img src={brand.mark} alt="" width="36" height="36" />
            <span>
              <strong>{brand.shortName}</strong>
              <small>{brand.clubName}</small>
            </span>
          </Link>

          <nav className="navbar-links">
            <ul>
              <li>
                <Link to="/shop">Shop all</Link>
              </li>
              {categories.map((category) => (
                <li key={category.id}>
                  <Link to={`/category/${category.id}`}>{category.name}</Link>
                </li>
              ))}
            </ul>
          </nav>

          <div className="navbar-actions">
            <form className="navbar-search" role="search" onSubmit={handleSearch}>
              {/* key: when the URL's query changes (e.g. Back button), show the new one */}
              <input
                key={query}
                type="search"
                name="q"
                defaultValue={query}
                placeholder="Search products"
                aria-label="Search products"
              />
              <button type="submit">Search</button>
            </form>
            <Link to="/cart">Cart ({count})</Link>
          </div>
        </div>
      </header>
    </>
  )
}

export default Navbar
