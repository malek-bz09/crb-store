import { Link } from 'react-router'
import { brand } from '../data/brand'
import './Hero.css'

function Hero() {
  return (
    <section className="hero">
      <img
        className="hero-image"
        src="/860184935_1785493500248266_4784916831923244551_n.jpg"
        alt="CRB players celebrating a goal in front of the stands"
      />
      <div className="hero-content">
        <p className="hero-kicker">{brand.clubName}</p>
        <h1 className="hero-title">
          Wear the <span>red</span>.
        </h1>
        <p className="hero-text">Jerseys, training wear and caps for every supporter.</p>
        <Link to="/shop" className="hero-cta">
          Shop now
        </Link>
      </div>
    </section>
  )
}

export default Hero
