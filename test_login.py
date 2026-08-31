from index import app

client = app.test_client()
# we don't have real credentials, but we can send a mock POST to /api/login and see if it crashes with 500
response = client.post('/api/login', json={'username': 'test', 'password': '123'})
print(response.status_code)
try:
    print(response.json)
except Exception as e:
    print("Not JSON:", e)
