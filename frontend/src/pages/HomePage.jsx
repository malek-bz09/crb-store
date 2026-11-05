import Hero from '../components/Hero'
import CategoryTiles from '../components/CategoryTiles'
import ProductGrid from '../components/ProductGrid'
import CatalogMessage from '../components/CatalogMessage'
import { useProducts } from '../context/products'

function HomePage() {
  const { products, loading, error } = useProducts()

  return (
    <>
      <Hero />
      <CategoryTiles />
      {loading || error ? (
        <CatalogMessage error={error} />
      ) : (
        <ProductGrid title="New in" products={products} />
      )}
    </>
  )
}

export default HomePage
