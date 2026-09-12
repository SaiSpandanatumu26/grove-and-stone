"""Public support configuration and a rate-limited, non-persistent contact form."""
import json
from urllib.error import URLError
from urllib.request import Request, urlopen

from email_validator import EmailNotValidError, validate_email
from flask import current_app

from .api import api, body, fail, invalid, respond, text_value
from .extensions import limiter


@api.get('/health')
def health():
    from sqlalchemy import text
    from .extensions import db
    db.session.execute(text('SELECT 1'))
    return respond({'status': 'ok'})


@api.get('/shop-info')
def shop_info():
    from .operations import setting, accepting_orders
    config = current_app.config
    return respond(dict(support_email=setting('support_email'), support_phone=setting('support_phone'), business_name=setting('business_name', 'Grove & Stone'), business_address=setting('business_address'), ordering_enabled=accepting_orders(), quality_report_hours=config['QUALITY_REPORT_HOURS'],
                        contact_backend=config['CONTACT_BACKEND'], shipping_fee=config['SHIPPING_FEE'], free_shipping_threshold=config['FREE_SHIPPING_THRESHOLD']))


@api.post('/contact')
@limiter.limit('3/minute;10/hour')
def contact():
    data = body({'full_name', 'email', 'phone', 'order_number', 'message'}, {'full_name', 'email', 'message'})
    for key, minimum, maximum in [('full_name', 2, 80), ('message', 10, 1000), ('order_number', 0, 80), ('phone', 0, 10)]:
        data[key] = text_value(data.get(key, ''), key, minimum, maximum)
    if data['phone'] and (len(data['phone']) != 10 or not data['phone'].isascii() or not data['phone'].isdigit()): invalid('phone', 'Enter a 10-digit mobile number.')
    try: data['email'] = validate_email(data['email'], check_deliverability=False).normalized
    except (EmailNotValidError, AttributeError, TypeError): invalid('email', 'Enter a valid email address.')
    config = current_app.config
    from .operations import setting
    support_email = setting('support_email')
    if config['CONTACT_BACKEND'] == 'demo': return respond({'message': 'Demo form validated. No email was sent.', 'demo': True})
    if config['CONTACT_BACKEND'] != 'resend' or not support_email or not all(config.get(key) for key in ('RESEND_API_KEY', 'CONTACT_FROM')):
        fail(503, 'CONTACT_UNAVAILABLE', 'The contact form is not configured yet. Please use the support details if shown.')
    payload = {'from': config['CONTACT_FROM'], 'to': [support_email], 'reply_to': data['email'], 'subject': 'Grove & Stone customer enquiry',
               'text': '\n'.join(f'{key}: {value}' for key, value in data.items())}
    req = Request('https://api.resend.com/emails', data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + config['RESEND_API_KEY'], 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response: json.load(response)
    except (URLError, TimeoutError, ValueError): fail(503, 'CONTACT_UNAVAILABLE', 'Your message could not be confirmed as sent. Please try again later.')
    return respond({'message': 'Your message has been sent. We will reply by email.'})
