#!/usr/bin/env python3
import requests

token = "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"
headers = {"Authorization": f"token {token}"}

# Test 1: User info
r = requests.get("https://api.github.com/user", headers=headers)
print(f"User: {r.status_code} - {r.text[:100]}")

# Test 2: List repos
r = requests.get("https://api.github.com/user/repos?per_page=5&sort=updated", headers=headers)
print(f"\nRepos: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Count: {len(data)}")
    for repo in data:
        print(f"  - {repo['full_name']}")
else:
    print(r.text[:300])

# Test 3: Check if jarvis-ai exists under different name
r = requests.get("https://api.github.com/search/repositories?q=jarvis-ai&per_page=5", headers=headers)
print(f"\nSearch: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Results: {data.get('total_count', 0)}")
    for item in data.get('items', []):
        print(f"  - {item['full_name']} ({item['size']}KB)")
