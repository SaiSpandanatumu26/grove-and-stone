"""Production entry point behind one trusted App Service or Render reverse proxy."""
from werkzeug.middleware.proxy_fix import ProxyFix

from backend import create_app

app = create_app()
if not app.secret_key or len(app.secret_key) < 32:
    raise RuntimeError('Set a retained SECRET_KEY of at least 32 random characters.')
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
