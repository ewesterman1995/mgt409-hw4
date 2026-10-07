import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  fetchCollections,
  fetchProduct,
  formatPrice,
  type Collection,
  type ProductDetail as Product,
} from '../api'
import { openChat } from '../chatEvents'

// Exact counts are only shown when stock is running low ("Only 4 left!").
const LOW_STOCK = 5

function stockLabel(quantity: number): string {
  if (quantity === 0) return 'Out of stock'
  if (quantity <= LOW_STOCK) return `Only ${quantity} left!`
  return 'In stock'
}

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [collections, setCollections] = useState<Collection[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCollections().then(setCollections).catch(() => {})
  }, [])

  useEffect(() => {
    if (!productId) return
    let cancelled = false
    fetchProduct(productId)
      .then((p) => {
        if (cancelled) return
        setProduct(p)
        setError(null)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [productId])

  if (error) return <p className="error">Could not load this product ({error}).</p>
  // Show loading until the product for the current URL has arrived.
  if (!product || product.product_id !== productId) return <p>Loading...</p>

  const collection = collections.find((c) => c.slug === product.collection)

  return (
    <section>
      <Link to="/products" className="back-link">
        ← Back to the lineup
      </Link>
      <div className="product-detail">
        <img src={product.image_url} alt={product.name} />
        <div className="product-info">
          {collection && (
            <Link to={`/products?collection=${collection.slug}`} className="collection-badge">
              {collection.name}
            </Link>
          )}
          <h1>{product.name}</h1>
          <p className="price">{formatPrice(product.price)}</p>
          <p>{product.description}</p>
          <p className="meta">
            <strong>Type:</strong> {product.garment_type}
          </p>
          <p className="meta">
            <strong>Colors:</strong> {product.colors.join(', ')}
          </p>

          <div className="size-panel">
            <h2>Sizes</h2>
            <ul className="sizes">
              {product.sizes.map((s) => (
                <li
                  key={s.size}
                  className={s.quantity === 0 ? 'out' : s.quantity <= LOW_STOCK ? 'low' : ''}
                >
                  <span className="size">{s.size}</span>
                  <span>{stockLabel(s.quantity)}</span>
                </li>
              ))}
            </ul>
            <button type="button" className="button button-secondary" onClick={openChat}>
              Questions about this item? Ask our assistant
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
