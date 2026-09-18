from backend import create_app


def test_public_images_cache_and_revalidate_without_caching_private_api():
    client = create_app({'TESTING': True}).test_client()
    image = client.get('/api/v1/media/mango.png')
    assert image.status_code == 200
    assert image.cache_control.public and image.cache_control.max_age == 86400
    assert image.headers.get('ETag')
    assert client.get('/api/v1/media/mango.png', headers={'If-None-Match': image.headers['ETag']}).status_code == 304
    missing = client.get('/api/v1/media/missing.png')
    assert missing.status_code == 404 and missing.cache_control.no_store
    assert client.get('/api/v1/me').cache_control.no_store
    assert client.get('/api/v1/media/%2e%2e/package.json').status_code == 404
