#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase Sync Module
Синхронизация данных между ПК через Firebase Realtime Database
"""

import json
import os
import threading
import time
import hashlib
from pathlib import Path

try:
    import firebase_admin
    from firebase_admin import credentials, db, auth
    FIREBASE_OK = True
except ImportError:
    FIREBASE_OK = False
    print("Firebase не установлен: pip install firebase-admin")


class FirebaseSync:
    """Синхронизация данных между ПК через Firebase"""
    
    def __init__(self, app=None):
        self.app = app
        self.user_id = None
        self.current_session = None
        self.is_connected = False
        self._sync_lock = threading.Lock()
        self._last_sync_data = {}
        self._listener_ref = None
        
        if FIREBASE_OK:
            self._init_firebase()
    
    def _init_firebase(self):
        """Инициализация Firebase"""
        try:
            if firebase_admin._apps:
                self.db = firebase_admin.db
                return
            
            cred_path = Path(__file__).parent / "firebase_credentials.json"
            if cred_path.exists():
                cred = credentials.Certificate(str(cred_path))
                firebase_admin.initialize_app(cred, {
                    'databaseURL': 'https://jarvis-ai-default-rtdb.firebaseio.com'
                })
            else:
                print("Firebase credentials не найдены")
                return
            
            self.db = firebase_admin.db
            print("✅ Firebase инициализирован")
        except Exception as e:
            print(f"Firebase init error: {e}")
    
    def _hash_password(self, password):
        """Хеширование пароля SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email, password, user_data):
        """
        Регистрация нового пользователя
        
        Args:
            email: Email пользователя
            password: Пароль
            user_data: Словарь с данными (имя, дата рождения и т.д.)
        
        Returns:
            tuple: (success, user_id, session_id)
        """
        if not FIREBASE_OK:
            print("Firebase не доступен")
            return False, None, None
        
        try:
            # Создаём пользователя в Firebase Auth
            user = auth.create_user(
                email=email,
                password=password
            )
            
            # Сохраняем данные пользователя в Realtime Database
            user_ref = self.db.reference(f'users/{user.uid}')
            user_ref.set({
                'email': email,
                'password_hash': self._hash_password(password),
                'data': user_data,
                'created_at': time.time(),
                'last_login': time.time(),
                'active_sessions': {}
            })
            
            print(f"✅ Пользователь зарегистрирован: {user.uid}")
            return True, user.uid, None
            
        except Exception as e:
            print(f"❌ Регистрация ошибка: {e}")
            return False, None, None
    
    def login_user(self, email, password):
        """
        Вход пользователя
        
        Returns:
            tuple: (success, user_data, session_id)
        """
        if not FIREBASE_OK:
            return False, None, None
        
        try:
            # Получаем пользователя по email
            user = auth.get_user_by_email(email)
            
            # Проверяем пароль
            password_hash = self._hash_password(password)
            
            # Получаем данные пользователя
            user_ref = self.db.reference(f'users/{user.uid}')
            user_data = user_ref.get()
            
            if not user_data:
                return False, None, None
            
            # Проверяем хеш пароля
            stored_hash = user_data.get('password_hash')
            if stored_hash != password_hash:
                return False, None, None
            
            # Создаём сессию
            import uuid
            session_id = str(uuid.uuid4())
            pc_info = self._get_pc_info()
            
            # Сохраняем сессию
            user_ref.child('active_sessions').child(session_id).set({
                'pc_info': pc_info,
                'login_time': time.time(),
                'last_active': time.time()
            })
            
            # Обновляем last_login
            user_ref.update({'last_login': time.time()})
            
            self.user_id = user.uid
            self.current_session = session_id
            self.is_connected = True
            
            print(f"✅ Вход выполнен: {session_id}")
            return True, user_data.get('data'), session_id
            
        except Exception as e:
            print(f"❌ Вход ошибка: {e}")
            return False, None, None
    
    def auto_login(self, user_id):
        """
        Автоматический вход с сохранённой сессией
        
        Returns:
            tuple: (success, user_data, session_id)
        """
        if not FIREBASE_OK:
            return False, None, None
        
        try:
            user_ref = self.db.reference(f'users/{user_id}')
            user_data = user_ref.get()
            
            if not user_data:
                return False, None, None
            
            # Создаём новую сессию
            import uuid
            session_id = str(uuid.uuid4())
            pc_info = self._get_pc_info()
            
            # Сохраняем сессию
            user_ref.child('active_sessions').child(session_id).set({
                'pc_info': pc_info,
                'login_time': time.time(),
                'last_active': time.time()
            })
            
            self.user_id = user_id
            self.current_session = session_id
            self.is_connected = True
            
            print(f"✅ Авто-вход выполнен: {session_id}")
            return True, user_data.get('data'), session_id
            
        except Exception as e:
            print(f"❌ Авто-вход ошибка: {e}")
            return False, None, None
    
    def _get_pc_info(self):
        """Получает уникальную информацию ПК"""
        import platform
        import uuid
        
        pc_id_path = Path(__file__).parent / ".pc_id"
        if pc_id_path.exists():
            pc_id = pc_id_path.read_text().strip()
        else:
            pc_id = str(uuid.uuid4())
            pc_id_path.write_text(pc_id)
        
        return {
            'pc_id': pc_id,
            'os': platform.system(),
            'hostname': platform.node()
        }
    
    def sync_data(self, data):
        """
        Синхронизация данных с Firebase
        
        Args:
            data: Словарь с данными для синхронизации
        """
        if not self.is_connected or not FIREBASE_OK:
            return
        
        with self._sync_lock:
            try:
                sync_ref = self.db.reference(f'sync/{self.user_id}')
                sync_ref.update({
                    'data': data,
                    'last_sync': time.time(),
                    'session': self.current_session
                })
                self._last_sync_data = data
                print("✅ Данные синхронизированы")
            except Exception as e:
                print(f"❌ Синхронизация ошибка: {e}")
    
    def load_synced_data(self):
        """
        Загрузка синхронизированных данных
        
        Returns:
            dict: Синхронизированные данные
        """
        if not self.is_connected or not FIREBASE_OK:
            return None
        
        try:
            sync_ref = self.db.reference(f'sync/{self.user_id}')
            data = sync_ref.get()
            if data and 'data' in data:
                print("✅ Данные загружены из Firebase")
                return data['data']
            return None
        except Exception as e:
            print(f"❌ Загрузка данных ошибка: {e}")
            return None
    
    def listen_for_changes(self, callback):
        """
        Слушает изменения в Firebase
        
        Args:
            callback: Функция, вызываемая при изменении данных
        """
        if not self.is_connected or not FIREBASE_OK:
            return
        
        def on_change(event):
            if event.event_type in ['put', 'patch']:
                data = event.snapshot.value
                if data and 'data' in data:
                    session = data.get('session')
                    if session != self.current_session:
                        callback(data['data'])
        
        try:
            sync_ref = self.db.reference(f'sync/{self.user_id}')
            self._listener_ref = sync_ref
            sync_ref.listen(on_change)
            print("👂 Слушаем изменения...")
        except Exception as e:
            print(f"❌ Слушатель ошибка: {e}")
    
    def logout_current_session(self):
        """Выход из текущей сессии"""
        if not self.is_connected or not FIREBASE_OK:
            return
        
        try:
            user_ref = self.db.reference(f'users/{self.user_id}')
            user_ref.child('active_sessions').child(self.current_session).delete()
            self.is_connected = False
            self.current_session = None
            print("🚪 Выход выполнен")
        except Exception as e:
            print(f"❌ Выход ошибка: {e}")
    
    def check_other_sessions(self):
        """
        Проверяет, есть ли другие активные сессии
        
        Returns:
            bool: True если есть другие сессии
        """
        if not self.is_connected or not FIREBASE_OK:
            return False
        
        try:
            user_ref = self.db.reference(f'users/{self.user_id}')
            sessions = user_ref.child('active_sessions').get()
            
            if sessions:
                other_sessions = [s for s in sessions.keys() if s != self.current_session]
                if other_sessions:
                    print(f"⚠️ Найдены другие сессии: {len(other_sessions)}")
                    return True
            return False
        except Exception as e:
            print(f"❌ Проверка сессий ошибка: {e}")
            return False
    
    def force_logout_all(self):
        """Принудительный выход со всех устройств"""
        if not self.is_connected or not FIREBASE_OK:
            return
        
        try:
            user_ref = self.db.reference(f'users/{self.user_id}')
            user_ref.child('active_sessions').delete()
            self.logout_current_session()
            print("🚪 Выход со всех устройств")
        except Exception as e:
            print(f"❌ Выход ошибка: {e}")


# Глобальный экземпляр синхронизации
firebase_sync = FirebaseSync()
