import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { api, list } from '../lib/api';
import { useCart } from '../stores/cart';
import { Screen, Status } from '../components/State';

const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

export default function Checkout() {
  const lines = useCart((state) => state.lines);
  const clear = useCart((state) => state.clear);
  const navigate = useNavigate();
  const addresses = useQuery({ queryKey: ['addresses'], queryFn: () => api('/auth/addresses/') });
  const zones = useQuery({ queryKey: ['zones'], queryFn: () => api('/locations/?type=ZONE') });
  const [form, setForm] = useState({ shipping_address: '', delivery_zone_id: '', delivery_instructions: '', origin_pickup_required: false, destination_delivery_required: false });
  const quote = useQuery({ queryKey: ['delivery-quote', form.delivery_zone_id, form.origin_pickup_required, form.destination_delivery_required], enabled: Boolean(form.delivery_zone_id), queryFn: () => api('/orders/delivery-quote/', { method: 'POST', body: JSON.stringify({ delivery_zone_id: Number(form.delivery_zone_id), origin_pickup_required: form.origin_pickup_required, destination_delivery_required: form.destination_delivery_required }) }) });
  const create = useMutation({ mutationFn: () => api('/orders/', { method: 'POST', body: JSON.stringify({ ...form, delivery_zone_id: Number(form.delivery_zone_id), items: lines.map((line) => ({ product: line.product, quantity: line.quantity })) }) }), onSuccess: (order) => { clear(); navigate(`/orders/${order.id}`); } });
  const subtotal = lines.reduce((total, line) => total + Number(line.price) * line.quantity, 0);
  const selectAddress = (id) => {
    const address = list(addresses.data).find((row) => String(row.id) === id);
    if (address) setForm({ ...form, shipping_address: [address.street_address, address.full_location].filter(Boolean).join(', '), delivery_zone_id: address.location ? String(address.location) : form.delivery_zone_id, delivery_instructions: address.delivery_notes || form.delivery_instructions });
  };
  return <Screen eyebrow="SECURE CHECKOUT" title="Choose how it gets there" description="Depot collection is lowest cost. Seller pickup and destination last mile are optional and buyer-paid."><div className="checkout-grid"><form className="form card-panel" onSubmit={(event) => { event.preventDefault(); create.mutate(); }}>
    <Status loading={addresses.isLoading || zones.isLoading} error={addresses.error || zones.error} />
    {list(addresses.data).length > 0 && <label>Saved address<select defaultValue="" onChange={(event) => selectAddress(event.target.value)}><option value="">Choose</option>{list(addresses.data).map((address) => <option key={address.id} value={address.id}>{address.label} · {address.street_address}</option>)}</select></label>}
    <label>Full delivery address<textarea required value={form.shipping_address} onChange={(event) => setForm({ ...form, shipping_address: event.target.value })} /></label>
    <label>Destination zone<select required value={form.delivery_zone_id} onChange={(event) => setForm({ ...form, delivery_zone_id: event.target.value })}><option value="">Choose zone</option>{list(zones.data).map((zone) => <option key={zone.id} value={zone.id}>{zone.full_address}</option>)}</select></label>
    <label className="check"><input type="checkbox" checked={form.origin_pickup_required} onChange={(event) => setForm({ ...form, origin_pickup_required: event.target.checked })} /><span>Pickup from seller required <small>Optional local rider; seller may deliver to depot.</small></span></label>
    <label className="check"><input type="checkbox" checked={form.destination_delivery_required} onChange={(event) => setForm({ ...form, destination_delivery_required: event.target.checked })} /><span>Deliver from destination depot to my address <small>Leave off to collect from depot.</small></span></label>
    <label>Delivery instructions<textarea value={form.delivery_instructions} onChange={(event) => setForm({ ...form, delivery_instructions: event.target.value })} /></label>
    {create.error && <p className="error">{create.error.message}</p>}<button disabled={!lines.length || !quote.data || create.isPending}>{create.isPending ? 'Creating order…' : 'Place order'}</button>
  </form><aside className="card-panel"><small>SERVER DELIVERY QUOTE</small>{lines.map((line) => <div className="line" key={line.product}><span>{line.name} × {line.quantity}</span><strong>{money(Number(line.price) * line.quantity)}</strong></div>)}<div className="fee"><span>Products</span><strong>{money(subtotal)}</strong></div><div className="fee"><span>Origin pickup</span><strong>{money(quote.data?.origin_pickup_fee)}</strong></div><div className="fee"><span>Inter-district / zone</span><strong>{money(quote.data?.inter_district_fee)}</strong></div><div className="fee"><span>Destination delivery</span><strong>{money(quote.data?.destination_delivery_fee)}</strong></div><h2>{money(subtotal + Number(quote.data?.delivery_fee || 0))}</h2><p>{quote.data?.delivery_service?.replaceAll('_', ' ') || 'Select a zone for a server quote.'}</p></aside></div></Screen>;
}
