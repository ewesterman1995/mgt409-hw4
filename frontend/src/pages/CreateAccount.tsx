import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api'
import { useAuth } from '../authContext'
import PasswordInput from '../components/PasswordInput'

const MIN_PASSWORD_LENGTH = 8

export default function CreateAccount() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm: '',
  })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const update = (field: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`)
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    try {
      setUser(
        await register({
          first_name: form.first_name,
          last_name: form.last_name,
          email: form.email,
          password: form.password,
        }),
      )
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="form-page">
      <h1>Create Account</h1>
      <form onSubmit={handleSubmit}>
        <label>
          First name
          <input value={form.first_name} onChange={update('first_name')} required autoComplete="given-name" />
        </label>
        <label>
          Last name
          <input value={form.last_name} onChange={update('last_name')} required autoComplete="family-name" />
        </label>
        <label>
          Email
          <input type="email" value={form.email} onChange={update('email')} required autoComplete="email" />
        </label>
        <label>
          Password
          <PasswordInput
            value={form.password}
            onChange={update('password')}
            required
            minLength={MIN_PASSWORD_LENGTH}
            autoComplete="new-password"
          />
          <span className="hint">At least {MIN_PASSWORD_LENGTH} characters.</span>
        </label>
        <label>
          Confirm password
          <PasswordInput
            value={form.confirm}
            onChange={update('confirm')}
            required
            autoComplete="new-password"
          />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button type="submit" className="button" disabled={submitting}>
          {submitting ? 'Creating account...' : 'Create Account'}
        </button>
      </form>
      <p>
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </section>
  )
}
