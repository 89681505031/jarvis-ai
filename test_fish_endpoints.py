#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест endpoints Fish Audio"""

import sys
sys.path.insert(0, '.')

API_KEY = "AQ.Ab8RN6JZNmnFKgsHRnWI9-riAbXaq9-XCPQn0L1VwIeWcg1WQw"
BASE_URL = "https://api.fish.audio"

endpoints = [
    f"{BASE_URL}/v1/tts",
    f"{BASE_URL}/tts",
    f"{BASE_URL}/api/tts",
    f"{BASE_URL}/voice/synthesize",
]

headers = {"Authorization": f"Bearer {API_KEY}"}

print("=== ТЕСТ ENDPOINTS ===\n")

for ep in endpoints:
    try:
        import requests
        r = requests.post(
            ep,
            headers=headers,
            json={"text": "test", "reference_id": "4c3eaacc1a0545cdb0295bfddf3e3785", "model_id": "s2.1-pro-free"},
            timeout=10,
            verify=False
        )
        print(f"{ep} [HTTP {r.status_code}] {r.text[:100] if r.status_code != 200 else 'OK'}")
    except Exception as e:
        print(f"{ep} [ERROR: {e}]")

print("\n=== ТЕСТ ПОЛНОГО ЗАПРОСА ===")
try:
    r = requests.post(
        f"{BASE_URL}/v1/tts",
        headers=headers,
        json={
            "text": "Привет, я Джарвис.",
            "reference_id": "4c3eaacc1a0545cdb0295bfddf3e3785",
            "model_id": "s2.1-pro-free",
            "format": "mp3",
        },
        timeout=60,
        verify=False
    )
    print(f"\nStatus: {r.status_code}")
    if r.status_code == 200:
        with open('sounds/test_fish_full.mp3', 'wb') as f:
            f.write(r.content)
        print("✅ Успех! Файл сохранён")
    else:
        print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"ERROR: {e}")
