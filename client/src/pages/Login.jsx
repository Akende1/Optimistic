import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api, auth } from '../lib/api';
import { Screen } from '../components/State';

export default function Login() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError('');
    try { const data = await api('/auth/login/', { method: 'POST', body: JSON.stringify(form) }); auth.set(data.access, data.refresh, data.user); navigate(data.user?.role === 'SELLER' ? '/seller' : data.user?.role === 'COURIER' ? '/courier' : '/'); }
    catch (problem) { setError(problem.message); } finally { setBusy(false); }
  }
  return <Screen eyebrow="WELCOME BACK" title="Sign in" description="Access your orders, store, or delivery work."><form className="form card-panel" onSubmit={submit}><label>Username or email<input value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} autoComplete="username" required /></label><label>Password<input type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} autoComplete="current-password" required /></label>{error && <p className="error" role="alert">{error}</p>}<button disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button><Link className="text-link" to="/password-reset">Forgot password?</Link><p>New to Optimistic? <Link className="text-link" to="/register">Create an account</Link></p></form></Screen>;
}
