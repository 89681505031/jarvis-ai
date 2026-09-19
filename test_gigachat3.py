#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест GigaChat - финальный"""

import requests
import base64
import json

API_KEY = 'MDFhMDU5YjItYjhjNy03ODRhLTk0MmItZjI2YzNmNjA4NzI0'

print("=" * 60)
print("ТЕСТ GIGACHAT - ФИНАЛЬНЫЙ")
print("=" * 60)

# Декодируем UUID
uuid_val = base64.b64decode(API_KEY).decode('utf-8')
print(f"\nUUID из ключа: {uuid_val}")

# Вариант 1: OAuth с username:password где password пустой
print("\n[1] OAuth с username: (пустой пароль)...")
try:
    creds = f"{uuid_val}:"
    auth_b64 = base64.b64encode(creds.encode()).decode()
    
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    
    response = session.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data={"scope": "GIGACHAT_API_PERS"},
        timeout=10,
        verify=False,
    )
    
    print(f"    Status: {response.status_code}")
    print(f"    Response: {response.text[:300]}")
    
except Exception as e:
    print(f"    ERROR: {e}")

# Вариант 2: OAuth с просто API ключом как Basic
print("\n[2] OAuth с API ключом как Basic...")
try:
    session2 = requests.Session()
    session2.headers.update({
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    
    response2 = session2.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data={"scope": "GIGACHAT_API_PERS"},
        timeout=10,
        verify=False,
    )
    
    print(f"    Status: {response2.status_code}")
    print(f"    Response: {response2.text[:300]}")
    
except Exception as e:
    print(f"    ERROR: {e}")

# Вариант 3: OAuth с API ключом без Basic префикса
print("\n[3] OAuth с API ключом без префикса...")
try:
    session3 = requests.Session()
    session3.headers.update({
        "Authorization": API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
    })
    
    response3 = session3.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data={"scope": "GIGACHAT_API_PERS"},
        timeout=10,
        verify=False,
    )
    
    print(f"    Status: {response3.status_code}")
    print(f"    Response: {response3.text[:300]}")
    
except Exception as e:
    print(f"    ERROR: {e}")

print("\n" + "=" * 60)
print("РЕКОМЕНДАЦИЯ:")
print("Ключ требует обновления на https://developer.sber.ru/")
print("Нужно создать новый проект и получить свежие credentials")
print("=" * 60)
