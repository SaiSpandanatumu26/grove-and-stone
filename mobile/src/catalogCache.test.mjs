import assert from 'node:assert/strict';
import { test } from 'node:test';
import { readCatalogCache } from './catalogCache.ts';

test('catalog cache rejects corrupt, future and expired snapshots', () => {
  const now = 100000000, snapshot = { products: [{ id: 'fruit', name: 'Mango', images: ['/mango.webp'] }], banners: [], seasons: [], savedAt: now };
  assert.equal(readCatalogCache('invalid', now), null);
  assert.equal(readCatalogCache(JSON.stringify({ ...snapshot, savedAt: now + 1 }), now), null);
  assert.equal(readCatalogCache(JSON.stringify({ ...snapshot, savedAt: now - 86400001 }), now), null);
  assert.equal(readCatalogCache(JSON.stringify({ ...snapshot, products: [{}] }), now), null);
  assert.deepEqual(readCatalogCache(JSON.stringify(snapshot), now), snapshot);
});
