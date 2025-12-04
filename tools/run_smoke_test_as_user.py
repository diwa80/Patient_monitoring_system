#!/usr/bin/env python3
# Smoke test as a specific user (nurse/admin)
import os, sys
import urllib.request, urllib.parse, http.cookiejar, json

# Ensure project root is on sys.path so imports work when executed from tools/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BASE = 'http://127.0.0.1:5000'
USERNAME='testnurse'
PASSWORD='nurse123'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
login_url = BASE + '/login'
login_data = urllib.parse.urlencode({'username': USERNAME, 'password': PASSWORD}).encode('utf-8')
req = urllib.request.Request(login_url, data=login_data)
try:
    res = opener.open(req)
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

paths = ['/api/stats/overview', '/api/charts/temperature', '/api/latest_readings', '/api/alerts?status=new']
for p in paths:
    fetch(p)

print('\nUser smoke test completed.')
