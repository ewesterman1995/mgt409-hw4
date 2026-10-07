import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { openChat } from '../chatEvents'

// Home banner: three happy campus photos that crossfade with a slow zoom.
// `position` keeps the people in frame in the wide, short banner.
const SLIDES = [
  { src: '/campus/hero.jpg', position: 'center 72%', label: 'Yale cheerleaders at the Yale Bowl' },
  { src: '/campus/family.jpg', position: 'center 30%', label: 'Yale graduates in caps and gowns' },
  { src: '/campus/about.jpg', position: 'center 25%', label: 'Harkness Tower in the fall' },
]
const SLIDE_MS = 6000

const prefersReducedMotion = () =>
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false

export default function HeroSlideshow() {
  const [current, setCurrent] = useState(0)
  const [paused, setPaused] = useState(false)

  useEffect(() => {
    // No auto-advance for people who ask their device to reduce motion.
    if (paused || prefersReducedMotion()) return
    const timer = setInterval(() => setCurrent((c) => (c + 1) % SLIDES.length), SLIDE_MS)
    return () => clearInterval(timer)
  }, [paused])

  return (
    <section
      className="home-hero"
      aria-roledescription="carousel"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {SLIDES.map((s, i) => (
        <div
          key={s.src}
          className={`hero-slide${i === current ? ' active' : ''}`}
          style={{ backgroundImage: `url(${s.src})`, backgroundPosition: s.position }}
          role="img"
          aria-label={s.label}
          aria-hidden={i !== current}
        />
      ))}
      <div className="hero-content">
        <p className="home-hero-eyebrow">Officially licensed Yale apparel</p>
        <h1>Shop Bulldog Blue</h1>
        <p className="hero-sub">For students, parents, and anyone who wants to rep Yale.</p>
        <div className="hero-actions">
          <Link to="/products" className="button">
            Shop all products
          </Link>
          <button type="button" className="button hero-button-ghost" onClick={openChat}>
            Ask our assistant
          </button>
        </div>
      </div>
      <div className="hero-dots" role="group" aria-label="Choose a photo">
        {SLIDES.map((s, i) => (
          <button
            key={s.src}
            type="button"
            className={i === current ? 'active' : ''}
            aria-label={`Show photo ${i + 1}: ${s.label}`}
            aria-pressed={i === current}
            onClick={() => setCurrent(i)}
          />
        ))}
      </div>
    </section>
  )
}
