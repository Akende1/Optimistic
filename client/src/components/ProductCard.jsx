import { Link } from 'react-router-dom';

const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

export default function ProductCard({ product, badge }) {
  const image = product.images?.find((item) => item.is_primary)?.image_url || product.images?.[0]?.image_url;
  return <Link className="market-card" to={`/products/${product.id}`}>
    <div className="market-card-media">
      {badge && <span className="deal-badge">{badge}</span>}
      {image ? <img src={image} alt={product.name} loading="lazy" /> : <span className="product-fallback">{product.name?.slice(0, 2).toUpperCase()}</span>}
    </div>
    <div className="market-card-copy">
      <small>{product.category_name}</small>
      <h3>{product.name}</h3>
      <strong>{money(product.price)}</strong>
      <p>{product.seller_name || 'Verified marketplace seller'}</p>
      <span className={Number(product.available_stock ?? product.stock) > 0 ? 'stock-ok' : 'stock-out'}>{Number(product.available_stock ?? product.stock) > 0 ? 'In stock' : 'Out of stock'}</span>
    </div>
  </Link>;
}
