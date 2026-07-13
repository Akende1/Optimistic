import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import ProductCard from '../components/ProductCard';
import { api, list } from '../lib/api';

export default function Products() {
  const [params, setParams] = useSearchParams();
  const page = Number(params.get('page') || 1);
  const categories = useQuery({ queryKey: ['categories'], queryFn: () => api('/categories/') });
  const queryString = params.toString();
  const products = useQuery({ queryKey: ['products', queryString], queryFn: () => api(`/products/?${queryString}`), placeholderData: (previous) => previous });
  const rows = list(products.data);
  const totalPages = Math.max(1, Math.ceil((products.data?.count || rows.length) / 20));
  const update = (key, value) => { const next = new URLSearchParams(params); value ? next.set(key, value) : next.delete(key); if (key !== 'page') next.delete('page'); setParams(next); };
  const pageNumbers = Array.from({ length: Math.min(5, totalPages) }, (_, index) => Math.min(Math.max(page - 2, 1) + index, totalPages)).filter((value, index, array) => array.indexOf(value) === index);
  return <main className="market-container catalog-page">
    <div className="catalog-heading"><div><span className="eyebrow">MARKETPLACE CATALOG</span><h1>Find the right product</h1><p>{products.data?.count ?? 0} active listings from verified sellers</p></div><label className="sort-control">Sort by<select value={params.get('ordering') || '-created_at'} onChange={(event) => update('ordering', event.target.value)}><option value="-created_at">Newest</option><option value="price">Price: low to high</option><option value="-price">Price: high to low</option></select></label></div>
    <div className="catalog-layout"><aside className="filter-panel"><div className="filter-title"><h2>Filters</h2><button className="text-button" onClick={() => setParams({})}>Clear</button></div><label>Search<input value={params.get('search') || ''} onChange={(event) => update('search', event.target.value)} placeholder="Phone, shoes, parts…" /></label><fieldset><legend>Category</legend><label className="radio-row"><input type="radio" checked={!params.get('category')} onChange={() => update('category', '')} />All categories</label>{list(categories.data).map((category) => <label className="radio-row" key={category.id}><input type="radio" checked={params.get('category') === String(category.id)} onChange={() => update('category', String(category.id))} />{category.name}</label>)}</fieldset><fieldset><legend>Price range (ZMW)</legend><div className="price-fields"><input type="number" min="0" placeholder="Min" value={params.get('min_price') || ''} onChange={(event) => update('min_price', event.target.value)} /><input type="number" min="0" placeholder="Max" value={params.get('max_price') || ''} onChange={(event) => update('max_price', event.target.value)} /></div></fieldset><label className="radio-row"><input type="checkbox" checked={params.get('in_stock') === 'true'} onChange={(event) => update('in_stock', event.target.checked ? 'true' : '')} />In stock only</label></aside>
      <section className="catalog-results">{products.isFetching && <div className="catalog-progress">Updating catalog…</div>}{products.error && <p className="notice error">{products.error.message}</p>}{!products.isLoading && !rows.length && <div className="empty-catalog"><h2>No products found</h2><p>Try removing a filter or searching for a broader term.</p><button onClick={() => setParams({})}>Reset filters</button></div>}<div className="market-product-grid catalog">{rows.map((product) => <ProductCard product={product} key={product.id} />)}</div>{totalPages > 1 && <nav className="pagination" aria-label="Product pages"><button disabled={page <= 1} onClick={() => update('page', String(page - 1))} aria-label="Previous page">‹</button>{pageNumbers.map((number) => <button className={number === page ? 'active' : ''} aria-current={number === page ? 'page' : undefined} onClick={() => update('page', String(number))} key={number}>{number}</button>)}<button disabled={page >= totalPages} onClick={() => update('page', String(page + 1))} aria-label="Next page">›</button></nav>}</section>
    </div>
  </main>;
}
