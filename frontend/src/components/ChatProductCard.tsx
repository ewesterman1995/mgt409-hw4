import { Link } from 'react-router-dom'
import { formatPrice, type ProductCardData } from '../api'

// Variant A: a compact card inside the chat, under the assistant's reply.
// Links to the same detail page as every other product card.
export default function ChatProductCard({ product }: { product: ProductCardData }) {
  return (
    <Link to={`/products/${product.product_id}`} className="chat-card">
      <img src={product.image_url} alt={product.name} loading="lazy" />
      <span className="chat-card-body">
        <span className="chat-card-name">{product.name}</span>
        <span className="chat-card-price">{formatPrice(product.price)}</span>
        <span className="chat-card-info">{product.short_description}</span>
      </span>
    </Link>
  )
}
