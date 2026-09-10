"""Opt-in, repeatable sample catalog for a loopback PostgreSQL *_local database only."""
import argparse
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.engine import make_url

from . import create_app
from .extensions import db
from .models import CMSBanner, Customer, MangoSeason, Order, OrderLine, PincodeService, Product, Variant


def seed():
    today = date.today()
    catalog = [
        ('alphonso-mangoes', 'Alphonso Mangoes', 'mango', 'Ratnagiri, India', 'mango', 'Golden, fragrant and wonderfully sweet.', 649, 0),
        ('dragon-fruit', 'Dragon Fruit', 'exotic', 'Maharashtra, India', 'dragonfruit', 'A vibrant pink shell with delicately sweet white flesh.', 249, 0),
        ('california-almonds', 'California Almonds', 'dry_fruit', 'California, USA', 'almonds', 'A satisfying crunch for your everyday handful.', 399, 5),
        ('green-kiwi', 'Green Kiwi', 'exotic', 'New Zealand', 'kiwi', 'Bright, tangy and full of refreshing flavour.', 299, 0),
        ('strawberries', 'Strawberries', 'exotic', 'Mahabaleshwar, India', 'strawberries', 'Sweet berries with a refreshing tang.', 199, 0),
        ('blueberries', 'Blueberries', 'exotic', 'Peru', 'blueberries', 'Little blue bites for breakfast bowls and snacking.', 349, 0),
        ('avocado', 'Avocado', 'exotic', 'Karnataka, India', 'avocado', 'Creamy green flesh for toast, salads and dips.', 279, 0),
        ('passion-fruit', 'Passion Fruit', 'exotic', 'Meghalaya, India', 'passionfruit', 'A fragrant golden centre with a bright tropical tang.', 299, 0),
        ('lychee', 'Lychee', 'exotic', 'Bihar, India', 'lychee', 'Delicate, juicy fruit with a floral sweetness.', 249, 0),
        ('pears', 'Pears', 'exotic', 'South Africa', 'pears', 'Mellow sweetness and a juicy, satisfying bite.', 229, 0),
        ('whole-cashews', 'Whole Cashews', 'dry_fruit', 'Goa, India', 'cashews', 'Creamy, crunchy kernels for your everyday handful.', 349, 5),
        ('pistachios', 'Pistachios', 'dry_fruit', 'California, USA', 'pistachios', 'Naturally rich green kernels in their shells.', 499, 5),
        ('kesar-mangoes', 'Kesar Mangoes', 'mango', 'Gir, India', 'mango', 'Saffron-coloured flesh with a fragrant sweetness.', 599, 0),
        ('langra-mangoes', 'Langra Mangoes', 'mango', 'Varanasi, India', 'mango', 'A much-loved variety with aromatic, juicy flesh.', 549, 0),
        ('dasheri-mangoes', 'Dasheri Mangoes', 'mango', 'Malihabad, India', 'mango', 'Sweet, fragrant mangoes from a celebrated growing region.', 549, 0),
    ]
    for slug, name, category, origin, image, description, price, gst in catalog:
        existing = db.session.scalar(select(Product).where(Product.slug == slug))
        if existing:
            # Correct only the original demo's weight-based mango packs; retain stock, IDs and prices.
            if category == 'mango':
                for i, pack in enumerate(sorted(existing.variants, key=lambda item: item.sku), 1):
                    if pack.sku == f'DEMO-{slug.upper()}-{i}' and pack.pack_type == 'weight' and pack.weight_grams == i * 1000:
                        pack.pack_type, pack.pack_label, pack.weight_grams, pack.unit_count = 'box', f'Box of {i * 6}', None, i * 6
            continue
        upcoming = category == 'mango' and slug != 'alphonso-mangoes'
        base_weight = 125 if slug == 'blueberries' else 250 if category == 'dry_fruit' or slug == 'strawberries' else 500 if slug in {'avocado', 'passion-fruit', 'lychee', 'pears'} else 1000
        product = Product(name=name, slug=slug, category=category, origin=origin, short_description=description,
                          long_description=description + ' Choose a pack to suit your basket. This catalog entry is sample content for the local review.',
                          images=[f'/api/v1/media/{image}.png'], season_status='coming_soon' if upcoming else 'in_season', is_active=True, is_gift_eligible=category == 'dry_fruit',
                          handling_notes='Keep in a cool, dry place.' if category == 'dry_fruit' else 'Refrigerate ripe fruit and enjoy soon after delivery.',
                          variants=[Variant(sku=f'DEMO-{slug.upper()}-{i}', pack_label=f'Box of {i * 6}' if category == 'mango' else f'{base_weight * i} g',
                                            pack_type='box' if category == 'mango' else 'weight', weight_grams=None if category == 'mango' else base_weight * i,
                                            unit_count=i * 6 if category == 'mango' else None, price=Decimal(price * i), gst_percent=gst,
                                            stock_qty=0 if upcoming else 40, cod_allowed=True, is_default=i == 1) for i in (1, 2)])
        db.session.add(product)
    db.session.flush()
    if not db.session.scalar(select(CMSBanner.id).limit(1)):
        for i, (title, subtitle, image, cta, url) in enumerate([
            ('Fresh finds.\nBig flavour.', 'Exotic fruits, crunchy dry fruits and seasonal mangoes. Find your next favourite, one fresh pick at a time.', 'hero', 'Explore the collection', '/category'),
            ('Meet your\nnew favourites.', 'A little adventurous. A lot delicious. Explore our collection of exotic fruits.', 'dragonfruit', 'Discover exotic fruits', '/category?category=exotic'),
            ('A little crunch.\nA lot to love.', 'Make room for everyday goodness with our dry fruit collection.', 'almonds', 'Shop dry fruits', '/category?category=dry_fruit'),
        ]):
            db.session.add(CMSBanner(title=title, subtitle=subtitle, image=f'/api/v1/media/{image}.png', cta_label=cta, cta_url=url,
                                     season_state='live', start_date=today - timedelta(days=i), end_date=today + timedelta(days=365), is_published=True))
    for mango in db.session.scalars(select(Product).where(Product.category == 'mango', Product.slug.in_([item[0] for item in catalog]))):
        if db.session.scalar(select(MangoSeason.id).where(MangoSeason.product_id == mango.id)): continue
        upcoming = mango.season_status == 'coming_soon'
        db.session.add(MangoSeason(variety_name=mango.name.replace(' Mangoes', '') + ' · sample harvest', product=mango,
                                  harvest_start=today + timedelta(days=30 if upcoming else -7), harvest_end=today + timedelta(days=90 if upcoming else 30),
                                  status='upcoming' if upcoming else 'live', waitlist_enabled=upcoming))
    for pincode, city, state in [('500001', 'Hyderabad', 'Telangana'), ('400001', 'Mumbai', 'Maharashtra'), ('560001', 'Bengaluru', 'Karnataka')]:
        if not db.session.get(PincodeService, pincode):
            db.session.add(PincodeService(pincode=pincode, city=city, state=state, serviceable=True, mango_eligible=True, cod_allowed=True, delivery_days_min=2, delivery_days_max=4))
    customer = db.session.scalar(select(Customer).where(Customer.email == 'review@example.com'))
    if not customer:
        customer = Customer(full_name='Demo Shopper', email='review@example.com', phone='9876500000', password='GroveReview2026!')
        db.session.add(customer); db.session.flush()
    if not db.session.scalar(select(Order.id).where(Order.order_number == 'GS-900001')):
        product = db.session.scalar(select(Product).where(Product.slug == 'california-almonds'))
        variant = next(pack for pack in product.variants if pack.is_default)
        address = dict(full_name='Demo Shopper', phone='9876500000', line1='Sample address for local review', city='Hyderabad', state='Telangana', pincode='500001', address_type='home')
        db.session.add(Order(order_number='GS-900001', customer=customer, status='delivered', address=address, pincode='500001', delivery_date=today - timedelta(days=2),
                             payment_method='cod', payment_status='paid', subtotal=variant.price, shipping=0, gst=(variant.price * variant.gst_percent / (100 + variant.gst_percent)).quantize(Decimal('0.01')), grand_total=variant.price,
                             created_at=datetime.now(timezone.utc) - timedelta(days=6), customer_notes='Synthetic order for local reorder review; no payment or delivery occurred.',
                             lines=[OrderLine(product_name=product.name, variant_label=variant.pack_label, sku=variant.sku, qty=1, unit_price=variant.price)]))
    db.session.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirm-local-demo', action='store_true', required=True)
    parser.parse_args()
    app = create_app()
    url = make_url(app.config['SQLALCHEMY_DATABASE_URI'])
    if url.host not in {'localhost', '127.0.0.1', '::1'} or not (url.database or '').endswith('_local'):
        raise SystemExit('Demo seeding requires a loopback host and a database name ending in _local.')
    with app.app_context(): db.create_all(); seed()
    print('Local demo ready: 15 products, 3 banners, 4 sample harvests, delivery coverage and a synthetic past order. No notifications or payments sent.')
