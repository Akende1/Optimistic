import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';
import { Screen, Status } from '../components/State';

export default function SellerProfile() {
  const [form, setForm] = useState(null);
  const query = useQuery({ queryKey: ['seller-profile'], queryFn: async () => { const value = await api('/sellers/me/'); setForm(value); return value; } });
  const save = useMutation({ mutationFn: () => { const body = new FormData(); ['store_name', 'phone', 'description', 'profile_image', 'banner_image'].forEach((key) => form[key] != null && body.append(key, form[key])); return api('/sellers/update_profile/', { method: 'PATCH', body }); }, onSuccess: () => query.refetch() });
  return <Screen eyebrow="SELLER STORE" title="Store profile" description="Public store presentation is separated from protected KYC and payout details."><Status loading={query.isLoading} error={query.error || save.error} />{form && <form className="form card-panel" onSubmit={(event) => { event.preventDefault(); save.mutate(); }}><label>Store name<input value={form.store_name || ''} onChange={(event) => setForm({ ...form, store_name: event.target.value })} /></label><label>Public phone<input value={form.phone || ''} onChange={(event) => setForm({ ...form, phone: event.target.value })} /></label><label>Description<textarea value={form.description || ''} onChange={(event) => setForm({ ...form, description: event.target.value })} /></label><label>Logo<input type="file" accept="image/*" onChange={(event) => setForm({ ...form, profile_image: event.target.files[0] })} /></label><label>Banner<input type="file" accept="image/*" onChange={(event) => setForm({ ...form, banner_image: event.target.files[0] })} /></label><button disabled={save.isPending}>Save store</button></form>}</Screen>;
}
