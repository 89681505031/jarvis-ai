#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. PRO - WEB ADMIN PANEL
Панель мониторинга и управления подписками
"""

import os
import sys
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarvis-pro-admin-secret-key-2024'

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================
DATA_DIR = Path(__file__).parent
LICENSE_FILE = DATA_DIR / "jarvis_license.json"
STATS_FILE = DATA_DIR / "admin_stats.json"
KEYS_FILE = DATA_DIR / "generated_keys.json"
SECRET_KEY = "JARVIS_PRO_SECRET_2024_KEY"

# ============================================================================
# УПРАВЛЕНИЕ ДАННЫМИ
# ============================================================================

def load_stats():
    """Загрузка статистики"""
    if STATS_FILE.exists():
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    # Инициализация статистики
    return {
        "total_downloads": 0,
        "total_licenses": 0,
        "active_subscriptions": 0,
        "trial_users": 0,
        "users": {},  # user_id -> license_data
        "generated_keys": [],
        "last_updated": datetime.now().isoformat()
    }

def save_stats(stats):
    """Сохранение статистики"""
    stats['last_updated'] = datetime.now().isoformat()
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

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
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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

def get_user_id():
    """Получение уникального ID пользователя"""
    try:
        import uuid
        # Пробуем получить UUID компьютера
        cmd_output = os.popen('powershell -Command "Get-CimInstance Win32_ComputerSystemProduct | Select-Object -ExpandProperty UUID"').read().strip()
        if cmd_output:
            return cmd_output
    except:
        pass
    
    # Fallback
    return f"HW_{uuid.getnode():012X}"

# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def dashboard():
    """Главная панель мониторинга"""
    stats = load_stats()
    
    # Подсчёт онлайн пользователей (активные сессии за последние 5 минут)
    online_users = 0
    for user_id, user_data in stats.get('users', {}).items():
        if user_data.get('last_active'):
            last_active = datetime.fromisoformat(user_data['last_active'])
            if (datetime.now() - last_active).total_seconds() < 300:
                online_users += 1
    
    return render_template('dashboard.html', stats=stats, online_users=online_users)

@app.route('/api/stats')
def api_stats():
    """API для получения статистики"""
    stats = load_stats()
    
    # Подсчёт онлайн
    online_users = 0
    for user_id, user_data in stats.get('users', {}).items():
        if user_data.get('last_active'):
            last_active = datetime.fromisoformat(user_data['last_active'])
            if (datetime.now() - last_active).total_seconds() < 300:
                online_users += 1
    
    return jsonify({
        "total_downloads": stats.get('total_downloads', 0),
        "total_licenses": stats.get('total_licenses', 0),
        "active_subscriptions": stats.get('active_subscriptions', 0),
        "trial_users": stats.get('trial_users', 0),
        "online_users": online_users,
        "total_users": len(stats.get('users', {})),
        "generated_keys_count": len(stats.get('generated_keys', [])),
        "last_updated": stats.get('last_updated')
    })

@app.route('/api/users')
def api_users():
    """API для получения списка пользователей"""
    stats = load_stats()
    users = []
    
    for user_id, user_data in stats.get('users', {}).items():
        end_date = datetime.fromisoformat(user_data['end_date'])
        days_left = (end_date - datetime.now()).days
        
        is_online = False
        if user_data.get('last_active'):
            last_active = datetime.fromisoformat(user_data['last_active'])
            if (datetime.now() - last_active).total_seconds() < 300:
                is_online = True
        
        users.append({
            "user_id": user_id,
            "type": user_data.get('type', 'unknown'),
            "start_date": user_data.get('start_date'),
            "end_date": user_data.get('end_date'),
            "days_left": days_left,
            "is_active": datetime.now() <= end_date,
            "is_online": is_online,
            "key": user_data.get('key', 'N/A')[:16] + "..."
        })
    
    return jsonify(users)

@app.route('/generate', methods=['GET', 'POST'])
def generate_key_page():
    """Страница генерации ключей"""
    generated_key = None
    user_id = ""
    
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        if not user_id:
            user_id = f"USER_{int(time.time())}"
        
        # Генерируем ключ
        generated_key = generate_key(user_id)
        
        # Сохраняем в статистику
        stats = load_stats()
        if 'generated_keys' not in stats:
            stats['generated_keys'] = []
        
        stats['generated_keys'].append({
            "key": generated_key,
            "user_id": user_id,
            "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "timestamp": int(time.time())
        })
        
        save_stats(stats)
    
    return render_template('generate.html', generated_key=generated_key, user_id=user_id)

@app.route('/activate', methods=['GET', 'POST'])
def activate_page():
    """Страница активации через ID пользователя"""
    message = None
    message_type = None  # 'success' или 'error'
    user_id = ""
    
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        
        if not user_id:
            message = "❌ Введите ID пользователя"
            message_type = 'error'
        else:
            # Генерируем ключ для пользователя
            key = generate_key(user_id)
            
            # Сохраняем лицензию
            stats = load_stats()
            
            user_data = {
                "type": "subscription",
                "user_id": user_id,
                "key": key,
                "start_date": datetime.now().isoformat(),
                "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "activated": True,
                "activated_at": datetime.now().isoformat()
            }
            
            # Сохраняем пользователя
            if 'users' not in stats:
                stats['users'] = {}
            stats['users'][user_id] = user_data
            
            # Обновляем статистику
            stats['total_licenses'] = stats.get('total_licenses', 0) + 1
            stats['active_subscriptions'] = stats.get('active_subscriptions', 0) + 1
            
            save_stats(stats)
            
            message = f"✅ Пользователь {user_id} активирован!\nКлюч: {key}"
            message_type = 'success'
    
    return render_template('activate.html', message=message, message_type=message_type, user_id=user_id)

@app.route('/api/activate', methods=['POST'])
def api_activate():
    """API для активации пользователя"""
    data = request.json
    user_id = data.get('user_id', '').strip()
    
    if not user_id:
        return jsonify({"error": "Введите ID пользователя"}), 400
    
    # Генерируем ключ
    key = generate_key(user_id)
    
    # Сохраняем
    stats = load_stats()
    if 'users' not in stats:
        stats['users'] = {}
    
    user_data = {
        "type": "subscription",
        "user_id": user_id,
        "key": key,
        "start_date": datetime.now().isoformat(),
        "end_date": (datetime.now() + timedelta(days=30)).isoformat(),
        "activated": True,
        "activated_at": datetime.now().isoformat()
    }
    
    stats['users'][user_id] = user_data
    stats['total_licenses'] = stats.get('total_licenses', 0) + 1
    stats['active_subscriptions'] = stats.get('active_subscriptions', 0) + 1
    
    save_stats(stats)
    
    return jsonify({
        "success": True,
        "user_id": user_id,
        "key": key,
        "end_date": user_data['end_date']
    })

@app.route('/api/track', methods=['POST'])
def api_track():
    """API для трекинга от JARVIS (онлайн статус)"""
    data = request.json
    user_id = data.get('user_id')
    action = data.get('action')  # 'download', 'active', 'heartbeat'
    
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400
    
    stats = load_stats()
    
    if action == 'download':
        stats['total_downloads'] = stats.get('total_downloads', 0) + 1
        save_stats(stats)
        return jsonify({"success": True, "message": "Download tracked"})
    
    elif action == 'heartbeat':
        # Обновляем last_active
        if 'users' not in stats:
            stats['users'] = {}
        
        if user_id in stats['users']:
            stats['users'][user_id]['last_active'] = datetime.now().isoformat()
            save_stats(stats)
            return jsonify({"success": True, "message": "Heartbeat received"})
        else:
            return jsonify({"error": "User not found"}), 404
    
    return jsonify({"error": "Unknown action"}), 400

# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 J.A.R.V.I.S. PRO - ADMIN PANEL")
    print("="*60)
    print(f"\n📊 Панель мониторинга: http://localhost:5000")
    print(f"🔑 Генератор ключей: http://localhost:5000/generate")
    print(f"⚡ Активация: http://localhost:5000/activate")
    print(f"\n{'='*60}\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
