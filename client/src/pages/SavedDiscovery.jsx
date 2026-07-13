import { Link } from 'react-router-dom';
import { useDiscovery } from '../stores/discovery';
import { Screen } from '../components/State';
export default function SavedDiscovery({mode='wishlist'}){const rows=useDiscovery(state=>state[mode]);return <Screen eyebrow="DISCOVERY" title={mode==='wishlist'?'Wishlist':'Recently viewed'} description="Saved on this device for the MVP.">{!rows.length&&<p className="notice">Nothing here yet.</p>}<div className="grid">{rows.map(product=><Link className="card" to={`/products/${product.id}`} key={product.id}><div className="image">{product.image&&<img src={product.image} alt=""/>}</div><h3>{product.name}</h3><strong>K {product.price}</strong></Link>)}</div></Screen>}
