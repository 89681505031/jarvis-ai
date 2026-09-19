#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест GigaChat API с Bearer token"""

import requests
import json
import uuid

API_KEY = 'MDFhMDU5YjItYjhjNy03ODRhLTk0MmItZjI2YzNmNjA4NzI0'

print("=" * 60)
print("ТЕСТ GIGACHAT API - BEARER FORMAT")
print("=" * 60)

# Пробуем как Bearer token напрямую
print("\n[1] Пробуем Bearer token...")
try:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    })
    
    response = session.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json={
            "model": "GigaChat",
            "messages": [
                {"role": "system", "content": "Ты Джарвис. Отвечай кратко."},
                {"role": "user", "content": "Привет. Как дела?"}
            ],
            "temperature": 0.6,
            "max_tokens": 50,
        },
        timeout=15,
        verify=False,
    )
    
    print(f"    Status: {response.status_code}")
    print(f"    Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print("\n✅ УСПЕХ с Bearer!")
        chat_data = response.json()
        choices = chat_data.get("choices") or []
        if choices:
            content = choices[0].get("message", {}).get("content", "").strip()
            print(f"    Ответ: {content}")
    else:
        print(f"\n❌ Bearer не сработал")
        
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")

# Пробуем OAuth с UUID как username
print("\n[2] Пробуем OAuth с UUID как username...")
try:
    import base64
    uuid_val = base64.b64decode(API_KEY).decode('utf-8')
    print(f"    UUID: {uuid_val}")
    
    # Пробуем как username без password
    creds = f"{uuid_val}:"
    auth_b64 = base64.b64encode(creds.encode()).decode()
    print(f"    Auth header: Basic {auth_b64[:30]}...")
    
    session2 = requests.Session()
    session2.headers.update({
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
        "RqUID": str(uuid.uuid4()),
    })
    
    response2 = session2.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data={"scope": "GIGACHAT_API_PERS"},
        timeout=10,
        verify=False,
    )
    
    print(f"    Status: {response2.status_code}")
    print(f"    Response: {response2.text[:500]}")
    
    if response2.status_code == 200:
        print("\n✅ OAuth УСПЕШЕН!")
        token_data = response2.json()
        token = token_data.get("access_token")
        print(f"    Token: {token[:30]}...")
    else:
        print(f"\n❌ OAuth не сработал")
        
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
