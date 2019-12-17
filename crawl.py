import requests
import ujson as json
from multiprocessing import Pool


FUNCTION_URL = ''
MIN_MOVIE_ID = 10001
MAX_MOVIE_ID = 191500
PROCESS_NUM = 8
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
    print(f"movie-{code}")
    return res


with Pool(PROCESS_NUM) as p:
    results = p.map(request_one, [i for i in range(MIN_MOVIE_ID, MAX_MOVIE_ID + 1)])

results = [r for r in results if r['status']]
print(f"finished - {len(results)} movies collected")
