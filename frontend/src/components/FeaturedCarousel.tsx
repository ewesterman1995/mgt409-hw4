import { useEffect, useState } from 'react'
import type { Product } from '../api'
import ProductCard from './ProductCard'

const VISIBLE = 4
const ROTATE_MS = 4000

// Shows VISIBLE products at a time and advances one step every ROTATE_MS.
// Pauses while the mouse is over it.
export default function FeaturedCarousel({ products }: { products: Product[] }) {
  const [start, setStart] = useState(0)
  const [paused, setPaused] = useState(false)
  const count = products.length

  useEffect(() => {
    if (paused || count <= VISIBLE) return
    const timer = setInterval(() => setStart((s) => (s + 1) % count), ROTATE_MS)
    return () => clearInterval(timer)
  }, [paused, count])

  if (count === 0) return null

  const shown = Array.from(
    { length: Math.min(VISIBLE, count) },
    (_, i) => products[(start + i) % count],
  )
  const step = (delta: number) => setStart((s) => (s + delta + count) % count)

  return (
    <div
      className="carousel"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      <button type="button" className="carousel-arrow" onClick={() => step(-1)} aria-label="Previous">
        ‹
      </button>
      <div className="carousel-track">
        {shown.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
      <button type="button" className="carousel-arrow" onClick={() => step(1)} aria-label="Next">
        ›
      </button>
    </div>
  )
}
