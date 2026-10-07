import { useState, type InputHTMLAttributes } from 'react'

// Password field with a Show/Hide button that is always visible
// (the browser's own reveal icon disappears once the field loses focus).
export default function PasswordInput(props: Omit<InputHTMLAttributes<HTMLInputElement>, 'type'>) {
  const [visible, setVisible] = useState(false)

  return (
    <span className="password-input">
      <input {...props} type={visible ? 'text' : 'password'} />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Hide password' : 'Show password'}
        aria-pressed={visible}
      >
        {visible ? 'Hide' : 'Show'}
      </button>
    </span>
  )
}
