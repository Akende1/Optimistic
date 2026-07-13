import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { useCart } from '../stores/cart';
import { useDiscovery } from '../stores/discovery';

const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

export default function Product() {
  const { id } = useParams();
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);
  const add = useCart((state) => state.add);
  const toggle = useDiscovery((state) => state.toggleWishlist);
  const recordView = useDiscovery((state) => state.view);
  const wishlist = useDiscovery((state) => state.wishlist);
  const query = useQuery({ queryKey: ['product', id], queryFn: () => api(`/products/${id}/`) });
  const product = query.data;
  useEffect(() => { if (product) recordView({ id: product.id, name: product.name, price: product.price, image: product.images?.[0]?.image_url }); }, [product, recordView]);
  if (query.isLoading) return <main className="market-container detail-state">Loading product…</main>;
  if (query.error) return <main className="market-container detail-state notice error">{query.error.message}</main>;
  const images = product.images || [];
  const available = Number(product.available_stock ?? product.stock ?? 0);
  const saved = wishlist.some((row) => row.id === product.id);
  return <main className="market-container product-page">
    <nav className="breadcrumbs"><Link to="/">Home</Link><span>/</span><Link to={`/products?category=${product.category}`}>{product.category_name}</Link><span>/</span><span>{product.name}</span></nav>
    <section className="product-decision">
      <div className="product-gallery"><div className="product-main-image">{images[selectedImage]?.image_url ? <img src={images[selectedImage].image_url} alt={product.name} /> : <span className="product-fallback large">{product.name.slice(0, 2).toUpperCase()}</span>}</div>{images.length > 1 && <div className="product-thumbnails">{images.map((image, index) => <button className={selectedImage === index ? 'active' : ''} onClick={() => setSelectedImage(index)} key={image.id}><img src={image.image_url} alt={`${product.name} view ${index + 1}`} /></button>)}</div>}</div>
      <div className="purchase-panel"><span className="category-pill">{product.category_name}</span><h1>{product.name}</h1><Link className="seller-line" to={`/sellers/${product.seller}`}>Sold by <strong>{product.seller_name}</strong> <span>Verified seller</span></Link><div className="price-block"><small>Price</small><strong>{money(product.price)}</strong><span>Taxes and delivery calculated by the server at checkout</span></div><div className="availability"><span className={available ? 'status-dot ready' : 'status-dot'} />{available ? `${available} available` : 'Currently out of stock'}</div><div className="purchase-controls"><label>Quantity<div className="quantity-stepper"><button onClick={() => setQuantity(Math.max(1, quantity - 1))} aria-label="Decrease quantity">−</button><input value={quantity} onChange={(event) => setQuantity(Math.min(Math.max(Number(event.target.value) || 1, 1), available || 1))} inputMode="numeric" /><button onClick={() => setQuantity(Math.min(quantity + 1, available))} disabled={quantity >= available} aria-label="Increase quantity">+</button></div></label><button className="add-cart" disabled={!available} onClick={() => add({ product: product.id, name: product.name, price: product.price, quantity })}>Add to cart</button><button className="save-product" onClick={() => toggle({ id: product.id, name: product.name, price: product.price, image: images[0]?.image_url })}>{saved ? 'Saved to wishlist' : 'Save for later'}</button></div><div className="commerce-assurances"><div><strong>Protected payment</strong><span>Payment state confirmed by Optimistic</span></div><div><strong>Flexible delivery</strong><span>Local, depot, and inter-district options</span></div><div><strong>Buyer support</strong><span>Line cancellation and returns where eligible</span></div></div></div>
    </section>
    <section className="product-information"><article><span className="eyebrow">PRODUCT INFORMATION</span><h2>About this item</h2><p>{product.description}</p></article><article><span className="eyebrow">SPECIFICATIONS</span><h2>Product details</h2><dl className="spec-table">{Object.entries(product.attributes || {}).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{String(value)}</dd></div>)}<div><dt>Shipping class</dt><dd>{product.shipping_class || 'Standard'}</dd></div>{product.weight_kg && <div><dt>Package weight</dt><dd>{product.weight_kg} kg</dd></div>}</dl></article></section>
  </main>;
}
