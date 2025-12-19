import requests

try:
    response = requests.get('http://127.0.0.1:5000/idcard/api/students/1', timeout=5)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Students found: {len(data.get("students", []))}')
        if data.get("students"):
            print(f'First student: {data["students"][0]["name"]}')
    else:
        print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {e}')