import type { Banner, Product, Season } from './api';

export type CatalogSnapshot = { products: Product[]; banners: Banner[]; seasons: Season[]; savedAt: number };
export const CATALOG_CACHE_KEY = 'gs-public-catalog-v1';
export function readCatalogCache(raw: string | null, now = Date.now()): CatalogSnapshot | null {
  try {
    const value = JSON.parse(raw || 'null');
    if (!value || typeof value.savedAt !== 'number' || value.savedAt > now || now - value.savedAt > 86400000) return null;
    if (![value.products, value.banners, value.seasons].every(Array.isArray)) return null;
    if (!value.products.every((p: Product) => p && typeof p.id === 'string' && typeof p.name === 'string' && Array.isArray(p.images))) return null;
    return value;
  } catch { return null; }
}
