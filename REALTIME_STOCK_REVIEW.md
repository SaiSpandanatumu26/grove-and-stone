# Grove & Stone — live stock check

Open **http://localhost:8081/**. Stock now refreshes automatically without a page reload.

- Catalog, search and wishlist cards show In stock, Only N packs left (five or fewer), or Unavailable now.
- Product pages update the selected pack's available count. An unavailable pack cannot be added; another available pack can still be selected.
- Cart lines show current stock. Sold-out and unavailable products, or quantities above current stock, block checkout. Decreasing an excessive quantity clamps it to the available amount. Items are not silently removed or repriced.
- Checkout detects shortages while the customer fills the form and directs them back to review the cart.
- A **Check stock now** button requests an immediate check. Connection failures show that availability may be outdated, and retry automatically.

## Update behavior

This is near-real-time polling: the next check starts five seconds after a successful response, rather than using a permanent socket connection. It uses the existing Flask/PostgreSQL stack without a new service or package. Reads cover watched products and cart items, in batches of at most 100 IDs. Inactive and deleted products/packs become unavailable.

Checks pause while the browser tab is hidden or the native app is backgrounded. Returning to the app triggers an immediate check. Failed requests retry with a 10–30 second backoff; each polling cycle has an eight-second timeout. Cancelled/obsolete responses cannot overwrite a newer subscription.

Adding to a cart does not reserve stock. Placing an order reserves it; cancellation and unpaid-order expiry restore it. All these committed changes are visible in the stock endpoint. The server's transactional add/checkout checks remain authoritative if two customers compete for the same pack between refreshes. A network outage does not falsely mark the last known quantities as verified.

## Verified

- **37 backend tests passed**, including stock request validation, inactive/missing products, admin inventory changes, reservations/cancellations and existing concurrent checkout protection.
- TypeScript checks and Android bundle export passed.
- Browser test: reduced the sample almond pack from 40 to 2 and saw the catalog and selected pack update automatically; changed it to zero and verified Add and Checkout were disabled; restored 40 and verified checkout re-enabled without reloading.
- Sample inventory was restored after testing. No new database table or deployment is required. Real-device execution remains untested.
