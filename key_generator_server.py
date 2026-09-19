#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. PRO - ОТДЕЛЬНЫЙ ГЕНЕРАТОР КЛЮЧЕЙ
Запуск: python key_generator_server.py
URL: http://localhost:5001
"""

import os
import sys
import json
import hashlib
import hmac
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
DATA_DIR = Path(__file__).parent
KEYS_FILE = DATA_DIR / "generated_keys.json"
SECRET_KEY = "JARVIS_PRO_SECRET_2024_KEY"
PORT = 5001  # Отдельный порт для генератора

# ============================================================================
# ГЕНЕРАЦИЯ КЛЮЧЕЙ
# ============================================================================

def generate_key(user_id=None):
    """Генерация ключа активации"""
    if user_id is None:
        user_id = f"USER_{int(time.time())}"
    
    data = {
        "user_id": user_id,
        "timestamp": int(time.time()),
        "type": "subscription",
        "days": 30,
        "version": "1.0",
        "product": "JARVIS_PRO"
    }
    
    data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode(),
        data_str.encode(),
        hashlib.sha256
    ).hexdigest()
    
    combined = f"{data_str}::{signature}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()
    
    formatted = key_hash.upper()
    parts = [formatted[i:i+4] for i in range(0, 32, 4)]
    return "-".join(parts)

def load_generated_keys():
    """Загрузка сгенерированных ключей"""
    if KEYS_FILE.exists():
        try:
            with open(KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return []

def save_generated_keys(keys):
    """Сохранение сгенерированных ключей"""
    with open(KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(keys, f, ensure_ascii=False, indent=2)

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Главная страница генератора"""
    return render_template('keygen.html')

@app.route('/generate', methods=['POST'])
def api_generate():
    """API для генерации ключа"""
    data = request.get_json()
    user_id = data.get('user_id', '').strip() if data else ''
    
    if not user_id:
        user_id = f"USER_{int(time.time())}"
    
    # Генерируем ключ
    key = generate_key(user_id)
    
    # Сохраняем в файл
    keys = load_generated_keys()
    keys.append({
        "key": key,
        "user_id": user_id,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "timestamp": int(time.time())
    })
    save_generated_keys(keys)
    
    return jsonify({
        "success": True,
        "key": key,
        "user_id": user_id,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })

@app.route('/api/keys')
def api_get_keys():
    """Получение списка всех сгенерированных ключей"""
    keys = load_generated_keys()
    return jsonify(keys)

@app.route('/api/stats')
def api_stats():
    """Статистика генерации"""
    keys = load_generated_keys()
    return jsonify({
        "total_keys": len(keys),
        "unique_users": len(set(k.get('user_id', '') for k in keys)),
        "last_generated": keys[-1] if keys else None
    })

if __name__ == '__main__':
    print("=" * 70)
    print("🔑 J.A.R.V.I.S. PRO - ГЕНЕРАТОР КЛЮЧЕЙ")
    print("=" * 70)
    print(f"\n🌐 URL: http://localhost:{PORT}")
    print(f"📁 Папка: {DATA_DIR}")
    print(f"💾 Файл ключей: {KEYS_FILE}")
    print(f"\n⚠️  НЕ ЗАКРЫВАЙТЕ ЭТО ОКНО!")
    print("=" * 70)
    
    app.run(host='0.0.0.0', port=PORT, debug=False)
