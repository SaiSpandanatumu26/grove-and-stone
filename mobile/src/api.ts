import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';

export type Category = 'exotic' | 'dry_fruit' | 'mango';
export type Variant = { id: string; sku: string; pack_label: string; price: string; gst_percent: string; stock_qty: number; is_default: boolean };
export type Product = { id: string; name: string; slug: string; category: Category; origin: string; short_description: string; long_description: string; images: string[]; season_status: string; is_active?: boolean; default_variant: Variant | null; variants?: Variant[]; handling_notes?: string; ripeness_note?: string };
export type Customer = { id: string; full_name: string; email: string; phone: string };
export type Line = { id: string; qty: number; unit_price: string; line_total: string; product: Product; variant: Variant };
export type Cart = { lines: Line[]; subtotal: string; included_gst: string; total_before_shipping: string; pincode: string | null; block_reason: string | null; can_checkout: boolean };
export type Banner = { id: string; title: string; subtitle: string; image: string; cta_label: string; cta_url: string; season_state: string };
export type Season = { id: string; variety_name: string; harvest_start: string; harvest_end: string; status: string; waitlist_enabled: boolean; product: Product | null };
export type Order = { id: string; order_number: string; created_at: string; grand_total: string; subtotal: string; shipping: string; gst: string; status: string; payment_status: string; payment_method: string; payment_backend?: string; payment_expires_at?: string; delivery_date: string; address: Record<string, string>; customer_notes?: string; shipment?: { carrier: string; tracking_number: string; tracking_url?: string }; refund?: { status: string; amount: string }; lines?: { product_name: string; variant_label: string; qty: number; line_total: string }[] };
type Tokens = { access_token: string; refresh_token: string };
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || (__DEV__ ? (Platform.OS === 'web' ? `http://${globalThis.location.hostname}:5000/api/v1` : 'http://10.0.2.2:5000/api/v1') : 'https://grove-and-stone.onrender.com/api/v1')).replace(/\/$/, '');
export const media = (path: string) => path.startsWith('/') ? API_URL.replace(/\/api\/v1$/, '') + path : path;
const tokenStore = {
  get: () => Platform.OS === 'web' ? Promise.resolve(sessionStorage.getItem('gs-auth')) : SecureStore.getItemAsync('gs-auth'),
  set: (value: string) => Platform.OS === 'web' ? Promise.resolve(sessionStorage.setItem('gs-auth', value)) : SecureStore.setItemAsync('gs-auth', value),
  clear: () => Platform.OS === 'web' ? Promise.resolve(sessionStorage.removeItem('gs-auth')) : SecureStore.deleteItemAsync('gs-auth'),
};
let tokens: Tokens | null = null, guest = '', refreshing: Promise<void> | null = null;
export const signedIn = () => !!tokens;
export async function initSession() {
  guest = await AsyncStorage.getItem('gs-guest') || Crypto.randomUUID();
  await AsyncStorage.setItem('gs-guest', guest);
  const raw = await tokenStore.get();
  try { tokens = raw ? JSON.parse(raw) : null; } catch { await clearSession(); }
}
export async function setSession(value: Tokens) {
  tokens = { access_token: value.access_token, refresh_token: value.refresh_token };
  await tokenStore.set(JSON.stringify(tokens));
  guest = Crypto.randomUUID(); // The previous guest cart was merged by the server.
  await AsyncStorage.setItem('gs-guest', guest);
}
export async function clearSession() {
  tokens = null;
  await tokenStore.clear();
  guest = Crypto.randomUUID();
  await AsyncStorage.setItem('gs-guest', guest);
}
export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export async function api<T = any>(path: string, method = 'GET', data?: unknown, retry = true, timeoutMs = 15000): Promise<T> {
  const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(API_URL + path, { method, signal: controller.signal, headers: {
      'Content-Type': 'application/json', 'X-Session-Id': guest,
      ...(tokens && !path.startsWith('/auth/') ? { Authorization: 'Bearer ' + tokens.access_token } : {}),
      ...(tokens && path === '/auth/logout' ? { Authorization: 'Bearer ' + tokens.access_token } : {}),
    }, ...(data !== undefined ? { body: JSON.stringify(data) } : {}) });
    if (response.status === 401 && tokens && retry && (!path.startsWith('/auth/') || path === '/auth/logout')) {
      if (!refreshing) refreshing = (async () => {
        const next = await api<{ access_token: string }>('/auth/refresh', 'POST', { refresh_token: tokens!.refresh_token }, false);
        tokens = { ...tokens!, access_token: next.access_token };
        await tokenStore.set(JSON.stringify(tokens));
      })().finally(() => { refreshing = null; });
      await refreshing;
      return api<T>(path, method, data, false);
    }
    if (response.status === 204) return undefined as T;
    const payload = await response.json();
    if (!response.ok) throw new ApiError(response.status, [payload.message, ...Object.entries(payload.fields || {}).map(([key, value]) => `${key}: ${value}`)].join(' '));
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error('Could not reach the shop. Check your connection and try again.');
  } finally { clearTimeout(timeout); }
}
export async function all<T>(path: string, timeoutMs = 15000): Promise<T[]> {
  let items: T[] = [], page = 1, total = 0;
  do {
    const result = await api<{ items: T[]; total: number }>(`${path}${path.includes('?') ? '&' : '?'}page_size=50&page=${page++}`, 'GET', undefined, true, timeoutMs);
    items = items.concat(result.items); total = result.total;
    if (!result.items.length) break;
  } while (items.length < total);
  return items;
}
