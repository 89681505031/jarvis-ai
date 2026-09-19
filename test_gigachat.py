#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест GigaChat API"""

import requests
import json
import uuid
import time

API_KEY = 'MDFhMDU5YjItYjhjNy03ODRhLTk0MmItZjI2YzNmNjA4NzI0'

print("=" * 60)
print("ТЕСТ GIGACHAT API")
print("=" * 60)

# Шаг 1: OAuth
print("\n[1] Получаю OAuth токен...")
try:
    session = requests.Session()
    session.headers.update({
        "Authorization": f"Basic {API_KEY}",
        "Content-Type": "application/x-www-form-urlencoded",
        "RqUID": str(uuid.uuid4()),
    })
    
    response = session.post(
        "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        data={"scope": "GIGACHAT_API_PERS"},
        timeout=10,
        verify=False,
    )
    
    print(f"    Status: {response.status_code}")
    print(f"    Response: {response.text[:500]}")
    
    if response.status_code != 200:
        print("\n❌ ОШИБКА OAuth!")
        print(f"   Код: {response.status_code}")
        print(f"   Текст: {response.text}")
        exit(1)
    
    token_data = response.json()
    token = token_data.get("access_token")
    if not token:
        print("\n❌ Не получен access_token!")
        exit(1)
    
    print(f"    ✅ Токен получен: {token[:30]}...")
    print(f"    Expires at: {token_data.get('expires_at')}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА OAuth: {e}")
    exit(1)

# Шаг 2: Chat completion
print("\n[2] Отправляю запрос к GigaChat-Pro...")
try:
    session2 = requests.Session()
    session2.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    
    payload = {
        "model": "GigaChat-Pro",
        "messages": [
            {"role": "system", "content": "Ты Джарвис. Отвечай кратко."},
            {"role": "user", "content": "Привет. Как дела?"}
        ],
        "temperature": 0.6,
        "max_tokens": 50,
        "safe_mode": False,
    }
    
    response2 = session2.post(
        "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
        json=payload,
        timeout=15,
        verify=False,
    )
    
    print(f"    Status: {response2.status_code}")
    print(f"    Response: {response2.text[:500]}")
    
    if response2.status_code != 200:
        print("\n❌ ОШИБКА Chat API!")
        print(f"   Код: {response2.status_code}")
        print(f"   Текст: {response2.text}")
        
        # Проверяем common ошибки
        if response2.status_code == 401:
            print("\n💡 Проблема: Недействительный API ключ или токен")
        elif response2.status_code == 403:
            print("\n💡 Проблема: Нет доступа к API")
        elif response2.status_code == 429:
            print("\n💡 Проблема: Rate limiting (слишком много запросов)")
        elif response2.status_code == 500:
            print("\n💡 Проблема: Ошибка сервера GigaChat")
        
        exit(1)
    
    chat_data = response2.json()
    choices = chat_data.get("choices") or []
    
    if not choices:
        print("\n❌ GigaChat не вернул ответ!")
        exit(1)
    
    content = choices[0].get("message", {}).get("content", "").strip()
    if not content:
        print("\n❌ GigaChat вернул пустой ответ!")
        exit(1)
    
    print(f"\n✅ УСПЕХ!")
    print(f"   Ответ: {content}")
    
except Exception as e:
    print(f"\n❌ ОШИБКА Chat API: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 60)
print("✅ GIGACHAT РАБОТАЕТ!")
print("=" * 60)
