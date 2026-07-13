import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Screen } from '../components/State';

export default function CourierRegister() {
  const [form, setForm] = useState({ username: '', password: '', name: '', phone: '', email: '', partner_type: 'RIDER', service_area: '', vehicle_type: 'Motorcycle', id_number: '' });
  const register = useMutation({ mutationFn: () => api('/delivery-partners/register/', { method: 'POST', body: JSON.stringify(form) }) });
  const change = (event) => setForm({ ...form, [event.target.name]: event.target.value });
  if (register.data) return <Screen eyebrow="DELIVERY PARTNER" title="Application received" description="Assignments remain disabled until administrator verification."><div className="card-panel"><p>{register.data.message}</p><p>Partner reference: {register.data.partner_id}</p></div></Screen>;
  return <Screen eyebrow="DELIVERY PARTNER" title="Courier registration" description="Apply as an independent rider, courier/postal service, or bus operator."><form className="form card-panel" onSubmit={(event) => { event.preventDefault(); register.mutate(); }}>
    {['username', 'name', 'phone', 'email', 'service_area', 'vehicle_type', 'id_number'].map((key) => <label key={key}>{key.replaceAll('_', ' ')}<input name={key} type={key === 'email' ? 'email' : 'text'} required value={form[key]} onChange={change} /></label>)}
    <label>Password<input name="password" type="password" minLength="6" required value={form.password} onChange={change} /></label>
    <label>Partner type<select name="partner_type" value={form.partner_type} onChange={change}><option value="RIDER">Independent rider</option><option value="COURIER">Courier company / postal service</option><option value="BUS">Bus operator</option><option value="SELF">Seller self-delivery</option></select></label>
    <button disabled={register.isPending}>{register.isPending ? 'Submitting…' : 'Submit application'}</button>{register.error && <p className="error">{register.error.message}</p>}
  </form></Screen>;
}
