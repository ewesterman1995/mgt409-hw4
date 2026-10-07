import { Link, Route, Routes } from 'react-router-dom'
import ChatWidget from './components/ChatWidget'
import NavBar from './components/NavBar'
import About from './pages/About'
import Account from './pages/Account'
import CreateAccount from './pages/CreateAccount'
import Home from './pages/Home'
import Login from './pages/Login'
import PhotoCredits from './pages/PhotoCredits'
import ProductDetail from './pages/ProductDetail'
import Products from './pages/Products'

function App() {
  return (
    <>
      <NavBar />
      <main className="page">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="/credits" element={<PhotoCredits />} />
          <Route path="/account" element={<Account />} />
          <Route path="*" element={<p>Page not found.</p>} />
        </Routes>
      </main>
      <footer className="footer">
        <p>
          Campus Customs · 57 Broadway, New Haven, CT 06511 · <Link to="/credits">Photo credits</Link>
        </p>
        {/* Legal line Yale's licensing guide requires on licensed products. */}
        <p className="footer-legal">
          The Marks on this product are trademarks of Yale University and are used under official
          license.
        </p>
      </footer>
      <ChatWidget />
    </>
  )
}

export default App
