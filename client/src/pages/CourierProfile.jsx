import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Screen, Status } from '../components/State';

export default function CourierProfile() {
  const [form, setForm] = useState(null);
  const profile = useQuery({ queryKey: ['courier-profile'], queryFn: async () => { const value = await api('/delivery-partners/me/'); setForm(value); return value; } });
  const save = useMutation({ mutationFn: () => api('/delivery-partners/me/', { method: 'PATCH', body: JSON.stringify({ name: form.name, phone: form.phone, email: form.email, service_area: form.service_area, vehicle_type: form.vehicle_type }) }), onSuccess: () => profile.refetch() });
  return <Screen eyebrow="COURIER ACCOUNT" title="Courier profile" description="Verification controls assignment access."><Status loading={profile.isLoading} error={profile.error || save.error} />{form && <form className="form card-panel" onSubmit={(event) => { event.preventDefault(); save.mutate(); }}><span className="badge">{form.verification_status}</span>{['name', 'phone', 'email', 'service_area', 'vehicle_type'].map((key) => <label key={key}>{key.replaceAll('_', ' ')}<input value={form[key] || ''} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /></label>)}<button>Save profile</button></form>}</Screen>;
}
