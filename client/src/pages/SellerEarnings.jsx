import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, list } from '../lib/api';
import { Screen, Status } from '../components/State';

const money = (value) => new Intl.NumberFormat('en-ZM', { style: 'currency', currency: 'ZMW' }).format(Number(value || 0));

export default function SellerEarnings() {
  const [amount, setAmount] = useState('');
  const queryClient = useQueryClient();
  const analytics = useQuery({ queryKey: ['seller-analytics', 30], queryFn: () => api('/sellers/analytics/?days=30') });
  const payouts = useQuery({ queryKey: ['seller-payouts'], queryFn: () => api('/sellers/payout_requests/') });
  const withdraw = useMutation({
    mutationFn: () => api('/sellers/payout_requests/', { method: 'POST', body: JSON.stringify({ amount }) }),
    onSuccess: () => { setAmount(''); queryClient.invalidateQueries({ queryKey: ['seller-payouts'] }); queryClient.invalidateQueries({ queryKey: ['seller-analytics'] }); },
  });
  const balances = analytics.data?.balances;
  return <Screen eyebrow="SELLER FINANCE" title="Earnings and withdrawals" description="Balances are controlled by escrow and immutable ledger events. Withdrawal requests enter the administrator payout queue.">
    <Status loading={analytics.isLoading || payouts.isLoading} error={analytics.error || payouts.error} />
    {balances && <div className="metrics-grid"><article className="metric-card"><small>AVAILABLE</small><strong>{money(balances.available)}</strong></article><article className="metric-card"><small>PENDING</small><strong>{money(balances.pending)}</strong></article><article className="metric-card"><small>LIFETIME</small><strong>{money(balances.lifetime_earnings)}</strong></article></div>}
    <div className="finance-grid"><form className="form card-panel" onSubmit={(event) => { event.preventDefault(); withdraw.mutate(); }}><h2>Request withdrawal</h2><p>The verified payout destination on your seller profile will be used.</p><label>Amount (ZMW)<input type="number" min="1" step="0.01" required value={amount} onChange={(event) => setAmount(event.target.value)} /></label><button disabled={withdraw.isPending || Number(amount) > Number(balances?.available || 0)}>{withdraw.isPending ? 'Submitting…' : 'Request payout'}</button>{withdraw.error && <p className="error">{withdraw.error.message}</p>}</form><section><h2>Withdrawal history</h2><div className="stack">{list(payouts.data).map((row) => <article className="order-card" key={row.id}><div><strong>{money(row.amount)}</strong><p>{row.provider} · {new Date(row.requested_at).toLocaleDateString('en-ZM')}</p></div><span className="badge">{row.status}</span></article>)}</div>{!payouts.isLoading && !list(payouts.data).length && <p className="notice">No withdrawal requests yet.</p>}</section></div>
  </Screen>;
}
