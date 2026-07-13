import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Screen } from '../components/State';

export default function PasswordReset() {
  const [form, setForm] = useState({ email: '', code: '', new_password: '' });
  const [sent, setSent] = useState(false);
  const request = useMutation({ mutationFn: () => api('/auth/password-reset/request/', { method: 'POST', body: JSON.stringify({ email: form.email }) }), onSuccess: (data) => { setSent(true); if (data.debug_code) setForm((old) => ({ ...old, code: data.debug_code })); } });
  const confirm = useMutation({ mutationFn: () => api('/auth/password-reset/confirm/', { method: 'POST', body: JSON.stringify(form) }) });
  return <Screen eyebrow="ACCOUNT RECOVERY" title="Reset password" description="A short-lived code is sent without revealing whether an account exists.">{confirm.data ? <div className="card-panel"><h2>Password changed</h2><p>{confirm.data.message}</p><Link className="cta" to="/login">Sign in</Link></div> : <form className="form card-panel" onSubmit={(event) => { event.preventDefault(); sent ? confirm.mutate() : request.mutate(); }}><label>Email<input type="email" required value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>{sent && <><label>Six-digit code<input inputMode="numeric" maxLength="6" required value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} /></label><label>New password<input type="password" minLength="8" required value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })} /></label></>}<button disabled={request.isPending || confirm.isPending}>{sent ? 'Set new password' : 'Send reset code'}</button>{(request.error || confirm.error) && <p className="error">{(request.error || confirm.error).message}</p>}</form>}</Screen>;
}
