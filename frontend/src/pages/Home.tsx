import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCollections, fetchFeatured, type Collection, type Product } from '../api'
import FeaturedCarousel from '../components/FeaturedCarousel'
import HeroSlideshow from '../components/HeroSlideshow'
import { COLLECTION_PHOTOS } from '../campusPhotos'

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([])
  const [collections, setCollections] = useState<Collection[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetchFeatured(), fetchCollections()])
      .then(([f, c]) => {
        setFeatured(f)
        setCollections(c)
      })
      .catch((err: Error) => setError(err.message))
  }, [])

  return (
    <section className="home">
      <HeroSlideshow />

      {error && <p className="error">Could not load products ({error}). Is the backend running?</p>}

      <FeaturedCarousel products={featured} />

      <div className="shop-all">
        <Link to="/products" className="button">
          Shop all products
        </Link>
      </div>

      <div className="collections-band">
        <h2>Find Your Corner of Yale</h2>
        <div className="collection-grid">
          {collections.map((c) => {
            // Falls back to the collection's product photo for a new collection without one.
            const photo = COLLECTION_PHOTOS[c.slug] ?? c.image_url
            return (
              <Link key={c.slug} to={`/products?collection=${c.slug}`} className="collection-tile">
                {photo && <img src={photo} alt="" loading="lazy" />}
                <span className="collection-label">
                  <span className="collection-name">{c.name}</span>
                  <span className="collection-count">{c.count} items</span>
                </span>
              </Link>
            )
          })}
        </div>
      </div>
    </section>
  )
}
