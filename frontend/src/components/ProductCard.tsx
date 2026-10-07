import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'

// Just the fields a card shows. Used on the Products page (including "Matches from
// your chat") and the home carousel; every card links to the same detail page.
export type CardProduct = Pick<Product, 'product_id' | 'name' | 'price' | 'image_url' | 'description'>

export default function ProductCard({ product }: { product: CardProduct }) {
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <img src={product.image_url} alt={product.name} loading="lazy" />
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="short-description">{product.description}</p>
      </div>
    </Link>
  )
}
