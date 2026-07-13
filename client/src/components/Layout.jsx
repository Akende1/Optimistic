import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { auth } from '../lib/api';
import { useCart } from '../stores/cart';
import lightLogo from '../../../IMG-20260702-WA0114.jpg';
import darkLogo from '../../../IMG-20260702-WA0115.jpg';

const Brand = ({ footer = false }) => <Link className={`market-brand logo-brand${footer ? ' footer-brand' : ''}`} to="/" aria-label="Optimistic home">
  <span className={footer ? 'footer-logo-frame' : 'header-logo-frame'}><img src={footer ? darkLogo : lightLogo} alt="" /></span>
  <span className="brand-copy"><strong>Optimistic</strong><small>by Zuzelarian Technologies</small></span>
</Link>;
const NavIcon = ({ to, symbol, label, className = '' }) => <Link className={`nav-icon ${className}`} to={to}><span className="nav-symbol" aria-hidden="true">{symbol}</span><small>{label}</small></Link>;

export default function Layout() {
  const [search, setSearch] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const count = useCart((state) => state.lines.reduce((total, line) => total + line.quantity, 0));
  const user = auth.user();
  const submitSearch = (event) => { event.preventDefault(); navigate(search.trim() ? `/products?search=${encodeURIComponent(search.trim())}` : '/products'); };
  const logout = () => { auth.clear(); navigate('/'); window.location.reload(); };
  return <>
    <div className="utility-bar"><div className="market-container"><span>Optimistic by Zuzelarian Technologies</span><nav><Link to="/legal/terms">Buyer protection</Link><Link to="/courier/register">Deliver with us</Link>{user?.role === 'SELLER' && <Link to="/seller">Seller centre</Link>}</nav></div></div>
    <header className="market-nav"><div className="market-container nav-main"><Brand /><form className="global-search" onSubmit={submitSearch}><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search products, categories, or sellers" aria-label="Search marketplace" /><button>Search</button></form><nav className="nav-actions" aria-label="Account and cart">
      {!user && <><NavIcon className="nav-login" to="/login" symbol="◎" label="Log in" /><NavIcon className="nav-signup" to="/register" symbol="＋" label="Sign up" /></>}
      {user && <><NavIcon to="/account" symbol="◎" label="Account" />{user.role === 'BUYER' && <NavIcon to="/orders" symbol="▤" label="Orders" />}{user.role === 'SELLER' && <NavIcon to="/seller" symbol="▦" label="Dashboard" />}{user.role === 'COURIER' && <NavIcon to="/courier" symbol="◇" label="Deliveries" />}<NavIcon to="/notifications" symbol="◌" label="Alerts" /><button className="nav-icon nav-logout" onClick={logout}><span className="nav-symbol" aria-hidden="true">↗</span><small>Log out</small></button></>}
      {(!user || user.role === 'BUYER') && <Link className="nav-icon cart-action" to="/cart"><span className="cart-count">{count}</span><strong className="nav-symbol" aria-hidden="true">▱</strong><small>Cart</small></Link>}
    </nav></div><div className="market-container category-nav"><Link className="all-products" to="/products">All products</Link><Link to="/products?category_slug=electronics">Electronics</Link><Link to="/products?category_slug=fashion">Fashion</Link><Link to="/products?category_slug=home-garden">Home & garden</Link><Link to="/products?category_slug=food">Food</Link><Link to="/products?category_slug=beauty">Beauty</Link>{user?.role === 'SELLER' && <Link to="/seller/products">Manage products</Link>}</div></header>
    <Outlet />
    <nav className="mobile-dock" aria-label="Mobile navigation"><Link className={location.pathname === '/' ? 'active' : ''} to="/"><span>⌂</span>Home</Link><Link className={location.pathname.startsWith('/products') ? 'active' : ''} to="/products"><span>▦</span>Shop</Link>{(!user || user.role === 'BUYER') && <Link className={location.pathname === '/cart' ? 'active' : ''} to="/cart"><span className="dock-cart">{count}</span>Cart</Link>}<Link className={location.pathname === '/account' || location.pathname === '/login' ? 'active' : ''} to={user ? '/account' : '/login'}><span>○</span>{user ? 'Account' : 'Log in'}</Link></nav>
    <footer className="market-footer"><div className="market-container footer-grid"><div><Brand footer /><p>Verified local commerce, protected payments, and delivery designed for Zambia.</p></div><nav><strong>Marketplace</strong><Link to="/products">All products</Link><Link to="/register">Create account</Link><Link to="/courier/register">Become a courier</Link></nav><nav><strong>Trust and legal</strong><Link to="/legal/terms">Platform terms</Link><Link to="/legal/privacy">Privacy</Link><Link to="/legal/seller">Seller terms</Link></nav></div><div className="market-container footer-bottom">© 2026 Optimistic by Zuzelarian Technologies · Zambia</div></footer>
  </>;
}
