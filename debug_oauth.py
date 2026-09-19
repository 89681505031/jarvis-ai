#!/usr/bin/env python3
import requests

KEY = 'MDFhMDU5YjItYjhjNy03NGJjLWI4YWUtNDg5YTVjZTQ2Mzg5OjFmMjBkMmQ2LTIzMjItNGYzYS05OGE2LTdiNzA2YWExYmYxNg=='

print("Debug OAuth request...")

# Test with verbose logging
import urllib3
urllib3.disable_warnings()

session = requests.Session()
headers = {
    "Authorization": f"Basic {KEY}",
    "Content-Type": "application/x-www-form-urlencoded",
}
print(f"Headers: {headers}")
print(f"Auth header length: {len(headers['Authorization'])}")

# Try without RqUID first
r = session.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    data={"scope": "GIGACHAT_API_PERS"},
    headers=headers,
    timeout=10,
    verify=False,
)
print(f"\nWithout RqUID:")
print(f"  Status: {r.status_code}")
print(f"  Headers: {dict(r.headers)}")
print(f"  Body: {r.text[:500]}")

# Now with RqUID
import uuid
r2 = session.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    data={"scope": "GIGACHAT_API_PERS", "RqUID": str(uuid.uuid4())},
    headers=headers,
    timeout=10,
    verify=False,
)
print(f"\nWith RqUID:")
print(f"  Status: {r2.status_code}")
print(f"  Body: {r2.text[:500]}")

# Try with form data properly
r3 = session.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    data={"scope": "GIGACHAT_API_PERS"},
    headers={**headers, "RqUID": str(uuid.uuid4())},
    timeout=10,
    verify=False,
)
print(f"\nWith RqUID in headers:")
print(f"  Status: {r3.status_code}")
print(f"  Body: {r3.text[:500]}")
