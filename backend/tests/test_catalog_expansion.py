"""Expanded sample catalog and waitlist regressions, using a disposable database."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import func, select

from backend.demo_seed import seed
from backend.extensions import db
from backend.models import CMSBanner, MangoSeason, Product, WaitlistEntry
from backend.tests.test_api import app, setup, call


def test_sample_catalog_is_repeatable_and_preserves_existing_stock(setup, app):
    with app.app_context():
        seed()
        products = db.session.scalars(select(Product).where(Product.slug != 'alphonso')).all()
        assert len(products) == 19
        assert {category: sum(p.category == category for p in products) for category in ('exotic', 'dry_fruit', 'mango')} == {'exotic': 8, 'dry_fruit': 3, 'mango': 8}
        for product in products:
            assert (Path(__file__).parents[2] / 'mobile/assets/catalog' / product.images[0].rsplit('/', 1)[-1]).is_file()
            assert len(product.variants) == 2 and sum(v.is_default for v in product.variants) == 1
            if product.category == 'mango':
                assert all(v.pack_type == 'box' and v.unit_count in (6, 12) and v.weight_grams is None for v in product.variants)
            if product.season_status == 'coming_soon': assert all(v.stock_qty == 0 for v in product.variants)
        mango = next(p for p in products if p.slug == 'alphonso-mangoes')
        pack = next(v for v in mango.variants if v.is_default)
        pack.stock_qty, pack.pack_type, pack.weight_grams, pack.unit_count = 17, 'weight', 1000, None
        db.session.commit()
        seed()
        assert pack.stock_qty == 17 and pack.pack_type == 'box' and pack.unit_count == 6
        assert db.session.scalar(select(func.count()).select_from(Product)) == 20
        assert db.session.scalar(select(func.count()).select_from(MangoSeason)) == 8
        assert db.session.scalar(select(func.count()).select_from(CMSBanner).where(CMSBanner.cta_url == '/mango-season')) == 1


def test_waitlist_duplicates_are_private_and_concurrent_safe(setup, app):
    client, ids = setup
    with app.app_context():
        from datetime import date
        db.session.add(MangoSeason(product_id=ids['product'], variety_name='Sample harvest', harvest_start=date.today(), harvest_end=date.today(), status='upcoming', waitlist_enabled=False))
        db.session.commit()
    path = '/mango-season/waitlist'
    data = {'product_id': ids['product'], 'email': 'WAITLIST@example.com', 'phone': '9876543210', 'full_name': 'Test Shopper'}
    first = call(client, 'POST', path, data, status=201)
    assert first == call(client, 'POST', path, {'slug': 'alphonso', 'email': 'waitlist@example.com'})
    assert first == call(client, 'POST', path, {'slug': 'alphonso', 'phone': '9876543210'})
    assert set(first) == {'registered', 'message'}
    for invalid in ({}, {'phone': '１２３４５６７８９０'}, {'phone': '123'}, {'email': 'invalid'}, {'email': 'valid@example.com', 'full_name': 'A'}):
        call(client, 'POST', path, {'product_id': ids['product'], **invalid}, status=400)
    def submit(_):
        with app.test_client() as other:
            return other.post('/api/v1' + path, json={'product_id': ids['product'], 'email': 'parallel@example.com'}).status_code
    with ThreadPoolExecutor(max_workers=4) as pool: assert sorted(pool.map(submit, range(4))) == [200, 200, 200, 201]
    with app.app_context():
        assert db.session.scalar(select(func.count()).select_from(WaitlistEntry)) == 2
        season = db.session.scalar(select(MangoSeason))
        season.status = 'closed'; db.session.commit()
    call(client, 'POST', path, data, status=400)
