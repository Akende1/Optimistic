import { Link } from 'react-router-dom';
import { useCart } from '../stores/cart';
import { Screen } from '../components/State';

export default function Cart() {
  const { lines, remove } = useCart();
  const total = lines.reduce((sum, line) => sum + Number(line.price) * line.quantity, 0);
  return <Screen eyebrow="YOUR BASKET" title="Cart" description="Review your products before secure server-priced checkout.">{!lines.length && <div className="notice">Your cart is empty. <Link className="text-link" to="/products">Browse products</Link></div>}{lines.map((line) => <div className="line" key={line.product}><span>{line.name} × {line.quantity}</span><strong>K {(Number(line.price) * line.quantity).toFixed(2)}</strong><button className="button-quiet" onClick={() => remove(line.product)}>Remove</button></div>)}{lines.length > 0 && <div className="cart-total"><div><small>ESTIMATED SUBTOTAL</small><h2>K {total.toFixed(2)}</h2><p>The server confirms the authoritative total and delivery fee.</p></div><div className="actions"><Link className="cta" to="/checkout">Retail checkout</Link><Link className="button-quiet" to="/checkout/purchase-order">Purchase order</Link></div></div>}</Screen>;
}
