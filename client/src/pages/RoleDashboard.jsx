import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

function Metric({ label, value, hint }) {
  return <article className="metric-card"><small>{label}</small><strong>{value}</strong>{hint && <span>{hint}</span>}</article>;
}

function SalesChart({ rows = [] }) {
  const maximum = Math.max(...rows.map((row) => Number(row.gross_sales)), 1);
  if (!rows.length) return <p className="notice">Sales activity will appear after paid orders.</p>;
  return <div className="sales-chart" aria-label="Sales trend">
    {rows.map((row) => <div className="sales-bar" key={row.date} title={`${row.date}: ${money(row.gross_sales)}`}>
      <div style={{ height: `${Math.max((Number(row.gross_sales) / maximum) * 100, 3)}%` }} />
      <small>{new Date(`${row.date}T00:00:00`).toLocaleDateString('en-ZM', { day: 'numeric', month: 'short' })}</small>
    </div>)}
  </div>;
}

export function Seller() {
  const [days, setDays] = useState(30);
  const queryClient = useQueryClient();
  const analytics = useQuery({ queryKey: ['seller-analytics', days], queryFn: () => api(`/sellers/analytics/?days=${days}`) });
  const fulfillments = useQuery({ queryKey: ['fulfillments'], queryFn: () => api('/fulfillments/'), refetchInterval: 15000 });
  const transition = useMutation({
    mutationFn: ({ id, status }) => api(`/fulfillments/${id}/transition/`, { method: 'POST', body: JSON.stringify({ status }) }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fulfillments'] }); queryClient.invalidateQueries({ queryKey: ['seller-analytics'] }); },
  });
  const next = { AWAITING_ACCEPTANCE: 'ACCEPTED', ACCEPTED: 'PICKING', PICKING: 'PACKED', PACKED: 'READY_FOR_PICKUP' };
  const rows = list(fulfillments.data);
  const data = analytics.data;

  return <Screen eyebrow="SELLER OPERATIONS" title="Seller dashboard" description="Sales, inventory, earnings, and fulfillment—scoped only to your store.">
    <div className="dashboard-actions"><Link className="cta" to="/seller/products">Manage products</Link><Link className="button-quiet" to="/seller/kyc">KYC and payout profile</Link><label>Reporting period<select value={days} onChange={(event) => setDays(Number(event.target.value))}><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option><option value="365">1 year</option></select></label></div>
    <Status loading={analytics.isLoading} error={analytics.error} />
    {data && <>
      <div className="metrics-grid">
        <Metric label="NET SALES" value={money(data.sales.net)} hint={`${data.sales.orders} paid orders`} />
        <Metric label="UNITS SOLD" value={data.sales.units_sold} hint={`${money(data.sales.refunds)} refunded`} />
        <Metric label="AVAILABLE" value={money(data.balances.available)} hint={`${money(data.balances.pending)} pending`} />
        <Metric label="OPEN FULFILLMENTS" value={data.fulfillments.open} hint={`${data.products.low_stock} low-stock products`} />
      </div>
      <div className="analytics-grid">
        <section className="card-panel"><div className="panel-heading"><div><small>PERFORMANCE</small><h2>Gross sales trend</h2></div><strong>{money(data.sales.gross)}</strong></div><SalesChart rows={data.trend} /></section>
        <section className="card-panel"><small>CATALOG HEALTH</small><h2>{data.products.active} active products</h2><dl className="analytics-list"><div><dt>Total</dt><dd>{data.products.total}</dd></div><div><dt>Low stock</dt><dd>{data.products.low_stock}</dd></div><div><dt>Out of stock</dt><dd>{data.products.out_of_stock}</dd></div></dl></section>
      </div>
      <section className="card-panel top-products"><small>TOP PRODUCTS</small><h2>Best sellers</h2>{data.top_products.length ? <div className="stack">{data.top_products.map((product, index) => <div className="rank-row" key={product.product_id}><strong>{index + 1}</strong><span>{product.name}<small>{product.units_sold} units</small></span><b>{money(product.gross_sales)}</b></div>)}</div> : <p className="notice">No paid product sales in this period.</p>}</section>
    </>}
    <section className="fulfillment-section"><div className="panel-heading"><div><small>LIVE WORK QUEUE</small><h2>Fulfillment</h2></div><span>Refreshes every 15 seconds</span></div><Status loading={fulfillments.isLoading} error={fulfillments.error} empty={!fulfillments.isLoading && !rows.length} /><div className="grid compact">{rows.map((item) => <article className="card-panel" key={item.id}><small>ORDER #{item.order}</small><h3>{item.status.replaceAll('_', ' ')}</h3><p>Due {item.fulfill_by ? new Date(item.fulfill_by).toLocaleString('en-ZM') : '—'}</p>{next[item.status] && <button disabled={transition.isPending} onClick={() => transition.mutate({ id: item.id, status: next[item.status] })}>{next[item.status].replaceAll('_', ' ')}</button>}</article>)}</div></section>
  </Screen>;
}

export function Courier() { return <Screen eyebrow="COURIER OPERATIONS" title="Delivery queue" description="Assigned deliveries and custody actions."><p className="notice">Courier delivery workflow is available from assigned delivery records.</p></Screen>; }
