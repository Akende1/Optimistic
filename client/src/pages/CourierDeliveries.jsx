import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

const next = { ASSIGNED: 'PICKED_UP', PICKED_UP: 'IN_TRANSIT', IN_TRANSIT: 'OUT_FOR_DELIVERY', OUT_FOR_DELIVERY: 'DELIVERED' };

function DeliveryCard({ delivery, update }) {
  const [description, setDescription] = useState('');
  const send = (status) => update({ id: delivery.id, status, description, external_event_id: crypto.randomUUID(), occurred_at: new Date().toISOString() });
  return <article className="card-panel delivery-card"><div className="panel-heading"><div><small>ORDER #{delivery.order_id}</small><h2>{delivery.status.replaceAll('_', ' ')}</h2></div><span className="badge">{delivery.partner_name || 'Assigned courier'}</span></div><dl className="delivery-addresses"><div><dt>Pickup</dt><dd>{delivery.pickup_address}</dd></div><div><dt>Destination</dt><dd>{delivery.delivery_address}</dd></div></dl><label>Event note<input value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Location, recipient or exception detail" /></label><div className="actions">{next[delivery.status] && <button onClick={() => send(next[delivery.status])}>{next[delivery.status].replaceAll('_', ' ')}</button>} {!['DELIVERED', 'RETURNED', 'LOST', 'CANCELLED'].includes(delivery.status) && <button className="button-quiet" onClick={() => send('EXCEPTION')}>Report exception</button>}</div>{delivery.events?.length > 0 && <ol className="event-list">{delivery.events.slice(-4).reverse().map((event) => <li key={event.id}><strong>{event.status.replaceAll('_', ' ')}</strong><span>{event.location || event.description || new Date(event.occurred_at).toLocaleString('en-ZM')}</span></li>)}</ol>}</article>;
}

export default function CourierDeliveries() {
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ['deliveries'], queryFn: () => api('/deliveries/'), refetchInterval: 20000 });
  const mutation = useMutation({ mutationFn: ({ id, ...event }) => api(`/deliveries/${id}/events/`, { method: 'POST', body: JSON.stringify({ ...event, source: 'COURIER' }) }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['deliveries'] }) });
  const rows = list(query.data);
  return <Screen eyebrow="COURIER OPERATIONS" title="Assigned deliveries" description="Append verified custody and delivery events. Server state controls every allowed commercial outcome."><Status loading={query.isLoading} error={query.error || mutation.error} empty={!query.isLoading && !rows.length} /><div className="stack">{rows.map((delivery) => <DeliveryCard key={delivery.id} delivery={delivery} update={(event) => mutation.mutate(event)} />)}</div></Screen>;
}
