import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { api, all, ApiError, Banner, Cart, clearSession, Customer, initSession, Product, Season, setSession, signedIn } from './api';
import { useStock, withStock } from './stock';

function useShopState() {
  const [products, setProducts] = useState<Product[]>([]), [banners, setBanners] = useState<Banner[]>([]), [seasons, setSeasons] = useState<Season[]>([]);
  const [shopInfo, setShopInfo] = useState<{ ordering_enabled: boolean; business_name?: string }>({ ordering_enabled: false });
  const [cart, setCart] = useState<Cart | null>(null), [customer, setCustomer] = useState<Customer | null>(null), [wishlist, setWishlist] = useState<Product[]>([]);
  const [busy, setBusy] = useState(false), [ready, setReady] = useState(false), [notice, setNotice] = useState(''), [failed, setFailed] = useState(false);
  const pending = useRef(false);
  const live = useStock(ready ? cart?.lines.map(line => line.product.id) || [] : []);
  const liveProduct = (product: Product) => withStock(product, live.stock[product.id]);
  const liveCart = cart ? { ...cart, lines: cart.lines.map(line => {
    const product = liveProduct({ ...line.product, variants: [line.variant] });
    return { ...line, product, variant: product.variants![0] };
  }) } : null;
  const stockIssue = !!liveCart?.lines.some(line => line.product.is_active === false || ['coming_soon', 'off_season'].includes(line.product.season_status) || line.qty > line.variant.stock_qty);
  const refreshCart = async () => setCart(await api<Cart>('/cart'));
  const refreshWishlist = async () => setWishlist((await api<{ items: Product[] }>('/me/wishlist')).items);
  async function perform(task: () => Promise<void>, message = '') {
    if (pending.current) return false;
    pending.current = true; setBusy(true); setNotice('');
    try { await task(); if (message) setNotice(message); return true; }
    catch (error) {
      if (error instanceof ApiError && error.status === 401 && signedIn()) {
        await clearSession(); setCustomer(null); setWishlist([]); setCart(null);
        setNotice('Your session expired. Log in again to continue.');
      } else setNotice(error instanceof Error ? error.message : 'Please try again.');
      return false;
    } finally { pending.current = false; setBusy(false); live.refreshStock(); }
  }
  async function reload() {
    setFailed(false);
    const ok = await perform(async () => {
      // A sleeping free host may need a minute before ordinary API requests can run.
      await api('/health');
      setShopInfo(await api('/shop-info'));
      const [items, slides, hub, current] = await Promise.all([all<Product>('/products'), api<{ items: Banner[] }>('/banners'), api<{ varieties: Season[] }>('/mango-season'), api<Cart>('/cart')]);
      setProducts(items); setBanners(slides.items); setSeasons(hub.varieties); setCart(current);
      if (signedIn()) { setCustomer(await api<Customer>('/me')); await refreshWishlist(); }
    });
    setReady(true); setFailed(!ok);
  }
  useEffect(() => { initSession().then(reload).catch(() => { setReady(true); setFailed(true); setNotice('Could not restore your session. Please reload the page.'); }); }, []);
  async function authenticate(values: Record<string, string>, signup: boolean) {
    const result = await api('/auth/' + (signup ? 'signup' : 'login'), 'POST', values);
    await setSession(result); setCustomer(result.customer); await refreshCart(); await refreshWishlist();
    if (result.cart_merge?.adjustments?.length) setNotice('Your cart was merged. Some quantities changed to match available stock.');
  }
  async function logout() {
    await api('/auth/logout', 'POST', {}); await clearSession(); setCustomer(null); setWishlist([]); await refreshCart();
  }
  async function add(variant: string) { setCart(await api<Cart>('/cart/lines', 'POST', { variant_id: variant, qty: 1 })); }
  async function toggleWishlist(product: Product) {
    await api('/me/wishlist/' + product.id, wishlist.some(item => item.id === product.id) ? 'DELETE' : 'PUT', undefined);
    await refreshWishlist();
  }
  return { products, banners, seasons, shopInfo, cart: liveCart, setCart, customer, setCustomer, wishlist, busy, ready, failed, notice, setNotice, perform, reload, refreshCart, authenticate, logout, add, toggleWishlist, ...live, liveProduct, stockIssue };
}
const Shop = createContext<ReturnType<typeof useShopState> | null>(null);
export const useShop = () => useContext(Shop)!;
export function ShopProvider({ children }: { children: ReactNode }) { return <Shop.Provider value={useShopState()}>{children}</Shop.Provider>; }
