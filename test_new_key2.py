#!/usr/bin/env python3
import requests

KEY = 'MDFhMDU5YjItYjhjNy03NGJjLWI4YWUtNDg5YTVjZTQ2Mzg5OmE1Y2Y5YWZlLWRiMTUtNDY5Ni05N2M1LTNkZThjYmNiY2I1ZQ=='

print("Testing new GigaChat key...")

session = requests.Session()
session.headers.update({
    "Authorization": f"Basic {KEY}",
    "Content-Type": "application/x-www-form-urlencoded",
})

r = session.post(
    "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
    data={"scope": "GIGACHAT_API_PERS", "RqUID": "test-uuid"},
    timeout=10,
    verify=False,
)

print(f"OAuth: {r.status_code} - {r.text[:200]}")

if r.status_code == 200:
    token = r.json().get("access_token")
    print(f"Token: {token[:30]}...")
    
    # Test chat
    r2 = session.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json={
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": "Be brief."},
                {"role": "user", "content": "Hi"}
            ],
            "max_tokens": 20
        },
        timeout=15,
        verify=False,
    )
    print(f"Chat: {r2.status_code} - {r2.text[:200]}")
    
    if r2.status_code == 200:
        ans = r2.json()["choices"][0]["message"]["content"]
        print(f"ANSWER: {ans}")
        print("SUCCESS!")
else:
    print("FAILED - key still invalid")
