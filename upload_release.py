#!/usr/bin/env python3
"""Upload JARVIS_PRO.exe to GitHub Releases via API"""
import os
import sys
import json
import requests
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configuration
GITHUB_TOKEN = "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"
GITHUB_REPO = "89681505031/jarvis-ai"
RELEASE_TAG = "v2.0.2"
EXE_PATH = Path("dist/JARVIS_PRO_v2.0.2.exe")

def create_release():
    """Create GitHub Release and upload .exe"""
    
    if not EXE_PATH.exists():
        print(f"❌ EXE not found at {EXE_PATH}")
        sys.exit(1)
    
    exe_size = EXE_PATH.stat().st_size
    print(f"📦 EXE size: {exe_size / (1024*1024):.2f} MB")
    
    # Create release
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
    
    payload = {
        "tag_name": RELEASE_TAG,
        "target_commitish": "main",
        "name": f"JARVIS PRO {RELEASE_TAG}",
        "body": f"""# JARVIS PRO {RELEASE_TAG}

## 🎯 Features
- **Offline STT**: Vosk model (Russian)
- **AI**: Gemini 3.6 Flash
- **TTS**: Fish Audio (s2.1-pro-free)
- **Characters**: Jarvis, Astra, Luna, Terra, Cyber
- **Auto-update**: Checks for new versions on startup
- **Memory**: Saves user data in memory.json

## 📦 Installation
1. Download JARVIS_PRO.exe below
2. Run the executable
3. First run will download Vosk model if needed

## ⚠️ Requirements
- Windows 10/11
- No Python required (standalone)

## 🔄 Auto-Update
JARVIS will check for updates automatically. When new version is released, you'll be prompted to download.
""",
        "draft": False,
        "prerelease": False
    }
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    print("🚀 Creating GitHub Release...")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        release = response.json()
        upload_url = release["upload_url"].replace("{?name,label}", "")
        print(f"✅ Release created: {release['html_url']}")
    elif response.status_code == 422:
        # Release might already exist
        print("⚠️  Release might already exist, trying to find it...")
        list_response = requests.get(url, headers=headers)
        if list_response.status_code == 200:
            releases = list_response.json()
            for r in releases:
                if r["tag_name"] == RELEASE_TAG:
                    upload_url = r["upload_url"].replace("{?name,label}", "")
                    print(f"✅ Found existing release: {r['html_url']}")
                    break
            else:
                print("❌ Release not found")
                sys.exit(1)
        else:
            print(f"❌ Failed to list releases: {list_response.status_code}")
            sys.exit(1)
    else:
        print(f"❌ Failed to create release: {response.status_code}")
        print(f"Response: {response.text}")
        sys.exit(1)
    
    # Upload .exe
    print(f"\n📤 Uploading {EXE_PATH.name}...")
    
    files = {
        "file": (EXE_PATH.name, open(EXE_PATH, "rb"), "application/octet-stream")
    }
    
    upload_params = {
        "name": EXE_PATH.name,
        "label": EXE_PATH.name
    }
    
    upload_response = requests.post(upload_url, headers=headers, files=files, params=upload_params)
    
    if upload_response.status_code == 201:
        upload_data = upload_response.json()
        download_url = upload_data["browser_download_url"]
        print(f"✅ Upload successful!")
        print(f"\n🎉 DOWNLOAD URL: {download_url}")
        print(f"\n📋 Direct link for website button:")
        print(f"   {download_url}")
        print(f"\n🔗 GitHub Release page:")
        print(f"   {release['html_url']}")
    else:
        print(f"❌ Upload failed: {upload_response.status_code}")
        print(f"Response: {upload_response.text}")
        sys.exit(1)

if __name__ == "__main__":
    create_release()
