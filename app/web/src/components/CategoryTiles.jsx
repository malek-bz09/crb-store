import { Link } from 'react-router'
import { categories } from '../data/products'
import './CategoryTiles.css'

// One big photo link per category, under the hero
function CategoryTiles() {
  return (
    <section className="category-tiles">
      {categories.map((category) => (
        <Link key={category.id} to={`/category/${category.id}`} className="category-tile">
          <img src={category.image} alt="" loading="lazy" />
          <span>{category.name}</span>
        </Link>
      ))}
    </section>
  )
}

export default CategoryTiles
