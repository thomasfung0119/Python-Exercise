import requests
import asyncio
import aiohttp
import time 

session = requests.Session()

async def fetch(client):
    url = 'https://api.aax.com/v2/futures/funding/predictedFunding/1INCHUSDTFP'
    async with client.get(url) as resp:
        html = await resp.text()
        return html

async def async_example(coinlist):
    async with aiohttp.ClientSession() as client:
        result = await asyncio.gather(*[asyncio.ensure_future(fetch(client)) for _ in range(100)])
    return result

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    s = time.perf_counter()
    for _ in range(100):
        print(requests.get('https://api.aax.com/v2/futures/funding/predictedFunding/1INCHUSDTFP').json())
    Request_Time = time.perf_counter() - s
    
    s = time.perf_counter()
    for _ in range(100):
        print(session.get('https://api.aax.com/v2/futures/funding/predictedFunding/1INCHUSDTFP').json())
    Session_Time = time.perf_counter() - s

    s = time.perf_counter()
    x = asyncio.run(async_example())
    print(x)
    Async_Time = time.perf_counter() - s

    print(f'{Request_Time =}')
    print(f'{Session_Time =}')
    print(f'{Async_Time =}')