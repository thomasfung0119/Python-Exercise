import requests
import time
import hashlib
import hmac
import json
import pandas as pd

#get gateio spot balance
def gateio_sign(key, secret, method, url, query_string=None, payload_string=None):

    t = time.time()
    m = hashlib.sha512()
    m.update((payload_string or "").encode('utf-8'))
    hashed_payload = m.hexdigest()
    s = '%s\n%s\n%s\n%s\n%s' % (method, url, query_string or "", hashed_payload, t)
    sign = hmac.new(secret.encode('utf-8'), s.encode('utf-8'), hashlib.sha512).hexdigest()
    return {'KEY': key, 'Timestamp': str(t), 'SIGN': sign}

def gateio_get_spot_balance(apiKey, secret):
    host = "https://api.gateio.ws"
    prefix = "/api/v4"
    url = '/spot/accounts'
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
    query_param = ''
    sign_headers = gateio_sign(apiKey, secret, 'GET', prefix + url, query_param)
    headers.update(sign_headers)
    resp = requests.request('GET', host + prefix + url, headers=headers).json()
    standard_resp = { 'info': resp }
    for currency_info in resp:
        currency = currency_info['currency']
        free = float(currency_info['available'])
        used = float(currency_info['locked'])
        total = free + used
        standard_resp[currency] = {
            'free': standard_resp.get(currency, {}).get('free', 0) + free,
            'used': standard_resp.get(currency, {}).get('used', 0) + used,
            'total': standard_resp.get(currency, {}).get('total', 0) + total
        }

    currencies = [k for k in standard_resp if k != 'info']

    standard_resp['free'] = {}
    standard_resp['used'] = {}
    standard_resp['total'] = {}
    for currency in currencies:
        standard_resp['free'][currency] = standard_resp[currency]['free']
        standard_resp['used'][currency] = standard_resp[currency]['used']
        standard_resp['total'][currency] = standard_resp[currency]['total']
    
    return standard_resp
