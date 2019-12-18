from multiprocessing import Pool

import requests
import ujson as json
from tqdm import tqdm


FUNCTION_URL = ''
MIN_MOVIE_ID = 10001
MAX_MOVIE_ID = 191500
PROCESS_NUM = 24
FUNCTION_URL = 'https://asia-east2-graceful-rope-261606.cloudfunctions.net/crawl-function'
headers = {'Content-Type': 'application/json; charset=utf-8'}

def request_one(code):
    res = requests.post(FUNCTION_URL, json={'code': code}, headers=headers)
    try:
        res = json.loads(res.text)
    except:
        print(code)
        print(res.status_code)
        print(res.text)
    return res


results = []
movie_codes = list(range(MIN_MOVIE_ID, MAX_MOVIE_ID + 1))
with Pool(PROCESS_NUM) as p:
    for result in tqdm(p.imap_unordered(request_one, movie_codes), total=len(movie_codes)):
        results.append(result)

results = [r for r in results if r['status']]
print(f"finished - {len(results)} movies collected")
