import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Screen, Status } from '../components/State';

const next = { AWAITING_ACCEPTANCE: 'ACCEPTED', ACCEPTED: 'PICKING', PICKING: 'PACKED', PACKED: 'READY_FOR_PICKUP', READY_FOR_PICKUP: 'HANDED_OVER' };
export default function FulfillmentDetail() {
  const { id } = useParams(); const queryClient = useQueryClient();
  const [shipping, setShipping] = useState({ carrier: '', tracking_number: '' });
  const query = useQuery({ queryKey: ['fulfillment', id], queryFn: () => api(`/fulfillments/${id}/`), refetchInterval: 15000 });
  const transition = useMutation({ mutationFn: (status) => api(`/fulfillments/${id}/transition/`, { method: 'POST', body: JSON.stringify({ status, ...shipping }) }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fulfillment', id] }); queryClient.invalidateQueries({ queryKey: ['fulfillments'] }); } });
  const row = query.data; const target = next[row?.status];
  return <Screen eyebrow="SELLER FULFILLMENT" title={`Fulfillment #${id}`} description="Carrier and tracking are captured at handover; transitions cannot skip state."><Status loading={query.isLoading} error={query.error || transition.error} />{row && <div className="form card-panel"><span className="badge">{row.status.replaceAll('_', ' ')}</span><h2>Order #{row.order}</h2><p>Due {row.fulfill_by ? new Date(row.fulfill_by).toLocaleString('en-ZM') : '—'}</p>{row.status === 'READY_FOR_PICKUP' && <><label>Carrier<input required value={shipping.carrier} onChange={(event) => setShipping({ ...shipping, carrier: event.target.value })} /></label><label>Tracking or waybill number<input required value={shipping.tracking_number} onChange={(event) => setShipping({ ...shipping, tracking_number: event.target.value })} /></label></>}{target && <button disabled={transition.isPending || (target === 'HANDED_OVER' && (!shipping.carrier || !shipping.tracking_number))} onClick={() => transition.mutate(target)}>{target.replaceAll('_', ' ')}</button>}</div>}</Screen>;
}
