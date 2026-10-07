import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { fetchCategories, fetchCollections, type Category, type Collection } from '../api'
import { useAuth } from '../authContext'
import { openChat } from '../chatEvents'

// "Products" opens a menu on hover (or keyboard focus) with the shop's collections
// and kinds of garment, so shoppers can jump straight to what they want.
function ProductsMenu() {
  const [collections, setCollections] = useState<Collection[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    fetchCollections().then(setCollections).catch(() => {})
    fetchCategories().then(setCategories).catch(() => {})
  }, [])

  // Clicking a menu link leaves focus inside the menu, which would keep it open.
  const closeMenu = () => (document.activeElement as HTMLElement | null)?.blur()

  return (
    <div className="nav-menu">
      <NavLink to="/products" end className="nav-menu-trigger" aria-haspopup="true">
        Products <span aria-hidden="true">▾</span>
      </NavLink>
      <div className="nav-menu-panel">
        <div>
          <h3>Collections</h3>
          {collections.map((c) => (
            <Link key={c.slug} to={`/products?collection=${c.slug}`} onClick={closeMenu}>
              {c.name} <span className="nav-menu-count">{c.count}</span>
            </Link>
          ))}
        </div>
        <div>
          <h3>Shop by type</h3>
          {categories.map((c) => (
            <Link key={c.slug} to={`/products?type=${c.slug}`} onClick={closeMenu}>
              {c.name} <span className="nav-menu-count">{c.count}</span>
            </Link>
          ))}
        </div>
        <Link to="/products" className="nav-menu-all" onClick={closeMenu}>
          Shop all products →
        </Link>
      </div>
    </div>
  )
}

export default function NavBar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="utility-bar">
        <span>Officially licensed Yale apparel · 57 Broadway, New Haven</span>
        <button type="button" onClick={openChat}>
          Questions? Chat with us
        </button>
      </div>
      <div className="navbar">
        <Link to="/" className="brand" aria-label="Campus Customs home">
          <img src="/block-y.svg" alt="" className="brand-mark" />
          <span className="brand-text">
            <span className="brand-name">Campus Customs</span>
            <span className="brand-tagline">Officially Licensed Yale Apparel</span>
          </span>
        </Link>
        <nav>
          <NavLink to="/" end>
            Home
          </NavLink>
          <ProductsMenu />
          <NavLink to="/about">About Us</NavLink>
          {user ? (
            <>
              <NavLink to="/account" className="nav-pill" title="My Account">
                Hi, {user.first_name}
              </NavLink>
              <button type="button" className="nav-button" onClick={handleLogout}>
                Log Out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Log In</NavLink>
              <NavLink to="/create-account" className="nav-cta">
                Create Account
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}
