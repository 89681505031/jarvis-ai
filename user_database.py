#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
User Database Module
SQLite для хранения данных пользователя и API ключей
"""

import sqlite3
import os
from pathlib import Path


class UserDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = Path(__file__).parent / "jarvis_users.db"
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    birth_date TEXT,
                    birth_month TEXT,
                    birth_year INTEGER,
                    firebase_uid TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица API ключей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL UNIQUE,
                    api_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка инициализации БД: {e}")
    
    def set_user(self, name, birth_date, birth_month, birth_year, firebase_uid=None):
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (id, name, birth_date, birth_month, birth_year, firebase_uid)
                VALUES (1, ?, ?, ?, ?, ?)
            ''', (name, birth_date, birth_month, birth_year, firebase_uid))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка сохранения пользователя: {e}")
            return False
    
    def get_user(self):
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = 1')
            user = cursor.fetchone()
            conn.close()
            return dict(user) if user else None
        except Exception as e:
            print(f"Ошибка получения пользователя: {e}")
            return None
    
    def set_api_key(self, service, api_key):
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO api_keys (service, api_key)
                VALUES (?, ?)
            ''', (service, api_key))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Ошибка сохранения API ключа: {e}")
            return False
    
    def get_api_key(self, service):
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT api_key FROM api_keys WHERE service = ?', (service,))
            row = cursor.fetchone()
            conn.close()
            return row['api_key'] if row else None
        except Exception as e:
            print(f"Ошибка получения API ключа: {e}")
            return None
    
    def has_api_key(self, service):
        return self.get_api_key(service) is not None


# Глобальный экземпляр БД
db = UserDatabase()
