import { useQuery } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

export default function Returns() {
  const query = useQuery({ queryKey: ['returns'], queryFn: () => api('/returns/'), refetchInterval: 30000 });
  const rows = list(query.data);
  return <Screen eyebrow="RETURNS" title="Returns and inspections" description="Physical return custody is tracked separately from disputes, escrow, and refunds."><Status loading={query.isLoading} error={query.error} empty={!query.isLoading && !rows.length} /><div className="stack">{rows.map((row) => <article className="order-card" key={row.id}><div><small>ORDER #{row.order}</small><h3>{row.reason}</h3><p>{row.lines.length} line(s) · requested {new Date(row.created_at).toLocaleDateString('en-ZM')}</p></div><span className="badge">{row.status.replaceAll('_', ' ')}</span></article>)}</div></Screen>;
}
