import { useCallback, useEffect, useRef, useState } from 'react';
import { AppState, Platform } from 'react-native';
import { API_URL, Product, Variant } from './api';

type Stock = { id: string; is_active: boolean; season_status: string; variants: { id: string; stock_qty: number }[] };
export function withStock(product: Product, snapshot?: Stock): Product {
  if (!snapshot) return product;
  const packs = new Map(snapshot.variants.map(pack => [pack.id, pack.stock_qty]));
  const variant = (pack: Variant): Variant => ({ ...pack, stock_qty: packs.get(pack.id) ?? 0 });
  return { ...product, is_active: snapshot.is_active, season_status: snapshot.season_status,
    default_variant: product.default_variant ? variant(product.default_variant) : null, variants: product.variants?.map(variant) };
}

export function useStock(cartIds: string[]) {
  const [stock, setStock] = useState<Record<string, Stock>>({}), [watched, setWatched] = useState<string[]>([]);
  const [status, setStatus] = useState<'checking' | 'live' | 'offline' | 'paused'>('checking'), [checkedAt, setCheckedAt] = useState<number | null>(null);
  const counts = useRef(new Map<string, number>()), refresh = useRef<() => void>(() => {});
  const watchStock = useCallback((ids: string[]) => {
    const change = (delta: number) => {
      for (const id of new Set(ids)) { const count = (counts.current.get(id) || 0) + delta; if (count) counts.current.set(id, count); else counts.current.delete(id); }
      setWatched([...counts.current.keys()].sort());
    };
    change(1); return () => change(-1);
  }, []);
  const key = [...new Set([...cartIds, ...watched])].sort().join(',');
  useEffect(() => {
    let disposed = false, timer: ReturnType<typeof setTimeout> | undefined, controller: AbortController | undefined, failures = 0;
    const visible = () => AppState.currentState !== 'background' && AppState.currentState !== 'inactive' && (Platform.OS !== 'web' || document.visibilityState === 'visible');
    const stop = () => { clearTimeout(timer); controller?.abort(); controller = undefined; };
    const tick = async () => {
      if (disposed || !visible() || controller || !key) return;
      clearTimeout(timer);
      const request = controller = new AbortController(), timeout = setTimeout(() => request.abort(), 8000);
      setStatus('checking');
      try {
        const ids = key.split(','), items: Stock[] = [];
        for (let index = 0; index < ids.length; index += 100) {
          const response = await fetch(API_URL + '/stock/check', { method: 'POST', signal: request.signal, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ product_ids: ids.slice(index, index + 100) }) });
          if (!response.ok) throw new Error('Stock check unavailable');
          items.push(...(await response.json()).items);
        }
        if (disposed || controller !== request || !visible()) return;
        setStock(previous => ({ ...previous, ...Object.fromEntries(items.map(item => [item.id, item])) }));
        failures = 0; setCheckedAt(Date.now()); setStatus('live');
      } catch {
        if (!disposed && controller === request && visible()) { failures++; setStatus('offline'); }
      } finally {
        clearTimeout(timeout);
        if (controller === request) { controller = undefined; if (!disposed && visible()) timer = setTimeout(tick, Math.min(30000, 5000 * 2 ** failures)); }
      }
    };
    const resume = () => { stop(); if (visible()) tick(); else setStatus('paused'); };
    const subscription = AppState.addEventListener('change', resume);
    if (Platform.OS === 'web') { document.addEventListener('visibilitychange', resume); window.addEventListener('online', resume); }
    refresh.current = () => { if (!controller) tick(); };
    resume();
    return () => { disposed = true; stop(); subscription.remove(); if (Platform.OS === 'web') { document.removeEventListener('visibilitychange', resume); window.removeEventListener('online', resume); } };
  }, [key]);
  return { stock, stockStatus: status, stockCheckedAt: checkedAt, watchStock, refreshStock: useCallback(() => refresh.current(), []) };
}
