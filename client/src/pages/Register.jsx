import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, auth } from '../lib/api';
import { Screen } from '../components/State';

const initial = { full_name: '', phone_number: '', email: '', password: '', confirm_password: '', role: 'BUYER', seller_type: '', shop_name: '', accepts_terms: false, accepts_privacy: false };

export default function Register() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initial);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const change = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try { const data = await api('/auth/register/', { method: 'POST', body: JSON.stringify(form) }); auth.set(data.access, data.refresh, data.user); navigate('/verify'); }
    catch (problem) { setError(problem.message); } finally { setBusy(false); }
  }
  return <Screen eyebrow="JOIN OPTIMISTIC" title="Create an account" description="Buy confidently or build a verified marketplace store."><form className="form card-panel" onSubmit={submit}><label>Full name<input value={form.full_name} onChange={(event) => change('full_name', event.target.value)} autoComplete="name" required /></label><label>Phone number<input value={form.phone_number} onChange={(event) => change('phone_number', event.target.value)} autoComplete="tel" inputMode="tel" required /></label><label>Email<input type="email" value={form.email} onChange={(event) => change('email', event.target.value)} autoComplete="email" required /></label><label>Password<input type="password" value={form.password} onChange={(event) => change('password', event.target.value)} autoComplete="new-password" required /></label><label>Confirm password<input type="password" value={form.confirm_password} onChange={(event) => change('confirm_password', event.target.value)} autoComplete="new-password" required /></label><label>Account type<select value={form.role} onChange={(event) => change('role', event.target.value)}><option value="BUYER">Buyer</option><option value="SELLER">Seller</option></select></label>{form.role === 'SELLER' && <><label>Seller type<select value={form.seller_type} onChange={(event) => change('seller_type', event.target.value)} required><option value="">Select</option><option value="INDIVIDUAL">Individual</option><option value="BUSINESS">Business</option></select></label><label>Shop name<input value={form.shop_name} onChange={(event) => change('shop_name', event.target.value)} required /></label></>}<label className="check"><input type="checkbox" checked={form.accepts_terms} onChange={(event) => change('accepts_terms', event.target.checked)} /><span>I accept the <Link className="text-link" to="/legal/terms" target="_blank">Platform Terms</Link>.</span></label><label className="check"><input type="checkbox" checked={form.accepts_privacy} onChange={(event) => change('accepts_privacy', event.target.checked)} /><span>I acknowledge the <Link className="text-link" to="/legal/privacy" target="_blank">Privacy Notice</Link>.</span></label>{error && <p className="error" role="alert">{error}</p>}<button disabled={busy || !form.accepts_terms || !form.accepts_privacy}>{busy ? 'Creating account…' : 'Create account'}</button><p>Already registered? <Link className="text-link" to="/login">Log in</Link></p></form></Screen>;
}
