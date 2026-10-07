import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { changePassword, clearChatHistory, fetchAccount, type Account as AccountData } from '../api'
import { useAuth } from '../authContext'
import PasswordInput from '../components/PasswordInput'

const MIN_PASSWORD_LENGTH = 8

// My Account: only real data the store has about the shopper. There are no orders in
// the database, so the orders section truthfully says the account has none.
export default function Account() {
  const { user, loading } = useAuth()
  const [account, setAccount] = useState<AccountData | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!user) return
    fetchAccount()
      .then(setAccount)
      .catch((err: Error) => setError(err.message))
  }, [user])

  if (loading) return <p>Loading...</p>
  if (!user) {
    return (
      <section className="form-page">
        <h1>My Account</h1>
        <p>
          Please <Link to="/login">log in</Link> to see your account.
        </p>
      </section>
    )
  }
  if (error) return <p className="error">{error}</p>
  if (!account) return <p>Loading your account...</p>

  async function handleClearChat() {
    if (!window.confirm('Delete your saved chat history? This cannot be undone.')) return
    await clearChatHistory()
    setAccount((a) => (a ? { ...a, saved_messages: 0, last_chat_at: null } : a))
  }

  return (
    <section className="account">
      <h1>My Account</h1>

      <div className="account-grid">
        <div className="account-card">
          <h2>Profile</h2>
          <dl>
            <dt>Name</dt>
            <dd>
              {account.first_name} {account.last_name}
            </dd>
            <dt>Email</dt>
            <dd>{account.email}</dd>
            <dt>Member since</dt>
            <dd>{account.member_since}</dd>
          </dl>
        </div>

        <div className="account-card">
          <h2>Orders</h2>
          <p>There are no orders on this account.</p>
        </div>

        <div className="account-card">
          <h2>Saved chat</h2>
          {account.saved_messages > 0 ? (
            <>
              <p>
                {account.saved_messages} saved messages. Last chat: {account.last_chat_at}.
              </p>
              <p className="muted">Open the chat in the corner to pick up where you left off.</p>
              <button type="button" className="button button-secondary" onClick={handleClearChat}>
                Delete chat history
              </button>
            </>
          ) : (
            <p>No saved chats yet. Ask the assistant in the corner about anything we sell.</p>
          )}
        </div>

        <ChangePasswordCard />
      </div>
    </section>
  )
}

function ChangePasswordCard() {
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState<{ text: string; error: boolean } | null>(null)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (next.length < MIN_PASSWORD_LENGTH) {
      setMessage({ text: `New password must be at least ${MIN_PASSWORD_LENGTH} characters.`, error: true })
      return
    }
    if (next !== confirm) {
      setMessage({ text: 'New passwords do not match.', error: true })
      return
    }
    setSaving(true)
    try {
      await changePassword(current, next)
      setMessage({ text: 'Password changed.', error: false })
      setCurrent('')
      setNext('')
      setConfirm('')
    } catch (err) {
      setMessage({ text: (err as Error).message, error: true })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="account-card form-page">
      <h2>Change password</h2>
      <form onSubmit={handleSubmit}>
        <label>
          Current password
          <PasswordInput value={current} onChange={(e) => setCurrent(e.target.value)} required autoComplete="current-password" />
        </label>
        <label>
          New password
          <PasswordInput value={next} onChange={(e) => setNext(e.target.value)} required autoComplete="new-password" />
          <span className="hint">At least {MIN_PASSWORD_LENGTH} characters.</span>
        </label>
        <label>
          Confirm new password
          <PasswordInput value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" />
        </label>
        {message && (
          <p className={message.error ? 'error' : 'success'} role="alert">
            {message.text}
          </p>
        )}
        <button type="submit" className="button" disabled={saving}>
          {saving ? 'Saving...' : 'Change password'}
        </button>
      </form>
    </div>
  )
}
