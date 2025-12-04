#!/usr/bin/env python3
# Local smoke test using stdlib (urllib)
import urllib.request, urllib.parse, http.cookiejar, json

BASE = 'http://127.0.0.1:5000'
USERNAME='admin'
PASSWORD='admin123'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_url = BASE + '/login'
login_data = urllib.parse.urlencode({'username': USERNAME, 'password': PASSWORD}).encode('utf-8')
req = urllib.request.Request(login_url, data=login_data)
try:
    res = opener.open(req)
    body = res.read().decode('utf-8')
    print('Login request status:', res.getcode())
except Exception as e:
    print('Login failed:', e)
    raise SystemExit(1)

# Helper
def fetch(path):
    url = BASE + path
    try:
        r = opener.open(url)
        data = r.read().decode('utf-8')
        try:
            j = json.loads(data)
            print(path, '->', json.dumps(j, indent=2))
        except Exception:
            print(path, '-> (non-json)')
            print(data[:400])
    except Exception as e:
        print(path, 'error:', e)

# Endpoints to check
paths = [
    '/api/stats/overview',
    '/api/charts/temperature',
    '/api/latest_readings',
    '/api/alerts?status=new',
    '/api/beds'
]

for p in paths:
    fetch(p)

print('\nSmoke test completed.')
