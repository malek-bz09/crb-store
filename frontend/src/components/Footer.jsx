import { Link } from 'react-router'
import './Footer.css'
import { categories } from '../data/products'
import { brand } from '../data/brand'

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-columns">
        <div className="footer-about">
          <Link to="/" className="footer-logo">
            <img src={brand.mark} alt="" width="40" height="40" />
            {brand.shortName}
          </Link>
          <p>
            Gear for {brand.clubName} supporters, delivered to your door anywhere in Algeria.
            Pay cash when it arrives.
          </p>
        </div>

        <div className="footer-column">
          <h3>Shop</h3>
          <ul>
            {categories.map((category) => (
              <li key={category.id}>
                <Link to={`/category/${category.id}`}>{category.name}</Link>
              </li>
            ))}
          </ul>
        </div>

        <div className="footer-column">
          <h3>Help</h3>
          <ul>
            <li>
              <Link to="/faq">FAQ</Link>
            </li>
            <li>
              <Link to="/shipping">Shipping</Link>
            </li>
            <li>
              <Link to="/returns">Returns</Link>
            </li>
          </ul>
        </div>

        <div className="footer-column">
          <h3>Contact Us</h3>
          <p>Have questions? We'd love to hear from you.</p>
          <div className="footer-contact">
            <p>
              <strong>Email:</strong> <a href={`mailto:${brand.email}`}>{brand.email}</a>
            </p>
            <p>
              <strong>Phone:</strong> <a href={brand.phoneHref}>{brand.phone}</a>
            </p>
            <p>
              <strong>Address:</strong> {brand.city}
            </p>
          </div>
        </div>
      </div>

      <p className="footer-copyright">
        © {new Date().getFullYear()} {brand.shortName}. All rights reserved.
      </p>
    </footer>
  )
}

export default Footer
