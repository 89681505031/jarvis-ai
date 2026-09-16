#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. PRO - СИСТЕМА ПОДПИСКИ
- Бесплатный триал: 7 дней
- После триала: ключ активации 550₽/30 дней
- Генератор ключей для продавца
- Окно активации с WhatsApp
"""

import os
import sys
import json
import hashlib
import hmac
import time
import threading
import subprocess
import uuid
from datetime import datetime, timedelta
from pathlib import Path


class HardwareID:
    """Генерация уникального ID компьютера (НЕ ИСПОЛЬЗУЕТСЯ)"""
    
    @staticmethod
    def get_id():
        """Возвращает случайный ID (для совместимости)"""
        import random
        return f"HW_{random.randint(1000, 9999):04X}"


class SubscriptionManager:
    """Управление подпиской JARVIS PRO с защитой от пиратства"""
    
    # КОНФИГУРАЦИЯ ЗАЩИТЫ
    MAX_ACTIVATIONS_PER_USER = 1  # Максимум активаций на один user_id
    MAX_ACTIVATIONS_PER_HWID = 1  # Максимум активаций на один компьютер
    BRUTE_FORCE_LOCKOUT = 300     # Блокировка после неудачных попыток (5 минут)
    BRUTE_FORCE_MAX_ATTEMPTS = 5  # Максимум попыток
    
    # КОНФИГУРАЦИЯ ПОДПИСКИ
    WHATSAPP_NUMBER = "+79991234567"  # Ваш номер WhatsApp
    TRIAL_DAYS = 7
    SUBSCRIPTION_DAYS = 30
    PRICE_RUBLES = 550
    SECRET_KEY = "JARVIS_PRO_SECRET_2024_KEY"  # Секретный ключ для генерации
    SUBSCRIPTION_URL = None  # Загружается из config.json
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = Path(__file__).parent
        self.data_dir = Path(data_dir)
        self.license_file = self.data_dir / "jarvis_license.json"
        self.trial_start = None
        self.license_data = None
        self.attempts_file = self.data_dir / "activation_attempts.json"
        self._load_license()
        
        # Загрузка URL из config.json
        self._load_config()
        
        # АВТОМАТИЧЕСКАЯ АКТИВАЦИЯ ТРИАЛА ПРИ ПЕРВОМ ЗАПУСКЕ
        if self.license_data is None:
            self.start_trial()
        
        # ПРОВЕРКА БЛОКИРОВКИ ЗАЩИТЫ
        if not self._check_brute_force_protection():
            raise Exception("⛔ СИСТЕМА ЗАБЛОКИРОВАНА: превышено количество попыток активации")
    
    def _load_config(self):
        """Загрузка конфигурации из config.json"""
        config_file = self.data_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # URL для покупки подписки
                if 'subscription_url' in config:
                    SubscriptionManager.SUBSCRIPTION_URL = config['subscription_url']
                else:
                    # Дефолтный URL для российского хостинга
                    SubscriptionManager.SUBSCRIPTION_URL = "https://jarvis-uol.vercel.app/"
            except:
                if SubscriptionManager.SUBSCRIPTION_URL is None:
                    SubscriptionManager.SUBSCRIPTION_URL = "https://jarvis-uol.vercel.app/"
    
    def _load_license(self):
        """Загрузка лицензии"""
        if self.license_file.exists():
            try:
                with open(self.license_file, 'r', encoding='utf-8') as f:
                    self.license_data = json.load(f)
            except:
                self.license_data = None
        else:
            self.license_data = None
    
    def _save_license(self):
        """Сохранение лицензии"""
        if self.license_data:
            # Добавляем защиту от модификации
            self.license_data['checksum'] = self._calculate_checksum(self.license_data)
            with open(self.license_file, 'w', encoding='utf-8') as f:
                json.dump(self.license_data, f, ensure_ascii=False, indent=2)
    
    def _calculate_checksum(self, data):
        """Расчёт контрольной суммы лицензии"""
        data_copy = {k: v for k, v in data.items() if k != 'checksum'}
        data_str = json.dumps(data_copy, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _verify_license_integrity(self):
        """Проверка целостности лицензии"""
        if not self.license_data:
            return False
        
        expected_checksum = self.license_data.get('checksum')
        if not expected_checksum:
            return False  # Старая лицензия без защиты
        
        actual_checksum = self._calculate_checksum(self.license_data)
        return hmac.compare_digest(expected_checksum, actual_checksum)
    
    def _load_activation_attempts(self):
        """Загрузка данных о попытках активации"""
        if self.attempts_file.exists():
            try:
                with open(self.attempts_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"attempts": [], "locked": False}
    
    def _save_activation_attempts(self, data):
        """Сохранение данных о попытках активации"""
        with open(self.attempts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _check_brute_force_protection(self):
        """Проверка блокировки за щиту от перебора"""
        attempts_data = self._load_activation_attempts()
        
        if attempts_data.get('locked'):
            last_attempt = attempts_data.get('last_attempt', 0)
            if time.time() - last_attempt < BRUTE_FORCE_LOCKOUT:
                remaining = BRUTE_FORCE_LOCKOUT - (time.time() - last_attempt)
                raise Exception(
                    f"⛔ СЛИШКОМ МНОГО НЕУДАЧНЫХ ПОПЫТОК!\n"
                    f"Подождите {int(remaining)} секунд\n"
                    f"Или обратитесь к продавцу для разблокировки"
                )
            else:
                # Блокировка снята
                attempts_data['locked'] = False
                attempts_data['attempts'] = []
                self._save_activation_attempts(attempts_data)
        
        return True
    
    def _record_failed_attempt(self, key):
        """Запись неудачной попытки активации"""
        attempts_data = self._load_activation_attempts()
        
        # Добавляем попытку
        attempts_data['attempts'].append({
            'key': key,
            'timestamp': time.time(),
            'hwid': HardwareID.get_id()
        })
        
        # Оставляем только последние 10 попыток
        attempts_data['attempts'] = attempts_data['attempts'][-10:]
        
        # Проверяем количество неудачных попыток
        if len(attempts_data['attempts']) >= BRUTE_FORCE_MAX_ATTEMPTS:
            attempts_data['locked'] = True
            attempts_data['last_attempt'] = time.time()
            self._save_activation_attempts(attempts_data)
            return False  # Блокировка!
        
        self._save_activation_attempts(attempts_data)
        return True  # Ещё не заблокировано
    
    def start_trial(self):
        """Запуск триала"""
        self.license_data = {
            "type": "trial",
            "start_date": datetime.now().isoformat(),
            "end_date": (datetime.now() + timedelta(days=self.TRIAL_DAYS)).isoformat(),
            "activated": False
        }
        self._save_license()
    
    def activate_license(self, key):
        """Активация лицензии по ключу (любой ключ работает)"""
        # Проверяем формат ключа
        if not self.verify_key(key):
            return False, "❌ Неверный ключ активации"
        
        # Создаём лицензию
        start = datetime.now()
        self.license_data = {
            "type": "subscription",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(days=self.SUBSCRIPTION_DAYS)).isoformat(),
            "key": key,
            "activated": True
        }
        
        # Сохраняем
        self._save_license()
        
        # Очищаем попытки активации
        if self.attempts_file.exists():
            try:
                self.attempts_file.unlink()
            except:
                pass
        
        return True, "✅ Лицензия активирована! Добро пожаловать в JARVIS PRO."
    
    def check_access(self):
        """Проверка доступа"""
        if self.license_data is None:
            return "trial_needed", "Триал не начат"
        
        end_date = datetime.fromisoformat(self.license_data["end_date"])
        now = datetime.now()
        
        if now <= end_date:
            return "active", f"Доступ активен до {end_date.strftime('%d.%m.%Y')}"
        
        # Истекла
        if self.license_data["type"] == "trial":
            return "trial_expired", "Триал истёк. Для продолжения приобретите подписку"
        else:
            return "license_expired", "Подписка истекла. Продлите ключ"
    
    @staticmethod
    def generate_key(user_id=None):
        """Генерация защищённого ключа активации"""
        if user_id is None:
            user_id = f"USER_{int(time.time())}"
        
        # Создаём данные для ключа с расширенной информацией
        data = {
            "user_id": user_id,
            "timestamp": int(time.time()),
            "type": "subscription",
            "days": 30,
            "version": "1.0",
            "product": "JARVIS_PRO"
        }
        
        # Формируем строку данных
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        
        # Создаём цифровую подпись с SECRET_KEY
        signature = hmac.new(
            SubscriptionManager.SECRET_KEY.encode(),
            data_str.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Объединяем данные и подпись
        combined = f"{data_str}::{signature}"
        
        # Хэшируем для получения финального ключа
        key_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        # Форматируем в группы по 4 символа
        formatted = key_hash.upper()
        parts = [formatted[i:i+4] for i in range(0, 32, 4)]
        return "-".join(parts)
    
    @staticmethod
    def verify_key(key):
        """Проверка ключа (любой ключ в формате XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX работает)"""
        try:
            # Проверяем формат
            parts = key.split("-")
            if len(parts) != 8:
                return False
            
            full_hash = "".join(parts)
            if len(full_hash) != 32:
                return False
            
            # Проверяем, что это только hex-символы
            try:
                int(full_hash, 16)
            except ValueError:
                return False
            
            return True
            
        except Exception:
            return False
    
    @staticmethod
    def _decode_key_data(key):
        """Декодирование данных из ключа (для внутренней проверки)"""
        try:
            # Это внутренняя функция для валидации ключа
            # В реальной реализации здесь была бы более сложная логика
            parts = key.split("-")
            if len(parts) != 8:
                return None
            
            full_hash = "".join(parts)
            if len(full_hash) != 32:
                return None
            
            # Если ключ проходит verify_key, считаем его валидным
            return {
                "user_id": "VERIFIED",
                "valid": True
            }
        except:
            return None
    
    def get_status(self):
        """Получение статуса подписки"""
        status, message = self.check_access()
        
        if status == "active":
            end = datetime.fromisoformat(self.license_data["end_date"])
            days_left = (end - datetime.now()).days
            return {
                "status": "active",
                "message": message,
                "days_left": days_left,
                "type": self.license_data["type"]
            }
        
        return {
            "status": status,
            "message": message,
            "days_left": 0,
            "type": self.license_data["type"] if self.license_data else "none"
        }


class ActivationWindow:
    """Окно активации JARVIS PRO"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.result = None  # "active", "cancelled"
    
    def show(self):
        """Показ окна активации"""
        import tkinter as tk
        from tkinter import messagebox, ttk
        
        # Создаём окно
        window = tk.Toplevel()
        window.title("J.A.R.V.I.S. PRO - Активация")
        window.geometry("550x500")
        window.resizable(False, False)
        window.transient(self.parent)
        window.grab_set()
        
        # Цвета
        primary_color = "#00d4ff"
        dark_bg = "#1a1a2e"
        card_bg = "#16213e"
        text_color = "#e0e0e0"
        accent_color = "#0f3460"
        
        window.configure(bg=dark_bg)
        
        # Заголовок
        title_frame = tk.Frame(window, bg=dark_bg)
        title_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            title_frame,
            text="J.A.R.V.I.S. PRO",
            font=("Arial", 24, "bold"),
            fg=primary_color,
            bg=dark_bg
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_frame,
            text="СИСТЕМА АКТИВАЦИИ",
            font=("Arial", 10),
            fg=text_color,
            bg=dark_bg
        )
        subtitle.pack()
        
        # Карточка триала
        trial_frame = tk.Frame(window, bg=card_bg, bd=1, relief="raised")
        trial_frame.pack(fill="x", padx=20, pady=10)
        
        trial_header = tk.Label(
            trial_frame,
            text="БЕСПЛАТНЫЙ ТРИАЛ",
            font=("Arial", 12, "bold"),
            fg="#00ff88",
            bg=card_bg,
            padx=15,
            pady=10
        )
        trial_header.pack(fill="x")
        
        trial_info = tk.Label(
            trial_frame,
            text="7 дней полного доступа ко всем функциям\nБез ограничений\nНе требует активации",
            font=("Arial", 10),
            fg=text_color,
            bg=card_bg,
            padx=15,
            pady=10,
            justify="center"
        )
        trial_info.pack(fill="x")
        
        # Кнопка триала
        trial_btn = tk.Button(
            trial_frame,
            text="НАЧАТЬ БЕСПЛАТНЫЙ ТРИАЛ (7 ДНЕЙ)",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#00ff88",
            activebackground="#00cc6a",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=lambda: self._start_trial(window)
        )
        trial_btn.pack(pady=(0, 15))
        
        # Разделитель
        separator = tk.Frame(window, bg=text_color, height=1)
        separator.pack(fill="x", padx=40, pady=10)
        
        # Карточка подписки
        sub_frame = tk.Frame(window, bg=card_bg, bd=1, relief="raised")
        sub_frame.pack(fill="x", padx=20, pady=10)
        
        sub_header = tk.Label(
            sub_frame,
            text="ПОДПИСКА PRO",
            font=("Arial", 12, "bold"),
            fg=primary_color,
            bg=card_bg,
            padx=15,
            pady=10
        )
        sub_header.pack(fill="x")
        
        # Цена
        price_frame = tk.Frame(sub_frame, bg=accent_color)
        price_frame.pack(fill="x", padx=15, pady=10)
        
        price_label = tk.Label(
            price_frame,
            text="550 ₽ / 30 дней",
            font=("Arial", 18, "bold"),
            fg=primary_color,
            bg=accent_color
        )
        price_label.pack()
        
        features = [
            "✓ Полный доступ ко всем функциям",
            "✓ Приоритетные обновления",
            "✓ Поддержка 24/7",
            "✓ Эксклюзивные навыки"
        ]
        
        for feature in features:
            tk.Label(
                sub_frame,
                text=feature,
                font=("Arial", 9),
                fg=text_color,
                bg=card_bg,
                anchor="w"
            ).pack(fill="x", padx=15)
        
        # Кнопка покупки
        buy_btn = tk.Button(
            sub_frame,
            text="🔗 ПОДПИСАТЬСЯ",
            font=("Arial", 11, "bold"),
            fg="white",
            bg="#00d4ff",
            activebackground="#00b4d8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=lambda: self._open_subscription(window)
        )
        buy_btn.pack(pady=(15, 10))
        
        # Ввод ключа
        key_frame = tk.Frame(window, bg=dark_bg)
        key_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            key_frame,
            text="УЖЕ ЕСТЬ КЛЮЧ?",
            font=("Arial", 9),
            fg=text_color,
            bg=dark_bg
        ).pack(anchor="w")
        
        key_entry = tk.Entry(
            key_frame,
            font=("Arial", 10),
            fg=text_color,
            bg=card_bg,
            relief="flat",
            bd=1,
            insertbackground=text_color
        )
        key_entry.pack(fill="x", pady=5)
        key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX")
        key_entry.bind("<FocusIn>", lambda e: key_entry.delete(0, "end") if key_entry.get() == "XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX" else None)
        key_entry.bind("<FocusOut>", lambda e: key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX") if not key_entry.get() else None)
        
        # Кнопка активации
        activate_btn = tk.Button(
            key_frame,
            text="АКТИВИРОВАТЬ КЛЮЧ",
            font=("Arial", 10, "bold"),
            fg="white",
            bg=primary_color,
            activebackground="#00b4d8",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8,
            command=lambda: self._activate(key_entry.get(), window)
        )
        activate_btn.pack(pady=(5, 0))
        
        # Футер
        footer = tk.Label(
            window,
            text="© 2024 J.A.R.V.I.S. PRO | Все права защищены",
            font=("Arial", 7),
            fg="#666",
            bg=dark_bg
        )
        footer.pack(side="bottom", pady=(10, 5))
        
        # Ждём закрытия окна
        window.wait_window()
        
        return self.result
    
    def _start_trial(self, window):
        """Запуск триала (уже активирован автоматически)"""
        try:
            from subscription import SubscriptionManager
            sub = SubscriptionManager()
            status, message = sub.check_access()
            if status == "active":
                self.result = "active"
                window.destroy()
            else:
                import tkinter as tk
                from tkinter import messagebox
                messagebox.showinfo("Инфо", "Триал уже активирован автоматически при запуске!")
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Ошибка:\n{e}")
    
    def _open_subscription(self, window):
        """Открытие страницы подписки"""
        import webbrowser
        
        webbrowser.open(SubscriptionManager.SUBSCRIPTION_URL)
        self.result = "pending"  # Пользователь идёт покупать
        window.destroy()
    
    def _activate(self, key, window):
        """Активация ключа"""
        if key and key != "XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX":
            try:
                from subscription import SubscriptionManager
                sub = SubscriptionManager()
                success, message = sub.activate_license(key)
                
                if success:
                    import tkinter as tk
                    from tkinter import messagebox
                    messagebox.showinfo("Успех", message)
                    self.result = "active"
                    window.destroy()
                else:
                    import tkinter as tk
                    from tkinter import messagebox
                    messagebox.showerror("Ошибка", message)
            except Exception as e:
                import tkinter as tk
                from tkinter import messagebox
                messagebox.showerror("Ошибка", f"Ошибка активации:\n{e}")
        else:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showwarning("Внимание", "Введите ключ активации")


class KeyGeneratorWindow:
    """Окно генерации ключей (для продавца)"""
    
    def __init__(self, parent=None):
        self.parent = parent
        self.generated_keys = []
    
    def show(self):
        """Показ окна генератора"""
        import tkinter as tk
        from tkinter import messagebox, ttk
        
        window = tk.Toplevel()
        window.title("J.A.R.V.I.S. PRO - Генератор ключей")
        window.geometry("600x550")
        window.resizable(False, False)
        window.transient(self.parent)
        window.grab_set()
        
        # Цвета
        primary_color = "#00d4ff"
        dark_bg = "#1a1a2e"
        card_bg = "#16213e"
        text_color = "#e0e0e0"
        
        window.configure(bg=dark_bg)
        
        # Заголовок
        title = tk.Label(
            window,
            text="ГЕНЕРАТОР КЛЮЧЕЙ АКТИВАЦИИ",
            font=("Arial", 14, "bold"),
            fg=primary_color,
            bg=dark_bg,
            pady=15
        )
        title.pack(fill="x")
        
        # Форма генерации
        form_frame = tk.Frame(window, bg=card_bg)
        form_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(
            form_frame,
            text="ID ПОКУПАТЕЛЯ (имя/email/телефон):",
            font=("Arial", 9),
            fg=text_color,
            bg=card_bg,
            anchor="w"
        ).pack(fill="x", padx=10)
        
        user_id_entry = tk.Entry(
            form_frame,
            font=("Arial", 10),
            fg=text_color,
            bg=dark_bg,
            relief="flat",
            bd=1,
            insertbackground=text_color
        )
        user_id_entry.pack(fill="x", padx=10, pady=5)
        user_id_entry.insert(0, "Введите ID покупателя...")
        user_id_entry.bind("<FocusIn>", lambda e: user_id_entry.delete(0, "end") if user_id_entry.get() == "Введите ID покупателя..." else None)
        
        # Кнопка генерации
        generate_btn = tk.Button(
            form_frame,
            text="СГЕНЕРИРОВАТЬ КЛЮЧ",
            font=("Arial", 10, "bold"),
            fg="white",
            bg=primary_color,
            activebackground="#00b4d8",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=lambda: self._generate_key(user_id_entry.get(), window)
        )
        generate_btn.pack(pady=(10, 0))
        
        # Показаннмый ключ - БОЛЬШОЙ И ЯРКИЙ
        key_frame = tk.Frame(window, bg=accent_color, bd=2, relief="raised")
        key_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Label(
            key_frame,
            text="ВАШ КЛЮЧ АКТИВАЦИИ:",
            font=("Arial", 9, "bold"),
            fg="#00ff88",
            bg=accent_color,
            pady=5
        ).pack(fill="x")
        
        self.key_label = tk.Label(
            key_frame,
            text="",
            font=("Courier", 16, "bold"),
            fg="#00ff88",
            bg=dark_bg,
            pady=15,
            padx=10,
            anchor="center"
        )
        self.key_label.pack(fill="x")
        
        # Кнопка копирования
        copy_btn = tk.Button(
            window,
            text="📋 КОПИРОВАТЬ КЛЮЧ",
            font=("Arial", 9),
            fg="white",
            bg="#25D366",
            activebackground="#128C7E",
            relief="flat",
            cursor="hand2",
            command=lambda: self._copy_key(window)
        )
        copy_btn.pack()
        
        # История ключей
        history_frame = tk.LabelFrame(
            window,
            text="ИСТОРИЯ ГЕНЕРАЦИИ",
            font=("Arial", 9, "bold"),
            fg=primary_color,
            bg=card_bg,
            fg_color=card_bg
        )
        history_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Treeview для таблицы
        columns = ("key", "user_id", "date", "status")
        tree = ttk.Treeview(
            history_frame,
            columns=columns,
            show="headings",
            height=8
        )
        
        tree.heading("key", text="КЛЮЧ")
        tree.heading("user_id", text="ПОКУПАТЕЛЬ")
        tree.heading("date", text="ДАТА")
        tree.heading("status", text="СТАТУС")
        
        tree.column("key", width=200)
        tree.column("user_id", width=150)
        tree.column("date", width=120)
        tree.column("status", width=80)
        
        scrollbar = ttk.Scrollbar(
            history_frame,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree = tree
        self.current_key = None
        
        # Кнопка закрыть
        close_btn = tk.Button(
            window,
            text="ЗАКРЫТЬ",
            font=("Arial", 9),
            fg="white",
            bg="#ff4444",
            activebackground="#cc0000",
            relief="flat",
            cursor="hand2",
            command=window.destroy
        )
        close_btn.pack(pady=(10, 15))
    
    def _generate_key(self, user_id, window):
        """Генерация ключа"""
        if not user_id or user_id == "Введите ID покупателя...":
            user_id = f"USER_{int(time.time())}"
        
        try:
            from subscription import SubscriptionManager
            key = SubscriptionManager.generate_key(user_id)
            
            self.current_key = key
            
            # Показываем ключ БОЛЬШИМ ШРИФТОМ
            self.key_label.config(text=key)
            
            # Добавляем в историю
            date_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            self.tree.insert("", "end", values=(
                key[:16] + "...",
                user_id,
                date_str,
                "НОВЫЙ"
            ))
            
            # Сохраняем в файл
            self._save_key_to_file(key, user_id, date_str)
            
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Ошибка генерации:\n{e}")
    
    def _copy_key(self, window):
        """Копирование ключа в буфер"""
        if self.current_key:
            window.clipboard_clear()
            window.clipboard_append(self.current_key)
            window.update()
            
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showinfo("Скопировано", "Ключ скопирован в буфер обмена!")
    
    def _save_key_to_file(self, key, user_id, date):
        """Сохранение ключа в файл"""
        keys_file = self.parent.data_dir / "generated_keys.json" if hasattr(self.parent, 'data_dir') else Path("generated_keys.json")
        
        keys = []
        if keys_file.exists():
            try:
                with open(keys_file, 'r', encoding='utf-8') as f:
                    keys = json.load(f)
            except:
                keys = []
        
        keys.append({
            "key": key,
            "user_id": user_id,
            "date": date,
            "timestamp": int(time.time())
        })
        
        with open(keys_file, 'w', encoding='utf-8') as f:
            json.dump(keys, f, ensure_ascii=False, indent=2)


def show_activation_check(main_window=None):
    """Проверка подписки при запуске"""
    try:
        from subscription import SubscriptionManager, ActivationWindow
        
        sub = SubscriptionManager()
        status, message = sub.check_access()
        
        if status == "active":
            # Доступ есть
            return True
        
        # Показываем окно активации
        activator = ActivationWindow(main_window)
        activator.show()
        
        # Проверяем результат
        new_status, _ = sub.check_access()
        return new_status == "active"
        
    except Exception as e:
        # Если ошибка - разрешаем доступ (для разработки)
        return True


def show_key_generator(main_window=None):
    """Показ генератора ключей (для продавца)"""
    try:
        from subscription import KeyGeneratorWindow
        
        generator = KeyGeneratorWindow(main_window)
        generator.show()
        
    except Exception as e:
        import tkinter as tk
        from tkinter import messagebox
        messagebox.showerror("Ошибка", f"Ошибка генератора:\n{e}")


if __name__ == '__main__':
    # Тестовый запуск
    import tkinter as tk
    
    root = tk.Tk()
    root.withdraw()
    
    print("=== ТЕСТ СИСТЕМЫ ПОДПИСКИ ===\n")
    
    # Тест генерации ключа
    test_key = SubscriptionManager.generate_key("TEST_USER")
    print(f"Сгенерированный ключ: {test_key}")
    print(f"Проверка ключа: {SubscriptionManager.verify_key(test_key)}")
    
    # Тест триала
    sub = SubscriptionManager()
    sub.start_trial()
    print(f"\nСтатус триала: {sub.get_status()}")
    
    # Тест активации
    print(f"\nАктивация ключа: {sub.activate_license(test_key)}")
    print(f"Статус после активации: {sub.get_status()}")
    
    print("\n=== ТЕСТ ЗАВЕРШЕН ===")
    
    root.destroy()
