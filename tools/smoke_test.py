import urllib.request
import urllib.parse
import http.cookiejar
import json

BASE = 'http://127.0.0.1:5000'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def post(path, data):
    data_bytes = urllib.parse.urlencode(data).encode('utf-8')
    req = urllib.request.Request(BASE + path, data=data_bytes)
    return opener.open(req)

def get(path):
    req = urllib.request.Request(BASE + path)
    return opener.open(req)

print('Logging in as admin...')
try:
    resp = post('/login', {'username': 'admin', 'password': 'admin123'})
    print('Login response code:', resp.getcode())
except Exception as e:
    print('Login failed:', e)

endpoints = [
    '/api/stats/overview',
    '/api/charts/temperature',
    '/api/alerts?status=new',
    '/api/latest_readings'
]

for ep in endpoints:
    try:
        r = get(ep)
        code = r.getcode()
        body = r.read().decode('utf-8')
        print('\nGET', ep, '->', code)
        try:
            print(json.loads(body))
        except Exception:
            print('Non-JSON response (length):', len(body))
    except Exception as e:
        # If it's an HTTP error, try to print response body
        try:
            import urllib.error
            if isinstance(e, urllib.error.HTTPError):
                body = e.read().decode('utf-8')
                print('\nGET', ep, '-> HTTPError', e.code)
                print('Response body:', body)
            else:
                print('Error calling', ep, e)
        except Exception:
            print('Error calling', ep, e)

print('\nSmoke test complete')

# Check nurse dashboard HTML
html_check = '/nurse/dashboard'
try:
    r = get(html_check)
    html = r.read().decode('utf-8')
    print('\nGET', html_check, '->', r.getcode())
    if 'tempTrendChart' in html and 'bedSnapshotPanel' in html:
        print('Dashboard template contains expected elements')
    else:
        print('Dashboard template missing expected elements')
except Exception as e:
    print('Error fetching dashboard HTML:', e)

# Check user management page
html_check_users = '/users'
try:
    r = get(html_check_users)
    html = r.read().decode('utf-8')
    print('\nGET', html_check_users, '->', r.getcode())
    if 'createUserModal' in html or 'userTable' in html:
        print('User management template contains expected elements')
    else:
        print('User management template missing expected elements')
except Exception as e:
    print('Error fetching user management HTML:', e)
