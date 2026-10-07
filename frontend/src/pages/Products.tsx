import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import {
  fetchCategories,
  fetchCollections,
  fetchProducts,
  type Category,
  type Collection,
  type Product,
} from '../api'
import ProductCard from '../components/ProductCard'
import { COLLECTION_PHOTOS } from '../campusPhotos'

export default function Products() {
  const [searchParams] = useSearchParams()
  const collection = searchParams.get('collection') ?? ''
  const type = searchParams.get('type') ?? '' // kind of garment, from the Products menu
  // ?ids=a,b,c comes from "See more" in the chat.
  const ids = searchParams.get('ids') ?? ''
  const filterKey = ids ? `ids:${ids}` : type ? `type:${type}` : `collection:${collection}`
  const [products, setProducts] = useState<Product[] | null>(null)
  const [loadedFor, setLoadedFor] = useState<string | null>(null)
  const [collections, setCollections] = useState<Collection[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCollections().then(setCollections).catch(() => {})
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    let cancelled = false
    fetchProducts({ ids: ids || undefined, type: type || undefined, collection: collection || undefined })
      .then((p) => {
        if (cancelled) return
        setProducts(p)
        setLoadedFor(filterKey)
        setError(null)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [ids, type, collection, filterKey])

  const title = ids
    ? 'Matches from your chat'
    : type
      ? (categories.find((c) => c.slug === type)?.name ?? 'Products')
      : (collections.find((c) => c.slug === collection)?.name ?? 'Shop the Bulldog Lineup')
  const showingAll = !ids && !type && collection === ''
  // Slim campus-photo header; a collection gets its own photo from the home page tiles.
  const headerPhoto = (!ids && !type && COLLECTION_PHOTOS[collection]) || '/campus/classic.jpg'
  const count = products && loadedFor === filterKey ? products.length : null

  return (
    <section>
      <header className="page-header" style={{ backgroundImage: `url(${headerPhoto})` }}>
        <h1>{title}</h1>
        {count !== null && (
          <p>
            {count} {count === 1 ? 'style' : 'styles'}
          </p>
        )}
      </header>
      <div className="filter-chips" aria-label="Collections">
        <Link to="/products" className={showingAll ? 'chip active' : 'chip'}>
          All
        </Link>
        {ids && <span className="chip active">From chat</span>}
        {collections.map((c) => (
          <Link
            key={c.slug}
            to={`/products?collection=${c.slug}`}
            className={!ids && !type && collection === c.slug ? 'chip active' : 'chip'}
          >
            {c.name}
          </Link>
        ))}
      </div>
      <div className="filter-chips filter-chips-types" aria-label="Shop by type">
        {categories.map((c) => (
          <Link
            key={c.slug}
            to={`/products?type=${c.slug}`}
            className={!ids && type === c.slug ? 'chip active' : 'chip'}
          >
            {c.name}
          </Link>
        ))}
      </div>

      {error ? (
        <p className="error">Could not load products ({error}). Is the backend running?</p>
      ) : !products || loadedFor !== filterKey ? (
        <p>Loading products...</p>
      ) : products.length === 0 ? (
        <p>No matching products.</p>
      ) : (
        <div className="product-grid">
          {products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      )}
    </section>
  )
}
