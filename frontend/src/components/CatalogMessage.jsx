import './CatalogMessage.css'

// Shown while something loads (products by default), or when it couldn't be loaded
function CatalogMessage({ error, loadingText = 'Loading products…' }) {
  return (
    <p className="catalog-message" role={error ? 'alert' : 'status'}>
      {error ?? loadingText}
    </p>
  )
}

export default CatalogMessage
