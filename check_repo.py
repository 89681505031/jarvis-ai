#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

token = "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"
headers = {"Authorization": f"token {token}"}

# Проверяем доступ к репозиторию
r = requests.get("https://api.github.com/repos/89681505031/jarvis-ai", headers=headers)
print(f"jarvis-ai repo: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"  Name: {data['full_name']}")
    print(f"  Private: {data['private']}")
else:
    print(f"  Error: {r.text[:200]}")

# Проверяем все репозитории пользователя
r = requests.get("https://api.github.com/user/repos?per_page=100&sort=updated", headers=headers)
print(f"\nAll repos ({r.headers.get('X-Total-Count', '?')}):")
if r.status_code == 200:
    repos = r.json()
    for repo in repos:
        print(f"  - {repo['full_name']} (updated: {repo['updated_at']})")
else:
    print(f"  Error: {r.text[:200]}")
