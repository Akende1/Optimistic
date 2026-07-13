import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

const terminal = ['COMPLETED', 'CANCELLED', 'REFUNDED'];
const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

export default function OrderDetail() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [attempt, setAttempt] = useState(null);
  const [returnItem, setReturnItem] = useState('');
  const [returnReason, setReturnReason] = useState('');
  const order = useQuery({ queryKey: ['order', id], queryFn: () => api(`/orders/${id}/`), refetchInterval: (query) => terminal.includes(query.state.data?.status) ? false : 5000 });
  const deliveries = useQuery({ queryKey: ['deliveries'], queryFn: () => api('/deliveries/'), refetchInterval: 20000 });
  const refresh = () => { queryClient.invalidateQueries({ queryKey: ['order', id] }); queryClient.invalidateQueries({ queryKey: ['deliveries'] }); };
  const paymentAttempt = useMutation({ mutationFn: () => api(`/orders/${id}/payment-attempts/`, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ provider: 'TEST' }) }), onSuccess: setAttempt });
  const simulate = useMutation({ mutationFn: () => api(`/orders/${id}/simulate-payment/`, { method: 'POST', body: JSON.stringify({ attempt_id: attempt?.id, outcome: 'CAPTURED', event_id: crypto.randomUUID() }) }), onSuccess: refresh });
  const receipt = useMutation({ mutationFn: () => api(`/orders/${id}/confirm-receipt/`, { method: 'POST' }), onSuccess: refresh });
  const cancelLine = useMutation({ mutationFn: ({ item, quantity }) => api(`/orders/${id}/cancel-line/`, { method: 'POST', body: JSON.stringify({ item_id: item, quantity, reason: 'Buyer cancellation' }) }), onSuccess: refresh });
  const createReturn = useMutation({ mutationFn: () => api('/returns/', { method: 'POST', body: JSON.stringify({ order: Number(id), reason: returnReason, lines: [{ order_item: Number(returnItem), quantity: 1 }] }) }), onSuccess: () => { setReturnItem(''); setReturnReason(''); queryClient.invalidateQueries({ queryKey: ['returns'] }); } });
  const value = order.data;
  const delivery = list(deliveries.data).find((row) => String(row.order_id) === String(id));
  const failure = [paymentAttempt, simulate, receipt, cancelLine, createReturn].find((mutation) => mutation.error)?.error;

  return <Screen eyebrow={`ORDER #${id}`} title={value?.status_display || value?.status || 'Order detail'} description="Payment, fulfillment, delivery, return and refund states are confirmed by Django.">
    <Status loading={order.isLoading} error={order.error} />
    {value && <>
      <div className="timeline">{['PENDING', 'PAID', 'READY_FOR_DELIVERY', 'IN_TRANSIT', 'DELIVERED', 'COMPLETED'].map((status) => <span className={status === value.status ? 'active' : ''} key={status}>{status.replaceAll('_', ' ')}</span>)}</div>
      <div className="checkout-grid"><section className="stack">{value.items.map((item) => <article className="order-card" key={item.id}><div><small>{item.seller_name}</small><h3>{item.product_name}</h3><p>{item.active_quantity} active · {money(item.subtotal)}{Number(item.refunded_amount) > 0 && ` · ${money(item.refunded_amount)} refunded`}</p></div>{['PENDING', 'PAID'].includes(value.status) && item.active_quantity > 0 && <button className="button-quiet" disabled={cancelLine.isPending} onClick={() => cancelLine.mutate({ item: item.id, quantity: 1 })}>Cancel one</button>}</article>)}</section><aside className="card-panel"><small>SERVER TOTAL</small><div className="fee"><span>Products</span><strong>{money(value.product_subtotal)}</strong></div><div className="fee"><span>Origin pickup</span><strong>{money(value.origin_pickup_fee)}</strong></div><div className="fee"><span>Inter-district</span><strong>{money(value.inter_district_fee)}</strong></div><div className="fee"><span>Destination delivery</span><strong>{money(value.destination_delivery_fee)}</strong></div><h2>{money(value.total_amount)}</h2><p>{value.delivery_service?.replaceAll('_', ' ')}</p></aside></div>
      <div className="actions">{value.status === 'PENDING' && <Link className="cta" to={`/orders/${id}/payment`}>Pay or resume payment</Link>}{value.can_confirm_delivery && <button onClick={() => receipt.mutate()}>Confirm receipt</button>}</div>
      {delivery && <section className="card-panel top-products"><small>DELIVERY TRACKING</small><h2>{delivery.status.replaceAll('_', ' ')}</h2><p>{delivery.partner_name || 'Awaiting courier'} · {delivery.delivery_address}</p><ol className="event-list">{delivery.events?.slice().reverse().map((event) => <li key={event.id}><strong>{event.status.replaceAll('_', ' ')}</strong><span>{event.location || event.description || new Date(event.occurred_at).toLocaleString('en-ZM')}</span></li>)}</ol></section>}
      {['DELIVERED', 'COMPLETED', 'DISPUTED'].includes(value.status) && <form className="form card-panel top-products" onSubmit={(event) => { event.preventDefault(); createReturn.mutate(); }}><h2>Request a return</h2><label>Product<select required value={returnItem} onChange={(event) => setReturnItem(event.target.value)}><option value="">Choose an order line</option>{value.items.filter((item) => item.active_quantity > 0).map((item) => <option key={item.id} value={item.id}>{item.product_name}</option>)}</select></label><label>Reason<textarea required value={returnReason} onChange={(event) => setReturnReason(event.target.value)} /></label><button disabled={createReturn.isPending}>{createReturn.isPending ? 'Submitting…' : 'Request return of one item'}</button></form>}
      {failure && <p className="notice error">{failure.message}</p>}
    </>}
  </Screen>;
}
