import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  clearChatHistory,
  fetchChatHistory,
  streamChatMessage,
  type ChatTurn,
  type ProductCardData,
  type SeeMore,
} from '../api'
import { useAuth } from '../authContext'
import { OPEN_CHAT_EVENT } from '../chatEvents'
import ChatProductCard from './ChatProductCard'

interface ChatMessage extends ChatTurn {
  error?: boolean
  products?: ProductCardData[]
  seeMore?: SeeMore | null
}

// Guests: the conversation is kept for this browser tab only, so a refresh doesn't
// lose it. Logged-in shoppers: it's saved in the database and loaded from there.
const GUEST_STORAGE_KEY = 'campusCustomsChat'

function loadGuestMessages(): ChatMessage[] {
  try {
    const saved = JSON.parse(sessionStorage.getItem(GUEST_STORAGE_KEY) ?? 'null')
    if (Array.isArray(saved)) return saved.filter((m) => !m.greeting)
  } catch {
    // ignore unreadable data
  }
  return []
}

// Under a reply with products: the best match as a card, plus the backend's
// "See 7 more hoodies →" / "Shop all 19 in Residential Colleges →" button.
// The page only changes when the shopper clicks it.
function ChatResults({ products, seeMore }: { products: ProductCardData[]; seeMore?: SeeMore | null }) {
  return (
    <div className="chat-cards">
      <ChatProductCard product={products[0]} />
      {seeMore && (
        <Link to={seeMore.href} className="chat-show-all">
          {seeMore.text}
        </Link>
      )}
    </div>
  )
}

export default function ChatWidget() {
  const { user, loading: authLoading } = useAuth()
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  // Live progress while the agent works, e.g. "Checking live stock…".
  const [status, setStatus] = useState('')
  // Best-matching product, shown instantly while the AI writes its answer.
  const [preview, setPreview] = useState<ProductCardData[]>([])
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Whose conversation is on screen: a user id, 'guest', or null while login status loads.
  // When it changes (log in, log out, switch accounts) the old conversation is replaced,
  // so the next person on this computer never sees someone else's chat.
  const owner = authLoading ? null : (user?.id ?? 'guest')
  const [shownOwner, setShownOwner] = useState<typeof owner>(null)
  if (owner !== shownOwner) {
    setShownOwner(owner)
    if (owner === 'guest') {
      setMessages(loadGuestMessages())
    } else {
      setMessages([])
      if (owner !== null) setLoadingHistory(true)
    }
  }

  // Logged in: load the saved conversation from the server.
  useEffect(() => {
    if (typeof owner !== 'number') return
    sessionStorage.removeItem(GUEST_STORAGE_KEY) // a guest chat from before login isn't kept
    let cancelled = false
    fetchChatHistory()
      .then((saved) => {
        if (cancelled) return
        setMessages(saved.map((m) => ({ role: m.role, content: m.content, products: m.products, seeMore: m.see_more })))
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoadingHistory(false)
      })
    return () => {
      cancelled = true
    }
  }, [owner])

  // Guests: keep the conversation for this tab.
  useEffect(() => {
    if (owner === 'guest') sessionStorage.setItem(GUEST_STORAGE_KEY, JSON.stringify(messages))
  }, [owner, messages])

  // Auto-minimize when the shopper goes to a different page (a card, "See more",
  // the nav...), so the chat doesn't cover what they came to see. The conversation
  // is kept; reopening picks up where they left off.
  const location = useLocation()
  const page = location.pathname + location.search
  const [lastPage, setLastPage] = useState(page)
  if (page !== lastPage) {
    setLastPage(page)
    setOpen(false)
  }

  // Other parts of the site (the header's "Chat with us", the home banner) can open the chat.
  useEffect(() => {
    const open = () => setOpen(true)
    window.addEventListener(OPEN_CHAT_EVENT, open)
    return () => window.removeEventListener(OPEN_CHAT_EVENT, open)
  }, [])

  // Keep the newest message in view.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages, sending, open])

  const hasConversation = messages.some((m) => m.role === 'user')
  const greeting = user
    ? `Hi ${user.first_name}! Ask me about Campus Customs gear. Our chat is saved to your account.`
    : 'Hi! Ask me about Campus Customs gear.'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    // Earlier turns for context (the backend uses the saved history instead for
    // logged-in shoppers). Error notices are left out.
    const history: ChatTurn[] = messages.filter((m) => !m.error).map(({ role, content }) => ({ role, content }))

    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setSending(true)
    setStatus('')
    setPreview([])
    try {
      const { reply, products, see_more } = await streamChatMessage(text, history, page, setStatus, setPreview)
      setMessages((m) => [...m, { role: 'assistant', content: reply, products, seeMore: see_more }])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: (err as Error).message, error: true }])
    } finally {
      setSending(false)
      setStatus('')
      setPreview([])
    }
  }

  async function handleClear() {
    const question = user
      ? 'Delete your saved chat history? This cannot be undone.'
      : 'Clear this conversation?'
    if (!window.confirm(question)) return
    try {
      if (user) await clearChatHistory()
      setMessages([])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', content: (err as Error).message, error: true }])
    }
  }

  return (
    <div className="chat-widget">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Campus Customs chat">
          <div className="chat-header">
            <span>Campus Customs Assistant</span>
            <span className="chat-header-actions">
              {hasConversation && (
                <button type="button" className="chat-clear" onClick={handleClear}>
                  Clear
                </button>
              )}
              <button type="button" onClick={() => setOpen(false)} aria-label="Minimize chat" title="Minimize">
                –
              </button>
            </span>
          </div>
          <div className="chat-messages" aria-live="polite">
            <div className="chat-turn assistant">
              <div className="chat-message assistant">{greeting}</div>
            </div>
            {loadingHistory && <div className="chat-message assistant typing">Loading your chat...</div>}
            {messages.map((msg, i) => (
              <div key={i} className={`chat-turn ${msg.role}`}>
                <div className={`chat-message ${msg.role}${msg.error ? ' error' : ''}`}>{msg.content}</div>
                {msg.products && msg.products.length > 0 && (
                  <ChatResults products={msg.products} seeMore={msg.seeMore} />
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-turn assistant">
                <div className="chat-message assistant typing chat-status" role="status">
                  <span className="chat-status-dot" aria-hidden="true" />
                  {status || 'Thinking…'}
                </div>
                {preview.length > 0 && (
                  <div className="chat-cards">
                    <ChatProductCard product={preview[0]} />
                  </div>
                )}
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              aria-label="Chat message"
              maxLength={2000}
            />
            <button type="submit" disabled={sending || loadingHistory || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
      <button
        type="button"
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
      >
        {open ? 'Minimize' : hasConversation ? 'Continue chat' : 'Chat'}
      </button>
    </div>
  )
}
