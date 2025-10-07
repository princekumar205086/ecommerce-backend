import requests
r = requests.get('http://127.0.0.1:8000/api/public/products/categories/')
print('status', r.status_code)
data = r.json()
print('count', data.get('count'))
print('results length', len(data.get('results')))
print('next', data.get('next'))
print('first id', data['results'][0]['id'] if data.get('results') else None)
