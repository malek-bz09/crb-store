import ProductGrid from '../components/ProductGrid'
import CatalogMessage from '../components/CatalogMessage'
import { useProducts } from '../context/products'

// Every product, for the hero's "Shop now" button
function ShopPage() {
  const { products, loading, error } = useProducts()

  if (loading || error) return <CatalogMessage error={error} />

  return <ProductGrid title="All products" products={products} />
}

export default ShopPage
