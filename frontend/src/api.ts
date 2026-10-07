// Types and fetch helpers for the FastAPI backend (backend/main.py).
// Vite proxies /api and /images to http://127.0.0.1:8000 (see vite.config.ts).

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  price: number
  image_url: string
  collection: string
}

export interface Collection {
  slug: string
  name: string
  count: number
  image_url: string | null
}

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends Product {
  search_tags: string[]
  sizes: SizeStock[]
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

// A kind of garment (Hoodies, T-shirts, ...) with its live product count.
export interface Category {
  slug: string
  name: string
  count: number
}

export const fetchCategories = () => getJson<Category[]>('/api/categories')

// All products, one collection, one kind of garment, or specific products by id.
export function fetchProducts(filter: { collection?: string; ids?: string; type?: string } = {}) {
  const params = new URLSearchParams()
  if (filter.ids) params.set('ids', filter.ids)
  else if (filter.type) params.set('type', filter.type)
  else if (filter.collection) params.set('collection', filter.collection)
  const query = params.toString()
  return getJson<Product[]>(query ? `/api/products?${query}` : '/api/products')
}

export const fetchFeatured = () => getJson<Product[]>('/api/featured')

export const fetchCollections = () => getJson<Collection[]>('/api/collections')

export const fetchProduct = (productId: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// --- Accounts ---

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
}

// Turn FastAPI error responses into one readable sentence.
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return String(body.detail[0].msg).replace(/^Value error, /, '')
    }
  } catch {
    // fall through
  }
  return 'Something went wrong. Please try again.'
}

async function postJson<T>(url: string, data?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: data === undefined ? undefined : JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>)
}

export const fetchCurrentUser = () => getJson<User | null>('/api/auth/me')

export const register = (input: RegisterInput) => postJson<User>('/api/auth/register', input)

export const login = (email: string, password: string) =>
  postJson<User>('/api/auth/login', { email, password })

export const logout = () => postJson<void>('/api/auth/logout')

export interface Account {
  first_name: string
  last_name: string
  email: string
  member_since: string
  saved_messages: number
  last_chat_at: string | null
}

export const fetchAccount = () => getJson<Account>('/api/account')

export const changePassword = (current_password: string, new_password: string) =>
  postJson<void>('/api/auth/change-password', { current_password, new_password })

// --- Chat ---

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

// A product the agent chose to show. Every field is read from the database by the
// backend; the model only picks which product_ids to include.
export interface ProductCardData {
  product_id: string
  name: string
  price: number
  image_url: string
  garment_type: string
  short_description: string
}


// Button under the chat's best-match card, built by the backend,
// e.g. { text: "See 7 more hoodies →", href: "/products?ids=a,b,c" }.
export interface SeeMore {
  text: string
  href: string
}

export interface ChatReply {
  reply: string
  products: ProductCardData[]
  see_more: SeeMore | null
}

// Sends the new message, the earlier turns (used for guests; logged-in shoppers'
// history comes from the database) and the page the shopper is on.
export const sendChatMessage = (message: string, history: ChatTurn[], page: string) =>
  postJson<ChatReply>('/api/chat', { message, history, page })

// Same as sendChatMessage, but streams: onPreview gets the best-matching product's
// card right away (before the AI answers), and onStatus gets live progress ("Checking
// live stock…") while the agent works. The backend sends one JSON object per line.
export async function streamChatMessage(
  message: string,
  history: ChatTurn[],
  page: string,
  onStatus: (text: string) => void,
  onPreview: (products: ProductCardData[]) => void,
): Promise<ChatReply> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history, page }),
  })
  if (!res.ok || !res.body) throw new Error(await errorMessage(res))

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value, { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (!line.trim()) continue
      const event = JSON.parse(line)
      if (event.type === 'status') onStatus(event.text)
      else if (event.type === 'preview') onPreview(event.products)
      else if (event.type === 'reply') return event as ChatReply
      else if (event.type === 'error') throw new Error(event.detail)
    }
    if (done) throw new Error('The connection closed before the reply arrived. Please try again.')
  }
}

// One saved message from a logged-in shopper's history.
export interface ChatHistoryMessage extends ChatTurn {
  products: ProductCardData[]
  see_more: SeeMore | null
}

export const fetchChatHistory = () => getJson<ChatHistoryMessage[]>('/api/chat/history')

export async function clearChatHistory(): Promise<void> {
  const res = await fetch('/api/chat/history', { method: 'DELETE' })
  if (!res.ok) throw new Error(await errorMessage(res))
}
