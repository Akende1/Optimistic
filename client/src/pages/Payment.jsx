import { Link, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

const terminal = ['CAPTURED', 'FAILED', 'EXPIRED', 'CANCELLED'];
export default function Payment() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const attempts = useQuery({ queryKey: ['payment-attempts', id], queryFn: () => api(`/orders/${id}/payment-attempts/`), refetchInterval: (query) => terminal.includes(list(query.state.data)[0]?.status) ? false : 4000 });
  const latest = list(attempts.data)[0];
  const create = useMutation({ mutationFn: () => api(`/orders/${id}/payment-attempts/`, { method: 'POST', headers: { 'Idempotency-Key': crypto.randomUUID() }, body: JSON.stringify({ provider: 'TEST' }) }), onSuccess: () => queryClient.invalidateQueries({ queryKey: ['payment-attempts', id] }) });
  const simulate = useMutation({ mutationFn: () => api(`/orders/${id}/simulate-payment/`, { method: 'POST', body: JSON.stringify({ attempt_id: latest.id, outcome: 'CAPTURED', event_id: crypto.randomUUID() }) }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['payment-attempts', id] }); queryClient.invalidateQueries({ queryKey: ['order', id] }); } });
  return <Screen eyebrow={`ORDER #${id}`} title="Payment" description="This screen can be safely reloaded; Django restores the latest attempt and remains authoritative."><Status loading={attempts.isLoading} error={attempts.error || create.error || simulate.error} />{!latest && <div className="card-panel"><h2>No payment attempt</h2><button onClick={() => create.mutate()}>Start simulated payment</button></div>}{latest && <div className="card-panel payment-state"><span className="badge">{latest.status}</span><h2>{latest.amount} {latest.currency}</h2><p>Provider: {latest.provider}</p>{latest.failure_code && <p className="error">{latest.failure_code}</p>}{!terminal.includes(latest.status) && <button onClick={() => simulate.mutate()}>Complete simulated payment</button>}{latest.status === 'CAPTURED' && <Link className="cta" to={`/orders/${id}`}>View confirmed order</Link>}{['FAILED', 'EXPIRED', 'CANCELLED'].includes(latest.status) && <button onClick={() => create.mutate()}>Try again</button>}</div>}</Screen>;
}
