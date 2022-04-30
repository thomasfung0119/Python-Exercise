import requests
import time
import hmac
import hashlib


class Auth(requests.auth.AuthBase):
    def __init__(self, apiKey, secret):
        self.apiKey = apiKey
        self.secret = secret

    def __call__(self, request):
        nonce = str(int(1000 * time.time()))
        strBody = request.body.decode() if request.body else ''
        message = nonce + ':' + request.method + request.path_url + (strBody or '')
        signature = hmac.new(self.secret.encode(), message.encode(), hashlib.sha256).hexdigest()
        request.headers.update({
            'X-ACCESS-NONCE': nonce,
            'X-ACCESS-KEY': self.apiKey,
            'X-ACCESS-SIGN': signature,
        })
        return request


class AAX:
    def __init__(self):
        self.url = 'https://api.aax.com/'
    
    def get_orderbook_snapshot(self, symbol, level=50):
        return requests.get(self.url + f'marketdata/v1.1/{symbol}@book_{level}').json()
    
    def get_mid_price(self, symbol):
        orderbook = self.get_orderbook_snapshot(symbol, level=20)
        best_bid = float(orderbook['bids'][0][0])
        best_ask = float(orderbook['asks'][0][0])
        return 0.5 * (best_bid + best_ask)


def get_balance(apiKey, secret, params):
    auth = Auth(apiKey, secret)
    resp = requests.get('https://api.aax.com/v2/account/balances', params=params, auth=auth).json()

    standard_resp = { 'info': resp }
    for currency_info in resp['data']:
        currency = currency_info['currency']
        free = float(currency_info['available'])
        used = float(currency_info['unavailable'])
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
