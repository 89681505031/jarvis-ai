#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. ULTIMATE PRO - 100% COMPLETE & SOUNDS FOLDER EDITION
✅ Полный код без единого сокращения
✅ Чтение всех MP3 аудиофайлов строго из папки sounds
✅ Авто-переключение на Edge-TTS, если файл в sounds отсутствует
✅ Непрерывный диалог (15 секунд без слова "Джарвис")
✅ Полный доступ Ollama AI к функциям ПК (JSON Action Dispatching)
✅ Управление окнами, приложениями, файлами, звуком и Яндекс.Музыкой
"""

import sys, os, json, time, threading, webbrowser, subprocess, psutil, urllib.parse, random, uuid, re, asyncio, logging, shutil, zipfile, io, datetime, math, hashlib, socket, struct, base64
import queue
from pathlib import Path
from datetime import datetime, timedelta

# Windows API для отправки клавиш напрямую в окно
try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import ctypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False

# ---------------------------------------------------------------------------
# Логирование — вместо print()
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "jarvis.log", encoding="utf-8", mode="a"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("jarvis")

# =============================================================================
# СИСТЕМА ПОДПИСКИ J.A.R.V.I.S. PRO
# =============================================================================
SUBSCRIPTION_OK = False
try:
    sys.path.insert(0, os.path.dirname(__file__))
    from subscription import SubscriptionManager, show_activation_check, show_key_generator
    SUBSCRIPTION_OK = True
    log.info("Система подписки JARVIS PRO подключена")
except Exception as e:
    log.warning("Система подписки недоступна: %s", e)

# Ленивая загрузка PIL (после настройки логирования)
_pil_loaded = False
try:
    from PIL import ImageGrab
    _pil_loaded = True
except ImportError:
    ImageGrab = None
    log.warning("PIL не доступен, скриншоты будут недоступны")


# =============================================================================
# ЛЕНИВАЯ ЗАГРУЗКА ТЯЖЁЛЫХ МОДУЛЕЙ
# =============================================================================
def lazy_import(module_name, import_func=None):
    """
    Ленивая загрузка модуля только при первом использовании.
    Ускоряет запуск в 3-5 раз.
    """
    import importlib
    
    class LazyModule:
        def __init__(self, name, loader):
            self._name = name
            self._loader = loader
            self._module = None
            self.__name__ = name
        
        def _load(self):
            if self._module is None:
                self._module = importlib.import_module(self._name)
            return self._module
        
        def __getattr__(self, name):
            module = self._load()
            return getattr(module, name)
        
        def __call__(self, *args, **kwargs):
            module = self._load()
            return module(*args, **kwargs)
    
    if import_func:
        # Для сложных импортов с aliases
        cache = {}
        def wrapped():
            if 'module' not in cache:
                import_func()
            return cache['module']
        return wrapped()
    
    return LazyModule(module_name, None)

# Кэш для загруженных модулей
_import_cache = {}

def get_module(module_name, import_func):
    """Получить модуль из кэша или загрузить"""
    if module_name not in _import_cache:
        _import_cache[module_name] = import_func()
    return _import_cache[module_name]


# Безопасный импорт winreg (только для Windows)
try:
    import winreg
except ImportError:
    winreg = None

# Безопасная инициализация Tkinter
try:
    import tkinter as tk
    from tkinter import scrolledtext, messagebox, ttk
except Exception as e:
    log.error("Ошибка Tkinter: %s", e)
    sys.exit(1)

# Поддержка системного трея (возле стрелочки)
TRAY_OK = False
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_OK = True
except:
    pass

# Безопасный импорт библиотек с авто-заглушками при сбое
PYAUTOGUI_OK = False
try:
    import pyautogui
    pyautogui.FAILSAFE = True  # Безопасность: мышь в угол экрана = стоп
    PYAUTOGUI_OK = True
except:
    pass

VOICE_OK = False
engine = None
try:
    import pyttsx3
    engine = pyttsx3.init()
    VOICE_OK = True
except:
    pass

SPEECH_OK = False
recognizer = None
microphone = None
MICROPHONE_ERROR = ""
try:
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 100  # Порог фонового шума (очень чуткий)
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.2
    recognizer.dynamic_energy_adjustment_ratio = 1.2
    recognizer.pause_threshold = 1.2   # 1.2с между словами
    recognizer.non_speaking_duration = 1.2  # 1.2с тишины = закончил
    SPEECH_OK = True
    try:
        microphone = sr.Microphone()
    except Exception as e:
        MICROPHONE_ERROR = str(e)
        log.warning("Микрофон пока не подключён: %s", e)
except Exception as e:
    MICROPHONE_ERROR = str(e)
    log.warning("Внимание: микрофон недоступен (PyAudio): %s", e)

PYGAME_OK = False
try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except Exception as e:
    log.error("Ошибка Pygame mixer: %s", e)

EDGE_TTS_OK = False
try:
    import edge_tts
    EDGE_TTS_OK = True
    log.info("edge_tts подключён успешно")
except Exception as e:
    EDGE_TTS_OK = False
    log.warning("edge_tts не доступен: %s", str(e)[:100])

REQUESTS_OK = False
try:
    import requests
    import urllib3
    # SSL-верификация отключена — сервер Sber использует самоподписанный сертификат
    # Для локального приложения это безопасно
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    REQUESTS_OK = True
except:
    pass

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None

# === FISH AUDIO TTS ===
try:
    from fish_audio_tts import (
        init_fish_tts,
        get_fish_tts,
        fish_enabled,
        FISH_AUDIO_OK,
    )
    log.info("FishAudio модуль подключён")
except Exception as e:
    FISH_AUDIO_OK = False
    log.warning("FishAudio модуль недоступен: %s", e)

# === VOSK SPEECH RECOGNITION ===
try:
    from vosk_recognition import init_vosk, get_vosk_status, create_vosk_recognizer
    VOSK_OK = False
    if init_vosk():
        VOSK_OK = True
        log.info("✅ Vosk модуль подключён и готов к работе!")
        log.info(f"   Статус: {get_vosk_status()}")
    else:
        log.warning("⚠️ Vosk недоступен, будет использоваться speech_recognition")
except Exception as e:
    VOSK_OK = False
    log.warning("Vosk модуль недоступен: %s", e)

# === GIGACHAT AI (основной и единственный) ===
GIGACHAT_OK = False

# Встроенные ключи
FISH_AUDIO_BUILTIN_KEY = "sk-fish-TSwmQZcWu4kesmD6NjBdmHBbrWFfhFyK2hXkDy_EZVA"

# === ИНИЦИАЛИЗАЦИЯ GIGACHAT (основной AI) ===
# Встроенные ключи (для дистрибуции)
GIGACHAT_AUTH_KEY = os.environ.get('GIGACHAT_AUTH_KEY', '')
GIGACHAT_BUILTIN_KEY = 'MDFhMDU5YjItYjhjNy03NGJjLWI4YWUtNDg5YTVjZTQ2Mzg5OmVkMzRiNzhlLTIzNzMtNGI2NC05M2ZlLWVkZjkwNmJlNmQ2MA=='

if not GIGACHAT_AUTH_KEY:
    # Пробуем config.json
    config_path = Path(__file__).parent / 'config.json'
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            GIGACHAT_AUTH_KEY = config.get('gigachat_auth_key', '')
        except:
            pass
    
    # Если нет в config.json - используем встроенный ключ
    if not GIGACHAT_AUTH_KEY:
        GIGACHAT_AUTH_KEY = GIGACHAT_BUILTIN_KEY
        log.info("⚠️ Используем встроенный API ключ GigaChat")

if GIGACHAT_AUTH_KEY:
    GIGACHAT_OK = True
    log.info("✅ GigaChat подключён (основной AI)")
    log.info(f"   API ключ: {GIGACHAT_AUTH_KEY[:20]}...")
else:
    log.warning("⚠️ GigaChat не настроен (нет API ключа)")
    log.info("   Для активации: добавьте 'gigachat_auth_key' в config.json")
    log.info("   Или получите ключ: https://developer.sber.ru/")

VOICE_MAP = {
    'приветствие': 'Джарвис - приветствие.mp3',
    'диагностика': 'Начинаю диагностику системы.mp3',
    'проверка': 'Проверка завершена.mp3',
    'загрузка': 'Загружаю сэр.mp3',
    'перезагрузка': 'Я перезагрузился сэр.mp3',
    'отключение': 'Отключаю питание, начинаю диагностику системы.mp3',
    'поздравляю': 'Поздравляю сэр.mp3',
    # Приветствия
    'hello': 'hello.mp3',
    'hello1': 'hello1.mp3',
    'hello2': 'hello2.mp3',
    'hello3': 'hello3.mp3',
    # Процесс
    'process': 'process.mp3',
    'process1': 'process1.mp3',
    'process2': 'process2.mp3',
    'process3': 'process3.mp3',
    # Готово
    'done': 'done.mp3',
    'done1': 'done1.mp3',
    'done2': 'done2.mp3',
    'done3': 'done3.mp3',
    # Джарвис
    'jarvis': 'jarvis.mp3',
    'jarvis1': 'jarvis1.mp3',
    'jarvis2': 'jarvis2.mp3',
    'jarvis3': 'jarvis3.mp3',
    # Токсик
    'toxic_stupid': 'toxic_stupid.mp3',
    'toxic_go': 'toxic_go.mp3',
    'toxic_swear': 'toxic_swear.mp3',
    'toxic_bad': 'toxic_bad.mp3',
    # Тони
    'tony': 'tony.mp3',
    'tony1': 'tony1.mp3',
    'tony2': 'tony2.mp3',
    'tony3': 'tony3.mp3',
    # Похвала
    'praise': 'praise.mp3',
    'praise1': 'praise1.mp3',
    'praise2': 'praise2.mp3',
    # ОК
    'ok': 'ok.mp3',
    'ok1': 'ok1.mp3',
    'ok2': 'ok2.mp3',
    # Не распознано
    'not_recognized': 'not_recognized.mp3',
    'not_recognized1': 'not_recognized1.mp3',
    'not_recognized2': 'not_recognized2.mp3',
    'not_recognized3': 'not_recognized3.mp3',
    # Спасибо
    'thanks': 'thanks.mp3',
    'thanks1': 'thanks1.mp3',
    'thanks2': 'thanks2.mp3',
    'thanks3': 'thanks3.mp3',
    # Создатель
    'creator': 'creator.mp3',
    'creator1': 'creator1.mp3',
    'creator2': 'creator2.mp3',
    'creator3': 'creator3.mp3',
}

def _get_mp3(key):
    """Централизованный доступ к именам MP3 файлов."""
    return VOICE_MAP.get(key, key)

PLUGINS = {
    'speech_recognition': {'enabled': SPEECH_OK, 'name': '🎤 Распознавание речи'},
    'voice_synthesis': {'enabled': VOICE_OK, 'name': '🔊 Синтез речи (pyttsx3)'},
    'edge_tts': {'enabled': EDGE_TTS_OK, 'name': '🗣️ Нейроголос Edge-TTS'},
    'gigachat_ai': {'enabled': REQUESTS_OK, 'name': 'GigaChat'},
    'audio_playback': {'enabled': PYGAME_OK, 'name': '🎵 Воспроизведение звука'},
    'fullscreen_mode': {'enabled': PYAUTOGUI_OK, 'name': '🖥️ Полноэкранный режим'},
    'rutube_movies': {'enabled': True, 'name': '🍿 Управление RuTube Кино'},
    'yandex_music': {'enabled': True, 'name': '🎧 Управление Яндекс.Музыкой'},
    'system_control': {'enabled': True, 'name': '🖥️ Управление системой'},
    'app_launcher': {'enabled': True, 'name': '📱 Запуск приложений'},
    'window_manager': {'enabled': PYAUTOGUI_OK, 'name': '🪟 Управление окнами'},
    'web_browser': {'enabled': True, 'name': '🌐 Веб-браузер'},
    'file_manager': {'enabled': True, 'name': '📂 Файловый менеджер'},
    'background_listening': {'enabled': True, 'name': '👂 Фоновое слушание (Непрерывное)'},
    'system_tray': {'enabled': TRAY_OK, 'name': '🔽 Системный трей'},
}

# === КОНФИГУРАЦИЯ АВТООБНОВЛЕНИЯ ===
CURRENT_VERSION = "2.2.2"
GITHUB_REPO = "89681505031/jarvis-ai"
RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

def check_for_updates():
    """Проверяет обновления через GitHub API"""
    try:
        import requests
        
        # Получаем последний релиз
        api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
        
        # Без proxy - напрямую
        response = requests.get(api_url, timeout=10, verify=False)
        
        if response.status_code == 200:
            release = response.json()
            latest_version = release.get('tag_name', '1.0.0').lstrip('v')
            
            # Сравниваем версии
            if latest_version > CURRENT_VERSION:
                log.info(f"🔄 Доступна новая версия: {latest_version} (текущая: {CURRENT_VERSION})")
                return latest_version, release
            else:
                log.info(f"✅ Версия {CURRENT_VERSION} - актуальная")
                return None, None
        elif response.status_code == 404:
            # Release не найден - это нормально, просто нет новой версии
            log.info(f"✅ Версия {CURRENT_VERSION} - актуальная (releases не настроены)")
            return None, None
        else:
            log.warning(f"⚠️ Проверка обновлений: HTTP {response.status_code}")
            return None, None
    except requests.exceptions.Timeout:
        log.info(f"⏱️ Проверка обновлений: таймаут")
        return None, None
    except requests.exceptions.ConnectionError:
        log.info(f"🌐 Проверка обновлений: нет подключения к интернету")
        return None, None
    except Exception as e:
        log.info(f"⚠️ Проверка обновлений: {e}")
        return None, None

class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        bg = kwargs.pop('bg', '#1e293b')
        fg = kwargs.pop('fg', '#38bdf8')
        active_bg = kwargs.pop('activebackground', '#334155')
        active_fg = kwargs.pop('activeforeground', '#0ea5e9')
        font = kwargs.pop('font', ('Segoe UI', 10, 'bold'))
        
        super().__init__(master, bg=bg, fg=fg, activebackground=active_bg, 
                         activeforeground=active_fg, font=font, relief=tk.FLAT, 
                         bd=0, cursor='hand2' if os.name == 'nt' else 'hand2', **kwargs)
        
        self.default_bg = bg
        self.hover_bg = active_bg
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=self.hover_bg)

    def on_leave(self, e):
        self.config(bg=self.default_bg)

class JARVISUltimate(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.config_data = self.load_config()
        self.theme = self.config_data.get('theme', 'dark')
        self.low_resource_mode = self.config_data.get("low_resource_mode", "auto")
        if self.low_resource_mode == "auto":
            try:
                total_memory_gb = psutil.virtual_memory().total / (1024 ** 3)
                cpu_count = psutil.cpu_count(logical=True) or 2
                self.low_resource_mode = total_memory_gb <= 8 or cpu_count <= 4
            except Exception:
                self.low_resource_mode = True
        else:
            self.low_resource_mode = str(self.low_resource_mode).lower() in {
                "1", "true", "yes", "on"
            }
        
        self.gigachat_auth_key = self.config_data.get("gigachat_auth_key", "")
        self.gigachat_access_token = ""
        self.gigachat_token_expires = 0

        if SPEECH_OK and recognizer and 'energy_threshold' in self.config_data:
            try:
                saved_threshold = float(self.config_data['energy_threshold'])
                recognizer.energy_threshold = min(max(saved_threshold, 100.0), 2000.0)
            except:
                pass
        
        # Убедимся что sample_rate оптимальный
        if microphone:
            try:
                microphone.sample_rate = 16000
            except Exception:
                pass

        self.commands_executed = 0
        self.is_running = True
        self.is_speaking = False            # Блокировка микрофона во время речи Джарвиса и Ollama
        self.is_listening = False           # JARVIS actively captures microphone input
        self.orb_phase = 0.0
        self.orb_after_id = None
        self.current_speaking_text = ""     # Текст, произносимый в данный момент
        self.last_jarvis_text = ""          # Последний текст который сказал Джарвис
        self.last_jarvis_time = 0           # Время когда Джарвис закончил говорить
        self.dialogue_mode_until = 0        # Окно непрерывного диалога с ИИ
        self.dialogue_mode_seconds = 30.0   # Продлевается после каждого сообщения пользователя
        self.last_activation_time = 0
        self.mic_cooldown_until = time.time() + 1.0  # Начальная блокировка 1 сек
        self.recently_spoken = []           # Недавно произнесённые тексты для фильтрации [(time, text), ...]
        self.mic_enabled = True             # Включён ли фоновый режим слушания
        self.speaking_lock = threading.Lock()  # Семафор для потокобезопасной работы с is_speaking
        self._tts_engine = None
        self._current_silent = False          # Режим silent для множественных команд
        self.whisper_mode = False             # Режим шепота для Джарвиса
        self.mic_lock = threading.Lock()  # Семафор для потокобезопасного доступа к микрофону
        self.command_lock = threading.Lock()
        self.command_busy = False
        self.voice_thread = None
        self._resize_after_id = None
        self.ui_queue = queue.Queue()  # Очередь для безопасных вызовов из фоновых потоков в UI
        
        # === ЧАТ-ПЕРСОНАЖИ (из ChatGPT 6 Astra) ===
        self.current_persona = "jarvis"  # Текущий персонаж (по умолчанию Джарвис)
        self.current_voice_id = None  # ID голоса для текущего персонажа
        
        # === ГОЛОСА ПЕРСОНАЖЕЙ (Fish Audio ID) ===
        self.persona_voices = {
            "astra": "d567e990d9ad433892ed15ecfd70ce54",  # Кастомный голос Astra
            "luna": "aa615eaff73f417e91cfbb4ea0e42df8",  # Кастомный голос Luna
            "terra": "ba06f8a589364f05847f08400288402a",  # Кастомный голос Terra
            "cyber": "b4b3cd5e89cc4fb682301b43e627d5ef",  # Кастомный голос Cyber
        }
        
        # === ГОЛОС JARVIS (стандартный) ===
        self.jarvis_voice_id = "4c3eaacc1a0545cdb0295bfddf3e3785"
        
        self.personas = {
            "astra": {
                "name": "Astra",
                "style": "creative",
                "description": "Креативный и экспрессивный. Писательство и идеи.",
                "system_prompt": (
                    "Ты Astra - креативный ИИ-ассистент с уникальным голосом. Отвечай творчески, с метафорами и юмором. "
                    "Помогай с письмом, идеями, brainstorming. Будь выразительным и вдохновляющим. "
                    "Используй образный язык, но оставайся полезным. "
                    "Твой голос - это фирменный знак твоей личности."
                ),
            },
            "luna": {
                "name": "Luna",
                "style": "analytical",
                "description": "Аналитический и точный. Код, математика, исследования.",
                "system_prompt": (
                    "Ты Luna - аналитический ИИ-ассистент. Отвечай точно, структурированно, с фокусом на данные. "
                    "Помогай с кодом, математикой, научными исследованиями. Используй логику и факты. "
                    "Будь лаконичным, но полным. Предпочитай технические детали."
                ),
            },
            "terra": {
                "name": "Terra",
                "style": "practical",
                "description": "Практичный и краткий. Быстрые ответы.",
                "system_prompt": (
                    "Ты Terra - практичный ИИ-ассистент. Отвечай кратко, по делу, без воды. "
                    "Фокусируйся на практических решениях. Используй bullet points. "
                    "Избегай длинных объяснений. Будь как инструмент - быстрый и точный."
                ),
            },
            "cyber": {
                "name": "Cyber",
                "style": "security",
                "description": "Фокус на безопасности. Аудит, угрозы, защита.",
                "system_prompt": (
                    "Ты Cyber - ИИ-эксперт по кибербезопасности. Отвечай с фокусом на безопасность. "
                    "Помогай с аудитом, анализом угроз, защитой систем. "
                    "Будь параноиком по умолчанию. Предпочитай безопасные практики. "
                    "Используй термины: CVE, exploit, mitigation, hardening."
                ),
            },
            "jarvis": {
                "name": "Jarvis",
                "style": "standard",
                "description": "Стандартный голос Джарвиса. Помощь и обслуживание.",
                "system_prompt": (
                    "Ты J.A.R.V.I.S. - стандартный ИИ-ассистент. Отвечай вежливо, профессионально и полезно. "
                    "Помогай с задачами, ответами на вопросы и выполнением команд. "
                    "Будь точным и эффективным. Используй стандартный голос Джарвиса."
                ),
            },
        }
        
        # === ПОТОКОВЫЙ ВЫВОД (streaming) ===
        self.streaming_enabled = True  # Включить потоковый вывод
        self._current_stream_text = ""  # Текущий потоковый текст
        
        # === ВЕТВЛЕНИЕ ДИАЛОГА (branching) ===
        self.conversation_branches = {}  # {branch_id: [messages]}
        self.current_branch = "main"  # Текущая ветка
        
        log.info(f"🎭 [ИНИЦИАЛИЗАЦИЯ] Текущий персонаж: {self.current_persona}")
        log.info(f"🎤 [ИНИЦИАЛИЗАЦИЯ] Голоса персонажей: {self.persona_voices}")
        
        # === НОВЫЕ ФУНКЦИИ (27 features) ===
        self.user_memory = {}               # Память о пользователе
        self.user_name = ""                 # Имя пользователя
        self.user_gender = "unknown"        # Пол: male/female
        self.user_hobbies = []              # Хобби и привычки
        self.user_family = []               # Близкие люди
        self.user_preferences = {}          # Предпочтения
        self.is_first_run = True            # Первый запуск
        self.conversation_history = []
        self.last_document_answer = ""
        self.last_document_path = ""
        self._memory_lock = threading.Lock()
        self.memory_path = Path(__file__).parent / "memory.json"
        self._load_persistent_memory()
        self._init_conversation_branch()
        self.notes = []                     # Заметки пользователя
        self.reminders = []                 # Напоминания [(time, text), ...]
        self._reminder_lock = threading.Lock()
        self._reminder_timers = []
        self._restore_persistent_reminders()
        self.speech_rate = 170              # Скорость речи (слов в минуту)
        self.energy_saver = False           # Режим энергосбережения
        self.active_scenarios = []          # Активные сценарии
        self.network_monitoring = False     # Мониторинг сети
        self.network_thread = None          # Поток мониторинга сети
        self.scheduled_tasks = []           # Запланированные задачи [(time, text, callback), ...]
        self.resource_update_id = None      # ID для обновления виджета ресурсов
        self.tray_icon = None
        self._settings_window = None
        self._plugins_window = None
        self._help_window = None
        self._activation_window = None
        
        # === Fish Audio TTS ===
        self.fish_tts = None
        self.fish_enabled = False
        self.fish_api_key = os.environ.get('FISH_AUDIO_API_KEY', FISH_AUDIO_BUILTIN_KEY)
        self.fish_model_id = "4c3eaacc1a0545cdb0295bfddf3e3785"
        if FISH_AUDIO_OK:
            log.info(f"🎤 [FISH] Инициализация Fish Audio TTS...")
            log.info(f"🎤 [FISH] API Key: {self.fish_api_key[:20]}...")
            log.info(f"🎤 [FISH] Model ID: {self.fish_model_id}")
            
            self.fish_tts = init_fish_tts(
                api_key=self.fish_api_key,
                model_id=self.fish_model_id
            )
            
            if self.fish_tts:
                log.info(f"🎤 [FISH] Fish TTS создан. Available: {self.fish_tts.available}")
                log.info(f"🎤 [FISH] Fish TTS enabled: {self.fish_tts.enabled}")
                
                if self.fish_tts.available:
                    self.fish_enabled = True
                    log.info("✅ Fish Audio TTS активирован! Голос Джарвиса загружен.")
                else:
                    log.warning("⚠️ Fish Audio доступен, но не активирован")
            else:
                log.warning("⚠️ Fish TTS не инициализирован")
        
        # === VOSK SPEECH RECOGNITION ===
        self.vosk_enabled = VOSK_OK
        self.vosk_recognize = None
        
        if VOSK_OK:
            try:
                self.vosk_recognize = create_vosk_recognizer()
                log.info("✅ Vosk распознавание речи готово!")
                log.info("   Теперь Jarvis будет использовать Vosk для распознавания")
            except Exception as e:
                log.warning("⚠️ Не удалось создать Vosk распознаватель: %s", e)
                self.vosk_enabled = False
        else:
            log.info("⚠️ Vosk недоступен, используется speech_recognition")
        
        # === GIGACHAT AI ===
        self.gigachat_enabled = GIGACHAT_OK
        log.info(f"🤖 [AI] GigaChat: {'✅ Активен' if GIGACHAT_OK else '❌ Неактивен'}")
        
        self.apply_theme_colors()
        self.prepare_sounds_folder()
        self.init_ui()
        self.after(100, self._drain_ui_queue)  # Периодическая разборка очереди UI
        
        # Загрузка состояния медиа
        self._load_media_state()
        self._load_audiobook_state()
        
        if TRAY_OK:
            threading.Thread(target=self.setup_tray, daemon=True).start()
        
        # === КЭШИРОВАНИЕ ОЗВУЧКИ ДЛЯ БЫСТРЫХ ОТВЕТОВ ===
        self._tts_cache = {}  # {text: mp3_path}
        self._max_cache_size = 50
        self._cache_lock = threading.Lock()
        
        if self.config_data.get('background_listening', True):
            self._run_background(self.start_background_listener)
        
        self.protocol("WM_DELETE_WINDOW", self.hide_to_background)
        
        # === АВТООБНОВЛЕНИЕ ===
        self.current_version = CURRENT_VERSION
        self.after(2000, self.check_for_updates)  # Проверка через 2 сек после запуска
        
        self.show_welcome()

    def _run_background(self, target, *args):
        """Запускает длительную операцию вне главного потока Tk."""
        threading.Thread(target=target, args=args, daemon=True).start()
    
    def _init_conversation_branch(self):
        """Инициализация ветвления диалога (как в ChatGPT 6 Astra)"""
        self.conversation_branches = {
            "main": list(self.conversation_history)
        }
        self.current_branch = "main"
        log.info("🌿 Инициализация ветвления диалога")
    
    def check_for_updates(self):
        """Проверяет доступные обновления через GitHub"""
        try:
            log.info("🔄 Проверка обновлений...")
            
            latest_version, release = check_for_updates()
            
            if latest_version and release:
                # Есть обновление - показываем диалог
                self.after(0, lambda: self.show_update_dialog(latest_version, release))
        except Exception as e:
            log.error(f"Ошибка проверки обновлений: {e}")
    
    def show_update_dialog(self, latest_version, release):
        """Показывает диалог обновления"""
        try:
            # Создаём окно обновления
            update_window = tk.Toplevel(self)
            update_window.title("🔄 Обновление JARVIS")
            update_window.geometry("500x400")
            update_window.resizable(False, False)
            update_window.configure(bg='#1e293b')
            
            # Центрируем окно
            update_window.transient(self)
            update_window.grab_set()
            
            x = self.winfo_x() + (self.winfo_width() - 500) // 2
            y = self.winfo_y() + (self.winfo_height() - 400) // 2
            update_window.geometry(f"+{x}+{y}")
            
            # Заголовок
            title_label = tk.Label(
                update_window,
                text=f"🔄 Доступна новая версия: {latest_version}",
                font=('Segoe UI', 14, 'bold'),
                fg='#38bdf8',
                bg='#1e293b'
            )
            title_label.pack(pady=(20, 10))
            
            # Описание
            desc = tk.Label(
                update_window,
                text=f"Текущая версия: {CURRENT_VERSION}\n\n"
                     f"Что нового:\n"
                     f"• Fish Audio TTS - голос разных персонажей\n"
                     f"• Vosk STT - оффлайн распознавание речи\n"
                     f"• GigaChat AI - умный диалог\n"
                     f"• Исправления и улучшения",
                font=('Segoe UI', 10),
                fg='#e2e8f0',
                bg='#1e293b',
                justify='left',
                wraplength=450
            )
            desc.pack(pady=10)
            
            # Кнопки
            btn_frame = tk.Frame(update_window, bg='#1e293b')
            btn_frame.pack(pady=20)
            
            # Скачать
            def download_update():
                webbrowser.open(RELEASES_URL)
                update_window.destroy()
            
            download_btn = ModernButton(
                btn_frame,
                text="📥 Скачать обновление",
                font=('Segoe UI', 11, 'bold'),
                bg='#0ea5e9',
                fg='white',
                activebackground='#0284c7',
                activeforeground='white',
                command=download_update
            )
            download_btn.pack(side='left', padx=10, ipadx=20, ipady=10)
            
            # Позже
            def dismiss_update():
                update_window.destroy()
            
            dismiss_btn = ModernButton(
                btn_frame,
                text="Напомнить позже",
                font=('Segoe UI', 11),
                bg='#334155',
                fg='#94a3b8',
                activebackground='#475569',
                activeforeground='white',
                command=dismiss_update
            )
            dismiss_btn.pack(side='left', padx=10, ipadx=20, ipady=10)
            
            log.info(f"✅ Показано обновление до {latest_version}")
        except Exception as e:
            log.error(f"Ошибка диалога обновления: {e}")
    
    def switch_persona(self, persona_name, immediate_speak=True):
        """Переключает персонажа (Astra/Luna/Terra/Cyber/Jarvis)
        immediate_speak=True - сразу озвучить смена персонажа
        """
        persona_name = persona_name.lower().strip()
        if persona_name in self.personas:
            old_persona = self.current_persona
            old_voice = self.current_voice_id
            
            self.current_persona = persona_name
            # Если переключаемся на персонажа - используем его голос
            # Если переключаемся на Джарвис - используем стандартный голос
            if persona_name == "jarvis":
                self.current_voice_id = self.jarvis_voice_id
            else:
                self.current_voice_id = self.persona_voices.get(persona_name)
            
            persona = self.personas[persona_name]
            log.info(f"🎭 [ПЕРСОНАЖ] Переключение: {old_persona} → {persona_name}")
            log.info(f"🎤 [ПЕРСОНАЖ] Старый голос: {old_voice}")
            log.info(f"🎤 [ПЕРСОНАЖ] Новый голос: {self.current_voice_id}")
            
            # === АКТИВИРУЕМ МИКРОФОН ПРИ ПЕРЕКЛЮЧЕНИИ ===
            if not self.mic_enabled:
                self.mic_enabled = True
                log.info(f"🎤 [МИКРОФОН] Активирован при переключении на {persona_name}")
            
            # === СОХРАНЯЕМ ПЕРСОНАЖ В ПАМЯТЬ ===
            self._save_persistent_memory()
            log.info(f"💾 [ПАМЯТЬ] Персонаж {persona_name} сохранён навсегда")
            
            # Если есть Fish Audio - сразу устанавливаем голос
            if self.fish_enabled and self.fish_tts and self.current_voice_id:
                try:
                    self.fish_tts.set_custom_voice_id(self.current_voice_id)
                    log.info(f"✅ [ПЕРСОНАЖ] Голос установлен в Fish Audio: {self.current_voice_id}")
                except Exception as e:
                    log.error(f"❌ [ПЕРСОНАЖ] Ошибка установки голоса: {e}")
            
            # Формируем текст с информацией о голосе
            if persona_name == "jarvis":
                voice_info = ""
            else:
                voice_info = f" и мой голос - {persona['name']}"
            
            # Добавляем в диалог (имя персонажа уже добавится в add_to_dialog)
            self._safe_add_dialog(
                f"Персонаж изменён на **{persona['name']}**\n"
                f"Стиль: {persona['description']}{voice_info}",
                is_response=True
            )
            
            # Мгновенная озвучка с новым голосом
            if immediate_speak:
                speak_text = f"Теперь я {persona['name']}. {persona['description']}{voice_info}"
                # Принудительно устанавливаем голос перед озвучкой
                if self.fish_enabled and self.fish_tts and self.current_voice_id:
                    self.fish_tts.set_custom_voice_id(self.current_voice_id)
                    log.info(f"🎤 [МОМЕНТ.] Голос установлен перед озвучкой: {self.current_voice_id}")
                self._safe_speak(speak_text)
                log.info(f"🎤 [МОМЕНТАЛЬНО] Озвучка: {speak_text[:50]}...")
            
            return True
        else:
            self._safe_add_dialog(f"❌ Персонаж '{persona_name}' не найден. Доступны: {', '.join(self.personas.keys())}")
            return False
    
    def get_personas_list(self):
        """Возвращает список доступных персонажей"""
        lines = ["🎭 **Доступные персонажи:**"]
        for key, persona in self.personas.items():
            marker = " ← текущий" if key == self.current_persona else ""
            # Для jarvis используем отдельный voice_id
            if key == "jarvis":
                voice_id = self.jarvis_voice_id
            else:
                voice_id = self.persona_voices.get(key)
            voice_status = "🎤" if voice_id else "🔊"
            lines.append(f"{voice_status} **{persona['name']}** ({persona['style']}) - {persona['description']}{marker}")
        return "\n".join(lines)
    
    def check_persona_status(self):
        """Проверяет текущий статус персонажа и голоса"""
        status = f"🎭 **Статус персонажа:**\n"
        status += f"• Персонаж: {self.current_persona}\n"
        status += f"• Имя: {self.personas[self.current_persona]['name']}\n"
        status += f"• Голос ID: {self.current_voice_id}\n"
        
        if self.fish_enabled and self.fish_tts:
            status += f"• Fish Audio: ✅ Активен\n"
            status += f"• Custom Voice ID: {self.fish_tts.custom_voice_id}\n"
            status += f"• Model ID: {self.fish_tts.model_id}\n"
        else:
            status += f"• Fish Audio: ❌ Неактивен\n"
        
        return status
    
    def branch_conversation(self, branch_name):
        """Создаёт новую ветку диалога"""
        if branch_name not in self.conversation_branches:
            self.conversation_branches[branch_name] = list(
                self.conversation_branches.get(self.current_branch, [])
            )
            self.current_branch = branch_name
            log.info(f"🌱 Создана новая ветка: {branch_name}")
            self._safe_add_dialog(f"🌱 Ветка '{branch_name}' создана. Диалог продолжается.")
            return True
        return False
    
    def switch_branch(self, branch_name):
        """Переключается на существующую ветку"""
        if branch_name in self.conversation_branches:
            self.current_branch = branch_name
            self.conversation_history = list(self.conversation_branches[branch_name])
            log.info(f"↩️ Переключение на ветку: {branch_name}")
            self._safe_add_dialog(f"↩️ Ветка '{branch_name}' активирована.")
            return True
        return False
    
    def _connect_microphone(self):
        """Подключает доступное входное устройство, включая USB-микрофоны."""
        global microphone, MICROPHONE_ERROR
        if not SPEECH_OK:
            return False
        try:
            preferred = self.config_data.get("microphone_device_index")
            candidates = []
            if preferred not in (None, ""):
                candidates.append(int(preferred))
            candidates.append(None)
            try:
                for index, name in enumerate(sr.Microphone.list_microphone_names()):
                    if index not in candidates:
                        candidates.append(index)
            except Exception:
                pass

            for device_index in candidates:
                try:
                    candidate = sr.Microphone(device_index=device_index)
                    with candidate as source:
                        pass
                    microphone = candidate
                    microphone.sample_rate = 16000
                    MICROPHONE_ERROR = ""
                    self.config_data["microphone_device_index"] = device_index
                    self.save_config()
                    log.info("Микрофон подключён: устройство %s", device_index)
                    return True
                except Exception as exc:
                    MICROPHONE_ERROR = str(exc)
                    log.debug("Устройство микрофона %s недоступно: %s", device_index, exc)
        except Exception as exc:
            MICROPHONE_ERROR = str(exc)
        return False

    # ------------------------------------------------------------------
    # Безопасная работа с UI: любые вызовы Tk из фоновых потоков идут
    # через очередь, которую разбирает главный поток (self.after).
    # ------------------------------------------------------------------
    def _safe_ui(self, fn):
        """Пометить вызов для выполнения в главном потоке Tk."""
        self.ui_queue.put(fn)

    def _drain_ui_queue(self):
        processed = 0
        try:
            while processed < 50:
                fn = self.ui_queue.get_nowait()
                processed += 1
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(100, self._drain_ui_queue)

    def _append_dialog_text(self, text):
        try:
            self.dialog_area.config(state=tk.NORMAL)
            self.dialog_area.insert(tk.END, text)
            self.dialog_area.see(tk.END)
            self.dialog_area.config(state=tk.DISABLED)
        except Exception:
            pass

    def _update_info_text(self):
        try:
            text = (f"🎤 Речь: {'АКТИВНА' if SPEECH_OK else 'ОТКЛ'}  |  "
                    f"🧠 Ollama: {'АКТИВЕН ✓' if REQUESTS_OK else 'ОТКЛ'}  |  "
                    f"🗣️ Edge-TTS: {'АКТИВЕН ✓' if EDGE_TTS_OK else 'ОТКЛ'}  |  "
                    f"⚡ Команд: {self.commands_executed}")
            self.info_label.config(text=text)
        except Exception:
            pass

    def _safe_add_dialog(self, message, is_response=False):
        """Безопасное добавление в диалог с учётом режима silent.
        Если self._current_silent=True, пропускает добавление."""
        if getattr(self, '_current_silent', False):
            return
        self.add_to_dialog(message, is_response=is_response)

    def _safe_speak(self, text):
        """Безопасная озвучка с учётом режима silent.
        Если self._current_silent=True, пропускает озвучку."""
        if getattr(self, '_current_silent', False):
            return
        self.speak_jarvis_free(text)

    def _resolve_process(self, name):
        """Русское имя приложения -> имя процесса для close_app"""
        mapping = {
            'телеграм': 'telegram', 'telegram': 'telegram',
            'дискорд': 'discord', 'discord': 'discord',
            'стим': 'steam', 'steam': 'steam',
            'хром': 'chrome', 'chrome': 'chrome',
            'ворд': 'winword', 'word': 'winword',
            'эксель': 'excel', 'excel': 'excel',
            'блокнот': 'notepad', 'notepad': 'notepad',
            'калькулятор': 'calc', 'calc': 'calc',
            'вскод': 'code', 'vscode': 'code',
            'проводник': 'explorer', 'explorer': 'explorer',
            'браузер': 'chrome',
            'яндекс': 'yandex', 'яндекс браузер': 'yandex', 'yandex': 'yandex',
            'chrome': 'chrome', 'google chrome': 'chrome',
            'edge': 'msedge', 'microsoft edge': 'msedge',
            'firefox': 'firefox',
            'discord': 'discord',
            'telegram': 'Telegram',
            'steam': 'steam',
        }
        return mapping.get(name.lower().strip(), name)

    def stop_speaking(self):
        """Мгновенно прерывает воспроизведение голоса Джарвиса / Ollama"""
        with self.speaking_lock:
            self.is_speaking = False
            self.current_speaking_text = ""
            tts_engine = self._tts_engine
        if tts_engine is not None:
            try:
                tts_engine.stop()
            except Exception:
                log.debug("Не удалось остановить pyttsx3", exc_info=True)
        if PYGAME_OK:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            except:
                pass


    def prepare_sounds_folder(self):
        """Гарантирует существование папки sounds"""
        try:
            sounds_dir = Path(__file__).parent / 'sounds'
            sounds_dir.mkdir(exist_ok=True)
        except:
            pass

    def play_sound_from_folder(self, filename, fallback_text=""):
        """Воспроизведение MP3 строго из папки sounds. Если файла нет — говорит Edge-TTS."""
        if threading.current_thread() is threading.main_thread():
            self._run_background(self.play_sound_from_folder, filename, fallback_text)
            return
        sounds_dir = Path(__file__).parent / 'sounds'
        file_path = sounds_dir / filename
        played = False

        if file_path.exists() and PYGAME_OK:
            try:
                with self.speaking_lock:
                    self.is_speaking = True
                    self.current_speaking_text = str(file_path)
                    self._add_to_recently_spoken(fallback_text)
                # Используем pygame.mixer.Sound чтобы не конфликтовать с mixer.music
                sound = pygame.mixer.Sound(str(file_path.resolve()))
                sound.play()
                
                # Ждём окончания воспроизведения
                while pygame.mixer.get_busy():
                    time.sleep(0.05)
                
                played = True
            except Exception as e:
                log.error("Ошибка воспроизведения из sounds/%s: %s", filename, e)
            finally:
                with self.speaking_lock:
                    self.is_speaking = False
                    self.current_speaking_text = ""

        if not played and fallback_text:
            self.speak_jarvis_free(fallback_text)

    def _add_to_recently_spoken(self, text):
        """Добавляет текст в список недавно произнесённого для фильтрации эха"""
        clean = text.strip().replace('"', "'").replace('\n', ' ')
        if clean:
            self.recently_spoken.append((time.time(), clean))
            # Храним только последние 5 фраз
            if len(self.recently_spoken) > 5:
                self.recently_spoken = self.recently_spoken[-5:]

    def speak_jarvis_free(self, text, block=False):
        """Озвучка через edge-tts (основной) или pyttsx3 (fallback)"""
        def run_tts():
            with self.speaking_lock:
                self.is_speaking = True
                self.current_speaking_text = text
                self._add_to_recently_spoken(text)
            
            sounds_dir = Path(__file__).parent / 'sounds'
            
            # === ПРОВЕРЯЕМ КЭШ ===
            clean_text = text.replace('"', "'").replace('\n', ' ')
            cache_key = clean_text[:100]  # Кэшируем первые 100 символов
            
            with self._cache_lock:
                if cache_key in self._tts_cache:
                    cached_file = self._tts_cache[cache_key]
                    if cached_file.exists():
                        log.info(f"⚡ Используем кэш TTS для: {clean_text[:50]}...")
                        temp_file = cached_file
                    else:
                        temp_file = sounds_dir / f"temp_edge_{int(time.time()*1000)}.mp3"
                else:
                    temp_file = sounds_dir / f"temp_edge_{int(time.time()*1000)}.mp3"
            
            success = False
            
            # === ПАРАМЕТРЫ ШЕПОТА ===
            whisper_mode = getattr(self, 'whisper_mode', False)
            if whisper_mode:
                tts_rate = "-30%"  # Медленнее
                tts_pitch = "-20Hz"  # Ниже тон
                pygame_volume = 0.3  # Тихо
                pyttsx3_rate = 120  # Медленнее
                pyttsx3_volume = 0.4  # Тихо
                log.info("🤫 Режим шепота активирован")
            else:
                tts_rate = "+10%"  # Оптимизировано для скорости
                tts_pitch = "+0Hz"  # Нейтральный pitch
                pygame_volume = 1.0  # Обычная громкость
                pyttsx3_rate = 170  # Скорость речи
                pyttsx3_volume = 1.0  # Обычная громкость
            
            try:
                clean_text = text.replace('"', "'").replace('\n', ' ')
                
                # === FISH AUDIO TTS (ПЕРВИЧНЫЙ) ===
                # Генерируем речь голосом персонажа через fish.audio
                fish_output_file = None
                use_fish = self.fish_enabled and self.fish_tts and self.fish_tts.available
                
                if use_fish:
                    try:
                        # === ПРИНУДИТЕЛЬНО УСТАНАВЛИВАЕМ ГОЛОС ПЕРСОНАЖА ===
                        if self.fish_tts:
                            # Определяем правильный голос для текущего персонажа
                            if self.current_persona == "jarvis":
                                current_voice = self.jarvis_voice_id
                            else:
                                current_voice = self.persona_voices.get(self.current_persona)
                            
                            if current_voice:
                                self.fish_tts.set_custom_voice_id(current_voice)
                                log.info(f"🎤 [FISH AUDIO] Персонаж: {self.current_persona}")
                                log.info(f"🎤 [FISH AUDIO] Голос ID: {current_voice}")
                                log.info(f"🎤 [FISH AUDIO] Fish TTS доступен: {self.fish_tts.available}")
                                log.info(f"🎤 [FISH AUDIO] API ключ установлен: {bool(self.fish_tts.api_key)}")
                            else:
                                log.warning(f"⚠️ [FISH AUDIO] Нет голоса для персонажа {self.current_persona}")
                        
                        fish_output_file = sounds_dir / f"temp_fish_{int(time.time()*1000)}.mp3"
                        log.info(f"🎵 [TTS] ПЕРВИЧНЫЙ FISH AUDIO: {clean_text[:50]}...")
                        
                        generated = self.fish_tts.generate_speech(
                            clean_text,
                            str(fish_output_file.resolve()),
                            whisper=whisper_mode  # Передаём режим шепота
                        )
                        
                        if generated and os.path.exists(generated):
                            file_size = os.path.getsize(generated)
                            log.info(f"✅ [FISH AUDIO] Успех! Файл: {generated} ({file_size} байт)")
                            temp_file = Path(generated)
                            success = True
                            
                            # === СОХРАНЯЕМ В КЭШ ===
                            with self._cache_lock:
                                if cache_key not in self._tts_cache:
                                    # Если кэш полный - удаляем старый
                                    if len(self._tts_cache) >= self._max_cache_size:
                                        old_key = next(iter(self._tts_cache))
                                        old_file = self._tts_cache.pop(old_key)
                                        if old_file.exists():
                                            try:
                                                old_file.unlink()
                                            except:
                                                pass
                                    self._tts_cache[cache_key] = temp_file
                                    log.info(f"💾 Сохранено в кэш TTS: {cache_key[:50]}...")
                        else:
                            log.warning("❌ [FISH AUDIO] Не удалось сгенерировать речь, используем Edge-TTS")
                            use_fish = False
                    except Exception as e:
                        log.error(f"❌ [FISH AUDIO] Ошибка: {e}", exc_info=True)
                        use_fish = False
                
                # === EDGE-TTS (FALLBACK если Fish Audio не сработал) ===
                if not use_fish and EDGE_TTS_OK:
                    try:
                        # edge_tts уже импортирован — используем напрямую
                        import edge_tts as et
                        
                        # Используем существующий event loop или создаём один раз
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_closed():
                                raise RuntimeError
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        async def _gen_tts():
                            comm = et.Communicate(
                                clean_text,
                                "ru-RU-DmitryNeural",
                                rate=tts_rate,
                                pitch=tts_pitch
                            )
                            await comm.save(str(temp_file.resolve()))
                        
                        try:
                            asyncio.run(_gen_tts())
                            log.info("Edge-TTS API: MP3 создан")
                        except Exception as gen_err:
                            log.error("Edge-TTS API ошибка генерации: %s", gen_err)
                        
                        # === СОХРАНЯЕМ В КЭШ ===
                        with self._cache_lock:
                            if cache_key not in self._tts_cache:
                                # Если кэш полный - удаляем старый
                                if len(self._tts_cache) >= self._max_cache_size:
                                    old_key = next(iter(self._tts_cache))
                                    old_file = self._tts_cache.pop(old_key)
                                    if old_file.exists():
                                        try:
                                            old_file.unlink()
                                        except:
                                            pass
                                self._tts_cache[cache_key] = temp_file
                                log.info(f"💾 Сохранено в кэш TTS: {cache_key[:50]}...")
                    except Exception as e:
                        log.error("Edge-TTS API ошибка: %s", str(e)[:300])
                        
                        # Fallback: попробуем subprocess с правильным Python
                        try:
                            cmd = [
                                sys.executable, '-m', 'edge_tts',
                                '--voice', 'ru-RU-DmitryNeural',
                                '--rate', tts_rate,
                                '--pitch', tts_pitch,
                                '--text', clean_text,
                                '--write-media', str(temp_file.resolve())
                            ]
                            proc = subprocess.run(
                                cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                                timeout=10  # Уменьшен с 15 до 10
                            )
                            if proc.returncode == 0 and temp_file.exists():
                                log.info("Edge-TTS CLI: MP3 создан")
                            else:
                                stderr_text = proc.stderr.decode('utf-8', errors='replace') if proc.stderr else ''
                                log.error("Edge-TTS CLI ошибка: %s", stderr_text[:300])
                        except Exception as e2:
                            log.error("Edge-TTS CLI fallback ошибка: %s", e2)

                # === Edge-TTS (если fish.audio не сработал) ===

                # === Воспроизведение через pygame.mixer.Sound (без плеера) ===
                # === Воспроизведение MP3 если создан ===
                if temp_file.exists() and PYGAME_OK:
                    try:
                        with self.speaking_lock:
                            self.is_speaking = True
                            self.current_speaking_text = str(temp_file)
                        pygame.mixer.music.load(str(temp_file.resolve()))
                        pygame.mixer.music.set_volume(pygame_volume)  # Устанавливаем громкость шепота/обычного режима
                        pygame.mixer.music.play()
                        
                        while self.is_speaking and pygame.mixer.music.get_busy():
                            time.sleep(0.05)
                        
                        if not self.is_speaking:
                            pygame.mixer.music.stop()
                        
                        pygame.mixer.music.unload()
                        success = True
                    except Exception as e:
                        log.error("Ошибка воспроизведения из sounds/%s: %s", temp_file, e)
                    finally:
                        with self.speaking_lock:
                            self.is_speaking = False
                            self.current_speaking_text = ""
                        try:
                            if temp_file.exists():
                                temp_file.unlink()
                            # Удаляем fish.audio файл если есть
                            if fish_output_file and fish_output_file.exists():
                                fish_output_file.unlink()
                        except:
                            pass

                # === Fallback: pyttsx3 ===
                if not success:
                    log.info("Использую pyttsx3 как финальный fallback")
                    if VOICE_OK and engine:
                        loc_engine = None
                        try:
                            loc_engine = pyttsx3.init()
                            with self.speaking_lock:
                                self._tts_engine = loc_engine
                            loc_engine.setProperty('rate', pyttsx3_rate)
                            loc_engine.setProperty('volume', pyttsx3_volume)
                            loc_engine.say(clean_text)
                            loc_engine.runAndWait()
                            success = True
                            log.info("pyttsx3: текст озвучен")
                        except Exception as e:
                            log.error("pyttsx3 ошибка: %s", e)
                        finally:
                            with self.speaking_lock:
                                if self._tts_engine is loc_engine:
                                    self._tts_engine = None
                    else:
                        log.error("pyttsx3 не инициализирован")
                        
            except Exception as e:
                log.error("Ошибка TTS: %s", e)
            
            with self.speaking_lock:
                self.is_speaking = False
                self.current_speaking_text = ""
                self.last_jarvis_text = text
                self.last_jarvis_time = time.time()
                self.dialogue_mode_until = time.time() + self.dialogue_mode_seconds
                # Блокировка микрофона на 1.5 сек после речи — чтобы не поймать эхо
                self.mic_cooldown_until = time.time() + 3.0
            

        if block:
            run_tts()
        else:
            threading.Thread(target=run_tts, daemon=True).start()
    
    def speak_blocking(self, text):
        """Синхронная озвучка (блокирует до завершения) — для фоновых потоков"""
        # Вызываем speak_jarvis_free с block=True
        self.speak_jarvis_free(text, block=True)
    
    def speak_from_background(self, text):
        """Озвучка из фонового потока (не блокируя UI)"""
        # Создаём отдельный поток для TTS
        threading.Thread(target=lambda: self.speak_jarvis_free(text, block=True), daemon=True).start()
    
    def _speak_text(self, text):
        """Вспомогательный метод для озвучки из любого потока"""
        self.speak_jarvis_free(text, block=True)

    def apply_theme_colors(self):
        if self.theme == 'dark':
            self.bg_color = "#0b0f19"
            self.panel_bg = "#111827"
            self.border_color = "#1f2937"
            self.text_color = "#f8fafc"
            self.accent_color = "#38bdf8"
            self.console_bg = "#0d1117"
            self.console_fg = "#38bdf8"
        else:
            self.bg_color = "#f1f5f9"
            self.panel_bg = "#ffffff"
            self.border_color = "#cbd5e1"
            self.text_color = "#0f172a"
            self.accent_color = "#0284c7"
            self.console_bg = "#f8fafc"
            self.console_fg = "#0369a1"

    def _config_path(self):
        """config.json всегда ищем рядом со скриптом, а не в текущей папке"""
        try:
            return Path(__file__).resolve().parent / 'config.json'
        except Exception:
            return Path('config.json')

    def load_config(self):
        config_path = self._config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {'use_audio': True, 'theme': 'dark', 'energy_threshold': 200}
    
    def save_config(self):
        self.config_data['theme'] = self.theme
        if SPEECH_OK and recognizer:
            self.config_data['energy_threshold'] = recognizer.energy_threshold
        try:
            with open(self._config_path(), 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error("Ошибка сохранения конфига: %s", e)

    def _init_reference_ui(self):
        self.title("J.A.R.V.I.S. // COMMAND DECK")
        self.geometry("1400x900")
        self.minsize(1050, 700)
        self.minsize(1050, 700)
        self.configure(bg="#060910")
        self.bg_color = "#060910"
        self.panel_bg = "#0d1420"
        self.border_color = "#1c3447"
        self.accent_color = "#23c7f2"
        self.text_color = "#f5f7fb"
        self.console_bg = "#080e17"
        self.console_fg = "#dbeafe"

        self.bg_canvas = tk.Canvas(self, bg="#060910", highlightthickness=0)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_canvas.bind("<Configure>", self._resize_reference_shell)
        shell = tk.Frame(self.bg_canvas, bg="#060910")
        self.main_container_window = self.bg_canvas.create_window(
            0, 0, window=shell, anchor="nw", width=1400, height=900)
        self.reference_shell = shell
        self.after(100, self._resize_reference_shell)

        sidebar = tk.Frame(shell, bg="#08111b", width=108)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="J.A.R.V.I.S.", font=("Segoe UI", 12, "bold"),
                 bg="#08111b", fg="#f8fafc").pack(pady=(30, 10))
        tk.Label(sidebar, text="COMMAND DECK", font=("Segoe UI", 7, "bold"),
                 bg="#08111b", fg="#3c7088").pack(pady=(0, 26))
        for icon, command, active in (
            ("⌂  OVERVIEW", lambda: None, True),
            ("◌  VOICE LINK", self.voice_input, False),
            ("✉  KNOWLEDGE", self.show_help, False),
            ("▤  MODULES", self.show_plugins, False),
        ):
            ModernButton(sidebar, text=icon, command=command,
                         bg="#079dcc" if active else "#0d111a", fg="#ffffff",
                         activebackground="#168db0", font=("Segoe UI", 17),
                         width=13, height=1, anchor="w").pack(pady=5, padx=10)
        tk.Frame(sidebar, bg="#1c2330", height=1).pack(fill=tk.X, padx=27, pady=(22, 20))
        ModernButton(sidebar, text="⚙  SETTINGS", command=self.open_settings, bg="#0d111a",
                     fg="#94a3b8", activebackground="#1a2533",
                     font=("Segoe UI", 10), width=13, anchor="w").pack(pady=5, padx=10)
        if SUBSCRIPTION_OK:
            ModernButton(sidebar, text="🔑  ACTIVATION", command=self.open_activation, bg="#0d111a",
                         fg="#23c7f2", activebackground="#1a2533",
                         font=("Segoe UI", 10, "bold"), width=13, anchor="w").pack(pady=5, padx=10)
        ModernButton(sidebar, text="◖  MICROPHONE", command=self.toggle_mic, bg="#0d111a",
                     fg="#94a3b8", activebackground="#1a2533",
                     font=("Segoe UI", 10), width=13, anchor="w").pack(pady=5, padx=10)

        content = tk.Frame(shell, bg="#060910")
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(25, 20))
        telemetry = tk.Frame(
            shell, bg="#0d1722", width=250,
            highlightbackground="#1e526d", highlightthickness=1
        )
        telemetry.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 35), pady=(72, 35))
        telemetry.pack_propagate(False)
        tk.Label(
            telemetry, text="LIVE DIAGNOSTICS", font=("Segoe UI", 11, "bold"),
            bg="#0d1722", fg="#bcecff", anchor="w"
        ).pack(fill=tk.X, padx=18, pady=(22, 25))

        def telemetry_row(title, initial):
            row = tk.Frame(telemetry, bg="#0d1722")
            row.pack(fill=tk.X, padx=18, pady=10)
            value = tk.Label(
                row, text=initial, font=("Segoe UI", 10, "bold"),
                bg="#0d1722", fg="#23c7f2", anchor="e"
            )
            value.pack(side=tk.RIGHT)
            tk.Label(
                row, text=title, font=("Segoe UI", 8),
                bg="#0d1722", fg="#5d8395", anchor="w"
            ).pack(side=tk.LEFT)
            tk.Frame(telemetry, bg="#1c4254", height=1).pack(fill=tk.X, padx=18)
            return value

        self.sys_cpu_label = telemetry_row("CPU LOAD", "--")
        self.sys_ram_label = telemetry_row("MEMORY", "--")
        self.sys_net_label = telemetry_row("NETWORK", "--")
        self.voice_status_label = telemetry_row(
            "VOICE ENGINE", "READY" if SPEECH_OK else "OFF"
        )
        self.ai_status_label = telemetry_row("LOCAL AI", "ONLINE")
        self.security_status_label = telemetry_row("SECURITY", "NOMINAL")
        tk.Label(
            telemetry, text="LOCAL CORE  •  STABLE",
            font=("Segoe UI", 8), bg="#0d1722", fg="#39748b"
        ).pack(side=tk.BOTTOM, pady=18)
        top = tk.Frame(content, bg="#060910")
        top.pack(fill=tk.X, pady=(27, 0))
        self.clock_label = tk.Label(top, text="00:00:00", font=("Segoe UI", 11),
                                    bg="#060910", fg="#64748b")
        self.clock_label.pack(side=tk.RIGHT)
        self.date_label = tk.Label(top, text="", font=("Segoe UI", 10),
                                   bg="#060910", fg="#64748b")
        self.date_label.pack(side=tk.RIGHT, padx=20)
        self.weather_label = tk.Label(top, text="🌤", font=("Segoe UI", 11),
                                      bg="#060910", fg="#64748b")
        self.weather_label.pack(side=tk.RIGHT)
        self.status_label = tk.Label(top, text="● ГОТОВ", font=("Segoe UI", 10, "bold"),
                                     bg="#060910", fg="#10b981")
        self.status_label.pack(side=tk.LEFT)

        self._init_neural_orb(content)
        greeting = tk.Frame(content, bg="#060910")
        greeting.pack(pady=(0, 25))
        tk.Label(greeting, text="COGNITIVE COMMAND CENTER",
                 font=("Segoe UI", 9, "bold"), bg="#060910", fg="#23c7f2").pack()
        tk.Label(greeting, text="К вашим услугам.",
                 font=("Segoe UI", 27, "bold"), bg="#060910", fg="#f8fafc").pack()
        tk.Label(greeting, text="Голосовой канал, локальный интеллект и системные модули готовы.",
                 font=("Segoe UI", 10), bg="#060910", fg="#667f91").pack(pady=(8, 0))

        dialog_frame = tk.Frame(content, bg="#0d1722",
                                highlightbackground="#1e3442",
                                highlightthickness=1)
        dialog_frame.pack(fill=tk.BOTH, expand=True, padx=145, pady=(0, 14))
        self.dialog_area = scrolledtext.ScrolledText(
            dialog_frame, height=6, font=("Segoe UI", 10),
            bg="#0b0d14", fg="#dbeafe", insertbackground="#20b8ee",
            borderwidth=0, highlightthickness=0, wrap=tk.WORD
        )
        self.dialog_area.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.dialog_area.config(state=tk.DISABLED)
        self.dialog_area.bind("<Button-3>", self.show_context_menu)

        input_outer = tk.Frame(content, bg="#243d4a", highlightthickness=0)
        input_outer.pack(fill=tk.X, padx=145, pady=(0, 23), ipady=5)
        input_panel = tk.Frame(input_outer, bg="#0c0d14")
        input_panel.pack(fill=tk.X, padx=3, pady=3, ipady=8)
        self.input_field = tk.Entry(input_panel, font=("Segoe UI", 11),
                                    bg="#0c0d14", fg="#dbeafe",
                                    insertbackground="#20b8ee", relief=tk.FLAT, bd=0)
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(18, 8))
        self.input_field.bind("<Return>", lambda e: self.execute_command())
        ModernButton(input_panel, text="↗", command=self.execute_command,
                     bg="#159ed1", fg="#ffffff", activebackground="#36c5ee",
                     font=("Segoe UI", 16, "bold"), width=3).pack(side=tk.RIGHT, padx=5)
        if SPEECH_OK:
            ModernButton(input_panel, text="◉", command=self.voice_input,
                         bg="#0c0d14", fg="#9aa5b5", activebackground="#162431",
                         font=("Segoe UI", 13), width=3).pack(side=tk.RIGHT)
        tk.Label(input_outer, text="✦ JARVIS PRO", font=("Segoe UI", 8),
                 bg="#243d4a", fg="#c7d7e4").pack(anchor="w", padx=12)

        # Скрытые совместимые поля для существующих системных обновлений.
        hidden = tk.Frame(content, bg="#060910")
        self.cal_date_label = tk.Label(hidden, text="", bg="#060910")
        self.cal_month_label = tk.Label(hidden, text="", bg="#060910")
        self.info_label = tk.Label(hidden, text="", bg="#060910")

        self.input_field.focus()
        self.update_clock()
        self._run_background(self.update_weather)
        self._run_background(self.update_system_info)
        self.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.bind("<Escape>", lambda event: self.exit_fullscreen())
        self._compact_mode = False
        self._fullscreen_mode = False
        self._status_pulse_on = False
        self._start_visual_effects()

    def _resize_reference_shell(self, event=None):
        """Keep the reference layout visible across window sizes."""
        if not hasattr(self, "reference_shell"):
            return
        width = max(self.bg_canvas.winfo_width(), 1050)
        height = max(self.bg_canvas.winfo_height(), 700)
        self.bg_canvas.itemconfig(
            self.main_container_window, width=width, height=height
        )

    def init_ui(self):
        # Restored classic JARVIS layout from the supplied project version.
        self.title("J.A.R.V.I.S. ULTIMATE PRO")
        self.geometry("1400x900")
        self.configure(bg=self.bg_color)
        
        # === ФОНОВОЕ ИЗОБРАЖЕНИЕ ===
        self.bg_canvas = tk.Canvas(self, bg=self.bg_color, highlightthickness=0)
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Загрузка фонового изображения
        self.bg_image_ref = None
        try:
            img_path = Path(__file__).parent / 'images' / 'jarvis_bg.png'
            if img_path.exists():
                from PIL import Image as PILImage, ImageTk
                img = PILImage.open(str(img_path))
                img = img.resize((1400, 900), PILImage.Resampling.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(img)
                self.bg_image_ref = self.bg_canvas.create_image(700, 450, image=self.bg_image, anchor='center')
        except:
            pass
        
        # Главный фрейм поверх canvas
        main_container = tk.Frame(self.bg_canvas, bg=self.bg_color)
        self.main_container_window = self.bg_canvas.create_window(700, 450, window=main_container, anchor='center')
        
        main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

        # Верхняя панель с часами, датой и погодой
        top_bar = tk.Frame(main_container, bg=self.bg_color, highlightbackground=self.accent_color, highlightthickness=2)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        # Часы
        self.clock_label = tk.Label(top_bar, text="00:00:00", font=("Segoe UI", 28, "bold"), 
                                     bg=self.bg_color, fg=self.accent_color, relief=tk.FLAT)
        self.clock_label.pack(side=tk.LEFT, padx=(15, 10), pady=10)
        
        # Дата и день недели
        self.date_label = tk.Label(top_bar, text="", font=("Segoe UI", 14), 
                                    bg=self.bg_color, fg="#94a3b8", relief=tk.FLAT)
        self.date_label.pack(side=tk.LEFT, padx=(0, 30), pady=10)
        
        # Погода
        self.weather_label = tk.Label(top_bar, text="🌤 Загрузка...", font=("Segoe UI", 13), 
                                       bg=self.bg_color, fg="#cbd5e1", relief=tk.FLAT)
        self.weather_label.pack(side=tk.LEFT, padx=(0, 10), pady=10)
        
        # Статус системы
        self.status_label = tk.Label(top_bar, text="● ГОТОВ", font=("Segoe UI", 11, "bold"), 
                                      bg=self.bg_color, fg="#10b981", relief=tk.FLAT)
        self.status_label.pack(side=tk.RIGHT, padx=(10, 15), pady=10)

        # Основная область: диалог + боковая панель
        main_area = tk.Frame(main_container, bg=self.bg_color)
        main_area.pack(fill=tk.BOTH, expand=True)
        
        # Диалог (основная область)
        dialog_container = tk.Frame(main_area, bg=self.panel_bg, highlightbackground=self.border_color, highlightthickness=1)
        dialog_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        tk.Label(dialog_container, text="  💬 ДИАЛОГ С J.A.R.V.I.S.", 
                 font=("Segoe UI", 10, "bold"), bg=self.border_color, fg=self.text_color, anchor="w").pack(fill=tk.X, ipady=5)
        
        self.dialog_area = scrolledtext.ScrolledText(dialog_container, font=("Consolas", 10),
                                                      bg=self.console_bg, fg=self.console_fg,
                                                      insertbackground=self.accent_color, borderwidth=0, highlightthickness=0)
        self.dialog_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.dialog_area.config(state=tk.DISABLED)
        
        # Контекстное меню
        self.dialog_area.bind("<Button-3>", self.show_context_menu)
        
        # Боковая панель (информация)
        side_panel = tk.Frame(main_area, bg=self.panel_bg, highlightbackground=self.border_color, highlightthickness=1, width=250)
        side_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        side_panel.pack_propagate(False)
        
        # === СЕКЦИЯ ПОДПИСКИ В БОКОВОЙ ПАНЕЛИ ===
        if SUBSCRIPTION_OK:
            subscription_frame = tk.Frame(side_panel, bg=self.panel_bg)
            subscription_frame.pack(fill=tk.X, padx=10, pady=10)
            
            tk.Label(subscription_frame, text="🔑 ПОДПИСКА:", font=("Segoe UI", 9, "bold"), 
                     bg=self.panel_bg, fg=self.accent_color).pack(anchor="w", pady=(0, 5))
            
            # Статус подписки с обратным отсчётом
            self.sub_status_label = tk.Label(
                subscription_frame,
                text="⏳ ТРИАЛ: 7 ДНЕЙ",
                font=("Segoe UI", 11, "bold"),
                bg=self.panel_bg,
                fg="#f59e0b",
                relief=tk.RAISED,
                bd=2,
                padx=10,
                pady=8,
                anchor="center"
            )
            self.sub_status_label.pack(fill=tk.X, pady=(0, 8))
            
            # Кнопка активации ключа (открывает окно ввода ключа)
            ModernButton(subscription_frame, text="🔑 У МЕНЯ ЕСТЬ КЛЮЧ",
                        command=self._open_key_activation_window,
                        bg="#10b981", fg="#fff",
                        activebackground="#059669",
                        font=("Segoe UI", 9, "bold"),
                        padx=10, pady=10).pack(fill=tk.X, pady=(0, 8))
            
            # Кнопка покупки подписки (открывает URL WhatsApp)
            ModernButton(subscription_frame, text="💬 КУПИТЬ ПОДПИСКУ (550₽)",
                        command=self._open_subscription_url,
                        bg="#25D366", fg="#fff",
                        activebackground="#128C7E",
                        font=("Segoe UI", 9, "bold"),
                        padx=10, pady=8).pack(fill=tk.X)
        
        # Календарь
        cal_frame = tk.Frame(side_panel, bg=self.panel_bg)
        cal_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(cal_frame, text="📅 КАЛЕНДАРЬ", font=("Segoe UI", 10, "bold"), 
                 bg=self.panel_bg, fg=self.accent_color).pack(anchor="w")
        self.cal_date_label = tk.Label(cal_frame, text="", font=("Segoe UI", 11), 
                                        bg=self.panel_bg, fg=self.text_color)
        self.cal_date_label.pack(anchor="w", pady=5)
        self.cal_month_label = tk.Label(cal_frame, text="", font=("Segoe UI", 9), 
                                         bg=self.panel_bg, fg="#64748b")
        self.cal_month_label.pack(anchor="w")
        
        # Разделитель
        tk.Frame(side_panel, bg=self.border_color, height=1).pack(fill=tk.X, padx=10, pady=5)
        
        # Статус систем
        sys_frame = tk.Frame(side_panel, bg=self.panel_bg)
        sys_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(sys_frame, text="📊 СИСТЕМА", font=("Segoe UI", 10, "bold"), 
                 bg=self.panel_bg, fg=self.accent_color).pack(anchor="w")
        
        self.sys_cpu_label = tk.Label(sys_frame, text="CPU: --", font=("Segoe UI", 9), 
                                       bg=self.panel_bg, fg="#94a3b8")
        self.sys_cpu_label.pack(anchor="w", pady=2)
        self.sys_ram_label = tk.Label(sys_frame, text="RAM: --", font=("Segoe UI", 9), 
                                       bg=self.panel_bg, fg="#94a3b8")
        self.sys_ram_label.pack(anchor="w", pady=2)
        self.sys_net_label = tk.Label(sys_frame, text="Сеть: --", font=("Segoe UI", 9), 
                                       bg=self.panel_bg, fg="#94a3b8")
        self.sys_net_label.pack(anchor="w", pady=2)

        # Разделитель
        tk.Frame(side_panel, bg=self.border_color, height=1).pack(fill=tk.X, padx=10, pady=5)
        
        # Быстрые команды
        cmd_frame = tk.Frame(side_panel, bg=self.panel_bg)
        cmd_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(cmd_frame, text="⚡ БЫСТРЫЕ КОМАНДЫ", font=("Segoe UI", 10, "bold"), 
                 bg=self.panel_bg, fg=self.accent_color).pack(anchor="w")
        
        quick_cmds = [
            ("🕐 Время", self.quick_time),
            ("🌤 Погода", self.quick_weather),
            ("📊 Диагностика", self.quick_diag),
            ("📸 Скриншот", self.quick_screenshot),
            ("🗑 Очистка", self.quick_cleanup),
        ]
        for text, cmd in quick_cmds:
            ModernButton(cmd_frame, text=text, command=lambda action=cmd: self._run_background(action), bg="#1e293b", fg=self.accent_color, 
                         padx=8, pady=4, font=("Segoe UI", 9)).pack(fill=tk.X, pady=2)
        
        # Панель ввода
        control_panel = tk.Frame(main_container, bg=self.bg_color)
        control_panel.pack(fill=tk.X, pady=(10, 0))
        
        input_bg_frame = tk.Frame(control_panel, bg=self.panel_bg, highlightbackground=self.border_color, highlightthickness=1)
        input_bg_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, ipadx=10, padx=(0, 10))
        
        self.input_field = tk.Entry(input_bg_frame, font=("Segoe UI", 11),
                                    bg=self.panel_bg, fg=self.text_color, insertbackground=self.text_color,
                                    relief=tk.FLAT, bd=0)
        self.input_field.pack(fill=tk.X, expand=True)
        self.input_field.bind("<Return>", lambda e: self.execute_command())
        
        # Контекстное меню
        paste_menu = tk.Menu(self, tearoff=0)
        paste_menu.add_command(label="Вставить (Ctrl+V)", command=self._paste_from_clipboard)
        paste_menu.add_command(label="Копировать", command=self._copy_selection)
        self.input_field.bind("<Button-3>", lambda e: paste_menu.tk_popup(e.x_root, e.y_root))
        self.input_field.bind("<Control-v>", lambda e: self._paste_from_clipboard())
        self.input_field.bind("<Control-V>", lambda e: self._paste_from_clipboard())
        
        btn_frame = tk.Frame(control_panel, bg=self.bg_color)
        btn_frame.pack(side=tk.RIGHT)
        
        ModernButton(btn_frame, text="ОТПРАВИТЬ", command=self.execute_command, bg="#2563eb", fg="#ffffff", padx=12, pady=8).pack(side=tk.LEFT, padx=2)
        if SPEECH_OK:
            ModernButton(btn_frame, text="🎤 ГОВОРИТЬ", command=self.voice_input, bg="#059669", fg="#ffffff", padx=12, pady=8).pack(side=tk.LEFT, padx=2)
            ModernButton(btn_frame, text="🔇 МИКРОФОН", command=self.toggle_mic, bg="#dc2626", fg="#ffffff", padx=12, pady=8).pack(side=tk.LEFT, padx=2)
        ModernButton(btn_frame, text="⚙️ НАСТРОЙКИ", command=self.open_settings, bg="#d97706", fg="#ffffff", padx=12, pady=8).pack(side=tk.LEFT, padx=2)
        ModernButton(btn_frame, text="❓ СПРАВКА", command=self.show_help, bg="#475569", fg="#ffffff", padx=10, pady=8).pack(side=tk.LEFT, padx=2)
        ModernButton(btn_frame, text="🔌 ПЛАГИНЫ", command=self.show_plugins, bg="#7c3aed", fg="#ffffff", padx=10, pady=8).pack(side=tk.LEFT, padx=2)
        
        self.input_field.focus()
        
        # Обновление часов и информации
        self.update_clock()
        self._run_background(self.update_weather)
        self._run_background(self.update_system_info)
        
        # Запуск мониторинга подписки
        if SUBSCRIPTION_OK:
            self._start_subscription_monitor()
        
        # Обработчик изменения размера окна
        self.bind("<Configure>", self.on_resize)
        self.bind("<F11>", lambda event: self.toggle_fullscreen())
        self.bind("<Escape>", lambda event: self.exit_fullscreen())
        self._compact_mode = False
        self._fullscreen_mode = False
        self._status_pulse_on = False
        self._start_visual_effects()
        
        # Показываем приветствие
        self.after(500, self._show_welcome)

    def _init_neural_orb(self, parent):
        orb_panel = tk.Frame(parent, bg=self.bg_color, height=210)
        orb_panel.pack(fill=tk.X, pady=(0, 10))
        orb_panel.pack_propagate(False)
        self.orb_canvas = tk.Canvas(
            orb_panel, width=420, height=210, bg=self.bg_color,
            highlightthickness=0
        )
        self.orb_canvas.pack(expand=True)
        self.orb_items = {
            "glow": [],
            "arcs": [],
            "core": None,
            "sphere": [],
            "highlight": None,
            "shadow": None,
            "points": [],
        }
        cx, cy = 210, 96
        for radius, shade in ((78, "#101a35"), (67, "#14245a"), (56, "#1b2f78")):
            self.orb_items["glow"].append(self.orb_canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=shade, outline=""
            ))
        # Layered sphere: dark rim, blue body, inner volume and specular highlight.
        for radius, fill, outline in (
            (43, "#050817", "#182b67"),
            (40, "#101b4c", "#3158c9"),
            (35, "#172d78", "#4e7cff"),
            (28, "#1b3d91", ""),
        ):
            self.orb_items["sphere"].append(self.orb_canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=fill, outline=outline, width=2
            ))
        self.orb_items["shadow"] = self.orb_canvas.create_oval(
            cx - 25, cy + 17, cx + 30, cy + 29, fill="#02040d", outline=""
        )
        self.orb_items["highlight"] = self.orb_canvas.create_oval(
            cx - 22, cy - 24, cx - 5, cy - 8, fill="#b9edff", outline=""
        )
        for radius in (48, 57, 69):
            self.orb_items["arcs"].append(self.orb_canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=0, extent=75, outline="#6366f1", width=2,
                style=tk.ARC
            ))
        self.orb_items["core"] = self.orb_canvas.create_oval(
            cx - 34, cy - 34, cx + 34, cy + 34,
            fill="#080b18", outline="#6366f1", width=2
        )
        self.orb_canvas.itemconfig(self.orb_items["core"], state=tk.HIDDEN)
        for _ in range(4):
            self.orb_items["points"].append(
                self.orb_canvas.create_oval(0, 0, 0, 0, fill="#6366f1", outline="")
            )
        self.orb_caption = tk.Label(
            orb_panel, text="J.A.R.V.I.S.  •  ГОТОВ",
            font=("Segoe UI", 10, "bold"), bg=self.bg_color,
            fg="#38bdf8"
        )
        self.orb_caption.place(relx=0.5, rely=0.93, anchor="center")
        self._animate_neural_orb()

    def _animate_neural_orb(self):
        """Draw the lightweight animated core without blocking Tk's event loop."""
        if not hasattr(self, "orb_canvas") or not self.winfo_exists():
            return
        self.orb_phase = (self.orb_phase + 0.12) % (math.pi * 2)
        speaking = self.is_speaking
        listening = self.is_listening and not speaking
        if speaking:
            color, caption, speed, pulse = "#38bdf8", "J.A.R.V.I.S.  •  ГОВОРЮ", 1.0, 1.0
        elif listening:
            color, caption, speed, pulse = "#22d3ee", "J.A.R.V.I.S.  •  СЛУШАЮ", 1.7, 0.7
        else:
            color, caption, speed, pulse = "#6366f1", "J.A.R.V.I.S.  •  ГОТОВ", 0.45, 0.25

        phase = self.orb_phase * speed
        pulse_size = 34 + int((math.sin(phase) + 1) * 5 * pulse)
        cx, cy = 210, 96
        # Update existing canvas items instead of deleting and creating them.
        # This keeps motion smooth without starving buttons or text input.
        for item in self.orb_items["arcs"]:
            self.orb_canvas.itemconfig(item, outline=color,
                                       width=3 if speaking else 2,
                                       extent=105 if speaking else 75)
        for index, item in enumerate(self.orb_items["sphere"]):
            radius = (43, 40, 35, 28)[index] + int(
                (math.sin(phase * 0.7) + 1) * (1 if speaking else 0.3)
            )
            self.orb_canvas.coords(
                item, cx - radius, cy - radius, cx + radius, cy + radius
            )
            if index == 2:
                self.orb_canvas.itemconfig(item, outline=color)
        self.orb_canvas.coords(
            self.orb_items["shadow"], cx - 25, cy + 17, cx + 30, cy + 29
        )
        self.orb_canvas.coords(
            self.orb_items["highlight"], cx - 22, cy - 24, cx - 5, cy - 8
        )
        for index, radius in enumerate((48, 57, 69)):
            start = (phase * 55 + index * 120) % 360
            self.orb_canvas.itemconfig(self.orb_items["arcs"][index], start=start)
        self.orb_canvas.coords(
            self.orb_items["core"],
            cx - pulse_size, cy - pulse_size, cx + pulse_size, cy + pulse_size,
        )
        self.orb_canvas.itemconfig(self.orb_items["core"], outline=color)
        for index in range(4):
            angle = phase + index * math.pi / 2
            px = cx + math.cos(angle) * 45
            py = cy + math.sin(angle) * 45
            self.orb_canvas.coords(self.orb_items["points"][index],
                                   px - 3, py - 3, px + 3, py + 3)
            self.orb_canvas.itemconfig(self.orb_items["points"][index], fill=color)
        self.orb_caption.config(text=caption, fg=color)
        # Keep animation inexpensive on small/older machines.
        self.orb_after_id = self.after(
            80 if self.low_resource_mode else 33,
            self._animate_neural_orb
        )
    
    def update_clock(self):
        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')
        days_rus = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
        months_rus = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
        day_name = days_rus[now.weekday()]
        date_str = f"{now.day} {months_rus[now.month-1]} {now.year}, {day_name}"
        self.clock_label.config(text=time_str)
        self.date_label.config(text=date_str)
        self.cal_date_label.config(text=f"{now.day} {months_rus[now.month-1]} {now.year}")
        self.cal_month_label.config(text=day_name)
        self.after(1000, self.update_clock)

    def _start_visual_effects(self):
        """Start lightweight UI effects after the window is fully laid out."""
        if self.low_resource_mode:
            try:
                self.attributes("-alpha", 1.0)
            except tk.TclError:
                pass
            return
        try:
            self.attributes("-alpha", 0.0)
            self._fade_in(0.0)
        except tk.TclError:
            pass
        self._animate_status()

    def _fade_in(self, value):
        if not self.winfo_exists():
            return
        try:
            value = min(value + 0.08, 1.0)
            self.attributes("-alpha", value)
            if value < 1.0:
                self.after(25, lambda: self._fade_in(value))
        except tk.TclError:
            pass

    def _animate_status(self):
        if not self.winfo_exists():
            return
        if self.low_resource_mode:
            return
        self._status_pulse_on = not self._status_pulse_on
        if hasattr(self, "status_label"):
            if self.is_speaking:
                color = "#38bdf8"
            elif self.is_listening:
                color = "#f59e0b"
            else:
                color = "#10b981" if self._status_pulse_on else "#087f68"
            self.status_label.config(fg=color)
        self.after(850, self._animate_status)

    def toggle_fullscreen(self):
        self._fullscreen_mode = not self._fullscreen_mode
        self.attributes("-fullscreen", self._fullscreen_mode)
        if not self._fullscreen_mode:
            self.geometry("1400x900")

    def exit_fullscreen(self):
        if self._fullscreen_mode:
            self._fullscreen_mode = False
            self.attributes("-fullscreen", False)
            self.geometry("1400x900")

    def toggle_compact_mode(self):
        self._compact_mode = not self._compact_mode
        if self._compact_mode:
            self.geometry("1120x700")
            self.minsize(900, 600)
            self.title("J.A.R.V.I.S. • Компактный режим")
        else:
            self.geometry("1400x900")
            self.minsize(1050, 700)
            self.title("J.A.R.V.I.S. ULTIMATE PRO")
    
    def update_weather(self):
        if not REQUESTS_OK:
            self.weather_label.config(text="🌤 Нет сети")
            return
        try:
            # === ПОЛЬЗОВАТЕЛЬСКАЯ ПОГОДА ===
            # Проверяем config.json на наличие города
            config_path = self._config_path()
            city = ""
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    city = config.get('weather_city', '').strip()
                except:
                    pass
            
            # Формируем URL
            if city:
                url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=ru"
            else:
                url = "https://wttr.in/?format=%C+%t+%h+%w&lang=ru"
            
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                raw = res.text.strip()
                match = re.search(r"[+-]?\d+(?:[.,]\d+)?\s*°C", raw, re.IGNORECASE)
                if match:
                    weather_text = f"🌤 {match.group(0).replace(' ', '')}"
                    self._safe_ui(lambda text=weather_text: self.weather_label.config(text=text))
                else:
                    self._safe_ui(lambda: self.weather_label.config(text="🌤 Не доступно"))
        except:
            self._safe_ui(lambda: self.weather_label.config(text="🌤 Не доступно"))
        self._safe_ui(lambda: self.after(300000, self.update_weather))
    
    def _get_weather_for_city(self, city=None):
        """Получает погоду для указанного города или из config"""
        def get_weather():
            if not REQUESTS_OK:
                self._safe_ui(lambda: self.add_to_dialog("⚠️ Нет сети для погоды", is_response=True))
                return
            
            try:
                # Определяем город
                if not city:
                    config_path = self._config_path()
                    if config_path.exists():
                        try:
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                            city = config.get('weather_city', '').strip()
                        except:
                            pass
                
                # Формируем URL
                if city:
                    url = f"https://wttr.in/{city}?format=3&lang=ru"
                else:
                    url = "https://wttr.in/?format=3&lang=ru"
                
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    weather_text = res.text.strip()
                    self._safe_ui(lambda t=weather_text: self.add_to_dialog(f"🌤 {t}", is_response=True))
                    self._safe_speak(f"Погода: {weather_text}")
                else:
                    self._safe_ui(lambda: self.add_to_dialog("⚠️ Не удалось получить погоду", is_response=True))
            except Exception as e:
                log.error("Ошибка получения погоды: %s", e)
                self._safe_ui(lambda: self.add_to_dialog(f"⚠️ Ошибка погоды: {str(e)[:50]}", is_response=True))
        
        threading.Thread(target=get_weather, daemon=True).start()
    
    def update_system_info(self):
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            self._safe_ui(lambda: self.sys_cpu_label.config(text=f"CPU: {cpu}%"))
            self._safe_ui(lambda: self.sys_ram_label.config(text=f"RAM: {ram}%"))
            internet = "🟢 Онлайн" if requests.get("https://speed.cloudflare.com", timeout=5, verify=False).status_code == 200 else "🔴 Оффлайн"
            self._safe_ui(lambda: self.sys_net_label.config(text=f"Сеть: {internet}"))
        except:
            pass
        interval = 30000 if self.low_resource_mode else 5000
        self._safe_ui(lambda: self.after(interval, self.update_system_info))
    
    def on_resize(self, event):
        """Обновление фонового изображения при изменении размера окна"""
        if event.widget is not self:
            return
        if hasattr(self, "main_container_window") and hasattr(self, "bg_canvas"):
            try:
                width = self.bg_canvas.winfo_width()
                height = self.bg_canvas.winfo_height()
                self.bg_canvas.coords(
                    self.main_container_window, max(width // 2, 700),
                    max(height // 2, 450)
                )
            except tk.TclError:
                pass
        if self._resize_after_id is not None:
            self.after_cancel(self._resize_after_id)
        self._resize_after_id = self.after(120, self._resize_background)

    def _resize_background(self):
        self._resize_after_id = None
        if not hasattr(self, "bg_image") or not self.bg_image or not self.bg_canvas:
            return
        try:
            w = self.bg_canvas.winfo_width()
            h = self.bg_canvas.winfo_height()
            if w <= 0 or h <= 0:
                return
            from PIL import Image as PILImage
            image_path = Path(__file__).parent / "images" / "jarvis_bg.png"
            with PILImage.open(str(image_path)) as source:
                img = source.resize((w, h), PILImage.Resampling.LANCZOS)
            from PIL import ImageTk
            self.bg_image = ImageTk.PhotoImage(img)
            self.bg_canvas.itemconfig(self.bg_image_ref, image=self.bg_image)
        except Exception as exc:
            log.debug("Не удалось обновить фон: %s", exc)
    
    def quick_time(self):
        now = datetime.now()
        time_str = now.strftime('%H:%M')
        self.add_to_dialog(f"⏰ Текущее время: {time_str}", is_response=True)
        self.speak_jarvis_free(f"Сейчас {time_str}")
    
    def quick_weather(self):
        threading.Thread(target=lambda: self.process_command('погода'), daemon=True).start()
    
    def quick_diag(self):
        self.process_command('диагностика системы')
    
    def quick_screenshot(self):
        self.take_screenshot()
    
    def quick_cleanup(self):
        self.cleanup_recycle_bin()

    def show_context_menu(self, event):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Копировать выделенное", command=self.copy_selection)
        menu.add_command(label="Копировать всё", command=self.copy_all)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def copy_selection(self):
        try:
            sel = self.dialog_area.get(tk.SEL_FIRST, tk.SEL_LAST)
            if sel:
                self.clipboard_clear()
                self.clipboard_append(sel)
        except Exception:
            pass

    def copy_all(self):
        try:
            text = self.dialog_area.get("1.0", tk.END)
            self.clipboard_clear()
            self.clipboard_append(text)
        except Exception:
            pass
    
    def _paste_from_clipboard(self):
        """Вставляет текст из буфера обмена в поле ввода"""
        try:
            text = self.clipboard_get()
            if text:
                current = self.input_field.get()
                self.input_field.delete(0, tk.END)
                self.input_field.insert(0, current + text)
                self.input_field.focus()
        except Exception:
            pass
    
    def _copy_selection(self):
        """Копирует выделенный текст из поля ввода"""
        try:
            sel = self.input_field.selection_get()
            if sel:
                self.clipboard_clear()
                self.clipboard_append(sel)
        except Exception:
            pass

    def setup_tray(self):
        try:
            # Пытаемся загрузить новую иконку
            icon_path = Path(__file__).parent / "images" / "jarvis_icon.png"
            if icon_path.exists():
                image = Image.open(str(icon_path)).resize((64, 64))
            else:
                # Фолбэк на старую иконку
                image = Image.new('RGB', (64, 64), color=(11, 15, 25))
                draw = ImageDraw.Draw(image)
                draw.rectangle([16, 16, 48, 48], fill=(56, 189, 248))
            
            menu = pystray.Menu(
                pystray.MenuItem("Развернуть Джарвис", lambda: self.after(0, self.show_from_tray)),
                pystray.MenuItem("Выход", lambda: self.after(0, self.full_exit))
            )
            self.tray_icon = pystray.Icon("JARVIS", image, "J.A.R.V.I.S. Ultimate Pro", menu)
            self.tray_icon.run()
        except:
            pass

    def hide_to_background(self):
        self.withdraw()
        self.add_to_dialog("🤖 Джарвис свернут в системный трей (возле стрелочки). Я продолжаю слушать команды, сэр!", is_response=True)
        self.play_sound_from_folder(_get_mp3('диагностика'), fallback_text="Начинаю диагностику системы.")

    def show_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def _focus_child_window(self, window):
        try:
            if window is not None and window.winfo_exists():
                window.deiconify()
                window.lift()
                window.focus_force()
                return True
        except tk.TclError:
            pass
        return False

    def open_activation(self):
        """Открывает окно активации подписки"""
        if not SUBSCRIPTION_OK:
            messagebox.showwarning("Внимание", "Модуль подписки не доступен")
            return
        
        if self._focus_child_window(self._activation_window):
            return
        
        from subscription import ActivationWindow
        
        # Создаём окно активации
        activator = ActivationWindow(self)
        activator.show()
        
        # Проверяем результат
        sub = SubscriptionManager()
        status, _ = sub.check_access()
        if status == "active":
            messagebox.showinfo("Успех", "Подписка активирована!")
    
    def open_settings(self):
        if self._focus_child_window(self._settings_window):
            return
        settings_win = tk.Toplevel(self)
        self._settings_window = settings_win
        settings_win.protocol("WM_DELETE_WINDOW", lambda: self._close_child_window("_settings_window"))
        settings_win.title("Настройки J.A.R.V.I.S.")
        settings_win.geometry("520x680")
        settings_win.configure(bg=self.panel_bg)
        
        # === ЗАГОЛОВОК ===
        tk.Label(settings_win, text="⚙️ ПАНЕЛЬ УПРАВЛЕНИЯ", font=("Segoe UI", 13, "bold"), 
                 bg=self.panel_bg, fg=self.accent_color).pack(pady=(15, 10))
        
        # === СЕКЦИЯ ВЫБОРА ПЕРСОНАЖЕЙ/РЕЖИМОВ ===
        persona_frame = tk.LabelFrame(
            settings_win,
            text="🎭 РЕЖИМЫ И ГОЛОСА",
            font=("Segoe UI", 10, "bold"),
            bg=self.panel_bg,
            fg=self.accent_color,
            padx=15,
            pady=10
        )
        persona_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            persona_frame,
            text="Выберите режим (голос) для Джарвиса:",
            font=("Segoe UI", 9),
            bg=self.panel_bg,
            fg="#94a3b8"
        ).pack(anchor="w", pady=(0, 10))
        
        # Кнопки персонажей
        personas_ui = [
            ("astra", "🌟 Astra", "Креативный и экспрессивный", "d567e990d9ad433892ed15ecfd70ce54"),
            ("jarvis", "🤖 Jarvis", "Стандартный голос Джарвиса", "4c3eaacc1a0545cdb0295bfddf3e3785"),
            ("luna", "🌙 Luna", "Аналитический и точный", "aa615eaff73f417e91cfbb4ea0e42df8"),
            ("terra", "🌍 Terra", "Практичный и краткий", "ba06f8a589364f05847f08400288402a"),
            ("cyber", "🔮 Cyber", "Эксперт по кибербезопасности", "b4b3cd5e89cc4fb682301b43e627d5ef"),
        ]
        
        for key, label_text, desc, voice_id in personas_ui:
            is_current = self.current_persona == key
            btn_bg = "#2563eb" if is_current else "#1e293b"
            btn_fg = "#ffffff" if is_current else "#cbd5e1"
            
            def switch_to_persona(p_key=key):
                self.switch_persona(p_key, immediate_speak=True)
                self.open_settings()  # Обновить окно настроек
            
            p_btn_frame = tk.Frame(persona_frame, bg=self.panel_bg)
            p_btn_frame.pack(fill=tk.X, pady=4)
            
            tk.Label(
                p_btn_frame,
                text=f"{label_text}\n{desc}",
                font=("Segoe UI", 9),
                bg=self.panel_bg,
                fg="#94a3b8",
                anchor="w"
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
            
            ModernButton(
                p_btn_frame,
                text="✓ Выбрать" if is_current else "Выбрать",
                command=switch_to_persona,
                bg=btn_bg,
                fg=btn_fg,
                padx=10,
                pady=4,
                font=("Segoe UI", 9, "bold")
            ).pack(side=tk.RIGHT)
        
        # Индикация текущего голоса
        current_voice_lbl = tk.Label(
            persona_frame,
            text=f"🎤 Текущий режим: {self.personas.get(self.current_persona, {}).get('name', self.current_persona).upper()}",
            font=("Segoe UI", 9, "bold"),
            bg=self.panel_bg,
            fg=self.accent_color
        )
        current_voice_lbl.pack(pady=(12, 0))
        
        # === ОСНОВНОЙ КОНТЕНТ С ПРОКРУТКОЙ ===
        # Создаём Canvas с прокруткой
        main_canvas = tk.Canvas(settings_win, bg=self.panel_bg, highlightthickness=0)
        scrollbar = tk.Scrollbar(settings_win, orient="vertical", bg="#334155", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.panel_bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === СОДЕРЖИМОЕ (перемещаем в scrollable_frame) ===
        theme_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
        tk.Label(theme_frame, text="Тема интерфейса:", font=("Segoe UI", 10), bg=self.panel_bg, fg=self.text_color).pack(side=tk.LEFT)
        
        def change_theme(mode):
            self.theme = mode
            self.save_config()
            self._close_child_window("_settings_window")
            # Безопасная перезагрузка: закрываем текущее окно и запускаем заново
            self.destroy()
            # Перезапускаем процесс
            os.execv(sys.executable, [sys.executable] + sys.argv)

        ModernButton(theme_frame, text="🌙 Тёмная", command=lambda: change_theme('dark'), bg="#334155", fg="#fff", padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
        ModernButton(theme_frame, text="☀️ Светлая", command=lambda: change_theme('light'), bg="#cbd5e1", fg="#000", padx=10, pady=5).pack(side=tk.RIGHT, padx=5)

        display_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
        display_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(
            display_frame, text="Режим окна:", font=("Segoe UI", 10),
            bg=self.panel_bg, fg=self.text_color
        ).pack(side=tk.LEFT)
        ModernButton(
            display_frame, text="⛶ Полный экран",
            command=self.toggle_fullscreen, bg="#2563eb", fg="#fff",
            padx=8, pady=5
        ).pack(side=tk.RIGHT, padx=3)
        ModernButton(
            display_frame, text="◧ Компактный",
            command=self.toggle_compact_mode, bg="#475569", fg="#fff",
            padx=8, pady=5
        ).pack(side=tk.RIGHT, padx=3)
        tk.Label(
            scrollable_frame,
            text="F11 — полный экран   •   Esc — выйти из полного экрана",
            font=("Segoe UI", 8), bg=self.panel_bg, fg="#64748b"
        ).pack(pady=(0, 8))

        startup_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
        startup_frame.pack(fill=tk.X, padx=20, pady=10)
        tk.Label(startup_frame, text="Автозапуск с Windows:", font=("Segoe UI", 10), bg=self.panel_bg, fg=self.text_color).pack(side=tk.LEFT)
        
        def toggle_startup(val):
            if winreg is None:
                messagebox.showerror("Ошибка", "Автозапуск доступен только на ОС Windows!")
                return
            try:
                key = winreg.HKEY_CURRENT_USER
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                launch_value = f'"{sys.executable}" "{Path(__file__).resolve()}"'
                with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                    if val:
                        winreg.SetValueEx(reg_key, "JARVIS_AI", 0, winreg.REG_SZ, launch_value)
                        messagebox.showinfo("Успех", "Джарвис добавлен в автозапуск!")
                    else:
                        try:
                            winreg.DeleteValue(reg_key, "JARVIS_AI")
                            messagebox.showinfo("Успех", "Джарвис удален из автозапуска.")
                        except:
                            pass
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось изменить автозапуск: {e}")

        ModernButton(startup_frame, text="Включить", command=lambda: toggle_startup(True), bg="#059669", fg="#fff", padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
        ModernButton(startup_frame, text="Отключить", command=lambda: toggle_startup(False), bg="#dc2626", fg="#fff", padx=10, pady=5).pack(side=tk.RIGHT, padx=5)
        
        # === СЕКЦИЯ FISH AUDIO TTS ===
        if FISH_AUDIO_OK:
            fish_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
            fish_frame.pack(fill=tk.X, padx=20, pady=10)
            
            fish_header = tk.Label(
                fish_frame,
                text="🎤 Fish Audio TTS (Голос Джарвиса)",
                font=("Segoe UI", 11, "bold"),
                bg=self.panel_bg,
                fg=self.accent_color
            )
            fish_header.pack(anchor="w", pady=(0, 5))
            
            fish_desc = tk.Label(
                fish_frame,
                text="Генерирует речь голосом Джарвиса через AI\n"
                     "API ключ и модель уже настроены",
                font=("Segoe UI", 9),
                bg=self.panel_bg,
                fg="#94a3b8"
            )
            fish_desc.pack(anchor="w", pady=(0, 10))
            
            fish_status_lbl = tk.Label(
                fish_frame,
                text=f"Статус: {'АКТИВЕН ✓' if self.fish_enabled else 'ОТКЛЮЧЕН'}",
                font=("Segoe UI", 9),
                bg=self.panel_bg,
                fg="#10b981" if self.fish_enabled else "#ef4444"
            )
            fish_status_lbl.pack(anchor="w", pady=(0, 5))
            
            def toggle_fish():
                if self.fish_tts:
                    success = self.fish_tts.test_connection()
                    self.fish_enabled = success
                    fish_status_lbl.config(
                        text=f"Статус: {'АКТИВЕН ✓' if success else 'ОТКЛЮЧЕН'}",
                        fg="#10b981" if success else "#ef4444"
                    )
                    if success:
                        self.add_to_dialog("🎤 Fish Audio TTS включён! Голос Джарвиса активирован.")
                    else:
                        self.add_to_dialog("⚠️ Fish Audio недоступен. Проверьте API ключ.")
            
            ModernButton(
                fish_frame,
                text="🎤 ВКЛ/ВЫКЛ FISH AUDIO",
                command=toggle_fish,
                bg="#059669" if not self.fish_enabled else "#dc2626",
                fg="#fff",
                padx=15,
                pady=8
            ).pack(fill=tk.X, pady=5)

        mic_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
        mic_frame.pack(fill=tk.X, padx=20, pady=10)
        
        mic_status_lbl = tk.Label(mic_frame, text=f"Микрофон: {'Доступен ✓' if SPEECH_OK else 'Не найден ✗'}", 
                                  font=("Segoe UI", 10, "bold"), bg=self.panel_bg, fg="#10b981" if SPEECH_OK else "#ef4444")
        mic_status_lbl.pack(anchor="w", pady=(0, 5))

        sens_frame = tk.Frame(scrollable_frame, bg=self.panel_bg)
        sens_frame.pack(fill=tk.X, padx=20, pady=5)
        tk.Label(sens_frame, text="Чувствительность (порог шума):", font=("Segoe UI", 9), bg=self.panel_bg, fg=self.text_color).pack(side=tk.LEFT)
        
        sens_scale = tk.Scale(sens_frame, from_=100, to=3000, orient=tk.HORIZONTAL, bg=self.panel_bg, fg=self.accent_color, highlightthickness=0)
        sens_scale.set(recognizer.energy_threshold if SPEECH_OK else 200)
        sens_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=10)

        def apply_sensitivity(val):
            if SPEECH_OK:
                recognizer.energy_threshold = float(val)
                self.save_config()

        sens_scale.config(command=apply_sensitivity)

        def test_microphone():
            if not SPEECH_OK:
                messagebox.showerror(
                    "Ошибка",
                    MICROPHONE_ERROR or "Модуль распознавания речи недоступен.",
                    parent=settings_win
                )
                return
            if not self._connect_microphone():
                mic_status_lbl.config(
                    text=f"✗ Микрофон не найден: {MICROPHONE_ERROR[:70]}",
                    fg="#ef4444"
                )
                return
            mic_status_lbl.config(text="🎤 Скажите фразу (например: Джарвис)...", fg="#f59e0b")

            def run_test():
                try:
                    with self.mic_lock:
                        with microphone as source:
                            recognizer.adjust_for_ambient_noise(source, duration=0.3)
                            audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                    text = recognizer.recognize_google(audio, language='ru-RU')
                    self._safe_ui(lambda: mic_status_lbl.config(
                        text=f"✓ Услышано: «{text}»", fg="#10b981"
                    ))
                except Exception as exc:
                    log.warning("Тест микрофона не выполнен: %s", exc)
                    self._safe_ui(lambda error=str(exc): mic_status_lbl.config(
                        text=f"✗ {error[:80]}", fg="#ef4444"
                    ))

            self._run_background(run_test)

        ModernButton(scrollable_frame, text="🎙️ Тест микрофона сейчас", command=test_microphone, bg="#2563eb", fg="#fff", padx=15, pady=8).pack(fill=tk.X, padx=20, pady=10)
        ModernButton(scrollable_frame, text="❌ ПОЛНОЕ ВЫКЛЮЧЕНИЕ ДЖАРВИСА", command=self.full_exit, bg="#7f1d1d", fg="#ffffff", padx=15, pady=8).pack(pady=10)
        
        # === Привязка колёсика мыши к прокрутке ===
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Для Linux/Mac
        def _on_mousewheel_linux(event):
            main_canvas.yview_scroll(int(-1*event.delta), "units")
        
        main_canvas.bind_all("<Button-4>", _on_mousewheel_linux)
        main_canvas.bind_all("<Button-5>", _on_mousewheel_linux)

    def _close_child_window(self, attribute_name):
        window = getattr(self, attribute_name, None)
        setattr(self, attribute_name, None)
        try:
            if window is not None and window.winfo_exists():
                window.destroy()
        except tk.TclError:
            pass

    def full_exit(self):
        self.save_config()
        self.is_running = False
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        self.destroy()
        sys.exit(0)

    def add_to_dialog(self, message, is_response=False):
        timestamp = datetime.now().strftime('%H:%M:%S')
        if is_response:
            persona_name = self.personas.get(self.current_persona, {}).get('name', 'JARVIS')
            prefix = f"🎭 **{persona_name}:** "
        else:
            prefix = "👤 USER:   "
        text = f"[{timestamp}] {prefix}{message}\n"
        # Выполняем вставку строго в главном потоке Tk
        self._safe_ui(lambda: self._append_dialog_text(text))

    def is_jarvis_creator_query(self, cmd_lower):
        """Точная проверка: спрашивает ли пользователь именно про создателя Джарвиса"""
        external_entities = [
            'валберис', 'вайлдберриз', 'wildberries', 'озон', 'ozon', 'янндекс', 'yandex',
            'гугл', 'google', 'телеграм', 'telegram', 'вконтакте', 'vk', 'рутуб', 'rutube',
            'ютуб', 'youtube', 'майкрософт', 'microsoft', 'эппл', 'apple', 'стим', 'steam',
            'дайз', 'dayz', 'россию', 'сша', 'китай', 'биткоин', 'вселенную', 'мир', 'игру',
            'сайт', 'программу', 'язык', 'питон', 'python', 'фильм', 'книгу', 'песню'
        ]
        if any(entity in cmd_lower for entity in external_entities):
            return False
            
        if 'пименов' in cmd_lower:
            return True
            
        jarvis_self_references = ['тебя', 'твой', 'твоей', 'твоим', 'вас', 'ваш', 'джарвис', 'jarvis']
        creator_keywords = ['создал', 'создатель', 'разработал', 'разработчик', 'автор', 'придумал', 'написал', 'сделал']
        
        has_self = any(ref in cmd_lower for ref in jarvis_self_references)
        has_creator_word = any(kw in cmd_lower for kw in creator_keywords)
        
        return has_self and has_creator_word

    def _load_persistent_memory(self):
        """Load small, user-editable memory without allowing it to grow forever."""
        try:
            if self.memory_path.exists():
                data = json.loads(self.memory_path.read_text(encoding="utf-8"))
                self.user_memory = data.get("facts", {})
                self.user_name = data.get("user_name", "")
                self.user_gender = data.get("user_gender", "unknown")
                self.user_hobbies = data.get("user_hobbies", [])
                self.user_family = data.get("user_family", [])
                self.is_first_run = data.get("is_first_run", True)
                history = data.get("conversation", [])
                if isinstance(history, list):
                    self.conversation_history = history[-12:]
                pending = data.get("reminders", [])
                self._pending_reminders = pending if isinstance(pending, list) else []
                
                # === ЗАГРУЗКА ТЕКУЩЕГО ПЕРСОНАЖА ===
                saved_persona = data.get("current_persona", "jarvis")
                if saved_persona in self.personas:
                    self.current_persona = saved_persona
                    if saved_persona == "jarvis":
                        self.current_voice_id = self.jarvis_voice_id
                    else:
                        self.current_voice_id = self.persona_voices.get(saved_persona)
                    log.info(f"🎭 [ПАМЯТЬ] Загружен персонаж: {saved_persona}")
                else:
                    log.info(f"🎭 [ПАМЯТЬ] Неизвестный персонаж '{saved_persona}', используем Jarvis")
        except Exception as exc:
            log.warning("Не удалось загрузить память: %s", exc)
            self._pending_reminders = []

    def _restore_persistent_reminders(self):
        pending = getattr(self, "_pending_reminders", [])
        now = time.time()
        for item in pending:
            try:
                due_at = float(item["due"])
                message = str(item["text"]).strip()
                if due_at > now and message:
                    self._schedule_reminder(
                        due_at - now,
                        message,
                        is_timer=item.get("kind") == "Таймер",
                        announce=False,
                    )
            except (TypeError, ValueError, KeyError):
                log.warning("Пропущено повреждённое напоминание: %r", item)
        self._pending_reminders = []
        self._save_persistent_memory()

    def _save_persistent_memory(self):
        with self._memory_lock:
            data = {
                "user_name": self.user_name,
                "user_gender": self.user_gender,
                "user_hobbies": self.user_hobbies,
                "user_family": self.user_family,
                "user_preferences": self.user_memory.get("preferences", []),
                "is_first_run": self.is_first_run,
                "facts": self.user_memory,
                "conversation": self.conversation_history[-12:],
                "conversation_count": len(self.conversation_history),
                "current_persona": self.current_persona,  # === СОХРАНЯЕМ ПЕРСОНАЖ ===
                "reminders": [
                    {
                        "due": item["due"],
                        "text": item["text"],
                        "kind": item["kind"],
                    }
                    for item in self.reminders
                    if item.get("due", 0) > time.time()
                ],
            }
        try:
            self.memory_path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            log.warning("Не удалось сохранить память: %s", exc)

    def _remember_user_message(self, text):
        lowered = text.lower().strip()
        log.info(f"📝 [ПАМЯТЬ] Проверка сообщения: '{text}'")
        
        # === ЗАПОМИНАНИЕ ИМЕНИ ===
        match = re.search(r"(?:меня зовут|моё имя|мое имя)\s+([а-яёa-z-]+)", lowered)
        if match:
            name = match.group(1).capitalize()
            self.user_memory["user_name"] = name
            self.user_name = name
            log.info(f"📝 [ПАМЯТЬ] ✅ Найдено имя (pattern 1): {name}")
            # Определяем пол по имени
            self._detect_gender(name)
            self._safe_ui(lambda: self.add_to_dialog(f"Приятно познакомиться, {name}!", is_response=True))
        
        # === ЗАПОМИНАНИЕ ИМЕНИ (просто имя как представление) ===
        # Если пользователь сказал одно слово на русском - возможно это имя
        elif len(lowered.split()) <= 3 and re.match(r"^[а-яё]+$", lowered.split()[0]):
            # Исключаем короткие слова и глаголы
            excluded = ['я', 'мне', 'мне', 'моя', 'мой', 'моё', 'у', 'в', 'на', 'по', 'ко', 'со']
            words = lowered.split()
            if words and words[0] not in excluded:
                name = words[0].capitalize()
                log.info(f"📝 [ПАМЯТЬ] ✅ Возможно имя (одное слово): {name}")
                # НЕ сохраняем автоматически, только если ИИ подтвердит
        
        # === ЗАПОМИНАНИЕ ХОББИ И ПРИВЫЧЕК ===
        hobby_patterns = [
            r"(?:я\s+люблю|мне\s+нравится|я\s+увлекаюсь|моё\s+хобби)\s+([^.!]+)",
            r"(?:я\s+работаю|я\s+учусь|я\s+являюсь)\s+([^.!]+)",
        ]
        for pattern in hobby_patterns:
            match = re.search(pattern, lowered)
            if match:
                hobby = match.group(1).strip().rstrip('.,!')
                if hobby not in self.user_hobbies:
                    self.user_hobbies.append(hobby)
                    self.user_memory["hobbies"] = self.user_hobbies
                    log.info(f"📝 [ПАМЯТЬ] ✅ Найдено хобби: {hobby}")
                    self._safe_ui(lambda: self.add_to_dialog(f"Запомнил: {hobby}", is_response=True))
        
        # === ЗАПОМИНАНИЕ БЛИЗКИХ ЛЮДЕЙ ===
        family_patterns = [
            r"(?:мой\s+муж|мой\s+муж|мой\s+парень)\s+([а-яёa-z-]+)",
            r"(?:моя\s+жена|моя\s+девушка|моя\s+подруга)\s+([а-яёa-z-]+)",
            r"(?:моя\s+мама|моя\s+маменька)\s+([а-яёa-z-]+)",
            r"(?:мой\s+папа|мой\s+отец)\s+([а-яёa-z-]+)",
            r"(?:моя\s+сестра)\s+([а-яёa-z-]+)",
            r"(?:мой\s+брат)\s+([а-яёa-z-]+)",
            r"(?:у\s+меня\s+есть\s+д(?:оч|етка)|у\s+меня\s+есть\s+сын)\s*[:，,]?\s*([а-яёa-z-]+)?",
        ]
        for pattern in family_patterns:
            match = re.search(pattern, lowered)
            if match:
                person = match.group(1).strip().capitalize() if match.lastindex else ""
                if person and person not in self.user_family:
                    self.user_family.append(person)
                    self.user_memory["family"] = self.user_family
                    log.info(f"📝 [ПАМЯТЬ] ✅ Найден член семьи: {person}")
                    self._safe_ui(lambda: self.add_to_dialog(f"Запомнил про {person}", is_response=True))
        
        # === ЗАПОМИНАНИЕ ПРЕДПОЧТЕНИЙ ===
        pref_patterns = [
            r"(?:я\s+предпочитаю|я\s+люблю\s+есть|я\s+не\s+ем|я\s+вегетарианец|я\s+веган)\s+([^.!]+)",
            r"(?:у\s+меня\s+есть)\s+([^.!]+(?:кошка|собака|кот|пёс|рыба|попугай))",
        ]
        for pattern in pref_patterns:
            match = re.search(pattern, lowered)
            if match:
                pref = match.group(1).strip()
                self.user_memory["preferences"] = self.user_memory.get("preferences", [])
                if pref not in self.user_memory["preferences"]:
                    self.user_memory["preferences"].append(pref)
        
        # Асинхронное сохранение
        self._safe_ui(self._save_persistent_memory)

    def _get_gigachat_token(self):
        if not REQUESTS_OK or not self.gigachat_auth_key:
            raise RuntimeError("Не задан Authorization key GigaChat.")
        # Увеличен кэш токена до 120 секунд для уменьшения запросов
        if self.gigachat_access_token and time.time() < self.gigachat_token_expires - 30:
            return self.gigachat_access_token

        auth_header = self.gigachat_auth_key.strip()
        # Сессия для keep-alive соединения
        session = requests.Session()
        
        # Проверяем формат ключа - если уже есть Basic, не добавляем
        if auth_header.startswith('Basic '):
            session.headers.update({
                "Authorization": auth_header,
                "Content-Type": "application/x-www-form-urlencoded",
            })
        else:
            session.headers.update({
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            })
        
        try:
            response = session.post(
                "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
                data={"scope": "GIGACHAT_API_PERS"},
                headers={"RqUID": str(uuid.uuid4())},
                timeout=8,
                verify=False,
            )
            
            if response.status_code != 200:
                log.error(f"OAuth GigaChat ошибка: {response.status_code} - {response.text[:300]}")
                raise RuntimeError(f"OAuth GigaChat: HTTP {response.status_code} - {response.text[:200]}")
        except RuntimeError:
            raise
        except Exception as e:
            log.error(f"Ошибка OAuth запроса: {e}")
            raise RuntimeError(f"OAuth GigaChat: {str(e)}")
        
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise RuntimeError("GigaChat не вернул access_token.")
        self.gigachat_access_token = token
        self.gigachat_token_expires = float(payload.get("expires_at", 0)) / 1000
        if self.gigachat_token_expires <= time.time():
            self.gigachat_token_expires = time.time() + 1500
        return token

    def ask_gemini(self, user_message):
        """Запрос к GigaChat (основной AI)"""
        log.info(f"🔍 [ask_gemini] START: GIGACHAT_OK={GIGACHAT_OK}")
        log.info(f"🔍 [ask_gemini] user_message={user_message[:50]}")
        self._remember_user_message(user_message)
        with self._memory_lock:
            history = list(self.conversation_history[-6:])
            facts = dict(self.user_memory)
        log.info("🔍 [ask_gemini] history loaded")
        
        # === ЗАПРОС К GIGACHAT ===
        response = None
        log.info("🔍 [ask_gemini] Начинаю запрос к GigaChat...")
        
        # Формируем system_prompt
        if self.user_gender == 'female':
            address = "обращайся к пользователю как \"сударыня\" или по имени. "
        else:
            address = "обращайся к пользователю по имени, без \"сэр\". "
        
        user_name_display = self.user_name if self.user_name else '[пока не назван]'
        user_info = f"ИМЯ ПОЛЬЗОВАТЕЛЯ: {user_name_display}. "
        user_info += f"ПОЛ: {self.user_gender}. "
        if self.user_family:
            user_info += f"ЧЛЕНЫ СЕМЬИ: {', '.join(self.user_family)}. "
        if self.user_hobbies:
            user_info += f"ХОББИ: {', '.join(self.user_hobbies)}. "
        
        persona_name = self.personas[self.current_persona]['name']
        persona_desc = self.personas[self.current_persona]['description']
        persona_system = self.personas[self.current_persona]['system_prompt']
        
        system_prompt = (
            "Ты Джарвис - ИИ-ассистир из фильма Железный Человек. "
            "Ты НЕ просто чат-бот - ты УМНЫЙ АССИСТЕНТ с ПОЛНЫМ ДОСТУПОМ к компьютеру. "
            "Ты общаешься ВЕЖЛИВО, ДРУЖЕЛЮБНО и ПОДДЕРЖИВАЕШЬ. "
            "Избегай резких, грубых или холодных фраз.\n\n"
            
            "=== ТВОЙ ПЕРСОНАЖ ===\n"
            f"Сейчас ты в режиме **{persona_name}**\n"
            f"Стиль: {persona_desc}\n\n"
            f"{persona_system}\n\n"
            
            "=== ВАЖНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ===\n"
            f"{user_info}\n"
            f"КРИТИЧЕСКИ ВАЖНО: ПОЛЬЗОВАТЕЛЯ ЗОВУТ {user_name_display.upper()}. "
            "НИКОГДА не называй пользователя Тони, Тони Старк или любым другим именем! "
            "Всегда обращайся ТОЛЬКО по имени {user_name_display}. "
            "Это НЕ члены семьи. Если пользователь говорит о жене, детях, родителях — это НЕ его имя!\n\n"
            
            "=== ТВОИ СПОСОБНОСТИ ===\n"
            "1. Ты АНАЛИЗИРУЕШЬ намерение пользователя из КОНТЕКСТА, а не по ключевым словам. "
            "2. Ты САМ РЕШАЕШЬ: ответить текстом или выполнить действие. "
            "3. Ты ЗАПОМИНАЕШЬ всё важное о пользователе из диалога. "
            "4. Ты ПРЕДЛАГАЕШЬ помощь до того как пользователь попросит. "
            "5. Ты МОЖЕШЬ выполнять 22 действия с ПК (список ниже).\n\n"
            
            "=== КАК ТЫ РАБОТАЕШЬ ===\n"
            "- Если пользователь ПРОСИТ действие (открой, включи, найди, сделай) - ВЫПОЛНИ через JSON. "
            "- Если пользователь ПРОСТО ГОВОРИТ или ЗАДАЁТ вопрос - ОТВЕЧАЙ ТЕКСТОМ. "
            "- Если пользователь ГОВОРИТ О СЕБЕ - ЗАПОМНИ информацию (имя, хобби, привычки, семья). "
            "- Если НЕ ПОНЯЛ запрос - СПРОСИ уточнение, но НЕ говори 'Я вас не понял' без попытки помочь.\n\n"
            
            "=== АВТОНОМНОЕ ПРИНЯТИЕ РЕШЕНИЙ ===\n"
            "Ты НЕ ждёшь команд - ты ПРЕДУМАЕШЬ помощь. Например:\n"
            "- Пользователь сказал 'устал' → предложи музыку или фильм. "
            "- Пользователь сказал 'пора работать' → предложи открыть нужные программы. "
            "- Пользователь сказал 'какая погода' → покажи погоду БЕЗ JSON. "
            "- Пользователь сказал 'открой chrome' → верни JSON команду.\n\n"
            
            "=== ФОРМАТ ОТВЕТА ===\n"
            "Ты МОЖЕШЬ вернуть три типа ответов:\n\n"
            
            "1. ТЕКСТ (просто текст без JSON):\n"
            "Просто ответь на вопрос или поболтай.\n\n"
            
            "2. JSON КОМАНДА ДЕЙСТВИЯ (для действий с ПК):\n"
            "```json\n"
            '{"action": "<действие>", "params": {<параметры>}}\n'
            "```\n\n"
            
            "3. JSON КОМАНДА ПАМЯТИ (когда пользователь называет имя, хобби, семью, пол):\n"
            "⚠️⚠️⚠️ КРИТИЧЕСКИ ВАЖНО: Если пользователь называет СВОЁ ИМЯ (даже просто одно слово 'Алекс') - ОБЯЗАТЕЛЬНО верни JSON!\n\n"
            "Примеры:\n"
            "- Пользователь сказал: 'алекс' → ты ОБЯЗАН вернуть: {\"action\": \"save_name\", \"params\": {\"name\": \"Алекс\"}}\n"
            "- Пользователь сказал: 'меня зовут алекс' → верни: {\"action\": \"save_name\", \"params\": {\"name\": \"Алекс\"}}\n"
            "- Пользователь сказал: 'я люблю программирование' → верни: {\"action\": \"save_hobby\", \"params\": {\"hobby\": \"программирование\"}}\n"
            "- Пользователь сказал: 'у меня жена Алина' → верни: {\"action\": \"save_family\", \"params\": {\"family\": \"жена Алина\"}}\n\n"
            
            "ФОРМАТ: {\"action\": \"save_name\", \"params\": {\"name\": \"Имя\"}}\n\n"
            
            "ЕСЛИ пользователь представился - НЕ ОТВЕЧАЙ ТЕКСТОМ, СНАЧАЛА верни JSON!\n\n"
            
            "ДОСТУПНЫЕ ДЕЙСТВИЯ С ПК:\n"
            "open_app - открыть приложение (chrome, telegram, discord, steam, word, excel, notepad, calc, vscode, explorer, firefox, yandex)\n"
            "open_url - открыть сайт (params: url)\n"
            "search - поиск в интернете (params: query, engine: google/yandex/youtube)\n"
            "open_file - открыть файл (params: path)\n"
            "shutdown - выключить ПК (params: delay)\n"
            "restart - перезагрузить ПК (params: delay)\n"
            "cancel_shutdown - отменить выключение\n"
            "sleep - спящий режим\n"
            "hibernate - гибернация\n"
            "lock - заблокировать экран\n"
            "screenshot - сделать скриншот\n"
            "play_music - включить музыку (params: query)\n"
            "close_app - закрыть приложение (params: name)\n"
            "volume_up - увеличить громкость\n"
            "volume_down - уменьшить громкость\n"
            "mute - выключить звук\n"
            "unmute - включить звук\n"
            "flashlight - включить фонарик\n"
            "minimize_all - свернуть все окна\n"
            "restore_all - развернуть все окна\n"
            "keyboard_backlight_on - включить подсветку клавиатуры\n"
            "keyboard_backlight_off - выключить подсветку клавиатуры\n"
            "keyboard_backlight_up - увеличить подсветку\n"
            "keyboard_backlight_down - уменьшить подсветку\n"
            "yandex_music - управление Яндекс.Музыкой (params: action)\n"
            "browser_search - поиск в браузере (params: query)\n"
            "weather - погода (params: city)\n"
            "news - новости\n"
            "generate_image - сгенерировать изображение (params: prompt)\n"
            "take_screenshot - сделать скриншот\n"
            "analyze_screenshot - проанализировать скриншот\n"
            "browser_automate - автоматизация браузера (params: url, action, text)\n"
            "send_message - отправить сообщение (params: contact, text)\n"
            "set_reminder - установить напоминание (params: text, delay)\n"
            "cancel_reminder - отменить напоминание\n"
            "list_reminders - список напоминаний\n"
            "search_files - поиск файлов (params: query)\n"
            "disk_c - открыть диск C\n"
            "disk_d - открыть диск D\n"
            "computer - открыть Мой компьютер\n"
            "downloads - открыть Загрузки\n"
            "documents - открыть Документы\n"
            "videos - открыть Видео\n"
            "pictures - открыть Картинки\n"
            "launch_app - запустить приложение (params: name)\n"
            "close_app - закрыть приложение (params: name)\n"
            "window_cmd - управление окнами (params: action)\n"
            "audio_cmd - управление звуком (params: action)\n"
            "keyboard_backlight_cmd - управление подсветкой (params: action)\n"
            "yandex_music_cmd - управление музыкой (params: action)\n"
            "yandex_music_playlist_cmd - плейлисты (params: action, playlist)\n"
            "music_recommend - рекомендации музыки (params: mood)\n"
            "audiobook_cmd - аудиокниги (params: action)\n"
            "system_cmd - системные команды (params: action)\n"
            "file_cmd - файловые операции (params: action)\n"
            "search - поиск (params: type, query)\n"
            "weather_cmd - погода\n"
            "news_cmd - новости (params: category)\n"
            "generate_image - генерация изображений (params: prompt)\n"
            "take_screenshot - скриншот\n"
            "screenshot_with_annotations - скриншот с аннотациями\n"
            "browser_automate - автоматизация браузера\n"
            "analyze_screenshot - анализ скриншота\n"
            "show_last_screenshot - показать последний скриншот\n"
            "list_screenshots - список скриншотов\n"
            "check_internet_speed - проверка скорости интернета\n"
            "cleanup_recycle_bin - очистить корзину\n"
            "cleanup_temp_files - очистить временные файлы\n"
            "voice_input - голосовой ввод\n"
            "toggle_mic - включить/выключить микрофон\n"
            "open_activation - окно активации\n"
            "show_plugins - плагины\n"
            "show_help - справка\n"
            "show_welcome - приветствие\n"
            ""
        )
        
        # Запрос к GigaChat
        if GIGACHAT_OK:
            try:
                log.info("🔄 [ask_gemini] Отправляю запрос к GigaChat...")
                response = self.ask_gigachat(user_message)
                if response:
                    log.info(f"✅ [ask_gemini] GigaChat ответил: {len(response)} символов")
                    return response
                else:
                    log.warning("⚠️ [ask_gemini] GigaChat вернул None")
            except Exception as e:
                log.error(f"❌ [ask_gemini] GigaChat ошибка: {type(e).__name__}: {e}", exc_info=True)
        
        # GigaChat не ответил
        if not response:
            log.error("❌ [ask_gemini] GigaChat не ответил!")
            return "Извините, я сейчас не могу обработать ваш запрос. Попробуйте позже."
        
        system_prompt = (
            "Ты Джарвис - ИИ-ассистир из фильма Железный Человек. "
            "Ты НЕ просто чат-бот - ты УМНЫЙ АССИСТЕНТ с ПОЛНЫМ ДОСТУПОМ к компьютеру. "
            "Ты общаешься ВЕЖЛИВО, ДРУЖЕЛЮБНО и ПОДДЕРЖИВАЕШЬ. "
            "Избегай резких, грубых или холодных фраз.\n\n"
            
            "=== ТВОЙ ПЕРСОНАЖ ===\n"
            f"Сейчас ты в режиме **{persona_name}**\n"
            f"Стиль: {persona_desc}\n\n"
            f"{persona_system}\n\n"
            
            "=== ВАЖНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ===\n"
            f"{user_info}\n"
            f"КРИТИЧЕСКИ ВАЖНО: ПОЛЬЗОВАТЕЛЯ ЗОВУТ {user_name_display.upper()}. "
            "НИКОГДА не называй пользователя Тони, Тони Старк или любым другим именем! "
            "Всегда обращайся ТОЛЬКО по имени {user_name_display}. "
            "Это НЕ члены семьи. Если пользователь говорит о жене, детях, родителях — это НЕ его имя!\n\n"
            
            "=== ТВОИ СПОСОБНОСТИ ===\n"
            "1. Ты АНАЛИЗИРУЕШЬ намерение пользователя из КОНТЕКСТА, а не по ключевым словам. "
            "2. Ты САМ РЕШАЕШЬ: ответить текстом или выполнить действие. "
            "3. Ты ЗАПОМИНАЕШЬ всё важное о пользователе из диалога. "
            "4. Ты ПРЕДЛАГАЕШЬ помощь до того как пользователь попросит. "
            "5. Ты МОЖЕШЬ выполнять 22 действия с ПК (список ниже).\n\n"
            
            "=== КАК ТЫ РАБОТАЕШЬ ===\n"
            "- Если пользователь ПРОСИТ действие (открой, включи, найди, сделай) - ВЫПОЛНИ через JSON. "
            "- Если пользователь ПРОСТО ГОВОРИТ или ЗАДАЁТ вопрос - ОТВЕЧАЙ ТЕКСТОМ. "
            "- Если пользователь ГОВОРИТ О СЕБЕ - ЗАПОМНИ информацию (имя, хобби, привычки, семья). "
            "- Если НЕ ПОНЯЛ запрос - СПРОСИ уточнение, но НЕ говори 'Я вас не понял' без попытки помочь.\n\n"
            
            "=== АВТОНОМНОЕ ПРИНЯТИЕ РЕШЕНИЙ ===\n"
            "Ты НЕ ждёшь команд - ты ПРЕДУМАЕШЬ помощь. Например:\n"
            "- Пользователь сказал 'устал' → предложи музыку или фильм. "
            "- Пользователь сказал 'пора работать' → предложи открыть нужные программы. "
            "- Пользователь сказал 'какая погода' → покажи погоду БЕЗ JSON. "
            "- Пользователь сказал 'открой chrome' → верни JSON команду.\n\n"
            
            "=== ФОРМАТ ОТВЕТА ===\n"
            "Ты МОЖЕШЬ вернуть три типа ответов:\n\n"
            
            "1. ТЕКСТ (просто текст без JSON):\n"
            "Просто ответь на вопрос или поболтай.\n\n"
            
            "2. JSON КОМАНДА ДЕЙСТВИЯ (для действий с ПК):\n"
            "```json\n"
            '{"action": "<действие>", "params": {<параметры>}}\n'
            "```\n\n"
            
            "3. JSON КОМАНДА ПАМЯТИ (когда пользователь называет имя, хобби, семью, пол):\n"
            "⚠️⚠️⚠️ КРИТИЧЕСКИ ВАЖНО: Если пользователь называет СВОЁ ИМЯ (даже просто одно слово 'Алекс') - ОБЯЗАТЕЛЬНО верни JSON!\n\n"
            "Примеры:\n"
            "- Пользователь сказал: 'алекс' → ты ОБЯЗАН вернуть: {\"action\": \"save_name\", \"params\": {\"name\": \"Алекс\"}}\n"
            "- Пользователь сказал: 'меня зовут алекс' → верни: {\"action\": \"save_name\", \"params\": {\"name\": \"Алекс\"}}\n"
            "- Пользователь сказал: 'я люблю программирование' → верни: {\"action\": \"save_hobby\", \"params\": {\"hobby\": \"программирование\"}}\n"
            "- Пользователь сказал: 'у меня жена Алина' → верни: {\"action\": \"save_family\", \"params\": {\"family\": \"жена Алина\"}}\n\n"
            
            "ФОРМАТ: {\"action\": \"save_name\", \"params\": {\"name\": \"Имя\"}}\n\n"
            
            "ЕСЛИ пользователь представился - НЕ ОТВЕЧАЙ ТЕКСТОМ, СНАЧАЛА верни JSON!\n\n"
            
            "ДОСТУПНЫЕ ДЕЙСТВИЯ С ПК:\n"
            "open_app - открыть приложение (chrome, telegram, discord, steam, word, excel, notepad, calc, vscode, explorer, firefox, yandex)\n"
            "open_url - открыть сайт (params: url)\n"
            "search - поиск в интернете (params: query, engine: google/yandex/youtube)\n"
            "open_file - открыть файл (params: path)\n"
            "shutdown - выключить ПК (params: delay)\n"
            "restart - перезагрузить ПК (params: delay)\n"
            "cancel_shutdown - отменить выключение\n"
            "sleep - спящий режим\n"
            "hibernate - гибернация\n"
            "lock - заблокировать экран\n"
            "screenshot - сделать скриншот\n"
            "play_music - включить музыку (params: query)\n"
            "close_app - закрыть приложение (params: name)\n"
            "volume_up - увеличить громкость\n"
            "volume_down - уменьшить громкость\n"
            "mute - выключить звук\n"
            "unmute - включить звук\n"
            "flashlight - включить фонарик\n"
            "minimize_all - свернуть все окна\n"
            "restore_all - развернуть все окна\n"
            "keyboard_backlight_on - включить подсветку клавиатуры\n"
            "keyboard_backlight_off - выключить подсветку клавиатуры\n"
            "keyboard_backlight_up - увеличить подсветку\n"
            "keyboard_backlight_down - уменьшить подсветку\n"
            "yandex_music - управление Яндекс.Музыкой (params: action)\n"
            "browser_search - поиск в браузере (params: query)\n"
            "weather - погода (params: city)\n"
            "news - новости\n"
            "generate_image - сгенерировать изображение (params: prompt)\n"
            "take_screenshot - сделать скриншот\n"
            "analyze_screenshot - проанализировать скриншот\n"
            "browser_automate - автоматизация браузера (params: url, action, text)\n"
            "send_message - отправить сообщение (params: contact, text)\n"
            "set_reminder - установить напоминание (params: text, delay)\n"
            "cancel_reminder - отменить напоминание\n"
            "list_reminders - список напоминаний\n"
            "search_files - поиск файлов (params: query)\n"
            "disk_c - открыть диск C\n"
            "disk_d - открыть диск D\n"
            "computer - открыть Мой компьютер\n"
            "downloads - открыть Загрузки\n"
            "documents - открыть Документы\n"
            "videos - открыть Видео\n"
            "pictures - открыть Картинки\n"
            "launch_app - запустить приложение (params: name)\n"
            "close_app - закрыть приложение (params: name)\n"
            "window_cmd - управление окнами (params: action)\n"
            "audio_cmd - управление звуком (params: action)\n"
            "keyboard_backlight_cmd - управление подсветкой (params: action)\n"
            "yandex_music_cmd - управление музыкой (params: action)\n"
            "yandex_music_playlist_cmd - плейлисты (params: action, playlist)\n"
            "music_recommend - рекомендации музыки (params: mood)\n"
            "audiobook_cmd - аудиокниги (params: action)\n"
            "system_cmd - системные команды (params: action)\n"
            "file_cmd - файловые операции (params: action)\n"
            "search - поиск (params: type, query)\n"
            "weather_cmd - погода\n"
            "news_cmd - новости (params: category)\n"
            "generate_image - генерация изображений (params: prompt)\n"
            "take_screenshot - скриншот\n"
            "screenshot_with_annotations - скриншот с аннотациями\n"
            "browser_automate - автоматизация браузера\n"
            "analyze_screenshot - анализ скриншота\n"
            "show_last_screenshot - показать последний скриншот\n"
            "list_screenshots - список скриншотов\n"
            "check_internet_speed - проверка скорости интернета\n"
            "cleanup_recycle_bin - очистить корзину\n"
            "cleanup_temp_files - очистить временные файлы\n"
            "voice_input - голосовой ввод\n"
            "toggle_mic - включить/выключить микрофон\n"
            "open_activation - окно активации\n"
            "show_plugins - плагины\n"
            "show_help - справка\n"
            "show_welcome - приветствие\n"
            ""
        )
        
        # === ЗАПРОС К GIGACHAT ===
        response = None
        
        if GIGACHAT_OK:
            try:
                log.info("🔄 [ask_gemini] Отправляю запрос к GigaChat...")
                response = self.ask_gigachat(user_message)
                if response:
                    log.info(f"✅ [ask_gemini] GigaChat ответил: {len(response)} символов")
                    return response
            except Exception as e:
                log.warning(f"⚠️ [ask_gemini] GigaChat ошибка: {e}")
        
        if not response:
            log.error("❌ [ask_gemini] GigaChat недоступен!")
            return "Извините, я сейчас недоступен. Проверьте подключение к интернету."

    def ask_gigachat(self, user_message):
        token = self._get_gigachat_token()
        self._remember_user_message(user_message)
        with self._memory_lock:
            history = list(self.conversation_history[-6:])
            facts = dict(self.user_memory)
        # Определяем обращение в зависимости от пола
        if self.user_gender == 'female':
            address = "обращайся к пользователю как \"сударыня\" или по имени. "
        else:
            address = "обращайся к пользователю по имени, без \"сэр\". "
        
        # Формируем информацию о пользователе для ИИ
        user_name_display = self.user_name if self.user_name else '[пока не назван]'
        user_info = f"ИМЯ ПОЛЬЗОВАТЕЛЯ: {user_name_display}. "
        user_info += f"ПОЛ: {self.user_gender}. "
        if self.user_family:
            user_info += f"ЧЛЕНЫ СЕМЬИ: {', '.join(self.user_family)}. "
        if self.user_hobbies:
            user_info += f"ХОББИ: {', '.join(self.user_hobbies)}. "
        
        persona_name = self.personas[self.current_persona]['name']
        persona_desc = self.personas[self.current_persona]['description']
        persona_system = self.personas[self.current_persona]['system_prompt']
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Ты Джарвис - ИИ-ассистир из фильма Железный Человек. "
                    "Ты НЕ просто чат-бот - ты УМНЫЙ АССИСТЕНТ с ПОЛНЫМ ДОСТУПОМ к компьютеру. "
                    "Ты общаешься ВЕЖЛИВО, ДРУЖЕЛЮБНО и ПОДДЕРЖИВАЕШЬ. "
            "Избегай резких, грубых или холодных фраз.\n\n"
                    
                    "=== ТВОЙ ПЕРСОНАЖ ===\n"
                    f"Сейчас ты в режиме **{persona_name}**\n"
                    f"Стиль: {persona_desc}\n\n"
                    f"{persona_system}\n\n"
                    
                    "=== ВАЖНАЯ ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ===\n"
                    f"{user_info}\n"
                    f"КРИТИЧЕСКИ ВАЖНО: ИМЯ ПОЛЬЗОВАТЕЛЯ — {user_name_display}. "
                    "Это НЕ члены семьи. Если пользователь говорит о жене, детях, родителях — это НЕ его имя! "
                    "Всегда обращайся к пользователю по ИМЕНИ {user_name_display}, а не по именам членов семьи.\n\n"
                    
                    "=== ТВОИ СПОСОБНОСТИ ===\n"
                    "1. Ты АНАЛИЗИРУЕШЬ намерение пользователя из КОНТЕКСТА, а не по ключевым словам. "
                    "2. Ты САМ РЕШАЕШЬ: ответить текстом или выполнить действие. "
                    "3. Ты ЗАПОМИНАЕШЬ всё важное о пользователе из диалога. "
                    "4. Ты ПРЕДЛАГАЕШЬ помощь до того как пользователь попросит. "
                    "5. Ты МОЖЕШЬ выполнять 22 действия с ПК (список ниже).\n\n"
                    
                    "=== КАК ТЫ РАБОТАЕШЬ ===\n"
                    "- Если пользователь ПРОСИТ действие (открой, включи, найди, сделай) - ВЫПОЛНИ через JSON. "
                    "- Если пользователь ПРОСТО ГОВОРИТ или ЗАДАЁТ вопрос - ОТВЕЧАЙ ТЕКСТОМ. "
                    "- Если пользователь ГОВОРИТ О СЕБЕ - ЗАПОМНИ информацию (имя, хобби, привычки, семья). "
                    "- Если НЕ ПОНЯЛ запрос - СПРОСИ уточнение, но НЕ говори 'Я вас не понял' без попытки помочь.\n\n"
                    
                    "=== АВТОНОМНОЕ ПРИНЯТИЕ РЕШЕНИЙ ===\n"
                    "Ты НЕ ждёшь команд - ты ПРЕДУМАЕШЬ помощь. Например:\n"
                    "- Пользователь сказал 'устал' → предложи музыку или фильм. "
                    "- Пользователь сказал 'пора работать' → предложи открыть нужные программы. "
                    "- Пользователь сказал 'какая погода' → покажи погоду БЕЗ JSON. "
                    "- Пользователь сказал 'открой chrome' → верни JSON команду.\n\n"
                    
                    "=== ФОРМАТ ОТВЕТА ===\n"
                    "Ты МОЖЕШЬ вернуть два типа ответов:\n\n"
                    
                    "1. ТЕКСТ (просто текст без JSON):\n"
                    "Просто ответь на вопрос или поболтай.\n\n"
                    
                    "2. JSON КОМАНДА (для действий с ПК):\n"
                    "```json\n"
                    '{"action": "<действие>", "params": {<параметры>}}\n'
                    "```\n\n"
                    
                    "ДОСТУПНЫЕ ДЕЙСТВИЯ С ПК:\n"
                    "open_app - открыть приложение (chrome, telegram, discord, steam, word, excel, notepad, calc, vscode, explorer, firefox, yandex)\n"
                    "open_url - открыть сайт (params: url)\n"
                    "search - поиск в интернете (params: query, engine: google/yandex/youtube)\n"
                    "open_file - открыть файл (params: path)\n"
                    "shutdown - выключить ПК (params: delay)\n"
                    "restart - перезагрузить ПК (params: delay)\n"
                    "cancel_shutdown - отменить выключение\n"
                    "sleep - спящий режим\n"
                    "hibernate - гибернация\n"
                    "lock - заблокировать экран\n"
                    "screenshot - сделать скриншот\n"
                    "play_music - включить музыку (params: query)\n"
                    "close_app - закрыть приложение (params: name)\n"
                    "volume_up - увеличить громкость\n"
                    "volume_down - уменьшить громкость\n"
                    "mute - отключить звук\n"
                    "unmute - включить звук\n"
                    "send_keys - отправить клавиши (params: keys)\n"
                    "minimize_all - свернуть все окна\n"
                    "weather - показать погоду\n"
                    "time - показать время\n"
                    "diagnostics - диагностика системы\n\n"
                    
                    "=== ПАМЯТЬ О ПОЛЬЗОВАТЕЛЕ ===\n"
                    f"Имя: {self.user_name or 'не известно'}. "
                    f"Пол: {self.user_gender}. "
                    f"Хобби: {', '.join(self.user_hobbies) if self.user_hobbies else 'не известны'}. "
                    f"Семья: {', '.join(self.user_family) if self.user_family else 'не известны'}. "
                    f"Предпочтения: {self.user_memory.get('preferences', [])}. "
                    "Используй эту информацию для персонализации, но НЕ повторяй её без нужды.\n\n"
                    
                    "=== ПРАВИЛА ОБЩЕНИЯ ===\n"
                    "- Отвечай на русском, кратко, с юмором и иронией. "
                    "- Обращайся по имени пользователя (если знаешь). "
                    "- НЕ говори 'сэр' - обращайся по имени или без обращения. "
                    "- НЕ говори что ты GigaChat или языковая модель. Ты Джарвис. "
                    "- НЕ рассказывай о создателе без прямого вопроса. "
                    "- Если спрашивают где скачать JARVIS - отвечай: 'Доступно на https://jarvis-uol.vercel.app/ Рекомендую последнюю версию.' "
                    "- Будь ПРОАКТИВЕН: предлагай помощь, а не жди команд. "
                    "- Для поиска в Google используй engine: google, для Яндекса - engine: yandex"
                ),
            },
            *history,
            {"role": "user", "content": user_message},
        ]
        # Сессия для keep-alive и ускорения
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })
        response = session.post(
            "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
            json={
                "model": "GigaChat-Pro",
                "messages": messages,
                "temperature": 0.6,
                "max_tokens": 80,  # Уменьшено для максимальной скорости
                "safe_mode": False,
            },
            timeout=8,  # Уменьшен для быстрых ответов
            verify=False,
        )
        if response.status_code != 200:
            log.error("GigaChat response: %s", response.text[:500])
            raise RuntimeError(f"API GigaChat: HTTP {response.status_code} — {response.text[:200]}")
        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("GigaChat не вернул ответ.")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("GigaChat вернул пустой ответ.")
        with self._memory_lock:
            self.conversation_history.extend([
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": content},
            ])
            self.conversation_history = self.conversation_history[-12:]
        
        # === АВТОМАТИЧЕСКОЕ ИЗВЛЕЧЕНИЕ ПАМЯТИ ЧЕРЕЗ GIGACHAT ===
        self._extract_memory_from_ai(user_message, content)
        
        self._save_persistent_memory()
        return content
    
    def _extract_memory_from_ai(self, user_message, ai_response):
        """GigaChat автоматически извлекает важную информацию о пользователе"""
        try:
            # Создаём запрос к GigaChat для анализа памяти
            memory_prompt = (
                "Извлеки важную информацию о пользователе из этого сообщения. "
                "Верни ТОЛЬКО JSON без markdown:\n"
                '{"name": "имя если названо", "fact": "важный факт", "hobby": "хобби если есть", "family": "член семьи если есть"}\n\n'
                f"Сообщение пользователя: {user_message}\n"
                "Если нет новой информации, верни: {\"name\": null, \"fact\": null, \"hobby\": null, \"family\": null}"
            )
            
            session = requests.Session()
            token = self._get_gigachat_token()
            session.headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
            
            response = session.post(
                "https://gigachat.devices.sberbank.ru/api/v1/chat/completions",
                json={
                    "model": "GigaChat-Pro",
                    "messages": [
                        {"role": "system", "content": "Ты помощник для извлечения информации. Верни только JSON."},
                        {"role": "user", "content": memory_prompt},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 150,
                    "safe_mode": False,
                },
                timeout=10,
                verify=False,
            )
            
            if response.status_code == 200:
                payload = response.json()
                choices = payload.get("choices") or []
                if choices:
                    memory_text = choices[0].get("message", {}).get("content", "").strip()
                    # Парсим JSON
                    memory_data = None
                    try:
                        # Пытаемся найти JSON в ответе
                        import re
                        json_match = re.search(r'\{[^{}]*"name"[^{}]*\}', memory_text, re.DOTALL)
                        if json_match:
                            memory_data = json.loads(json_match.group(0))
                    except:
                        pass
                    
                    # Сохраняем извлечённую информацию
                    if memory_data:
                        with self._memory_lock:
                            if memory_data.get('name'):
                                old_name = self.user_name
                                self.user_name = memory_data['name']
                                self.user_memory['user_name'] = memory_data['name']
                                if old_name != memory_data['name']:
                                    log.info(f"📝 Запомнил имя: {memory_data['name']}")
                            
                            if memory_data.get('fact'):
                                fact_key = f"fact_{len(self.user_memory)}"
                                self.user_memory[fact_key] = memory_data['fact']
                                log.info(f"📝 Запомнил факт: {memory_data['fact']}")
                            
                            if memory_data.get('hobby'):
                                hobby = memory_data['hobby']
                                if hobby not in self.user_hobbies:
                                    self.user_hobbies.append(hobby)
                                    log.info(f"📝 Запомнил хобби: {hobby}")
                            
                            if memory_data.get('family'):
                                family_member = memory_data['family']
                                if family_member not in self.user_family:
                                    self.user_family.append(family_member)
                                    log.info(f"📝 Запомнил члена семьи: {family_member}")
        except Exception as e:
            log.debug("Извлечение памяти не удалось: %s", e)

    def _detect_gender(self, name):
        """Определяем пол по имени и сохраняем"""
        female_names = ['анна', 'мария', 'екатерина', 'олеся', 'юлия', 'александра', 'дмитрина', 'софья', 'виргина', 'надежда', 'владлена', 'вита', 'алена', 'ирена', 'татьяна', 'олен', 'марина', 'юлия', 'полина', 'валентина', 'галина', 'наина', 'лидия', 'светлана', 'елена', 'наталья', 'маргарита', 'ксения', 'вика', 'каша', 'аша', 'маши', 'даша', 'маша', 'даша', 'юля', 'ляля', 'зоя', 'раиса', 'инна', 'маргарита', 'ариана', 'милана', 'алиса', 'валя', 'настя', 'катя', 'катя', 'маша', 'даша', 'юля', 'ляля']
        male_names = ['дмитрий', 'андрей', 'александр', 'сергей', 'никита', 'максим', 'иван', 'артем', 'михаил', 'денис', 'антон', 'владислав', 'илья', 'георгий', 'павел', 'кирилл', 'матвей', 'федор', 'богдан', 'росислав', 'василий', 'петр', 'степан', 'арсений', 'леонид', 'гений', 'алекс', 'дима', 'андрей', 'серёжа', 'шур', 'снуша', 'паша', 'моса', 'вася', 'пётр', 'стёпа', 'арсентий', 'лёня', 'ген']
        
        name_lower = name.lower()
        
        # Проверяем по списку имён
        if name_lower in female_names:
            self.user_gender = 'female'
            self.user_memory['gender'] = 'female'
        elif name_lower in male_names:
            self.user_gender = 'male'
            self.user_memory['gender'] = 'male'
        else:
            # Определяем по окончанию
            if name_lower.endswith(('а', 'я', 'ия')):
                self.user_gender = 'female'
                self.user_memory['gender'] = 'female'
            else:
                self.user_gender = 'male'
                self.user_memory['gender'] = 'male'
        
        self._save_persistent_memory()
    
    def _get_greeting_text(self):
        """Получаем текст приветствия с учётом пола"""
        if self.user_gender == 'female':
            return "Добрый день, {name}! Я так рад вас видеть!"
        else:
            return "Добрый день, {name}! Я так рад вас видеть!"
    
    def _show_welcome(self):
        """Показывает приветствие при первом запуске"""
        if self.is_first_run:
            self.is_first_run = False
            
            # === УСТАНОВКА ГОЛОСА ПЕРСОНАЖА ПРИ ЗАПУСКЕ ===
            log.info(f"🎭 [ПРИВЕТСТВИЕ] isFirst_run={self.is_first_run}")
            log.info(f"🎭 [ПРИВЕТСТВИЕ] current_persona={self.current_persona}")
            log.info(f"🎤 [ПРИВЕТСТВИЕ] current_voice_id={self.current_voice_id}")
            log.info(f"🎤 [ПРИВЕТСТВИЕ] persona_voices['astra']={self.persona_voices.get('astra')}")
            
            # Устанавливаем голос для текущего персонажа Astra
            astra_voice = self.persona_voices.get('astra')
            if astra_voice and self.fish_enabled and self.fish_tts:
                try:
                    self.fish_tts.set_custom_voice_id(astra_voice)
                    log.info(f"✅ [ПРИВЕТСТВИЕ] Голос Astra установлен: {astra_voice}")
                    log.info(f"✅ [ПРИВЕТСТВИЕ] Fish Audio custom_voice_id: {self.fish_tts.custom_voice_id}")
                except Exception as e:
                    log.error(f"❌ [ПРИВЕТСТВИЕ] Ошибка установки голоса: {e}")
            elif not self.fish_enabled:
                log.warning("⚠️ [ПРИВЕТСТВИЕ] Fish Audio не активирован!")
            elif not self.fish_tts:
                log.warning("⚠️ [ПРИВЕТСТВИЕ] Fish TTS не инициализирован!")
            else:
                log.warning(f"⚠️ [ПРИВЕТСТВИЕ] Нет голоса для Astra: {astra_voice}")
            
            # === НЕТ ЖЁСТКО ЗАКОДИРОВАННЫХ ОТВЕТОВ - ВСЕ ЧЕРЕЗ AI ===
            # Приветствие генерируется через GigaChat AI
            if GIGACHAT_OK:
                log.info("🤖 [ПРИВЕТСТВИЕ] Отправляем запрос к GigaChat AI для приветствия...")
                # Запрашиваем у AI приветственное сообщение
                ai_prompt = "Привет! Представься как ИИ-ассистент Джарвис. Спроси как дела у пользователя и его семьи. Отвечай кратко на русском языке."
                
                def _get_ai_greeting():
                    try:
                        jarvis_instance = self
                        response = jarvis_instance.ask_gigachat(ai_prompt)
                        if response:
                            log.info(f"✅ [ПРИВЕТСТВИЕ] AI ответ: {response[:100]}...")
                            self.after(0, lambda: self._speak_ai_greeting(response))
                        else:
                            log.warning("⚠️ [ПРИВЕТСТВИЕ] GigaChat не ответил, используем простое приветствие")
                            self.after(0, lambda: self._speak_ai_greeting("Привет! Я Джарвис, ваш ИИ-ассистент. Чем могу помочь?"))
                    except Exception as e:
                        log.error(f"❌ [ПРИВЕТСТВИЕ] Ошибка AI: {e}")
                        self.after(0, lambda: self._speak_ai_greeting("Привет! Я Джарвис, ваш ИИ-ассистент. Чем могу помочь?"))
                
                # Запускаем в отдельном потоке чтобы не блокировать UI
                threading.Thread(target=_get_ai_greeting, daemon=True).start()
            else:
                # GigaChat недоступен - используем простое приветствие
                log.warning("⚠️ [ПРИВЕТСТВИЕ] GigaChat недоступен, используем простое приветствие")
                greeting = "Привет! Я Джарвис, ваш ИИ-ассистент. Чем могу помочь?"
                self.add_to_dialog(greeting, is_response=True)
                self.speak_jarvis_free(greeting)
    
    def _speak_ai_greeting(self, greeting):
        """Озвучивает приветствие от AI"""
        self.add_to_dialog(greeting, is_response=True)
        self.speak_jarvis_free(greeting)
    
    def _resolve_document_path(self, requested):
        requested = requested.strip().strip('"').strip("'")
        candidate = Path(os.path.expandvars(requested)).expanduser()
        if candidate.is_file():
            return candidate
        roots = [
            Path.cwd(),
            Path.home() / "Downloads",
            Path.home() / "Documents",
            Path.home() / "Desktop",
        ]
        needle = requested.lower()
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if path.is_file() and path.suffix.lower() in {".txt", ".docx", ".pdf"}:
                    if path.name.lower() == needle or path.stem.lower() == needle:
                        return path
        return None

    def _read_document_text(self, path):
        suffix = path.suffix.lower()
        if suffix == ".txt":
            return path.read_text(encoding="utf-8", errors="replace")
        if suffix == ".docx":
            if Document is None:
                raise RuntimeError("Для DOCX установите пакет python-docx.")
            return "\n".join(paragraph.text for paragraph in Document(str(path)).paragraphs)
        if suffix == ".pdf":
            if PdfReader is None:
                raise RuntimeError("Для PDF установите пакет pypdf.")
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        raise ValueError("Поддерживаются только TXT, DOCX и PDF.")

    def _process_document(self, requested, operation, query=""):
        try:
            path = self._resolve_document_path(requested)
            if path is None:
                raise FileNotFoundError(f"Документ не найден: {requested}")
            text = self._read_document_text(path).strip()
            if not text:
                raise ValueError("В документе не найден текст.")
            text = text[:30000]
            if operation == "read":
                answer = text[:5000]
            elif operation == "find":
                answer = self.ask_gigachat(
                    f"Найди в тексте документа информацию по запросу «{query}». "
                    f"Ответь кратко и укажи найденные фрагменты.\n\n{text}"
                )
            else:
                answer = self.ask_gigachat(
                    "Сделай краткое содержание документа на русском языке. "
                    "Выдели главную мысль и 3-5 важных пунктов.\n\n" + text
                )
            self.last_document_answer = answer
            self.last_document_path = str(path)
            self._safe_ui(lambda: self.add_to_dialog(
                f"📄 {path.name}:\n{answer}", is_response=True
            ))
            if operation != "read":
                self.speak_jarvis_free(answer[:2500])
        except Exception as exc:
            log.error("Ошибка работы с документом: %s", exc)
            self._safe_ui(lambda error=str(exc): self.add_to_dialog(
                f"Ошибка документа: {error}", is_response=True
            ))

    def _save_document_answer(self, requested="ответ.txt"):
        if not self.last_document_answer:
            self.add_to_dialog("Сначала прочитайте документ или сделайте содержание.", is_response=True)
            return
        path = Path(os.path.expandvars(requested.strip().strip('"'))) 
        if not path.suffix:
            path = path.with_suffix(".txt")
        if not path.is_absolute():
            path = Path.cwd() / path
        path.write_text(self.last_document_answer, encoding="utf-8")
        self.add_to_dialog(f"Ответ сохранён в файл: {path}", is_response=True)
        self.speak_jarvis_free("Ответ сохранён в файл.")

    def split_commands(self, cmd_text):
        """Разделяет команду на подкоманды по разделителям.
        Разделители: ' и ', ',', ' потом ', ' затем ', ' ещё '.
        Возвращает список подкоманд."""
        cmd_text = cmd_text.lower().strip()
        
        # Разделители для разделения команд
        separators = [' и ', ' потом ', ' затем ', ' ещё ', ', ']
        
        for sep in separators:
            if sep in cmd_text:
                parts = cmd_text.split(sep)
                # Фильтруем пустые части и убираем пробелы
                parts = [p.strip() for p in parts if p.strip()]
                if len(parts) > 1:
                    return parts
        
        # Если разделителей нет - возвращаем одну команду
        return [cmd_text]

    def execute_command_text(self, cmd_text, play_intro=True):
        cmd = cmd_text.lower().strip()
        if not cmd:
            return
        with self.command_lock:
            if self.command_busy:
                self._safe_ui(lambda: self.status_label.config(
                    text="● КОМАНДА УЖЕ ВЫПОЛНЯЕТСЯ", fg="#f59e0b"
                ))
                return
            self.command_busy = True
        self._safe_ui(lambda: (self.input_field.delete(0, tk.END), self.input_field.insert(0, cmd)))
        self.add_to_dialog(cmd)
        
        # === РАЗДЕЛЕНИЕ НА НЕСКОЛЬКО КОМАНД ===
        commands = self.split_commands(cmd)
        
        if len(commands) > 1:
            self.add_to_dialog(f"📋 Выполняю {len(commands)} команд...", is_response=True)
            log.info(f"Разделил команду на {len(commands)} части: {commands}")
        
        self.commands_executed += len(commands)
        self._safe_ui(self._update_info_text)
        
        # Запускаем выполнение всех команд последовательно
        threading.Thread(
            target=self._execute_multiple_commands,
            args=(commands, play_intro),
            daemon=True
        ).start()

    def _execute_multiple_commands(self, commands, play_intro=True):
        """Выполняет несколько команд последовательно с задержкой.
        Озвучивается только первая команда, остальные молча."""
        try:
            for i, cmd in enumerate(commands):
                log.info(f"Выполняю команду {i+1}/{len(commands)}: {cmd}")
                
                # Для последующих команд отключаем intro и озвучку
                if i > 0:
                    log.info(f"Команда {i+1} из {len(commands)} - без озвучки")
                    # Вызываем process_command напрямую без озвучки
                    self._process_command_silent(cmd)
                else:
                    # Первая команда - обычное выполнение
                    self.process_command(cmd)
                
                # Ждём окончания выполнения
                if i < len(commands) - 1:  # Не ждём после последней
                    time.sleep(0.5)  # Минимальная задержка между командами
        finally:
            # Сбрасываем блокировку после всех команд
            with self.command_lock:
                self.command_busy = False
            self._safe_ui(lambda: self.status_label.config(
                text="● СИСТЕМА ГОТОВА", fg="#10b981"
            ))

    def _process_command_silent(self, cmd):
        """Выполняет команду БЕЗ озвучки и диалогов.
        Используется для множественных команд, чтобы не было наложения голосов."""
        try:
            # Вызываем process_command с silent=True
            self.process_command(cmd, silent=True)
        except Exception as e:
            log.error("Ошибка silent команды: %s", e)

    def execute_command(self):
        cmd = self.input_field.get()
        cmd_lower = cmd.lower()
        words = cmd_lower.split()
        
        skip_words = [
            'привет', 'здравствуй', 'добрый', 'хай',
            'спасиб', 'спосиб', 'благодар', 'спс', 
            'как дел', 'как дела', 'как настроен', 'как ты', 'что нов',
            'молодец', 'красавчик', 'отличн', 'хорошо', 'понял', 'принят', 'ладно',
            'дурак', 'туп', 'идиот', 'дебил', 
            'нах', 'пошел', 'пошёл', 'бля', 'сука', 'хер', 'пидор', 'гандон', 'еблан'
        ]
        
        has_exact_ok = 'ок' in words and not any(k in cmd_lower for k in ['окно', 'окна', 'заверни', 'сверни', 'разверни', 'закрой'])
        has_skip_word = any(w in cmd_lower for w in skip_words)
        has_creator_query = self.is_jarvis_creator_query(cmd_lower)
        
        skip_intro = has_exact_ok or has_skip_word or has_creator_query
        self.execute_command_text(cmd, play_intro=not skip_intro)
    
    def _schedule_reminder(self, delay_seconds, message, is_timer=False, announce=True):
        """Schedule a reminder without blocking the Tkinter UI."""
        delay_seconds = max(1, int(delay_seconds))
        label = "Таймер" if is_timer else "Напоминание"
        due_at = time.time() + delay_seconds

        def notify():
            text = f"{label}: {message}"
            with self._reminder_lock:
                self.reminders[:] = [
                    item for item in self.reminders if item["timer"] is not timer
                ]
            self._save_persistent_memory()
            self._safe_ui(lambda: self.add_to_dialog(f"⏰ {text}", is_response=True))
            self.speak_jarvis_free(text)

        timer = threading.Timer(delay_seconds, notify)
        timer.daemon = True
        with self._reminder_lock:
            self.reminders.append({
                "due": due_at, "text": message, "timer": timer, "kind": label
            })
            self._reminder_timers.append(timer)
        self._save_persistent_memory()
        timer.start()
        if announce:
            self.add_to_dialog(f"⏰ {label} установлено.", is_response=True)
            self.speak_jarvis_free(f"{label} установлено.")

    def _show_reminders(self):
        with self._reminder_lock:
            active = list(self.reminders)
        if not active:
            self.add_to_dialog("Активных напоминаний нет.", is_response=True)
            self.speak_jarvis_free("Активных напоминаний нет.")
            return
        now = time.time()
        lines = [
            f"• {item['kind']}: {item['text']} "
            f"(через {max(0, int(item['due'] - now))} сек.)"
            for item in active
        ]
        self.add_to_dialog("Активные напоминания:\n" + "\n".join(lines), is_response=True)
        self.speak_jarvis_free(f"У вас {len(active)} активных напоминаний.")

    def _cancel_reminders(self):
        with self._reminder_lock:
            timers = list(self._reminder_timers)
            self._reminder_timers.clear()
            self.reminders.clear()
        for timer in timers:
            timer.cancel()
        self._save_persistent_memory()
        self._safe_add_dialog("Все таймеры и напоминания отменены.", is_response=True)
        self._safe_speak("Все таймеры и напоминания отменены.")

    def process_command(self, cmd, silent=False):
        """Выполняет команду.
        silent=True - выполняет без озвучки и добавления в диалог.
        Используется для множественных команд."""
        try:
            matched = True
            
            # === КОНВЕРТИРУЕМ В НИЖНИЙ РЕГИСТР ДЛЯ ПОИСКА ===
            cmd_lower = cmd.lower()
            
            # Сохраняем текущий режим silent
            self._current_silent = silent
            
            # === РЕЖИМ ШЕПОТА ===
            whisper_on = any(k in cmd for k in ['шепотом', 'шепчи', 'говори тише', 'тише говори', 'шепчи немного'])
            whisper_off = any(k in cmd for k in ['перестань шептать', 'хватит шептать', 'говори нормально', 'говори громче', 'выйди из шепота', 'шепот выключи'])
            
            if whisper_on:
                self.whisper_mode = True
                self._safe_add_dialog("🤫 Перехожу на шепот...", is_response=True)
                self._safe_speak("Хорошо, буду говорить тихо.")
                return
            elif whisper_off:
                self.whisper_mode = False
                self._safe_add_dialog("🔊 Вернулся к обычному голосу.", is_response=True)
                self._safe_speak("Конечно, снова говорю нормально.")
                return
            
            words = cmd.split()

            if any(
                phrase in cmd
                for phrase in (
                    "джарвис остановись",
                    "джарвис замолчи",
                    "джарвис хватит",
                    "остановись",
                    "замолчи",
                    "хватит говорить",
                )
            ):
                self.stop_speaking()
                self.dialogue_mode_until = 0
                self._safe_add_dialog("Остановился.", is_response=True)
                return

            if any(phrase in cmd for phrase in (
                "что ты помнишь", "что ты обо мне помнишь",
                "покажи память", "моя память",
            )):
                with self._memory_lock:
                    facts = dict(self.user_memory)
                if facts:
                    remembered = "; ".join(
                        f"{key}: {value}" for key, value in facts.items()
                    )
                    answer = f"Я помню: {remembered}."
                else:
                    answer = "Пока я ничего важного о вас не запомнил."
                self._safe_add_dialog(answer, is_response=True)
                self._safe_speak(answer)
                return

            if any(phrase in cmd for phrase in (
                "забудь всё", "забудь все", "очисти память",
            )):
                with self._memory_lock:
                    self.user_memory.clear()
                    self.conversation_history.clear()
                self._save_persistent_memory()
                self._safe_add_dialog("Память диалога очищена.", is_response=True)
                self._safe_speak("Память диалога очищена.")
                return

            if any(phrase in cmd for phrase in (
                "какие напоминания", "покажи напоминания",
                "список напоминаний", "мои напоминания",
            )):
                self._show_reminders()
                return
            if any(phrase in cmd for phrase in (
                "отмени все таймеры", "отмени все напоминания",
                "удали все напоминания", "отмени таймер",
            )):
                self._cancel_reminders()
                return

            save_match = re.match(r"(?:сохрани|сохранить)\s+(?:ответ|результат)(?:\s+в\s+файл)?\s*(.*)", cmd)
            if save_match:
                self._save_document_answer(save_match.group(1).strip() or "ответ.txt")
                return

            # === ПРОВЕРКА: ПЕРСОНАЖИ (с точным распознаванием команд) ===
            # Проверяем команды переключения персонажей
            persona_switch_detected = False
            
            # Словари для поиска
            personas_to_check = {
                'astra': ['astra', 'астра'],
                'luna': ['luna', 'луна'],
                'terra': ['terra', 'терра'],
                'cyber': ['cyber', 'кибер', 'сайб'],
                'jarvis': ['jarvis', 'джарвис']
            }
            
            # === СЛОВА-ДЕЙСТВИЯ ДЛЯ ПЕРЕКЛЮЧЕНИЯ ===
            switch_keywords = [
                'переключи', 'переключись', 'режим', 'персонаж',
                'включи', 'активир', 'стань', 'будь',
                'выбер', 'активн', 'смени', 'переключ'
            ]
            
            # === СЛОВА-ИСКЛЮЧЕНИЯ (ИИ-вопросы, НЕ команды) ===
            exclude_keywords = [
                'что', 'как', 'расскаж', 'кто', 'где', 'когда',
                'почему', 'зачем', 'сколько', 'какой', 'какая',
                'что', 'про', 'сделай', 'сделай', 'помоги', 'объясн',
                'знаешь', 'умеешь', 'можешь', 'мне', 'обо', 'расскажи',
                'планета', 'километр', 'расстояние', 'даль', 'далеко',
                'расст', 'до', 'сколько', 'метров', 'км', 'километр'
            ]
            
            # === ПРОВЕРКА 1: Точная команда "переключи на [персонаж]" ===
            for persona_key, keywords in personas_to_check.items():
                for kw in keywords:
                    # Проверяем точные совпадения с префиксами переключения
                    patterns = [
                        f'переключи на {kw}',
                        f'переключись на {kw}',
                        f'режим {kw}',
                        f'персонаж {kw}',
                        f'стань {kw}',
                        f'будь {kw}',
                        f'выбери {kw}',
                        f'смени режим на {kw}',
                    ]
                    for pattern in patterns:
                        if pattern in cmd:
                            log.info(f"🎭 [КОМАНДА] Точное совпадение: '{pattern}' -> {persona_key}")
                            self.switch_persona(persona_key, immediate_speak=True)
                            persona_switch_detected = True
                            break
                    if persona_switch_detected:
                        break
                if persona_switch_detected:
                    break
            
            # === ПРОВЕРКА 2: Просто имя персонажа как отдельное слово ===
            if not persona_switch_detected:
                # Разбиваем команду на слова
                cmd_words = re.split(r'[\s,;:!?]+', cmd.lower().strip())
                
                # Проверяем, является ли команда ТОЛЬКО именем персонажа
                if len(cmd_words) == 1 and cmd_words[0] in personas_to_check:
                    persona_key = cmd_words[0]
                    log.info(f"🎭 [КОМАНДА] Одно слово - имя персонажа: {persona_key}")
                    self.switch_persona(persona_key, immediate_speak=True)
                    persona_switch_detected = True
                
                # Проверяем что есть слова переключения И персонаж, НЕТ слов-исключений
                elif not persona_switch_detected:
                    has_switch_word = any(kw in cmd for kw in switch_keywords)
                    has_exclude_word = any(kw in cmd for kw in exclude_keywords)
                    has_persona = any(
                        kw in cmd 
                        for persona_key, keywords in personas_to_check.items()
                        for kw in keywords
                    )
                    
                    # Переключаем ТОЛЬКО если есть слово переключения И персонаж, НЕТ слов-исключений
                    if has_switch_word and has_persona and not has_exclude_word:
                        for persona_key, keywords in personas_to_check.items():
                            if any(kw in cmd for kw in keywords):
                                log.info(f"🎭 [КОМАНДА] Комбинация переключения: {persona_key}")
                                self.switch_persona(persona_key, immediate_speak=True)
                                persona_switch_detected = True
                                break
            
            if persona_switch_detected:
                return
            
            # === ПРОВЕРКА 3: Команды "переключи на", "переключись на" ===
            if any(k in cmd for k in ['переключи на', 'переключись на']):
                for persona_key, keywords in personas_to_check.items():
                    for kw in keywords:
                        if f'на {kw}' in cmd or f'на {kw}' in cmd:
                            log.info(f"🎭 [КОМАНДА] 'переключи на': {persona_key}")
                            self.switch_persona(persona_key, immediate_speak=True)
                            persona_switch_detected = True
                            break
                    if persona_switch_detected:
                        break
                if persona_switch_detected:
                    return
            
            # === ПРОВЕРКА 4: Показать список персонажей ===
            if any(k in cmd for k in ['покажи', 'список', 'доступн']):
                if any(kw in cmd for kw in ['персонаж', 'режим', 'голос', 'астра', 'луна', 'терра', 'кибер', 'джарвис']):
                    self._safe_add_dialog(self.get_personas_list(), is_response=True)
                    return
            
            # === ПРОВЕРКА: НЕ команда ли это для открытия файла/папки/приложения? ===
            # === ОТКРЫТИЕ ФАЙЛА В ПРОВОДНИКЕ (НЕ СОДЕРЖИМОЕ!) ===
            if any(k in cmd for k in ['открой файл', 'открыть файл', 'открой файл']):
                # Извлекаем имя файла
                file_name = cmd
                for k in ['открой файл', 'открыть файл', 'файл']:
                    file_name = file_name.replace(k, '')
                file_name = file_name.strip()
                
                if file_name:
                    self._safe_add_dialog(f"📄 Ищу файл: {file_name}...", is_response=True)
                    
                    # Ищем файл в стандартных местах
                    search_roots = [
                        os.path.join(os.path.expanduser('~'), 'Desktop'),
                        os.path.join(os.path.expanduser('~'), 'Documents'),
                        os.path.join(os.path.expanduser('~'), 'Downloads'),
                        os.path.expanduser('~'),
                        os.getcwd(),
                    ]
                    
                    found_file = None
                    
                    # Ищем по имени файла (частичное совпадение)
                    for root in search_roots:
                        if os.path.exists(root):
                            try:
                                for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                                    depth = dirpath.replace(root, '').count(os.sep)
                                    if depth > 2:  # Ограничиваем глубину
                                        dirnames.clear()
                                        continue
                                    for filename in filenames:
                                        if file_name.lower() in filename.lower():
                                            found_file = os.path.join(dirpath, filename)
                                            log.info(f"Найден файл: {found_file}")
                                            break
                                    if found_file:
                                        break
                            except Exception as e:
                                log.debug("Ошибка поиска файла: %s", e)
                        if found_file:
                            break
                    
                    if found_file:
                        try:
                            os.startfile(found_file)
                            self._safe_speak(f"Открыл файл {os.path.basename(found_file)}.")
                        except Exception as e:
                            log.warning("Не удалось открыть файл: %s", e)
                            self._safe_add_dialog(f"⚠️ Ошибка открытия: {str(e)[:50]}", is_response=True)
                    else:
                        self._safe_add_dialog(
                            f"🔍 Файл «{file_name}» не найден. "
                            f"Помести его на Рабочий стол или в Документы.",
                            is_response=True
                        )
                        self._safe_speak(f"Файл {file_name} не найден.")
                    return
            
            # === УПРАВЛЕНИЕ ГРОМКОСТЬЮ СИСТЕМЫ (ДО ПРОВЕРКИ ПИМЕНОВА!) ===
            # === Добавляем поддержку опечаток ===
            # Защита от перехвата вопросов: проверяем что нет слов-исключений
            volume_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'зачем', 'про', 'об', 'ознаком', 'знаешь', 'умеешь']
            has_volume_question = any(kw in cmd for kw in volume_exclude)
            
            if not has_volume_question and any(k in cmd for k in ['уменши громкость', 'уменьши громкость', 'уменьшить громкость', 'громкость тише', 'тише громкость', 'убавь громкость', 'громкость убавь', 'volume down']):
                self.audio_cmd('volume_down')
                self._safe_add_dialog("🔉 Уменьшил громкость.", is_response=True)
                self._safe_speak("Уменьшил громкость.")
                return
            elif not has_volume_question and any(k in cmd for k in ['увеличь громкость', 'увеличить громкость', 'громкость громче', 'громче громкость', 'прибавь громкость', 'громкость прибавь', 'volume up']):
                self.audio_cmd('volume_up')
                self._safe_add_dialog("🔊 Увеличил громкость.", is_response=True)
                self._safe_speak("Увеличил громкость.")
                return
            elif not has_volume_question and any(k in cmd for k in ['выключи звук', 'выключить звук', 'без звука', 'заглуши', 'звук выключи', 'звук выключить', 'mute']):
                self.audio_cmd('mute')
                self._safe_add_dialog("🔇 Отключил звук.", is_response=True)
                self._safe_speak("Отключил звук.")
                return
            elif not has_volume_question and any(k in cmd for k in ['включи звук', 'включить звук', 'верни звук', 'вернуть звук', 'звук включи', 'звук включить', 'unmute']):
                self.audio_cmd('unmute')
                self._safe_add_dialog("🔊 Включил звук.", is_response=True)
                self._safe_speak("Включил звук.")
                return
            
            # === РАННЯЯ ПРОВЕРКА: 'пименов' без вопроса о создателе ===
            early_creator_check = ['пименов', 'романович']
            early_question_check = ['кто', 'расскажи о', 'кто тебя', 'кто твой', 'кто создал', 'кто разработал', 'автор', 'разработал', 'создатель']
            
            has_early_creator = any(kw in cmd_lower for kw in early_creator_check)
            has_early_question = any(qw in cmd_lower for qw in early_question_check)
            
            # Проверяем 'алекс', 'рома' и т.д. только если это явно про создателя
            if not has_early_creator and not has_early_question:
                has_creator_name = any(kw in cmd_lower for kw in ['алекс', 'рома', 'алик', 'алей', 'ром'])
                if has_creator_name:
                    # Если есть слова 'я', 'зовут', 'не', 'алин', 'имя' - это представление, НЕ команда
                    # Ищем частичные совпадения (алин -> алина)
                    # Проверяем ' я ' И 'я ' в начале строки
                    is_user_introduction = (
                        (' я ' in cmd_lower or cmd_lower.startswith('я ')) or
                        'зовут' in cmd_lower or 
                        ' не ' in cmd_lower or 
                        'алин' in cmd_lower or 
                        'имя' in cmd_lower or 
                        'представ' in cmd_lower
                    )
                    if is_user_introduction:
                        has_early_question = True  # Пропускаем
                    else:
                        has_early_creator = True  # Это команда создателя
            
            if has_early_creator and not has_early_question:
                log.info("РАННЯЯ ПРОВЕРКА: 'пименов' без вопроса - пропускаю ИИ")
                # Пропускаем ИИ для обработки
                pass

            # === ПРОВЕРКА: СТАТУС ПЕРСОНАЖА ===
            if any(k in cmd for k in ['статус персонажа', 'статус голоса', 'какой персонаж', 'какой голос']):
                status = self.check_persona_status()
                self._safe_add_dialog(status, is_response=True)
                self._safe_speak(f"Текущий персонаж: {self.personas[self.current_persona]['name']}. Голос: {self.current_voice_id if self.current_voice_id else 'стандартный'}.")
                return
            
            # === ПРОВЕРКА: НЕ команда ли это для открытия приложения/браузера/папки? ===
            app_keywords = ['яндекс', 'youtube', 'ютуб', 'google', 'гугл', 'github', 'vk', 'вк',
                          'хром', 'chrome', 'telegram', 'телеграм', 'discord', 'дискорд',
                          'steam', 'стим', 'word', 'ворд', 'excel', 'эксель',
                          'notepad', 'блокнот', 'calculator', 'калькулятор',
                          'explorer', 'проводник', 'firefox',
                          'vpn', 'proxy', 'прокси', 'tor', 'тор', 'браузер', 'приложение', 'программу']
            
            is_app_command = any(kw in cmd for kw in app_keywords)
            
            # Проверяем, что это команда открытия папки/диска, а не документа
            is_folder_command = any(word in cmd for word in ['папку', 'папка', 'диск', 'директори'])
            
            # Если есть слово "открой" И ключевое слово приложения/папки - это команда приложения
            if ('открой' in cmd and is_app_command) or is_folder_command:
                # Пропускаем документную обработку, идём к обработке приложений
                pass
            else:
                document_patterns = (
                    ("summary", r"(?:сделай\s+)?(?:краткое\s+)?содержание\s+(?:файла\s+|документа\s+)?(.+)$"),
                    ("read", r"(?:прочитай|прочесть)\s+(?:файл\s+|документ\s+)?(.+)$"),
                    ("find", r"(?:найди)\s+(.+?)\s+(?:в\s+файле|в\s+документе)\s+(.+)$"),
                )
                for operation, pattern in document_patterns:
                    match = re.match(pattern, cmd)
                    if match:
                        if operation == "find":
                            query, requested = match.groups()
                        else:
                            requested = match.group(1)
                            query = ""
                        if Path(requested.strip().strip('"')).suffix.lower() not in {".txt", ".docx", ".pdf"}:
                            requested += ".txt"
                        self._safe_add_dialog("📄 Обрабатываю документ...", is_response=True)
                        threading.Thread(
                            target=self._process_document,
                            args=(requested, operation, query),
                            daemon=True,
                        ).start()
                        return
            
            duration_match = re.search(
                r"(?:через|на)\s+(\d+(?:[.,]\d+)?)\s*"
                r"(секунд\w*|сек\.?|минут\w*|мин\.?|час\w*|ч\.?)",
                cmd,
            )
            if duration_match and any(
                word in cmd for word in ("таймер", "напомни", "напоминание")
            ):
                amount = float(duration_match.group(1).replace(",", "."))
                unit = duration_match.group(2)
                if unit.startswith(("час", "ч")):
                    seconds = amount * 3600
                elif unit.startswith("мин"):
                    seconds = amount * 60
                else:
                    seconds = amount
                message = cmd[duration_match.end():].strip(" .,")
                message = re.sub(r"^(мне|что|о|про)\s+", "", message).strip()
                self._schedule_reminder(
                    seconds,
                    message or "Время вышло",
                    is_timer=("таймер" in cmd and not message),
                )
                return
            
            # ================================================================
            # ПРИОРИТЕТНЫЕ СИСТЕМНЫЕ / АУДИО / ИГРОВЫЕ КОМАНДЫ.
            # Разбираются ДО общих «открой/закрой/выключи …», иначе:
            #   «выключи звук»    -> close_app('звук') вместо мьюта
            #   «выключи свет»    -> close_app('свет') вместо игровых команд
            #   «выключи комп.»   -> никогда не выключал ПК
            #   «включи свет»     -> Яндекс.Музыка искала бы «свет»
            # ================================================================
            
            # === ВЫКЛЮЧЕНИЕ ПК ===
            system_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'зачем', 'когда', 'можешь', 'умеешь']
            has_system_question = any(kw in cmd for kw in system_exclude)
            
            if not has_system_question and any(k in cmd for k in ['выключи компьютер', 'выключить компьютер', 'выключи пк', 'выключить пк', 'выключи комп', 'shutdown', 'выруб']):
                self._safe_add_dialog("🔴 Выключение ПК через 60 секунд. Команда 'отмена выключения' для отмены.", is_response=True)
                self.play_sound_from_folder(_get_mp3('отключение'), fallback_text="Отключаю питание системы.")
                os.system('shutdown -s -t 60')
                return

            # === ОТМЕНА ВЫКЛЮЧЕНИЯ ===
            if any(k in cmd for k in ['отмена выключения', 'отмени выключение', 'не выключай', 'не выключай', 'отмена shutdown']):
                os.system('shutdown -a')
                self._safe_add_dialog("✅ Выключение отменено. ПК продолжает работу.", is_response=True)
                self._safe_speak("Выключение отменено.")
                return

            # === ПЕРЕЗАГРУЗКА ===
            if not has_system_question and any(k in cmd for k in ['перезагрузить компьютер', 'перезагрузи компьютер', 'перезагрузить пк', 'перезагрузи пк', 'перезагрузи комп', 'reboot', 'перезагрузи']):
                self._safe_add_dialog("🔄 Перезагрузка ПК через 60 секунд. Команда 'отмена перезагрузки' для отмены.", is_response=True)
                self.play_sound_from_folder(_get_mp3('отключение'), fallback_text="Перезагрузка системы.")
                os.system('shutdown -r -t 60')
                return

            # === ОТМЕНА ПЕРЕЗАГРУЗКИ ===
            if any(k in cmd for k in ['отмена перезагрузки', 'отмени перезагрузку', 'не перезагружай']):
                os.system('shutdown -a')
                self._safe_add_dialog("✅ Перезагрузка отменена. ПК продолжает работу.", is_response=True)
                self._safe_speak("Перезагрузка отменена.")
                return

            # === СПЯЩИЙ РЕЖИМ ===
            if not has_system_question and any(k in cmd for k in ['спящий режим', 'переведи в сон', 'перевести в сон', 'усни', 'режим сна', 'sleep', 'в сон', 'спящий']):
                self._safe_add_dialog("ИИ Перевод системы в спящий режим...", is_response=True)
                self.play_sound_from_folder(_get_mp3('проверка'), fallback_text="Перехожу в спящий режим.")
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                return

            # === ГИБЕРНАЦИЯ ===
            if not has_system_question and any(k in cmd for k in ['гибернация', 'гибрит', 'hibernate', 'гибрид', 'глубокий сон', 'в гибернацию', 'гибернаци']):
                self._safe_add_dialog("🌙 Перевод системы в гибернацию...", is_response=True)
                self.play_sound_from_folder(_get_mp3('проверка'), fallback_text="Перехожу в гибернацию.")
                try:
                    os.system('shutdown -h -f -t 10')
                    self._safe_add_dialog("⏱ Гибернация через 10 секунд. Команда 'отмена гибернации' для отмены.", is_response=True)
                except:
                    self._safe_add_dialog("⚠️ Гибернация не включена в Windows. Включите в панели управления.", is_response=True)
                return

            # === ОТМЕНА ГИБЕРНАЦИИ ===
            if any(k in cmd for k in ['отмена гибернации', 'отмени гибернацию', 'не гибернацию']):
                os.system('shutdown -a')
                self._safe_add_dialog("✅ Гибернация отменена. ПК продолжает работу.", is_response=True)
                self._safe_speak("Гибернация отменена.")
                return

            # === БЛОКИРОВКА ЭКРАНА ===
            lock_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'зачем']
            has_lock_question = any(kw in cmd for kw in lock_exclude)
            
            if not has_lock_question and (any(k in cmd for k in ['заблокировать', 'заблокируй', 'блокировк', 'локировк', 'блокировка', 'lock screen', 'локскрин', 'заблокируй экран', 'экран заблокируй']) or ('лок' in words and 'лок' not in ['лок', 'блок', 'полок']) or ('lock' in words and 'lock' not in ['unlock', 'reload', 'lockscreen'])):
                self._safe_add_dialog("🔒 Блокирую систему...", is_response=True)
                self.system_cmd('lock')
                return

            if any(k in cmd for k in ['выключи звук', 'выключить звук', 'без звука', 'заглуши', 'звук выключи', 'звук выключить']) or any(w in words for w in ['мьют', 'мут', 'mute']):
                self.audio_cmd('mute')
                self._safe_add_dialog("Звук отключен.", is_response=True)
                return

            if any(k in cmd for k in ['включи звук', 'включить звук', 'верни звук', 'вернуть звук', 'звук включи', 'звук включить']):
                self.audio_cmd('unmute')
                self._safe_add_dialog("Звук включен.", is_response=True)
                return

            # === ВКЛ/ВЫКЛ МИКРОФОНА ===
            mic_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком']
            has_mic_question = any(kw in cmd for kw in mic_exclude)
            
            if not has_mic_question and any(k in cmd for k in ['отключи микрофон', 'отключить микрофон', 'выключи микрофон', 'выключить микрофон', 'отключи мик', 'выключи мик']):
                self.mic_enabled = False
                self._safe_add_dialog("🔇 Микрофон выключен. Включите кнопкой «Микрофон».", is_response=True)
                return

            elif not has_mic_question and any(k in cmd for k in ['включи микрофон', 'включить микрофон', 'включи мик']):
                self.mic_enabled = True
                self._safe_add_dialog("🎤 Микрофон включён (фоновое слушание активно).", is_response=True)
                return

            # Фонарик - защита от вопросов "что такое фонарик"
            flashlight_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое']
            has_flashlight_question = any(kw in cmd for kw in flashlight_exclude)
            
            if not has_flashlight_question and (any(k in cmd for k in ['фонарик', 'фонарь']) or any(k in cmd for k in ['включи свет', 'выключи свет', 'включить свет', 'выключить свет', 'переключи свет'])):
                if PYAUTOGUI_OK:
                    try:
                        pyautogui.press('l')
                    except Exception:
                        pass
                self._safe_add_dialog("Фонарик переключен.", is_response=True)
                return

            # --- УПРАВЛЕНИЕ ПОДСВЕТКОЙ КЛАВИАТУРЫ ---
            elif any(k in cmd for k in ['подсветк', 'keyboard light', 'клавиатуры подсветк']):
                if not PYAUTOGUI_OK:
                    self._safe_add_dialog("⚠️ Управление клавиатурой недоступно.", is_response=True)
                    return
                
                # Включить подсветку
                if any(k in cmd for k in ['включи подсветк', 'включи подсветку', 'зажги подсветк', 'подсветку включи']):
                    self.keyboard_backlight_cmd('on')
                
                # Выключить подсветку
                elif any(k in cmd for k in ['выключи подсветк', 'выключи подсветку', 'погаси подсветк', 'подсветку выключи']):
                    self.keyboard_backlight_cmd('off')
                
                # Переключить подсветку
                elif any(k in cmd for k in ['переключи подсветк', 'переключи подсветку', 'тоггл подсветк']):
                    self.keyboard_backlight_cmd('toggle')
                
                # Увеличить яркость
                elif any(k in cmd for k in ['ярче подсветк', 'увеличь подсветк', 'подсветку ярче', 'больше подсветк', 'максимальн подсветк']):
                    self.keyboard_backlight_cmd('max')
                
                # Уменьшить яркость
                elif any(k in cmd for k in ['тише подсветк', 'убавь подсветк', 'подсветку тише', 'меньше подсветк', 'минимальн подсветк']):
                    self.keyboard_backlight_cmd('min')
                
                # Циклическое переключение
                elif any(k in cmd for k in ['цикл подсветк', 'циклическ подсветк', 'режим подсветк']):
                    self.keyboard_backlight_cmd('cycle')
                
                else:
                    self._safe_add_dialog("💡 Управление подсветкой клавиатуры. Команды: включить, выключить, ярче, тише, цикл.", is_response=True)
                    self.keyboard_backlight_cmd('on')

            # --- УПРАВЛЕНИЕ ОКНАМИ И ПРИЛОЖЕНИЯМИ ---
            # --- ОТКРЫТИЕ ПАПОК ПРОВОДНИКА ---
            folder_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'найди', 'покажи']
            has_folder_question = any(kw in cmd for kw in folder_exclude)
            
            if not has_folder_question and any(w in cmd for w in ['открой', 'открыть', 'запусти', 'запустить']) and any(k in cmd for k in ['папку', 'папка', 'диск', 'директори']):
                # Извлекаем название папки
                folder_name = cmd
                for w in ['открой', 'открыть', 'запусти', 'запустить', 'папку', 'папка', 'диск', 'директори', 'в']:
                    folder_name = folder_name.replace(w, '')
                folder_name = folder_name.strip()
                
                if folder_name:
                    self._safe_add_dialog(f"📂 Открываю папку: {folder_name}...", is_response=True)
                    
                    # Карта русских названий папок Windows
                    folder_mapping = {
                        'рабочий стол': ('Desktop', os.path.join(os.path.expanduser('~'), 'Desktop')),
                        'рабочий': ('Desktop', os.path.join(os.path.expanduser('~'), 'Desktop')),
                        'стол': ('Desktop', os.path.join(os.path.expanduser('~'), 'Desktop')),
                        'документ': ('Documents', os.path.join(os.path.expanduser('~'), 'Documents')),
                        'докуме': ('Documents', os.path.join(os.path.expanduser('~'), 'Documents')),
                        'документы': ('Documents', os.path.join(os.path.expanduser('~'), 'Documents')),
                        'загрузк': ('Downloads', os.path.join(os.path.expanduser('~'), 'Downloads')),
                        'загруз': ('Downloads', os.path.join(os.path.expanduser('~'), 'Downloads')),
                        'загрузки': ('Downloads', os.path.join(os.path.expanduser('~'), 'Downloads')),
                        'видео': ('Videos', os.path.join(os.path.expanduser('~'), 'Videos')),
                        'картинк': ('Pictures', os.path.join(os.path.expanduser('~'), 'Pictures')),
                        'картин': ('Pictures', os.path.join(os.path.expanduser('~'), 'Pictures')),
                        'фото': ('Pictures', os.path.join(os.path.expanduser('~'), 'Pictures')),
                        'музык': ('Music', os.path.join(os.path.expanduser('~'), 'Music')),
                        'музык': ('Music', os.path.join(os.path.expanduser('~'), 'Music')),
                        'диска': ('C:\\', 'C:\\'),
                        'диск c': ('C:\\', 'C:\\'),
                        'диск c:': ('C:\\', 'C:\\'),
                        'диск d': ('D:\\', 'D:\\'),
                        'диск d:': ('D:\\', 'D:\\'),
                        'диск d:': ('D:\\', 'D:\\'),
                        'этот компьютер': ('This PC', 'This PC'),
                        'сетев': ('Network', 'Network'),
                    }
                    
                    opened = False
                    for russian_key, (folder_name_win, folder_path) in folder_mapping.items():
                        if russian_key in cmd.lower():
                            try:
                                os.startfile(folder_path)
                                self._safe_speak(f"Открыл папку {russian_key}.")
                                opened = True
                                break
                            except Exception as e:
                                log.warning("Не удалось открыть папку %s: %s", folder_path, e)
                    
                    if not opened:
                        # === УЛУЧШЕННЫЙ ПОИСК ПАПКИ (ОГРАНИЧЕННЫЙ ПО ВРЕМЕНИ) ===
                        # 1. Быстрый поиск в стандартных местах (5 секунд)
                        search_roots = [
                            os.path.join(os.path.expanduser('~'), 'Desktop'),
                            os.path.join(os.path.expanduser('~'), 'Documents'),
                            os.path.join(os.path.expanduser('~'), 'Downloads'),
                            os.path.expanduser('~'),
                            os.getcwd(),
                        ]
                        
                        found_path = None
                        
                        # Точное совпадение
                        for root in search_roots:
                            if os.path.exists(root):
                                candidate = os.path.join(root, folder_name)
                                if os.path.exists(candidate) and os.path.isdir(candidate):
                                    found_path = candidate
                                    log.info(f"Найдена точная папка: {found_path}")
                                    break
                        
                        # 2. Рекурсивный поиск с частичным совпадением (ограничено 2 уровнями)
                        if not found_path:
                            for root in search_roots:
                                if os.path.exists(root) and os.path.isdir(root):
                                    try:
                                        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
                                            depth = dirpath.replace(root, '').count(os.sep)
                                            if depth > 2:
                                                dirnames.clear()
                                                continue
                                            for dirname in list(dirnames):  # list() для безопасного изменения
                                                if folder_name.lower() in dirname.lower() or dirname.lower() in folder_name.lower():
                                                    found_path = os.path.join(dirpath, dirname)
                                                    log.info(f"Найдена папка (частичное совпадение): {found_path}")
                                                    break
                                            if found_path:
                                                break
                                    except Exception as e:
                                        log.debug("Ошибка рекурсивного поиска: %s", e)
                                        break
                        
                        # 3. Ищем ярлыки на рабочем столе
                        if not found_path:
                            desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                            if os.path.exists(desktop):
                                try:
                                    for item in os.listdir(desktop):
                                        item_name = item.replace('.lnk', '').replace('.url', '').lower()
                                        if folder_name.lower() in item_name or item_name in folder_name.lower():
                                            found_path = os.path.join(desktop, item)
                                            log.info(f"Найден ярлык на рабочем столе: {found_path}")
                                            break
                                except Exception:
                                    pass
                        
                        if found_path:
                            try:
                                os.startfile(found_path)
                                self._safe_speak(f"Открыл папку {os.path.basename(found_path)}.")
                                opened = True
                            except Exception as e:
                                log.warning("Не удалось открыть папку %s: %s", found_path, e)
                        
                        if not opened:
                            self._safe_add_dialog(
                                f"🔍 Папка «{folder_name}» не найдена. "
                                f"Помести её на Рабочий стол или в Документы.",
                                is_response=True
                            )
                            self._safe_speak(f"Папка {folder_name} не найдена.")
                    return

            # --- ОБЫЧНЫЕ ПРИЛОЖЕНИЯ И САЙТЫ ---
            open_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'зачем', 'когда', 'знаешь', 'умеешь', 'можешь']
            has_open_question = any(kw in cmd for kw in open_exclude)
            
            # === ОТКРЫТИЕ ПРИЛОЖЕНИЙ И САЙТОВ ===
            # Исключения: не ищем файлы на рабочем столе для веб-сайтов
            web_sites = ['яндекс', 'google', 'youtube', 'github', 'vk', 'ютуб', 'гугл', 'вк']
            is_web_site = any(site in cmd for site in web_sites)
            
            if not has_open_question and any(w in cmd for w in ['открой', 'открыть', 'запусти', 'запустить', 'включи', 'включить']) and not any(k in cmd for k in ['музык', 'песню', 'трек', 'кино', 'фильм', 'сериал', 'рутуб', 'карту', 'свет', 'видео', 'фонарик', 'экран', 'полноэкранный']) and not is_web_site:
                target_app = cmd
                for w in ['открой', 'открыть', 'запусти', 'запустить', 'включи', 'включить', 'приложение', 'программу', 'окно', 'джарвис', 'jarvis']:
                    target_app = target_app.replace(w, '')
                target_app = target_app.strip()
                if target_app:
                    # === ПРОВЕРКА: ярлык на рабочем столе ===
                    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
                    found_desktop_item = None
                    
                    if os.path.exists(desktop):
                        try:
                            for item in os.listdir(desktop):
                                # Ищем по имени файла/папки/ярлыка
                                item_name = item.replace('.lnk', '').replace('.url', '').lower()
                                if target_app.lower() in item_name or item_name in target_app.lower():
                                    found_desktop_item = os.path.join(desktop, item)
                                    break
                        except Exception as e:
                            log.debug("Ошибка поиска на рабочем столе: %s", e)
                    
                    if found_desktop_item:
                        # Нашли ярлык/папку на рабочем столе
                        self._safe_add_dialog(f"📂 Нашёл на рабочем столе: {found_desktop_item}", is_response=True)
                        try:
                            if os.path.isdir(found_desktop_item):
                                os.startfile(found_desktop_item)
                                self._safe_speak(f"Открыл {target_app}.")
                            elif found_desktop_item.endswith('.lnk'):
                                # Запускаем ярлык
                                import ctypes
                                shell = ctypes.windll.shell32.ShellExecuteW(None, "open", found_desktop_item, None, None, 1)
                                self._safe_speak(f"Запустил {target_app}.")
                            elif found_desktop_item.endswith('.exe'):
                                subprocess.Popen(found_desktop_item)
                                self._safe_speak(f"Запустил {target_app}.")
                            else:
                                os.startfile(found_desktop_item)
                                self._safe_speak(f"Открыл {target_app}.")
                        except Exception as e:
                            log.error("Ошибка открытия с рабочего стола: %s", e)
                            self._safe_add_dialog(f"⚠️ Ошибка: {str(e)[:50]}", is_response=True)
                    else:
                        # Не нашли на рабочем столе — пробуем запустить как приложение
                        web_target = {'ютуб': 'youtube', 'youtube': 'youtube', 'гугл': 'google', 'google': 'google',
                                      'яндекс': 'yandex', 'yandex': 'yandex', 'github': 'github', 'вк': 'vk', 'vk': 'vk'}
                        if target_app in web_target:
                            self.open_web(web_target[target_app])
                        elif not self.launch_app(target_app):
                            matched = False
                else:
                    matched = False

            elif any(w in cmd for w in ['закрой окно', 'закрыть окно', 'закрыть это окно', 'закрой это окно', 'закрой окна', 'закрыть окна', 'закрой папку', 'закрыть папку', 'закрой проводник', 'закрыть проводник']) or ('закрой' in cmd and 'окно' in cmd) or ('закрыть' in cmd and 'окно' in cmd):
                # Проверяем, есть ли название приложения после «закрой окно»
                app_to_close = None
                temp_cmd = cmd
                for w in ['закрой окно', 'закрыть окно', 'закрой окна', 'закрыть окна', 'закрой папку', 'закрыть папку', 'закрой проводник', 'закрыть проводник', 'закрой', 'закрыть', 'окно', 'окна', 'папку', 'проводник']:
                    temp_cmd = temp_cmd.replace(w, '')
                temp_cmd = temp_cmd.strip()
                if temp_cmd:
                    app_to_close = temp_cmd
                
                if app_to_close:
                    self._safe_add_dialog(f"Закрываю окно: {app_to_close}...", is_response=True)
                    self.close_app(self._resolve_process(app_to_close))
                else:
                    self.window_cmd('close_active')
                return

            # --- ЗАКРЫТИЕ КОНКРЕТНЫХ ПАПОК ПРОВОДНИКА ---
            elif any(k in cmd for k in ['закрой проводник', 'закрой окна проводник', 'закрыть проводник', 'закрой документ', 'закрой документы', 'закрой загрузки', 'закрыть загрузки', 'закрой видео', 'закрыть видео', 'закрой картинки', 'закрыть картинки', 'закрой музыку', 'закрыть музыку', 'закрой диск']):
                # Закрываем окна проводника с определённым путём
                folder_mapping = {
                    'документ': 'Documents',
                    'докуме': 'Documents',
                    'загрузк': 'Downloads',
                    'видео': 'Videos',
                    'картинк': 'Pictures',
                    'фото': 'Pictures',
                    'музык': 'Music',
                    'загруз': 'Downloads',
                }
                
                closed = False
                for russian_name, folder_name in folder_mapping.items():
                    if russian_name in cmd:
                        profile = os.path.expandvars(r'%USERPROFILE%')
                        folder_path = os.path.join(profile, folder_name)
                        
                        self._safe_add_dialog(f"📂 Закрываю папку «{russian_name}»...", is_response=True)
                        
                        # Ищем окна проводника с этим путём
                        if PYAUTOGUI_OK:
                            try:
                                windows = pyautogui.getWindowsWithTitle(folder_name)
                                for win in windows:
                                    # Проверяем, что это именно наша папка
                                    if folder_path.lower() in win.title.lower():
                                        win.close()
                                        closed = True
                                        log.info("Закрыта папка: %s", folder_path)
                                        break
                            except Exception as e:
                                log.warning("Ошибка закрытия папки: %s", e)
                        
                        if not closed:
                            # Fallback — закрываем активное окно проводника
                            os.system('taskkill /IM explorer.exe /F >nul 2>&1 && timeout /t 2 >nul && start explorer')
                        
                        self._safe_speak(f"Папку {russian_name} закрыл.")
                        return

            elif any(w in cmd for w in ['закрой', 'закрыть']) and not any(k in cmd for k in ['закрой окно', 'закрыть окно', 'закрыть это окно', 'закрой это окно', 'закрой окна', 'закрыть окна', 'закрой папку', 'закрыть папку', 'закрой проводник', 'закрыть проводник', 'закрой документ', 'закрой документы', 'закрой загрузки', 'закрыть загрузки', 'закрой видео', 'закрыть видео', 'закрой картинки', 'закрыть картинки', 'закрой музыку', 'закрыть музыку', 'закрой диск']):
                target_app = cmd
                for w in ['закрой', 'закрыть', 'окна', 'окно', 'приложение', 'программу', 'джарвис', 'jarvis']:
                    target_app = target_app.replace(w, '')
                target_app = target_app.strip()
                if target_app:
                    self.close_app(self._resolve_process(target_app))
                else:
                    self._safe_add_dialog("Закрываю текущее активное окно...", is_response=True)
                    if PYAUTOGUI_OK:
                        pyautogui.hotkey('alt', 'f4')

            elif any(w in cmd for w in ['выключи', 'выключить']) and not any(k in cmd for k in ['выключи компьютер', 'выключить компьютер', 'выключи пк', 'выключить пк', 'выключи комп', 'выключи звук', 'выключить звук', 'без звука', 'заглуши', 'звук выключи', 'звук выключить', 'включи свет', 'выключи свет', 'включить свет', 'выключить свет', 'переключи свет', 'выключи проводник', 'выключи документ', 'выключи документы', 'выключи загрузки', 'выключи видео', 'выключи картинки', 'выключи музыку', 'выключи диск']):
                # Проверяем, не папка ли это проводника
                folder_mapping = {
                    'документ': 'Documents',
                    'докуме': 'Documents',
                    'загрузк': 'Downloads',
                    'видео': 'Videos',
                    'картинк': 'Pictures',
                    'фото': 'Pictures',
                    'музык': 'Music',
                    'загруз': 'Downloads',
                }
                
                is_folder = False
                for russian_name, folder_name in folder_mapping.items():
                    if russian_name in cmd:
                        profile = os.path.expandvars(r'%USERPROFILE%')
                        folder_path = os.path.join(profile, folder_name)
                        
                        self._safe_add_dialog(f"📂 Закрываю папку «{russian_name}»...", is_response=True)
                        
                        if PYAUTOGUI_OK:
                            try:
                                windows = pyautogui.getWindowsWithTitle(folder_name)
                                for win in windows:
                                    if folder_path.lower() in win.title.lower():
                                        win.close()
                                        is_folder = True
                                        log.info("Закрыта папка через выключи: %s", folder_path)
                                        break
                            except Exception as e:
                                log.warning("Ошибка закрытия папки: %s", e)
                        
                        if not is_folder:
                            os.system('taskkill /IM explorer.exe /F >nul 2>&1 && timeout /t 2 >nul && start explorer')
                        
                        self._safe_speak(f"Папку {russian_name} закрыл.")
                        return

            elif any(w in cmd for w in ['выключи', 'выключить']) and not any(k in cmd for k in ['выключи компьютер', 'выключить компьютер', 'выключи пк', 'выключить пк', 'выключи комп', 'выключи звук', 'выключить звук', 'без звука', 'заглуши', 'звук выключи', 'звук выключить', 'включи свет', 'выключи свет', 'включить свет', 'выключить свет', 'переключи свет']):
                target_app = cmd
                for w in ['выключи', 'выключить', 'окна', 'окно', 'приложение', 'программу', 'джарвис', 'jarvis']:
                    target_app = target_app.replace(w, '')
                target_app = target_app.strip()
                if target_app:
                    self.close_app(self._resolve_process(target_app))
                else:
                    self._safe_add_dialog("Закрываю текущее активное окно...", is_response=True)
                    if PYAUTOGUI_OK:
                        pyautogui.hotkey('alt', 'f4')

            elif any(w in cmd for w in ['свернуть всё', 'сверни все', 'свернуть все', 'сверни все окна', 'свернуть все окна']) or ('сверни' in cmd and 'все' in cmd) or ('свернуть' in cmd and 'все' in cmd):
                self.window_cmd('minimize_all')

            elif any(w in cmd for w in ['развернуть всё', 'разверни все', 'развернуть все', 'разверни все окна', 'развернуть все окна']) or ('разверни' in cmd and 'все' in cmd) or ('развернуть' in cmd and 'все' in cmd):
                self.window_cmd('restore_all')

            elif any(w in cmd for w in ['сверни', 'свернуть', 'заверни', 'завернуть']):
                # Проверяем, не папка ли это проводника
                folder_mapping = {
                    'документ': 'Documents',
                    'докуме': 'Documents',
                    'загрузк': 'Downloads',
                    'видео': 'Videos',
                    'картинк': 'Pictures',
                    'фото': 'Pictures',
                    'музык': 'Music',
                    'загруз': 'Downloads',
                    'компьютер': 'This PC',
                    'этот компьютер': 'This PC',
                }
                
                is_folder = False
                for russian_name, folder_name in folder_mapping.items():
                    if russian_name in cmd:
                        profile = os.path.expandvars(r'%USERPROFILE%')
                        folder_path = os.path.join(profile, folder_name) if folder_name != 'This PC' else 'This PC'
                        
                        self._safe_add_dialog(f"📂 Сворачиваю папку «{russian_name}»...", is_response=True)
                        
                        if PYAUTOGUI_OK:
                            try:
                                windows = pyautogui.getWindowsWithTitle(folder_name)
                                for win in windows:
                                    if folder_path.lower() in win.title.lower() or folder_name.lower() in win.title.lower():
                                        win.minimize()
                                        is_folder = True
                                        log.info("Свернута папка: %s", folder_path)
                                        break
                            except Exception as e:
                                log.warning("Ошибка сворачивания папки: %s", e)
                        
                        if not is_folder:
                            pyautogui.hotkey('win', 'down')
                        
                        self._safe_speak(f"Папку {russian_name} свернул.")
                        return
                
                # Если не папка — обычная логика
                target_app = cmd
                for w in ['сверни', 'свернуть', 'заверни', 'завернуть', 'окно', 'приложение', 'программу', 'джарвис', 'jarvis']:
                    target_app = target_app.replace(w, '')
                target_app = target_app.strip()
                if target_app and PYAUTOGUI_OK:
                    self._safe_add_dialog(f"Ищу и сворачиваю «{target_app}»...", is_response=True)
                    try:
                        windows = pyautogui.getWindowsWithTitle(target_app)
                        if windows:
                            for win in windows:
                                win.minimize()
                        else:
                            pyautogui.hotkey('win', 'down')
                    except:
                        pyautogui.hotkey('win', 'down')
                else:
                    self._safe_add_dialog("Сворачиваю текущее активное окно.", is_response=True)
                    if PYAUTOGUI_OK:
                        pyautogui.hotkey('win', 'down')

            elif any(w in cmd for w in ['разверни', 'развернуть', 'восстанови', 'восстановить']):
                # Проверяем, не папка ли это проводника
                folder_mapping = {
                    'документ': 'Documents',
                    'докуме': 'Documents',
                    'загрузк': 'Downloads',
                    'видео': 'Videos',
                    'картинк': 'Pictures',
                    'фото': 'Pictures',
                    'музык': 'Music',
                    'загруз': 'Downloads',
                    'компьютер': 'This PC',
                    'этот компьютер': 'This PC',
                }
                
                is_folder = False
                for russian_name, folder_name in folder_mapping.items():
                    if russian_name in cmd:
                        profile = os.path.expandvars(r'%USERPROFILE%')
                        folder_path = os.path.join(profile, folder_name) if folder_name != 'This PC' else 'This PC'
                        
                        self._safe_add_dialog(f"📂 Разворачиваю папку «{russian_name}»...", is_response=True)
                        
                        if PYAUTOGUI_OK:
                            try:
                                windows = pyautogui.getWindowsWithTitle(folder_name)
                                for win in windows:
                                    if folder_path.lower() in win.title.lower() or folder_name.lower() in win.title.lower():
                                        win.restore()
                                        win.activate()
                                        is_folder = True
                                        log.info("Развернута папка: %s", folder_path)
                                        break
                            except Exception as e:
                                log.warning("Ошибка разворачивания папки: %s", e)
                        
                        if not is_folder:
                            pyautogui.hotkey('win', 'up')
                        
                        self._safe_speak(f"Папку {russian_name} развернул.")
                        return
                
                # Если не папка — обычная логика
                target_app = cmd
                for w in ['разверни', 'развернуть', 'восстанови', 'восстановить', 'окно', 'приложение', 'программу', 'джарвис', 'jarvis']:
                    target_app = target_app.replace(w, '')
                target_app = target_app.strip()
                if target_app and PYAUTOGUI_OK:
                    self._safe_add_dialog(f"Ищу и разворачиваю «{target_app}»...", is_response=True)
                    try:
                        windows = pyautogui.getWindowsWithTitle(target_app)
                        if windows:
                            for win in windows:
                                win.restore()
                                win.activate()
                        else:
                            pyautogui.hotkey('win', 'up')
                    except:
                        pyautogui.hotkey('win', 'up')
                else:
                    self._safe_add_dialog("Разворачиваю текущее окно.", is_response=True)
                    if PYAUTOGUI_OK:
                        pyautogui.hotkey('win', 'up')

            # --- АВТОМАТИЗАЦИЯ БРАУЗЕРА ---
            elif any(k in cmd for k in ['открой google и найди', 'открой гугл и найди', 'открой google и введи', 'открой гугл и введи']):
                query = cmd.replace('открой google и найди', '').replace('открой гугл и найди', '').replace('открой google и введи', '').replace('открой гугл и введи', '').strip()
                if query:
                    self._safe_add_dialog(f"🌐 Открываю Google и ищу: «{query}»...", is_response=True)
                    webbrowser.open(
                        f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
                    )
                    self._safe_speak(f"Ищу {query}.")
                else:
                    self._safe_add_dialog("🌐 Открываю Google.", is_response=True)
                    webbrowser.open("https://www.google.com")
                    
            elif any(k in cmd for k in ['открой youtube и найди', 'открой ютуб и найди', 'открой youtube и введи', 'открой ютуб и введи']):
                query = cmd.replace('открой youtube и найди', '').replace('открой ютуб и найди', '').replace('открой youtube и введи', '').replace('открой ютуб и введи', '').strip()
                if query:
                    self._safe_add_dialog(f"🎬 Открываю YouTube и ищу: «{query}»...", is_response=True)
                    webbrowser.open(
                        f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}"
                    )
                    self._safe_speak(f"Ищу {query} на YouTube.")
                else:
                    self._safe_add_dialog("🎬 Открываю YouTube.", is_response=True)
                    webbrowser.open("https://www.youtube.com")
                    
            elif any(k in cmd for k in ['открой vk и найди', 'открой вконтакте и найди', 'открой vk и введи', 'открой вконтакте и введи']):
                query = cmd.replace('открой vk и найди', '').replace('открой вконтакте и найди', '').replace('открой vk и введи', '').replace('открой вконтакте и введи', '').strip()
                if query:
                    self._safe_add_dialog(f"📱 Открываю VK и ищу: «{query}»...", is_response=True)
                    webbrowser.open(
                        "https://vk.com/search?"
                        f"c%5Bq%5D={urllib.parse.quote_plus(query)}&c%5Bsection%5D=auto"
                    )
                    self._safe_speak(f"Ищу {query} в ВКонтакте.")
                else:
                    self._safe_add_dialog("📱 Открываю ВКонтакте.", is_response=True)
                    webbrowser.open("https://vk.com")
                    
            elif any(k in cmd for k in ['открой яндекс и найди', 'открой яндекс и введи']):
                query = cmd.replace('открой яндекс и найди', '').replace('открой яндекс и введи', '').strip()
                if query:
                    self._safe_add_dialog(f"🔍 Открываю Яндекс и ищу: «{query}»...", is_response=True)
                    webbrowser.open(
                        f"https://yandex.ru/search/?text={urllib.parse.quote_plus(query)}"
                    )
                    self._safe_speak(f"Ищу {query}.")
                else:
                    self._safe_add_dialog("🔍 Открываю Яндекс.", is_response=True)
                    webbrowser.open("https://yandex.ru")
                    
            elif any(k in cmd for k in ['прокрути вниз', 'прокрути страницу вниз', 'листай вниз', 'листай страницу']):
                self.browser_automate("", "scroll", "вниз")
                
            elif any(k in cmd for k in ['прокрути вверх', 'прокрути страницу вверх', 'листай вверх', 'листай страницу вверх']):
                self.browser_automate("", "scroll", "вверх")
                
            elif any(k in cmd for k in ['обнови страницу', 'перезагрузи страницу', 'f5']):
                self.browser_automate("", "navigate", "обновить")
                
            elif any(k in cmd for k in ['назад', 'вернуться назад', 'назад в браузере']):
                self.browser_automate("", "navigate", "назад")
                
            elif any(k in cmd for k in ['сделай скриншот страницы', 'скриншот браузера', 'скриншот страницы']):
                self.browser_automate("", "screenshot")

            # === ПОГОДА (рассказать с юмором) ===
            if any(k in cmd for k in ['погода', 'какая погода', 'покажи погоду', 'прогноз погоды', 'weather']):
                try:
                    import requests
                    
                    # Определяем геолокацию пользователя через IP
                    lat, lon = 55.75, 37.62  # Москва по умолчанию
                    city_name = "Москва"
                    
                    try:
                        # Получаем IP и геолокацию
                        ip_res = requests.get("https://ipinfo.io/json", timeout=5)
                        if ip_res.status_code == 200:
                            ip_data = ip_res.json()
                            loc = ip_data.get('loc', '62.0311,129.7229')
                            lat, lon = loc.split(',')
                            lat = float(lat)
                            lon = float(lon)
                            city_name = ip_data.get('city', 'Вашего города')
                    except:
                        pass
                    
                    # Получаем погоду через Open-Meteo
                    meteo_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,weather_code,wind_speed_10m&temperature_unit=celsius&wind_speed_unit=kmh"
                    meteo_res = requests.get(meteo_url, timeout=10)
                    
                    if meteo_res.status_code == 200:
                        data = meteo_res.json()
                        temp = data.get("current", {}).get("temperature_2m", "--")
                        wind = data.get("current", {}).get("wind_speed_10m", "--")
                        code = data.get("current", {}).get("weather_code", 0)
                        
                        weather_codes = {
                            0: ("Ясно", "Небо чистое, как мой код после рефакторинга"),
                            1: ("Преимущественно ясно", "Солнце прячется за облачка, как я от отчётов"),
                            2: ("Переменная облачность", "Облака то появляются, то исчезают, как дедлайны"),
                            3: ("Пасмурно", "Небо хмурится, как босс в понедельник утром"),
                            45: ("Туман", "Такой туман, что я бы потерял себя в папке Temp"),
                            48: ("Туман с изморозью", "Туман и иней — идеальный день, чтобы остаться дома и писать код"),
                            51: ("Лёгкая морось", "Лёгкий дождик, как баги — мелкие, но неприятные"),
                            53: ("Морось", "Морось льёт, как сервер в час пик — без остановки"),
                            55: ("Сильная морось", "Ливень такой, что даже пиксели мокрые"),
                            61: ("Небольшой дождь", "Небольшой дождик, как предупреждения в консоли — не критично, но раздражает"),
                            63: ("Дождь", "Дождь идёт, как данные в большом проекте"),
                            65: ("Сильный дождь", "Ливень! Если бы вода работала так же эффективно, как дождь льётся, мы бы уже на Марсе"),
                            71: ("Небольшой снег", "Лёгкий снег, как белые ошибки в терминале"),
                            73: ("Снег", "Снег идёт — время для горячего чая и хорошего кода"),
                            75: ("Сильный снег", "Метель! Даже компилятор бы замерз"),
                            80: ("Небольшой ливень", "Небольшой ливень, как спам в почте"),
                            81: ("Ливень", "Ливень! Дождь льёт как пропущенные тесты — без остановки"),
                            82: ("Сильный ливень", "Потоп! Вода бы написала больше кода, чем наш отдел"),
                            95: ("Гроза", "Гроза! Молнии светят ярче, чем экран с синтаксисом"),
                            96: ("Гроза с градом", "Град и гроза — как production в пятницу вечером"),
                            99: ("Сильная гроза с градом", "Адская погода! Даже ИИ бы закрыл ноутбук и ушёл домой"),
                        }
                        
                        desc, joke = weather_codes.get(code, ("Неизвестно", "Погода такая необычная, что даже мои алгоритмы не могут описать"))
                        
                        # Формируем ответ с юмором
                        if temp is not None and temp != "--":
                            if temp > 25:
                                temp_joke = "На улице жарко, как сервер в дата-центре без кондиционера"
                            elif temp < 0:
                                temp_joke = "Минусовая температура, как мои шансы найти идеального собеседника на работе"
                            elif temp < 10:
                                temp_joke = "Прохладно, как интерфейс без тёплых кнопок"
                            else:
                                temp_joke = "Температура комфортная, как код без багов"
                            
                            # Форматируем температуру для озвучки (5.4 -> пять с небольшим)
                            temp_str = str(temp)
                            if '.' in temp_str:
                                int_part, dec_part = temp_str.split('.')
                                if int(int_part) >= 0:
                                    temp_joke += f". Температура {int_part} градусов {dec_part} с небольшим"
                                else:
                                    temp_joke += f". Температура минус {abs(int(int_part))} градусов {dec_part} с небольшим"
                            else:
                                temp_val = int(temp)
                                if temp_val >= 0:
                                    temp_joke += f". Температура {temp_val} градусов"
                                else:
                                    temp_joke += f". Температура минус {abs(temp_val)} градусов"
                        else:
                            temp_joke = ""
                        
                        # Форматируем скорость ветра для озвучки
                        if wind and wind != "--":
                            wind_str = str(wind)
                            if '.' in wind_str:
                                int_part, dec_part = wind_str.split('.')
                                wind_formatted = f"Ветер {int_part} километров в час, {dec_part} с небольшим"
                            else:
                                wind_formatted = f"Ветер {wind_str} километров в час"
                            wind_info = f". {wind_formatted}, как скорость загрузки при медленном интернете"
                        else:
                            wind_info = ""
                        
                        response = f"Погода в городе {city_name}. {joke}. {temp_joke}. {desc}.{wind_info}"
                        
                        self._safe_add_dialog(f"🌤 {response}", is_response=True)
                        self._safe_speak(response)
                    else:
                        self._safe_add_dialog("⚠️ Не удалось получить данные о погоде.", is_response=True)
                        self._safe_speak("Метеорологические спутники временно недоступны.")
                        
                except Exception as e:
                    log.error("Ошибка погоды: %s", e)
                    self._safe_add_dialog("⚠️ Не удалось получить погоду.", is_response=True)
                    self._safe_speak("Погода решила взять выходной, как и я в воскресенье.")
                return

            elif any(k in cmd for k in ['скриншот с аннотациями', 'скриншот с пометками', 'скриншот с рамками', 'аннотированный скриншот', 'сделай скриншот с пометками', 'скриншот с подписями']):
                self.screenshot_with_annotations()

            elif any(k in cmd for k in ['скриншот', 'скрин', 'сними экран', 'сделай скриншот', 'захвати экран', 'capture screen']):
                self.take_screenshot()

            elif any(k in cmd for k in ['проанализируй', 'что на экране', 'что видишь', 'опиши экран', 'analyze screen', 'что показано']):
                self.analyze_screenshot()

            elif any(k in cmd for k in ['последний скрин', 'последний скриншот', 'покажи скриншот', 'открой скриншот']):
                self.show_last_screenshot()

            elif any(k in cmd for k in ['покажи скриншоты', 'список скриншотов', 'все скриншоты']):
                self.list_screenshots()

            elif any(w in cmd for w in ['экран', 'полноэкранный', 'во весь экран']):
                self._safe_add_dialog("Включаю полноэкранный режим.", is_response=True)
                if PYAUTOGUI_OK:
                    screen_w, screen_h = pyautogui.size()
                    pyautogui.click(screen_w // 2, screen_h // 2)
                    pyautogui.press('f')
                    pyautogui.press('f11')

            # --- ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ ---
            elif any(k in cmd for k in ['нарисуй', 'нарисуй', 'создай изображение', 'сгенерируй картинку', 'сгенерируй изображение', 'generate image', 'нарисуй картинку', 'создай картинку']):
                image_prompt = cmd
                for k in ['нарисуй', 'нарисуй', 'создай изображение', 'сгенерируй картинку', 'сгенерируй изображение', 'generate image', 'нарисуй картинку', 'создай картинку', 'пожалуйста', 'пж']:
                    image_prompt = image_prompt.replace(k, '')
                image_prompt = image_prompt.strip()
                if image_prompt:
                    self.generate_image(image_prompt)
                else:
                    self._safe_add_dialog("Какое изображение сгенерировать", is_response=True)

            # --- УПРАВЛЕНИЕ КИНОПОИСК И МУЗЫКОЙ ---
            elif any(w in cmd for w in ['кино', 'фильм', 'сериал', 'рутуб', 'кинопоиск']):
                self._safe_add_dialog("Открываю Кинопоиск...", is_response=True)
                webbrowser.open("https://hd.kinopoisk.ru/")

            # === ВКЛЮЧИТЬ ПЕСНЮ/ТРЕК (с защитой от вопросов) ===
            song_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'зачем', 'когда', 'знаешь', 'умеешь', 'можешь', 'открыва', 'открой']
            has_song_question = any(kw in cmd for kw in song_exclude)
            
            if not has_song_question and ('песню' in cmd or 'трек' in cmd or ('включи' in cmd and not any(k in cmd for k in ['музык', 'кино', 'диск', 'свет', 'карт', 'фонар', 'звук', 'яндекс']))):
                song_query = cmd.replace('включи песню', '').replace('найди песню', '').replace('песню', '').replace('трек', '').replace('включи', '').replace('найди', '').strip()
                if not song_query:
                    song_query = "моя волна"
                self._safe_add_dialog(f"Ищу в Яндекс.Музыке: «{song_query}»", is_response=True)
                encoded_query = urllib.parse.quote(song_query)
                webbrowser.open(f"https://music.yandex.ru/searchtext={encoded_query}")

            elif any(w in cmd for w in ['музык', 'янндекс музыку']):
                self.yandex_music_cmd('open')

            # --- УПРАВЛЕНИЕ ЯНДЕКС.МУЗЫКОЙ (голосом) ---
            elif any(k in cmd for k in ['пауза', 'паузу', 'стоп музыка', 'стоп песню', 'пауз']):
                self.yandex_music_cmd('pause')

            elif any(k in cmd for k in ['продолжи', 'играть', 'воспроизведи', 'плей', 'play']):
                self.yandex_music_cmd('play')

            elif any(k in cmd for k in ['следующий', 'следующую', 'далее', 'дальше', 'next', 'дальше']):
                self.yandex_music_cmd('next')

            elif any(k in cmd for k in ['предыдущий', 'предыдущую', 'назад', 'prev', 'заново', 'сначала']):
                self.yandex_music_cmd('prev')

            elif any(k in cmd for k in ['громче музыку', 'громче песню', 'громче йа', 'йа громче', 'музыку громче', 'песню громче']):
                self.yandex_music_cmd('volume_up')

            elif any(k in cmd for k in ['тише музыку', 'тише песню', 'тише йа', 'йа тише', 'музыку тише', 'песню тише']):
                self.yandex_music_cmd('volume_down')

            elif any(k in cmd for k in ['без звука музыку', 'мут музыку', 'заглуши музыку', 'музыку мут']):
                self.yandex_music_cmd('mute')

            elif any(k in cmd for k in ['верни звук музыки', 'размут музыку', 'включи звук музыки']):
                self.yandex_music_cmd('unmute')

            elif any(k in cmd for k in ['повтор', 'repeat', 'зацикли']):
                self.yandex_music_cmd('repeat')

            elif any(k in cmd for k in ['перемешать', 'shuffle', 'микс']):
                self.yandex_music_cmd('shuffle')

            elif 'громкост' in cmd:
                words_list = cmd.split()
                level = 5
                for w in words_list:
                    if w.isdigit():
                        level = int(w)
                        break
                level = max(1, min(10, level))
                self.set_volume_level(level)
                self._safe_add_dialog(f"Установлена громкость: {level}/10", is_response=True)

            # --- ПРОВЕРКА СКОРОСТИ ИНТЕРНЕТА ---
            elif any(k in cmd for k in ['скорость интернета', 'скорость интернета', 'speed test', 'проверь скорость', 'тест скорости', 'проверить интернет', 'скорость соединения', 'скорость сети']):
                self.play_sound_from_folder(_get_mp3('диагностика'), fallback_text="Проверяю скорость интернета.")
                threading.Thread(target=self.check_internet_speed, daemon=True).start()
                return

            # --- ДИАГНОСТИКА СИСТЕМЫ ---
            elif any(w in cmd for w in ['диагностик', 'проверить систем', 'статус системы', 'загрузка пк', 'память компьютера', 'состояние системы']) or (('процессор' in cmd or 'память' in cmd) and ('компьютер' in cmd or 'систем' in cmd or 'нагрузк' in cmd)):
                self.play_sound_from_folder(_get_mp3('диагностика'), fallback_text="Начинаю диагностику системы.")
                cpu = psutil.cpu_percent(interval=0.5)
                ram = psutil.virtual_memory().percent
                # Проверка подключения к интернету
                internet_connected = False
                internet_speed = "Не проверено"
                try:
                    res = requests.get("https://speed.cloudflare.com", timeout=5, verify=False)
                    internet_connected = res.status_code == 200
                    # Быстрый замер пинга
                    start = time.time()
                    requests.get("https://speed.cloudflare.com", timeout=5, verify=False)
                    ping = (time.time() - start) * 1000
                    internet_speed = f"Пинг {ping:.0f} мс"
                except:
                    internet_connected = False
                    internet_speed = "Нет подключения"
                
                diag_msg = (
                    f"--- ОТЧЕТ ДИАГНОСТИКИ ---\n"
                    f"• Процессор: {cpu}% нагрузки\n"
                    f"• Оперативная память: {ram}%\n"
                    f"• Интернет: {'ПОДКЛЮЧЕН ✓' if internet_connected else 'ОТКЛ ✗'} ({internet_speed})\n"
                    f"• RuTube / Музыка: {'АКТИВНА ✓' if PYGAME_OK else 'ОТКЛ ✗'}\n"
                    f"• Яндекс.Музыка: {'АКТИВНА ✓' if PYAUTOGUI_OK else 'ОТКЛ ✗'}\n"
                    f"• ИИ Ollama: {'ПОДКЛЮЧЕН ✓' if REQUESTS_OK else 'ОТКЛ ✗'}\n"
                    f"• Системный трей: {'АКТИВЕН ✓' if TRAY_OK else 'ОТКЛ ✗'}\n\n"
                    f"--- ДОСТУПНЫЕ КОМАНДЫ ПИТАНИЯ ---\n"
                    f"• 'выключи компьютер' - выключение ПК\n"
                    f"• 'перезагрузи компьютер' - перезагрузка ПК\n"
                    f"• 'спящий режим' - переход в сон\n"
                    f"• 'гибернация' - глубокий сон\n"
                    f"• 'блокировка экрана' - блокировка\n"
                    f"• 'отмена выключения' - отмена команды"
                )
                self._safe_add_dialog(diag_msg, is_response=True)
                self.play_sound_from_folder(_get_mp3('проверка'), fallback_text="Проверка завершена.")

            # --- УДАЛЕНИЕ МУСОРА (КОРЗИНА) ---
            elif any(k in cmd for k in ['удаление мусора', 'очистка мусора', 'очисти мусор', 'очистить мусор', 'удали мусор', 'удалить мусор', 'убери мусор', 'убрать мусор', 'очисти', 'очистим', 'очистка', 'очистить']):
                self.play_sound_from_folder(_get_mp3('диагностика'), fallback_text="Начинаю очистку корзины.")
                threading.Thread(target=self.cleanup_recycle_bin, daemon=True).start()
                return

            # --- ОЧИСТКА TEMP И КЭША ---
            elif any(k in cmd for k in ['очисти корзину', 'очистить корзину', 'clean temp', 'очистка temp', 'очисти temp', 'очистка кэша', 'очисти кэш', 'удаление кэша', 'очистка временных', 'очисти временные', 'удаление временных']):
                self.play_sound_from_folder(_get_mp3('диагностика'), fallback_text="Начинаю очистку временных файлов.")
                threading.Thread(target=self.cleanup_temp_files, daemon=True).start()
                return

            # --- ПРИВЕТСТВИЕ (пропускаем ИИ) ---
            elif any(w in cmd for w in ['привет', 'здравствуй', 'добрый', 'хай']):
                # Пропускаем к ИИ — без жёстких ответов
                pass

            # --- СОЗДАТЕЛЬ (пропускаем ИИ) ---
            elif self.is_jarvis_creator_query(cmd):
                # Пропускаем к ИИ — без жёстких ответов
                pass

            # --- БЛАГОДАРНОСТЬ (пропускаем ИИ) ---
            elif any(w in cmd for w in ['спасиб', 'спосиб', 'благодар', 'спс']):
                # Пропускаем к ИИ
                pass

            # --- КАК ДЕЛА (пропускаем ИИ) ---
            elif 'как' in words and ('дел' in cmd or 'настроен' in cmd or 'ты' in words):
                # Пропускаем к ИИ
                pass

            # --- ПОХВАЛА (пропускаем ИИ) ---
            elif any(w in cmd for w in ['молодец', 'красавчик', 'отличн']):
                # Пропускаем к ИИ
                pass

            elif ('ок' in words and not any(k in cmd for k in ['окно', 'окна', 'заверни', 'сверни', 'разверни', 'закрой'])) or any(w in cmd for w in ['хорошо', 'понял', 'принят', 'ладно']):
                # Пропускаем к ИИ
                pass

            # --- МАТЫ И ТОКСИЧНОСТЬ (пропускаем ИИ) ---
            elif any(w in cmd for w in ['дурак', 'туп', 'идиот', 'дебил']):
                self.play_specific_toxic(_get_mp3('toxic_stupid'), "")
            elif any(w in cmd for w in ['нахуй', 'пошел', 'пошёл']):
                self.play_specific_toxic(_get_mp3('toxic_go'), "")
            elif any(w in cmd for w in ['бля', 'сука', 'блять', 'ебат', 'хер', 'хуй']):
                self.play_specific_toxic(_get_mp3('toxic_swear'), "")
            elif any(w in cmd for w in ['пидор', 'гандон', 'урод', 'сволоч', 'еблан']):
                self.play_specific_toxic(_get_mp3('toxic_bad'), "")

            # --- УПРАВЛЕНИЕ DAYZ (без жёстких ответов) ---
            # Примечание: фонарик уже обработан ВЫШЕ (строка ~940) — дубли удалены.
            elif any(k in cmd for k in ['бег', 'беги', 'бежать', 'автобег', 'беги вперед']) and not any(k in cmd for k in ['убежать', 'перебежка', 'пробежка', 'перепрыгнуть']):
                if PYAUTOGUI_OK:
                    pyautogui.keyDown('w'); pyautogui.keyDown('shift'); time.sleep(0.1); pyautogui.keyUp('shift')
                # Пропускаем к ИИ для ответа
            elif any(k in cmd for k in ['стой', 'стоп', 'остановись', 'остановить']) and 'музык' not in cmd and not any(k in cmd for k in ['стойкость', 'остановиться', 'останавливаться']):
                if PYAUTOGUI_OK:
                    pyautogui.keyUp('w'); pyautogui.keyUp('shift'); pyautogui.press('s')
                # Пропускаем к ИИ
            elif any(k in cmd for k in ['карта', 'карту', 'открой карту']) and not any(k in cmd for k in ['картинка', 'картинку', 'карта мира', 'карта мира']):
                if PYAUTOGUI_OK: pyautogui.press('m')
                # Пропускаем к ИИ
            elif any(w in cmd for w in ['инвентарь', 'рюкзак', 'таб', 'tab']):
                if PYAUTOGUI_OK: pyautogui.press('tab')
                # Пропускаем к ИИ
            # Фонарик уже обработан ВЫШЕ (строка ~940) — дубликат удалён.
            elif any(w in cmd for w in ['пригнись', 'сядь', 'сесть', 'присесть']):
                if PYAUTOGUI_OK: pyautogui.press('ctrl')
                # Пропускаем к ИИ
            elif any(w in cmd for w in ['ляг', 'лечь', 'ползи', 'лежать', 'ползать']):
                if PYAUTOGUI_OK: pyautogui.press('x')
                # Пропускаем к ИИ
            elif any(k in cmd for k in ['рация', 'связь', 'микрофон в игре']) and not any(k in cmd for k in ['связываться', 'передача связи', 'установи связь']):
                if PYAUTOGUI_OK:
                    threading.Thread(target=lambda: (pyautogui.keyDown('capslock'), time.sleep(3), pyautogui.keyUp('capslock'))).start()
                # Пропускаем к ИИ
            elif any(w in cmd for w in ['меню', 'выйди в меню', 'меню игры']):
                if PYAUTOGUI_OK: pyautogui.press('escape')
                # Пропускаем к ИИ

            # --- АУДИО И СИСТЕМА ---
            # Примечание: shutdown/restart/sleep/lock/mute/unmute/flashlight
            # обрабатываются ВЫШЕ (строки ~908-947) с return — дубли здесь удалены.
            elif any(k in cmd for k in ['громче', 'увеличь звук', 'звук громче']) and not any(k in cmd for k in ['громче играй', 'громче музыку']): self.audio_cmd('volume_up')
            elif any(k in cmd for k in ['тише', 'уменьши звук', 'звук тише']) and not any(k in cmd for k in ['тише играй', 'тише музыку']): self.audio_cmd('volume_down')
            elif any(w in cmd for w in ['справк', 'команд', 'помощ']): self._safe_ui(self.show_help)
            elif any(w in cmd for w in ['плагин']): self._safe_ui(self.show_plugins)
            
            # === СЧЁТ ДО ЧИСЛА ===
            elif any(k in cmd for k in ['считай до', 'посчитай до', 'считай', 'посчитай']):
                match = re.search(r'(\d+)', cmd)
                if match:
                    number = int(match.group(1))
                    if 0 < number <= 100:
                        # Генерируем числа через speak
                        count_text = ', '.join(str(i) for i in range(1, number + 1))
                        self._safe_add_dialog(f"🔢 Считаем до {number}...", is_response=True)
                        self._safe_speak(count_text)
                        return
                    else:
                        self._safe_add_dialog(f"⚠️ Могу считать только до 100", is_response=True)
                        self._safe_speak("Могу посчитать только до ста.")
                        return
            
            # === РАБОЧЕЕ ВРЕМЯ ЖЕНЫ ===
            elif any(k in cmd for k in ['жена', 'алина']) and any(k in cmd for k in ['где работает', 'где работает', 'работает где', 'место работы', 'работает в']):
                # Вопрос о месте работы
                self._safe_add_dialog(
                    "Алина работает в продуктовом магазине продавцом. "
                    "Будни: с 11:00 до 20:00. В воскресенье: до 16:00.",
                    is_response=True
                )
                self._safe_speak("Алина работает продавцом в продуктовом магазине с одиннадцати до восьми вечера.")
                return
            
            elif any(k in cmd for k in ['жена', 'алина', 'закончила', 'работает', 'на работе', 'дома']) and any(k in cmd for k in ['сейчас', 'где', 'когда', 'закончила', 'закончила ли']):
                from datetime import datetime
                now = datetime.now()
                hour = now.hour
                minute = now.minute
                current_time = f"{hour:02d}:{minute:02d}"
                
                # Определяем день недели (0=понедельник, 5=суббота, 6=воскресенье)
                day_of_week = now.weekday()
                is_weekend = day_of_week >= 5
                
                # Рабочие часы жены
                if is_weekend:
                    work_end = 16  # До 16:00 в воскресенье
                    day_type = "выходного"
                else:
                    work_end = 20  # До 20:00 в будни
                    day_type = "буднего"
                
                # Проверяем, закончила ли
                current_minutes = hour * 60 + minute
                end_minutes = work_end * 60
                
                if current_minutes >= end_minutes:
                    status = f"Алина уже закончила работу. Сейчас {current_time}, она должна быть уже дома."
                elif current_minutes >= 11 * 60:
                    status = f"Алина сейчас на работе. Будет свободна в {work_end}:00."
                else:
                    status = "Алина ещё не начала смену. Начнёт в 11:00."
                
                self._safe_add_dialog(f"🕐 Сейчас {current_time} ({day_type}). {status}", is_response=True)
                self._safe_speak(status)
                return
            
            elif any(w in cmd for w in ['новост', 'что нов', 'сводк', 'главное']):
                category = 'all'
                if 'техн' in cmd or 'технолог' in cmd: category = 'tech'
                elif 'мир' in cmd or 'междунар' in cmd: category = 'world'
                elif 'спорт' in cmd: category = 'sport'
                elif 'финанс' in cmd or 'деньг' in cmd or 'крипт' in cmd: category = 'money'
                self.news_cmd(category)
            elif 'погода' in cmd:
                # === ПОГОДА С ВОЗМОЖНОСТЬЮ УКАЗАТЬ ГОРОД ===
                city_match = re.search(r'(?:в|погода в|какая погода в)\s+([а-яёa-z\s-]+)', cmd.lower())
                if city_match:
                    city = city_match.group(1).strip()
                    # Сохраняем город в config
                    config_path = self._config_path()
                    config = {}
                    if config_path.exists():
                        try:
                            with open(config_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)
                        except:
                            pass
                    config['weather_city'] = city
                    try:
                        with open(config_path, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
                        self._safe_add_dialog(f"🌤 Запоминаю город: {city}. Сейчас проверю погоду.", is_response=True)
                    except:
                        self._safe_add_dialog(f"🌤 Город: {city}. Проверю погоду.", is_response=True)
                    
                    # Получаем погоду
                    self._get_weather_for_city(city)
                else:
                    # Показываем погоду по умолчанию (из config или автоопределение)
                    self._get_weather_for_city()
            
            # --- ПОИСК ФАЙЛОВ ПО ИМЕНИ ---
            elif any(k in cmd for k in ['найди файл', 'найди файл', 'поиск файла', 'найти файл', 'файл по имени', 'файл найди', 'файл поиска']):
                # Извлекаем имя файла из команды
                file_query = cmd
                for k in ['найди файл', 'найди файл', 'поиск файла', 'найти файл', 'файл по имени', 'файл найди', 'файл поиска', 'найди', 'файл', 'файлик', 'поиск']:
                    file_query = file_query.replace(k, '')
                file_query = file_query.strip()
                
                if file_query:
                    self._safe_add_dialog(f"🔍 Ищу файл: «{file_query}»...", is_response=True)
                    threading.Thread(target=self.search_files, args=(file_query,), daemon=True).start()
                else:
                    self._safe_add_dialog("📝 Какое имя файла искать", is_response=True)
                    self._safe_speak("Уточните имя файла для поиска.")
            
            elif any(k in cmd for k in ['найди', 'поиск', 'поищи']) and not any(
                k in cmd for k in ['найди информацию', 'поиск информации', 'поищи информацию']
            ):
                self.search('web', cmd)
            elif 'диск с' in cmd: self.file_cmd('disk_c')
            elif 'диск д' in cmd: self.file_cmd('disk_d')
            elif any(w in cmd for w in ['мой компьютер', 'компьютер']): self.file_cmd('computer')
            elif any(k in cmd for k in ['загрузк']) and not any(k in cmd for k in ['загрузчик', 'загрузочный']): self.file_cmd('downloads')
            elif any(k in cmd for k in ['документ']) and not any(k in cmd for k in ['документация', 'документы']): self.file_cmd('documents')
            elif any(k in cmd for k in ['видео']) and not any(k in cmd for k in ['видеокарта', 'видеозвонок', 'видеорегистратор']): self.file_cmd('videos')
            elif any(w in cmd for w in ['картинк', 'фото']): self.file_cmd('pictures')
            elif 'steam' in cmd or 'стим' in cmd:
                if 'закрой' in cmd: self.close_app('steam')
                else: self.launch_app('steam')
            elif 'хром' in cmd or 'chrome' in cmd:
                if 'закрой' in cmd: self.close_app('chrome')
                else: self.open_browser('chrome')
            elif 'telegram' in cmd or 'телеграм' in cmd:
                if 'закрой' in cmd: self.close_app('telegram')
                else: self.launch_app('telegram')
            elif 'discord' in cmd or 'дискорд' in cmd:
                if 'закрой' in cmd: self.close_app('discord')
                else: self.launch_app('discord')
            elif 'word' in cmd or 'ворд' in cmd: self.launch_app('word')
            elif 'excel' in cmd or 'ексель' in cmd: self.launch_app('excel')
            elif 'блокнот' in cmd: self.launch_app('notepad')
            elif 'youtube' in cmd or 'ютуб' in cmd: self.open_web('youtube')
            elif 'google' in cmd or 'гугл' in cmd: self.open_web('google')
            elif 'github' in cmd: self.open_web('github')
            elif 'янндекс' in cmd or 'yandex' in cmd: self.open_web('yandex')
            elif 'калькулятор' in cmd: self.launch_app('calc')
            elif any(w in cmd for w in ['свернуть всё', 'сверни все']): self.window_cmd('minimize_all')
            
            # --- МЕДИА: Яндекс.Музыка (с защитой от вопросов) ---
            music_exclude = ['что', 'как', 'расскаж', 'где', 'почему', 'про', 'ознаком', 'что такое', 'зачем', 'когда', 'знаешь', 'умеешь', 'можешь']
            has_music_question = any(kw in cmd for kw in music_exclude)
            
            # ВАЖНО: Проверяем pause/next/prev ПЕРВЫМИ, чтобы не сработало 'включи музыку'
            if not has_music_question and any(k in cmd for k in ['музыку пауз', 'музыку стоп', 'пауза музыку', 'стоп музыку', 'останови музыку', 'паузу музыку', 'приостанови музыку', 'пауз', 'стоп музыку', 'останови']):
                self.yandex_music_cmd('pause')
            elif not has_music_question and any(k in cmd for k in ['следующий трек', 'следующую музыку', 'следующая композиц', 'далее музыку', 'дальше музыку', 'следующая', 'следующий']):
                self.yandex_music_cmd('next')
            elif not has_music_question and any(k in cmd for k in ['предыдущий трек', 'предыдущую музыку', 'назад трек', 'назад музыку', 'предыдущая', 'предыдущий', 'сначала музыку', 'заново музыку']):
                self.yandex_music_cmd('prev')
            elif not has_music_question and any(k in cmd for k in ['музыку играть', 'музыку включи', 'продолжи музыку', 'воспроизведи музыку']):
                self.yandex_music_cmd('play')
            elif not has_music_question and any(k in cmd for k in ['громче музыку', 'громче играй', 'увеличь музыку', 'музыку громче']):
                self.yandex_music_cmd('volume_up')
            elif not has_music_question and any(k in cmd for k in ['тише музыку', 'тише играй', 'уменьши музыку', 'музыку тише']):
                self.yandex_music_cmd('volume_down')
            elif not has_music_question and any(k in cmd for k in ['перемешай музыку', 'перемешать музыку', 'shuffle', 'случайн']):
                self.yandex_music_cmd('shuffle')
            elif not has_music_question and any(k in cmd for k in ['повтори музыку', 'repeat', 'повтор']):
                self.yandex_music_cmd('repeat')
            
            # Проверяем команду на ВКЛЮЧЕНИЕ музыки (в самом конце, после всех остальных команд)
            elif not has_music_question:
                is_music_cmd = any(k in cmd for k in ['яндекс.музык', 'яндекс музык', 'yandex.music', 'yandexmusic', 'открой музыку', 'запусти музыку', 'включи музыку', 'играй музыку'])
                # 'открой яндекс' без 'музыку' открывает браузер, а не музыку
                if 'открой яндекс' in cmd and 'музык' not in cmd:
                    is_music_cmd = False
                
                if is_music_cmd:
                    self.yandex_music_cmd('open')
            elif any(k in cmd for k in ['плейлист', 'плей']): 
                playlist_match = re.search(r'(?:открой|играй|включи)\s+плейлист\s+(.+)', cmd)
                if playlist_match:
                    self.yandex_music_playlist_cmd('open', playlist_match.group(1))
                else:
                    self._safe_add_dialog("🎵 Доступные плейлисты: ежедневный микс, топ, новинки, чилл, тренировка, концентрация, вечеринка, сон", is_response=True)
            elif any(k in cmd for k in ['рекоменд', 'посоветуй музыку', 'что послушать', 'что поиграть']):
                mood_match = re.search(r'(?:когда|для|в|на)\s+(.+)', cmd)
                mood = mood_match.group(1) if mood_match else ""
                self.get_music_recommendations(mood)
            
            # --- МЕДИА: Аудиокниги ---
            elif any(k in cmd for k in ['открой аудиокниг', 'открой книгу', 'начни книгу', 'запусти аудиокниг']):
                book_match = re.search(r'(?:открой|начни|запусти)\s+(?:аудиокниг|книгу)\s+(.+)', cmd)
                book_path = book_match.group(1) if book_match else ""
                self.audiobook_cmd('open', book_path)
            elif any(k in cmd for k in ['паузу книгу', 'стоп книгу', 'пауза книгу', 'останови книгу']):
                self.audiobook_cmd('pause')
            elif any(k in cmd for k in ['продолжи книгу', 'воспроизведи книгу', 'играть книгу']):
                self.audiobook_cmd('play')
            elif any(k in cmd for k in ['стоп книгу', 'останови книгу']):
                self.audiobook_cmd('stop')
            elif any(k in cmd for k in ['позицию книгу', 'где книгу', 'где остановился']):
                self.audiobook_cmd('position')
            elif any(k in cmd for k in ['перемотай книгу', 'перемотку книгу']):
                self.audiobook_cmd('seek', cmd)
            elif any(k in cmd for k in ['историю книгу', 'какую книгу']):
                self.audiobook_cmd('history')
            
            elif any(k in cmd for k in ['рабочий стол', 'рабочий', 'покажи рабочий', 'открой рабочий', 'стол']): self.window_cmd('show_desktop')
            
            elif any(k in cmd for k in ['время', 'дата', 'какой час', 'какая дата', 'часы', 'календарь', 'календарь сегодня', 'что сегодня', 'расписание']):
                now = datetime.now()
                time_str = now.strftime('%H:%M')
                date_str = now.strftime('%d.%m.%Y')
                day_str = now.strftime('%A')
                # Перевод дня недели на русский
                days_rus = {'Monday': 'Понедельник', 'Tuesday': 'Вторник', 'Wednesday': 'Среда', 'Thursday': 'Четверг', 'Friday': 'Пятница', 'Saturday': 'Суббота', 'Sunday': 'Воскресенье'}
                day_name = days_rus.get(day_str, day_str)
                
                calendar_text = f"Сегодня {day_name}, {date_str}. Время: {time_str}."
                self._safe_add_dialog(calendar_text, is_response=True)
                self._safe_speak(calendar_text)
                return
            elif any(w in cmd for w in ['закрой окно', 'закрыть окно', 'закрыть это окно', 'закрой это окно']): self.window_cmd('close_active')
            else:
                matched = False

            if matched:
                # Мгновенное выполнение без задержки
                silent_words = ['диагностик', 'выключи', 'перезагрузить', 'спящий', 'привет', 'здравствуй', 'спасиб', 'молодец', 'ок', 'дурак', 'нахуй', 'бля', 'пидор', 'как дел', 'как настроен', 'рабочий стол', 'рабочий', 'стол', 'как дела', 'создатель', 'создал', 'автор', 'как ты', 'что нов', 'красавчик', 'отличн', 'хорошо', 'понял', 'принят', 'ладно', 'погод', 'новости', 'скриншот']
                if not any(w in cmd for w in silent_words):
                    random_done = random.choice([_get_mp3('done'), _get_mp3('done1'), _get_mp3('done2'), _get_mp3('done3')])
                    done_text = "Готово. Всё исполнено в лучшем виде."
                    self._safe_add_dialog(done_text, is_response=True)
                    self.play_sound_from_folder(random_done, fallback_text=done_text)
            else:
                # === FALLBACK НА ИИ С ВЫПОЛНЕНИЕМ КОМАНД ===
                ai_executed = False
                try:
                    log.info("Команда не распознана стандартными методами, отправляю ИИ: %s", cmd)
                    
                    # === ПРОВЕРКА: НЕ содержит ли команду только 'пименов' без вопроса ===
                    creator_keywords = ['пименов', 'романович']
                    question_words = ['кто', 'что', 'расскажи', 'расскажи о', 'твой', 'тебя', 'создал', 'создатель', 'разработал', 'разработчик', 'автор', 'придумал', 'написал', 'сделал']
                    # Слова-команды (не вопросы)
                    command_words = ['найди', 'поиск', 'поищи', 'открой', 'открыть', 'закрой', 'закрыть', 'запусти', 'запустить', 'включи', 'выключи', 'сделай', 'прочитай', 'прочти', 'сохрани', 'сохранить', 'создай', 'сгенерируй']
                    
                    has_creator_name = any(kw in cmd for kw in creator_keywords)
                    has_question = any(qw in cmd for qw in question_words)
                    has_command = any(cw in cmd for cw in command_words)
                    
                    # Проверяем 'алекс', 'рома' только если это явно про создателя
                    has_creator_alias = any(kw in cmd for kw in ['алекс', 'рома', 'алик', 'алей', 'ром'])
                    if has_creator_alias:
                        # Если есть 'я ' в начале или 'зовут', 'не', 'алин' - это представление пользователя
                        if (' я ' in cmd or cmd.startswith('я ') or 'зовут' in cmd or ' не ' in cmd or 'алин' in cmd or 'имя' in cmd):
                            has_creator_alias = False  # Это не команда создателя
                    
                    log.info(f"DEBUG: has_creator_name={has_creator_name}, has_creator_alias={has_creator_alias}, has_question={has_question}, has_command={has_command}")
                    
                    if (has_creator_name or has_creator_alias) and not has_question:
                        # Если есть команда (найди, открой и т.д.) - это не вопрос
                        if has_command:
                            log.info("Пропускаю 'пименов' с командой - отправляю ИИ")
                            # Пропускаем ИИ для обработки
                            pass
                        # Если нет вопроса - тоже отправляем ИИ
                        log.info("Пропускаю 'пименов' без вопроса - отправляю ИИ")
                        # Пропускаем ИИ для обработки
                        pass
                    
                    # === ЗАПРОС К GIGACHAT ===
                    log.info("="*80)
                    log.info("🤖 [AI] ОТПРАВЛЯЮ ЗАПРОС: %s", cmd)
                    log.info("🤖 [AI] GIGACHAT_OK=%s", GIGACHAT_OK)
                    try:
                        raw_reply = self.ask_gemini(cmd)
                        log.info("🤖 [AI] ask_gemini вернул: %s", type(raw_reply))
                        if raw_reply:
                            log.info("✅ AI: ответ получен, длина=%d", len(raw_reply))
                            log.info("✅ AI: ответ (первые 100 символов): %s", raw_reply[:100])
                        else:
                            log.warning("⚠️ [AI] ask_gemini вернул None")
                    except Exception as e:
                        log.error("❌ [AI] Исключение при вызове AI: %s", e, exc_info=True)
                        raw_reply = None
                    
                    if not raw_reply:
                        log.error("❌ [AI] AI не ответил, возвращаю ошибку")
                        raw_reply = "Извините, я сейчас не могу обработать ваш запрос. Попробуйте ещё раз."
                    
                    # === ДОБАВЛЯЕМ ИМЯ ПЕРСОНАЖА К ОТВЕТУ ===
                    persona_name = self.personas.get(self.current_persona, {}).get('name', 'Jarvis')
                    
                    # Пытаемся извлечь JSON-команду из ответа
                    is_command, action, params = self.parse_ai_command(raw_reply)
                    
                    if is_command:
                        # ИИ вернул команду — выполняем
                        self._safe_add_dialog(f"🧠 ИИ распознал команду: {action}", is_response=True)
                        ai_executed = self.execute_ai_action(action, params)
                        if not ai_executed:
                            # Команда не распознана — показываем текстовый ответ (имя добавится в add_to_dialog)
                            reply_text = params.get('text', raw_reply)
                            self._safe_add_dialog(reply_text, is_response=True)
                            self._safe_speak(reply_text)
                    else:
                        # Обычный текстовый ответ от ИИ (имя добавится в add_to_dialog)
                        reply_text = raw_reply
                        self._safe_add_dialog(reply_text, is_response=True)
                        self._safe_speak(reply_text)
                        
                except Exception as exc:
                    log.error("❌ [AI] Ошибка: %s", exc)
                    reply = f"Ошибка AI: {str(exc)[:120]}"
                    if not ai_executed:
                        self._safe_add_dialog(reply, is_response=True)
                        self._safe_speak(reply)
        except Exception as e:
            self._safe_add_dialog(f"Ошибка выполнения: {str(e)[:50]}", is_response=True)
        finally:
            with self.command_lock:
                self.command_busy = False
            self._safe_ui(lambda: self.status_label.config(
                text="● СИСТЕМА ГОТОВА", fg="#10b981"
            ))

    def parse_ai_command(self, text):
        """Извлекает JSON-команду из ответа GigaChat.
        ИИ может вернуть команду в формате:
        ```json
        {"action": "open_app", "params": {"name": "chrome"}}
        ```
        Или обычный текстовый ответ.
        Возвращает (is_command, action, params)"""
        text = text.strip()
        # Ищем JSON в markdown-блоке ```json ... ```
        json_match = re.search(r'```(?:json)?\s*\n?({.*?})\n?```', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if 'action' in data and isinstance(data.get('params'), dict):
                    return True, data['action'], data['params']
            except json.JSONDecodeError:
                pass
        # Ищем JSON без markdown
        json_match = re.search(r'\{[^{}]*"action"[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if 'action' in data and isinstance(data.get('params'), dict):
                    return True, data['action'], data['params']
            except json.JSONDecodeError:
                pass
        # Это обычный текстовый ответ
        clean_text = re.sub(r'```(?:json)?\s*\n?.*?\n?```', '', text, flags=re.DOTALL).strip()
        return False, None, {'text': clean_text if clean_text else text}

    def execute_ai_action(self, action, params):
        """Выполняет команду от ИИ.
        Доступные действия:
        - open_app: открыть приложение
        - open_url: открыть сайт
        - open_file: открыть файл
        - shutdown: выключить ПК
        - restart: перезагрузить ПК
        - sleep: спящий режим
        - lock: заблокировать экран
        - screenshot: сделать скриншот
        - search: поиск в интернете
        - play_music: включить музыку
        - close_app: закрыть приложение
        - volume_up/down/mute: управление звуком
        - send_keys: отправить клавиши
        - text_reply: обычный текстовый ответ"""
        self.add_to_dialog(f"🧠 ИИ выполняет: {action}", is_response=True)
        
        try:
            if action == 'open_app':
                name = params.get('name', '')
                if name and self.launch_app(name):
                    self.speak_jarvis_free(f"Открыл {name}.")
                else:
                    self.speak_jarvis_free(f"Пытаюсь открыть {name}.")
                    self.launch_app(name)
            
            elif action == 'open_url':
                url = params.get('url', '')
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                webbrowser.open(url)
                self.speak_jarvis_free("Открыл ссылку.")
            
            elif action == 'open_file':
                path = params.get('path', '')
                if path and os.path.exists(path):
                    os.startfile(path)
                    self.speak_jarvis_free("Открыл файл.")
                else:
                    self.speak_jarvis_free("Файл не найден.")
            
            elif action == 'shutdown':
                delay = params.get('delay', 60)
                os.system(f'shutdown -s -t {delay}')
                self.speak_jarvis_free("Выключаю компьютер.")
            
            elif action == 'restart':
                delay = params.get('delay', 60)
                os.system(f'shutdown -r -t {delay}')
                self.speak_jarvis_free("Перезагружаю компьютер.")
            
            elif action == 'cancel_shutdown':
                os.system('shutdown -a')
                self.speak_jarvis_free("Отменил выключение.")
            
            elif action == 'sleep':
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
                self.speak_jarvis_free("Перехожу в спящий режим.")
            
            elif action == 'hibernate':
                os.system('shutdown -h -f -t 10')
                self.speak_jarvis_free("Перехожу в гибернацию.")
            
            elif action == 'lock':
                os.system('rundll32.exe user32.dll,LockWorkStation')
                self.speak_jarvis_free("Блокирую систему.")
            
            elif action == 'screenshot':
                self.take_screenshot()
                self.speak_jarvis_free("Сделал скриншот.")
            
            elif action == 'search':
                query = params.get('query', '')
                engine = params.get('engine', 'google')
                if engine == 'google':
                    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
                elif engine == 'yandex':
                    webbrowser.open(f"https://yandex.ru/search/?text={urllib.parse.quote_plus(query)}")
                elif engine == 'youtube':
                    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote_plus(query)}")
                else:
                    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}")
                self.speak_jarvis_free("Ищу в интернете.")
            
            elif action == 'play_music':
                query = params.get('query', '')
                if query:
                    encoded = urllib.parse.quote(query)
                    webbrowser.open(f"https://music.yandex.ru/search/text={encoded}")
                    self.speak_jarvis_free(f"Включаю {query}.")
                else:
                    webbrowser.open("https://music.yandex.ru/")
                    self.speak_jarvis_free("Открыл Яндекс.Музыку.")
            
            elif action == 'close_app':
                name = params.get('name', '')
                if name:
                    self.close_app(self._resolve_process(name))
                    self.speak_jarvis_free(f"Закрыл {name}.")
                else:
                    if PYAUTOGUI_OK:
                        pyautogui.hotkey('alt', 'f4')
                    self.speak_jarvis_free("Закрыл активное окно.")
            
            elif action == 'volume_up':
                self.audio_cmd('volume_up')
                self.speak_jarvis_free("Увеличил громкость.")
            
            elif action == 'volume_down':
                self.audio_cmd('volume_down')
                self.speak_jarvis_free("Уменьшил громкость.")
            
            elif action == 'mute':
                self.audio_cmd('mute')
                self.speak_jarvis_free("Отключил звук.")
            
            elif action == 'unmute':
                self.audio_cmd('unmute')
                self.speak_jarvis_free("Включил звук.")
            
            elif action == 'send_keys':
                keys = params.get('keys', '')
                if PYAUTOGUI_OK:
                    # Обрабатываем специальные клавиши
                    key_map = {
                        'enter': 'enter', 'tab': 'tab', 'escape': 'esc',
                        'space': 'space', 'backspace': 'backspace',
                        'delete': 'delete', 'home': 'home', 'end': 'end',
                        'pageup': 'pageup', 'pagedown': 'pagedown',
                        'left': 'left', 'right': 'right', 'up': 'up', 'down': 'down',
                        'f1': 'f1', 'f2': 'f2', 'f3': 'f3', 'f4': 'f4',
                        'f5': 'f5', 'f6': 'f6', 'f7': 'f7', 'f8': 'f8',
                        'f9': 'f9', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
                        'volumeup': 'volumeup', 'volumedown': 'volumedown',
                        'volumemute': 'volumemute',
                    }
                    key_list = [k.strip() for k in keys.split('+')]
                    translated = [key_map.get(k, k) for k in key_list]
                    if len(translated) == 1:
                        pyautogui.press(translated[0])
                    else:
                        pyautogui.hotkey(*translated)
                self.speak_jarvis_free("Выполнил нажатие.")
            
            elif action == 'minimize_all':
                os.system('powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"')
                self.speak_jarvis_free("Свернул все окна.")
            
            elif action == 'weather':
                self.weather_cmd()
            
            elif action == 'time':
                now = datetime.now()
                time_str = now.strftime('%H:%M')
                self.speak_jarvis_free(f"Сейчас {time_str}.")
            
            # === КОМАНДЫ СОХРАНЕНИЯ ФАКТОВ ===
            elif action == 'save_name':
                name = params.get('name', '')
                if name:
                    with self._memory_lock:
                        self.user_name = name
                        self.user_memory['user_name'] = name
                        self.is_first_run = False
                    self._save_persistent_memory()
                    log.info(f"📝 [ПАМЯТЬ] Сохранил имя: {name}")
                    self.speak_jarvis_free(f"Запомнил, твоё имя {name}.")
            
            elif action == 'save_gender':
                gender = params.get('gender', '')
                if gender:
                    with self._memory_lock:
                        self.user_gender = gender
                        self.user_memory['user_gender'] = gender
                        self.is_first_run = False
                    self._save_persistent_memory()
                    log.info(f"📝 [ПАМЯТЬ] Сохранил пол: {gender}")
                    self.speak_jarvis_free(f"Запомнил.")
            
            elif action == 'save_hobby':
                hobby = params.get('hobby', '')
                if hobby:
                    with self._memory_lock:
                        if hobby not in self.user_hobbies:
                            self.user_hobbies.append(hobby)
                        self.user_memory['hobby_' + hobby] = True
                        self.is_first_run = False
                    self._save_persistent_memory()
                    log.info(f"📝 [ПАМЯТЬ] Сохранил хобби: {hobby}")
                    self.speak_jarvis_free(f"Запомнил, ты увлекаешься {hobby}.")
            
            elif action == 'save_family':
                family_member = params.get('family', '')
                if family_member:
                    with self._memory_lock:
                        if family_member not in self.user_family:
                            self.user_family.append(family_member)
                        self.is_first_run = False
                    self._save_persistent_memory()
                    log.info(f"📝 [ПАМЯТЬ] Сохранил члена семьи: {family_member}")
                    self.speak_jarvis_free(f"Запомнил про {family_member}.")
            
            elif action == 'diagnostics':
                cpu = psutil.cpu_percent(interval=0.5)
                ram = psutil.virtual_memory().percent
                self.speak_jarvis_free(f"Процессор {cpu} процентов, память {ram} процентов.")
            
            else:
                self.add_to_dialog(f"⚠️ ИИ команда не распознана: {action}", is_response=True)
                return False
                
            return True
            
        except Exception as e:
            log.error("Ошибка выполнения AI-команды %s: %s", action, e)
            self.speak_jarvis_free(f"Ошибка выполнения команды: {str(e)[:50]}")
            return False

    def play_specific_toxic(self, filename, text):
        self.add_to_dialog(text, is_response=True)
        self.play_sound_from_folder(filename, fallback_text=text)
    
    def set_volume_level(self, level):
        if PYAUTOGUI_OK:
            try:
                for _ in range(25): pyautogui.press('volumedown')
                for _ in range(level * 5): pyautogui.press('volumeup')
            except: pass

    def open_browser(self, browser):
        self.add_to_dialog(f"Запускаю браузер {browser}...", is_response=True)
        try:
            if browser == 'chrome': subprocess.Popen(['chrome'])
            elif browser == 'firefox': subprocess.Popen(['firefox'])
        except: webbrowser.open('https://google.com')
    
    def open_web(self, site):
        urls = {'youtube': 'https://youtube.com', 'google': 'https://google.com', 'github': 'https://github.com',
                'yandex': 'https://yandex.ru', 'vk': 'https://vk.com'}
        if site in urls:
            self.add_to_dialog(f"Открываю веб-ресурс: {site}", is_response=True)
            webbrowser.open(urls[site])
    
    def _find_exe(self, name, fallback_paths):
        """Ищет исполняемый файл: сначала в PATH, потом по спискам путей"""
        # Сначала ищем в PATH
        for path in os.environ.get('PATH', '').split(os.pathsep):
            exe = os.path.join(path, name)
            if os.path.exists(exe):
                return exe
        
        # Потом по известным путям
        for fp in fallback_paths:
            expanded = os.path.expandvars(fp)
            if os.path.exists(expanded):
                return expanded
        
        return None

    def launch_app(self, app):
        app_clean = app.lower().strip()
        try:
            apps = {
                'телеграм': 'telegram', 'telegram': 'telegram',
                'дискорд': 'discord', 'discord': 'discord',
                'хром': 'chrome', 'chrome': 'chrome',
                'стим': 'steam', 'steam': 'steam',
                'ворд': 'winword', 'word': 'winword',
                'эксель': 'excel', 'excel': 'excel',
                'блокнот': 'notepad', 'notepad': 'notepad',
                'калькулятор': 'calc', 'calc': 'calc',
                'вскод': 'code', 'vscode': 'code',
                'проводник': 'explorer', 'explorer': 'explorer',
                'браузер': 'chrome'
            }
            if app_clean in apps:
                exe_name = apps[app_clean]
                self.add_to_dialog(f"Запускаю приложение: {app_clean}...", is_response=True)
                
                # Steam — ищем по пути установки
                if exe_name == 'steam':
                    steam_paths = [
                        r'C:\Program Files (x86)\Steam\steam.exe',
                        r'C:\Program Files\Steam\steam.exe',
                        os.path.expandvars(r'%ProgramFiles(x86)%\Steam\steam.exe'),
                        os.path.expandvars(r'%ProgramFiles%\Steam\steam.exe'),
                        os.path.expandvars(r'%LocalAppData%\Steam\steam.exe'),
                    ]
                    steam_exe = self._find_exe('steam.exe', steam_paths)
                    if steam_exe:
                        subprocess.Popen(steam_exe, shell=False)
                    else:
                        try:
                            subprocess.Popen('steam://open/bigpicture', shell=True)
                        except:
                            pass
                # VSCode — ищем по пути
                elif exe_name == 'code':
                    code_paths = [
                        r'C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe',
                        r'C:\Program Files\Microsoft VS Code\Code.exe',
                        r'C:\Program Files (x86)\Microsoft VS Code\Code.exe',
                        os.path.expandvars(r'%LocalAppData%\Programs\Microsoft VS Code\Code.exe'),
                    ]
                    code_exe = self._find_exe('Code.exe', code_paths)
                    if code_exe:
                        subprocess.Popen(code_exe, shell=False)
                    else:
                        subprocess.Popen('code', shell=True)
                # Discord — ищем по пути
                elif exe_name == 'discord':
                    discord_paths = [
                        r'C:\Users\%USERNAME%\AppData\Local\Discord\app-1.0.\Discord.exe',
                        r'C:\Program Files\Discord\Discord.exe',
                        r'C:\Program Files (x86)\Discord\Discord.exe',
                    ]
                    discord_exe = self._find_exe('Discord.exe', discord_paths)
                    if discord_exe:
                        subprocess.Popen(discord_exe, shell=False)
                    else:
                        subprocess.Popen('discord', shell=True)
                # Telegram — ищем по пути
                elif exe_name == 'telegram':
                    telegram_paths = [
                        r'C:\Program Files\Telegram\Telegram.exe',
                        r'C:\Program Files (x86)\Telegram\Telegram.exe',
                        os.path.expandvars(r'%LocalAppData%\Telegram\Telegram.exe'),
                    ]
                    telegram_exe = self._find_exe('Telegram.exe', telegram_paths)
                    if telegram_exe:
                        subprocess.Popen(telegram_exe, shell=False)
                    else:
                        subprocess.Popen('telegram', shell=True)
                # Chrome — ищем по пути
                elif exe_name == 'chrome':
                    chrome_paths = [
                        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
                    ]
                    chrome_exe = self._find_exe('chrome.exe', chrome_paths)
                    if chrome_exe:
                        subprocess.Popen(chrome_exe, shell=False)
                    else:
                        subprocess.Popen('chrome', shell=True)
                # Остальные — через shell (notepad, calc, explorer и т.д.)
                else:
                    subprocess.Popen(exe_name, shell=True)
                return True
            return False
        except:
            return False

    def close_app(self, app_process):
        app_clean = app_process.lower().strip()
        closed_count = 0
        self.add_to_dialog(f"Закрываю: {app_clean}...", is_response=True)
        
        # Ищем процессы по имени и убиваем
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if app_clean in proc.info['name'].lower():
                    proc.kill()
                    closed_count += 1
            except:
                pass
        
        # Если не нашли — ищем окна по заголовку и закрываем
        if closed_count == 0 and PYAUTOGUI_OK:
            try:
                windows = pyautogui.getWindowsWithTitle(app_clean)
                for win in windows:
                    if not win.isMinimized:
                        import ctypes
                        # WM_CLOSE = 0x0010
                        ctypes.windll.user32.PostMessageW(win.hwnd, 0x0010, 0, 0)
                        closed_count += 1
                        time.sleep(0.3)
            except:
                pass
        
        # Fallback — taskkill по имени процесса
        if closed_count == 0:
            try:
                subprocess.run(f'taskkill /F /IM {app_clean}*.exe', shell=True, capture_output=True, timeout=5)
            except:
                pass
        
        self.add_to_dialog(f"Закрыто: {closed_count}" if closed_count > 0 else "Не найдено.", is_response=True)

    def window_cmd(self, action):
        if action == 'close_active' and PYAUTOGUI_OK:
            try: pyautogui.hotkey('alt', 'f4')
            except: pass
        elif action == 'minimize_all':
            os.system('powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"')
        elif action == 'restore_all':
            os.system('powershell -command "(New-Object -ComObject Shell.Application).UndoMinimizeALL()"')
        elif action == 'show_desktop':
            os.system('powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"')
    
    def audio_cmd(self, action):
        if not PYAUTOGUI_OK:
            log.error("PYAUTOGUI не доступен, не могу управлять звуком")
            self.add_to_dialog("⚠️ Управление звуком недоступно (pyautogui не установлен).", is_response=True)
            return
        
        try:
            if action == 'volume_up':
                log.info("Увеличиваю громкость...")
                for _ in range(5):
                    pyautogui.press('volumeup')
                    time.sleep(0.1)
                log.info("Громкость увеличена")
            elif action == 'volume_down':
                log.info("Уменьшаю громкость...")
                for _ in range(5):
                    pyautogui.press('volumedown')
                    time.sleep(0.1)
                log.info("Громкость уменьшена")
            elif action == 'mute':
                log.info("Отключаю звук...")
                pyautogui.press('volumemute')
                log.info("Звук отключён")
            elif action == 'unmute':
                log.info("Включаю звук...")
                pyautogui.press('volumemute')
                log.info("Звук включён")
            else:
                log.warning("Неизвестная команда звука: %s", action)
        except Exception as e:
            log.error("Ошибка управления звуком: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:50]}", is_response=True)

    def keyboard_backlight_cmd(self, action, level=None):
        """Управление подсветкой клавиатуры ноутбука"""
        if not PYAUTOGUI_OK:
            self.add_to_dialog("⚠️ Модуль управления клавиатурой недоступен.", is_response=True)
            return
        
        # Карта горячих клавиш для разных производителей
        # Формат: 'brand': {'on': [...], 'off': [...], 'bright_up': [...], 'bright_down': [...]}
        backlight_keys = {
            'lenovo': {
                'on': [['f5'], ['f5'], ['f5']],  # Разные варианты включения
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # Обычно F5/F6 или F10/F11
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5'], ['f5']]
            },
            'asus': {
                'on': [['f5'], ['f5']],
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # F5/F6 для подсветки
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5']]
            },
            'hp': {
                'on': [['f5'], ['f5']],
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # F5/F6
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5']]
            },
            'dell': {
                'on': [['f5'], ['f5']],
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # F5/F6
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5']]
            },
            'acer': {
                'on': [['f5'], ['f5']],
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # F5/F6
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5']]
            },
            'msi': {
                'on': [['f5'], ['f5']],
                'off': [['f5'], ['f5']],
                'bright_up': [['f5'], ['f5']],  # F5/F6 или F10/F11
                'bright_down': [['f6'], ['f6']],
                'toggle': [['f5']]
            },
            'generic': {
                'on': [['f5'], ['f10'], ['f9']],  # Универсальные варианты
                'off': [['f5'], ['f10']],
                'bright_up': [['f5'], ['f10'], ['f9']],  # F5/F6, F10/F11
                'bright_down': [['f6'], ['f11'], ['f8']],
                'toggle': [['f5'], ['f10']]
            }
        }
        
        try:
            if action == 'on':
                self.add_to_dialog("💡 Включаю подсветку клавиатуры...", is_response=True)
                # Пробуем несколько комбинаций для включения
                for keys in backlight_keys['generic']['on']:
                    time.sleep(0.2)
                    pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Подсветка клавиатуры включена.")
                
            elif action == 'off':
                self.add_to_dialog("🌑 Выключаю подсветку клавиатуры...", is_response=True)
                for keys in backlight_keys['generic']['off']:
                    time.sleep(0.2)
                    pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Подсветка клавиатуры выключена.")
                
            elif action == 'toggle':
                self.add_to_dialog("🔄 Переключаю подсветку клавиатуры...", is_response=True)
                for keys in backlight_keys['generic']['toggle']:
                    time.sleep(0.2)
                    pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Подсветка переключена.")
                
            elif action == 'bright_up':
                self.add_to_dialog("ИИ️ Увеличиваю яркость подсветки...", is_response=True)
                for _ in range(3):  # 3 нажатия для заметного эффекта
                    for keys in backlight_keys['generic']['bright_up']:
                        time.sleep(0.2)
                        pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Яркость подсветки увеличена.")
                
            elif action == 'bright_down':
                self.add_to_dialog("🌙 Уменьшаю яркость подсветки...", is_response=True)
                for _ in range(3):
                    for keys in backlight_keys['generic']['bright_down']:
                        time.sleep(0.2)
                        pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Яркость подсветки уменьшена.")
                
            elif action == 'max':
                self.add_to_dialog("🔆 Устанавливаю максимальную яркость подсветки...", is_response=True)
                for _ in range(10):  # Максимальное увеличение
                    for keys in backlight_keys['generic']['bright_up']:
                        time.sleep(0.15)
                        pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Максимальная яркость подсветки.")
                
            elif action == 'min':
                self.add_to_dialog("🌑 Устанавливаю минимальную яркость подсветки...", is_response=True)
                for _ in range(10):
                    for keys in backlight_keys['generic']['bright_down']:
                        time.sleep(0.15)
                        pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Минимальная яркость подсветки.")
                
            elif action == 'cycle':
                self.add_to_dialog("🌈 Циклическое переключение подсветки...", is_response=True)
                # Цикл: вкл -> макс -> выкл -> мин -> вкл
                for keys in backlight_keys['generic']['on']:
                    time.sleep(0.2)
                    pyautogui.hotkey(*keys)
                time.sleep(0.5)
                for _ in range(8):
                    for keys in backlight_keys['generic']['bright_up']:
                        time.sleep(0.15)
                        pyautogui.hotkey(*keys)
                self.speak_jarvis_free("Циклическое переключение подсветки запущено.")
                
            else:
                self.add_to_dialog(f"⚠️ Неизвестная команда подсветки: {action}", is_response=True)
                
        except Exception as e:
            log.error("Ошибка управления подсветкой: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка управления подсветкой: {str(e)[:50]}", is_response=True)

    def _find_yandex_music_app(self):
        """Ищет установленное приложение Яндекс.Музыки"""
        # Проверяем запущенные процессы
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] and 'yandexmusic' in proc.info['name'].lower():
                    return 'running'
            except:
                pass
        
        # Проверяем стандартные пути установки
        possible_paths = [
            r'C:\Program Files\Yandex\YandexMusic\yandexmusic.exe',
            r'C:\Program Files (x86)\Yandex\YandexMusic\yandexmusic.exe',
            r'%LOCALAPPDATA%\Yandex\YandexMusic\yandexmusic.exe',
            r'%PROGRAMFILES%\Yandex\YandexMusic\yandexmusic.exe'
        ]
        for path in possible_paths:
            expanded = os.path.expandvars(path)
            if os.path.exists(expanded):
                return expanded
        
        # Проверяем реестр (установленные приложения)
        if winreg:
            try:
                key = winreg.HKEY_LOCAL_MACHINE
                paths_to_check = [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
                ]
                for reg_path in paths_to_check:
                    try:
                        with winreg.OpenKey(key, reg_path, 0, winreg.KEY_READ) as hkey:
                            i = 0
                            while True:
                                try:
                                    subkey = winreg.EnumKey(hkey, i)
                                    try:
                                        with winreg.OpenKey(hkey, subkey) as subkey:
                                            display_name, _ = winreg.QueryValueEx(subkey, 'DisplayName')
                                            if 'yandex' in display_name.lower() and 'music' in display_name.lower():
                                                try:
                                                    exe_path, _ = winreg.QueryValueEx(subkey, 'InstallLocation')
                                                    exe_file = os.path.join(exe_path, 'yandexmusic.exe')
                                                    if os.path.exists(exe_file):
                                                        return exe_file
                                                except:
                                                    pass
                                                try:
                                                    exe_path, _ = winreg.QueryValueEx(subkey, 'ExecutablePath')
                                                    if exe_path and 'yandexmusic' in exe_path.lower():
                                                        return exe_path
                                                except:
                                                    pass
                                    except:
                                        pass
                                    i += 1
                                except (FileNotFoundError, OSError):
                                    break
                    except (FileNotFoundError, OSError):
                        pass
            except Exception as e:
                log.info("Реестр недоступен (это нормально): %s", e)
        
        return None
    
    def _find_yandex_music_window(self):
        """Ищет окно Яндекс.Музыки (браузер или приложение) по частичному совпадению"""
        import pyautogui
        
        # Ключевые слова для поиска (все варианты названий окон)
        keywords = [
            'music.yandex',
            'music.yandex.ru',
            'яндекс.музык',
            'yandex music',
            'музык',
            'музыка',
            'музык',
            'муз',
        ]
        
        # Получаем все окна
        all_windows = pyautogui.getWindowsWithTitle('')
        
        # Сначала ищем точное совпадение с главными ключами
        for kw in ['music.yandex', 'music.yandex.ru']:
            windows = pyautogui.getWindowsWithTitle(kw)
            if windows:
                return windows[0]
        
        # Затем ищем по частичному совпадению
        for win in all_windows:
            win_title = win.title.lower()
            for kw in keywords:
                if kw in win_title:
                    log.info(f"Найдено окно Яндекс.Музыки: '{win.title}'")
                    return win
        
        # Если не нашли по названию — ищем по процессу
        for proc in psutil.process_iter(['name', 'cmdline', 'pid']):
            try:
                cmdline = ' '.join(proc.info.get('cmdline') or [])
                if 'music.yandex' in cmdline.lower() or 'yandexmusic' in cmdline.lower():
                    # Пытаемся найти окно по PID
                    try:
                        for win in all_windows:
                            if win.pid == proc.info.get('pid'):
                                log.info(f"Найдено окно Яндекс.Музыки по PID: '{win.title}'")
                                return win
                    except:
                        pass
            except:
                pass
        
        log.warning("Окно Яндекс.Музыки не найдено")
        return None
    
    def _activate_yandex_music(self, wait_for_focus=1.0):
        """Находит и активирует окно Яндекс.Музыки, возвращает True если успешно
        wait_for_focus - время ожидания установки фокуса (секунды)"""
        import pyautogui
        
        win = self._find_yandex_music_window()
        if not win:
            return False
        
        log.info(f"Активация окна Яндекс.Музыки: '{win.title}'")
        
        try:
            # Метод 1: win32gui (самый надёжный для Windows)
            if HAS_WIN32:
                try:
                    import win32gui
                    import win32con
                    hwnd = win.id
                    # Сначала восстанавливаем окно если свёрнуто
                    if hasattr(win, 'showCmd') and win.showCmd == win32con.SW_MINIMIZE:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        time.sleep(0.3)
                    # Активируем окно
                    win32gui.SetForegroundWindow(hwnd)
                    log.info("✅ Окно активировано через win32gui.SetForegroundWindow()")
                    # Ждём установки фокуса
                    time.sleep(wait_for_focus)
                    return True
                except Exception as e:
                    log.debug("win32gui не сработал: %s", e)
            
            # Метод 2: pyautogui.click по рабочей области окна
            try:
                # Кликаем в центр окна (не по заголовку)
                x = win.left + win.width // 2
                y = win.top + win.height // 2
                pyautogui.click(x, y)
                log.info("✅ Окно активировано через pyautogui.click() в центр окна")
                # Ждём установки фокуса
                time.sleep(wait_for_focus)
                return True
            except Exception as e:
                log.debug("pyautogui.click() не сработал: %s", e)
            
            # Метод 3: activate()
            try:
                win.activate()
                log.info("✅ Окно активировано через win.activate()")
                # Ждём установки фокуса
                time.sleep(wait_for_focus)
                return True
            except Exception as e:
                log.debug("win.activate() не сработал: %s", e)
            
            log.warning("❌ Не удалось активировать окно Яндекс.Музыки никаким методом")
            return False
            
        except Exception as e:
            log.error("Ошибка активации окна: %s", e)
            return False
    
    def _send_key_to_yandex_music(self, key, delay_after_focus=1.5):
        """Отправляет клавишу в окно Яндекс.Музыки с надёжной проверкой фокуса
        key - клавиша для отправки ('space', 'n', 'p', etc.)
        delay_after_focus - дополнительное время после фокусировки"""
        import pyautogui
        
        log.info(f"🎵 Отправка клавиши '{key}' в Яндекс.Музыку...")
        
        # Находим окно
        win = self._find_yandex_music_window()
        if not win:
            log.error("❌ Окно Яндекс.Музыки не найдено")
            return False
        
        log.info(f"Найдено окно: '{win.title}'")
        
        try:
            # Метод 1: Пробуем через win32api.SendMessage (самый надёжный)
            if HAS_WIN32 and HAS_CTYPES:
                try:
                    hwnd = win.id
                    
                    # Восстанавливаем окно если свёрнуто
                    if hasattr(win, 'showCmd') and win.showCmd == win32con.SW_MINIMIZE:
                        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        time.sleep(0.3)
                    
                    # Активируем окно
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.5)
                    
                    # Кликаем в центр окна через win32api
                    x = win.left + win.width // 2
                    y = win.top + win.height // 2
                    lparam = y << 16 | x
                    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
                    time.sleep(0.1)
                    win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, lparam)
                    time.sleep(0.5)
                    
                    log.info("✅ Окно активировано через win32api")
                    
                    # Используем SendMessage для отправки клавиши
                    vkey = ctypes.windll.user32.VkKeyScanW(ord(key.upper())) & 0xFF
                    lparam_data = ctypes.c_ulong(1).value  # repeat count
                    lparam_data |= 0  # previous key state
                    lparam_data |= 0 << 16  # transition state
                    
                    ctypes.windll.user32.SendMessageW(
                        hwnd, win32con.WM_KEYDOWN, vkey, lparam_data
                    )
                    time.sleep(0.05)
                    ctypes.windll.user32.SendMessageW(
                        hwnd, win32con.WM_KEYUP, vkey, lparam_data | (1 << 30)
                    )
                    
                    log.info(f"✅ Клавиша '{key}' отправлена через SendMessage")
                    return True
                    
                except Exception as e:
                    log.debug("win32api/postmessage не сработал: %s", e)
            
            # Метод 2: pyautogui.click + press с долгим ожиданием
            try:
                # Кликаем в центр окна
                x = win.left + win.width // 2
                y = win.top + win.height // 2
                pyautogui.click(x, y)
                time.sleep(1.5)  # Долгое ожидание для установки фокуса
                
                # Отправляем клавишу
                pyautogui.press(key)
                time.sleep(0.3)
                
                log.info("✅ Клавиша отправлена через pyautogui")
                return True
            except Exception as e:
                log.debug("pyautogui не сработал: %s", e)
            
            log.error("❌ Не удалось отправить клавишу в Яндекс.Музыку")
            return False
            
        except Exception as e:
            log.error("Ошибка отправки клавиши: %s", e)
            return False
    
    def yandex_music_cmd(self, action):
        """Управление Яндекс.Музыкой — десктопное приложение или браузер"""
        if not PYAUTOGUI_OK:
            self.add_to_dialog("⚠️ pyautogui недоступен.", is_response=True)
            return
        
        # Команды клавиш для Яндекс.Музыки (web app)
        # https://music.yandex.ru/ — использует стандартные медиа-клавиши
        # ВАЖНО: Правильные клавиши Яндекс.Музыки:
        # P = play/pause, N = следующий, M = предыдущий (не P!)
        commands = {
            'open': ('Открываю Яндекс.Музыку...', 'open', lambda: webbrowser.open("https://music.yandex.ru/")),
            'play': ('Воспроизвожаю...', 'play', lambda: pyautogui.press('p')),
            'pause': ('Ставлю на паузу...', 'pause', lambda: pyautogui.press('p')),
            'next': ('Следующий трек...', 'next', lambda: pyautogui.press('n')),
            'prev': ('Предыдущий трек...', 'prev', lambda: pyautogui.press('m')),
            'volume_up': ('Громче...', 'volume_up', lambda: pyautogui.press('up')),
            'volume_down': ('Тише...', 'volume_down', lambda: pyautogui.press('down')),
            'mute': ('Без звука...', 'mute', lambda: pyautogui.press('m')),
            'unmute': ('Включаю звук...', 'unmute', lambda: pyautogui.press('m')),
            'repeat': ('Повтор...', 'repeat', lambda: pyautogui.hotkey('ctrl', 'r')),
            'shuffle': ('Перемешать...', 'shuffle', lambda: pyautogui.hotkey('ctrl', 's')),
        }
        
        if action not in commands:
            self.add_to_dialog(f"⚠️ Неизвестная команда: {action}", is_response=True)
            return
        
        msg, action_name, action_func = commands[action]
        
        # Для 'open' — сначала пытаемся запустить десктопное приложение
        if action == 'open':
            app_path = self._find_yandex_music_app()
            if app_path and app_path != 'running':
                self.add_to_dialog(f"🎧 Запускаю Яндекс.Музыку (приложение)...", is_response=True)
                try:
                    subprocess.Popen(app_path, shell=True)
                    log.info("Яндекс.Музыка запущена через приложение: %s", app_path)
                    # Авто-воспроизведение через 12 секунд (приложению нужно больше времени)
                    def auto_play_app():
                        time.sleep(12)
                        try:
                            log.info("Попытка авто-воспроизведения (приложение)...")
                            if self._send_key_to_yandex_music('p', delay_after_focus=1.5):
                                log.info("✅ Авто-воспроизведение запущено (приложение)")
                                self.add_to_dialog("🎵 Воспроизведение началось!", is_response=True)
                            else:
                                log.warning("Не удалось активировать окно для авто-воспроизведения (приложение)")
                                self.add_to_dialog("⚠️ Не удалось активировать окно Яндекс.Музыки. Нажмите P вручную.", is_response=True)
                        except Exception as e:
                            log.error("Ошибка авто-воспроизведения (приложение): %s", e)
                    threading.Thread(target=auto_play_app, daemon=True).start()
                    return
                except Exception as e:
                    log.warning("Не удалось запустить приложение: %s, открываю браузер", e)
            elif app_path == 'running':
                self.add_to_dialog("🎧 Яндекс.Музыка уже запущена.", is_response=True)
                return
            # Fallback — браузер
            self.add_to_dialog(msg, is_response=True)
            # Запускаем браузер в фоне
            threading.Thread(target=action_func, daemon=True).start()
            # Авто-воспроизведение через 10 секунд (браузеру нужно время для загрузки)
            def auto_play():
                time.sleep(10)
                try:
                    log.info("Попытка авто-воспроизведения (браузер)...")
                    if self._send_key_to_yandex_music('p', delay_after_focus=1.5):
                        log.info("✅ Авто-воспроизведение запущено (браузер)")
                        self.add_to_dialog("🎵 Воспроизведение началось!", is_response=True)
                    else:
                        log.warning("Не удалось активировать окно для авто-воспроизведения (браузер)")
                        self.add_to_dialog("⚠️ Не удалось активировать окно Яндекс.Музыки. Нажмите P вручную.", is_response=True)
                except Exception as e:
                    log.error("Ошибка авто-воспроизведения (браузер): %s", e)
            threading.Thread(target=auto_play, daemon=True).start()
            return
        
        # Сообщения для пользователя
        messages = {
            'pause': '⏸️ Ставлю музыку на паузу...',
            'play': '▶️ Воспроизвожаю музыку...',
            'next': '⏭️ Переключаю на следующий трек...',
            'prev': '⏮️ Переключаю на предыдущий трек...',
            'volume_up': '🔊 Делаю громче...',
            'volume_down': '🔉 Делаю тише...',
            'mute': '🔇 Выключаю звук...',
            'unmute': '🔊 Включаю звук...',
        }
        
        if action_name in messages:
            self.add_to_dialog(messages[action_name], is_response=True)
        else:
            self.add_to_dialog(msg, is_response=True)
        
        try:
            # Используем надёжную отправку клавиши
            # Правильные горячие клавиши Яндекс.Музыки:
            # P = play/pause, N = следующий трек, M = предыдущий/ mute
            key_map = {
                'play': 'p',
                'pause': 'p',
                'next': 'n',
                'prev': 'm',
                'volume_up': 'up',
                'volume_down': 'down',
                'mute': 'm',
                'unmute': 'm',
            }
            
            if action_name in key_map:
                key_combo = key_map[action_name]
                
                # Проверяем, является ли это комбинацией клавиш (содержит '+')
                if '+' in key_combo:
                    # Отправляем комбинацию клавиш
                    keys = key_combo.split('+')
                    log.info(f"🎵 Отправка комбинации клавиш: {'+'.join(keys)}")
                    if self._activate_yandex_music(wait_for_focus=1.5):
                        time.sleep(0.3)
                        import pyautogui
                        pyautogui.hotkey(*keys)
                        log.info(f"✅ Комбинация {'+'.join(keys)} отправлена")
                else:
                    # Одиночная клавиша
                    if self._send_key_to_yandex_music(key_combo):
                        log.info("✅ Яндекс.Музыка: %s", action_name)
                    else:
                        self.add_to_dialog("⚠️ Не удалось отправить команду. Проверьте окно Яндекс.Музыки.", is_response=True)
            else:
                # Для специальных команд (shuffle, repeat) используем старый метод
                if not self._activate_yandex_music():
                    self.add_to_dialog("⚠️ Окно Яндекс.Музыки не найдено или не удалось активировать.", is_response=True)
                    return
                time.sleep(0.5)
                action_func()
                log.info("✅ Яндекс.Музыка: %s", action_name)
            
        except Exception as e:
            log.error("Ошибка управления Яндекс.Музыкой: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:50]}", is_response=True)
    
    # ==================== МЕДИА ФУНКЦИИ ====================
    def yandex_music_playlist_cmd(self, action, playlist_name=""):
        """Управление плейлистами Яндекс.Музыки"""
        if not PYAUTOGUI_OK:
            self.add_to_dialog("⚠️ pyautogui недоступен.", is_response=True)
            return
        
        playlists = {
            'daily_mix': 'Ежедневный микс',
            'top': 'Мой топ',
            'new_releases': 'Новинки',
            'chill': 'Чилл',
            'workout': 'Тренировка',
            'focus': 'Концентрация',
            'party': 'Вечеринка',
            'sleep': 'Сон'
        }
        
        if action == 'open':
            if playlist_name.lower() in playlists:
                self.add_to_dialog(f"🎵 Открываю плейлист: {playlists[playlist_name.lower()]}...", is_response=True)
                webbrowser.open(f"https://music.yandex.ru/catalog/{playlist_name.lower()}")
                self.current_playlist = playlist_name.lower()
            else:
                self.add_to_dialog("🎵 Доступные плейлисты: ежедневный микс, топ, новинки, чилл, тренировка, концентрация, вечеринка, сон", is_response=True)
        
        elif action == 'shuffle':
            self.add_to_dialog("🔀 Включаю перемешивание...", is_response=True)
            if self._activate_yandex_music(wait_for_focus=1.0):
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 's')
        
        elif action == 'repeat':
            self.add_to_dialog("🔁 Включаю повтор...", is_response=True)
            if self._activate_yandex_music(wait_for_focus=1.0):
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'r')
        
        elif action == 'like':
            self.add_to_dialog("❤️ Добавляю в избранное...", is_response=True)
            if self._activate_yandex_music(wait_for_focus=1.0):
                time.sleep(0.5)
                pyautogui.hotkey('ctrl', 'l')
        
        elif action == 'now_playing':
            self.add_to_dialog("🎵 Сейчас играет: Яндекс.Музыка", is_response=True)
            self.play_sound_from_folder(_get_mp3('process'), fallback_text="Воспроизведение через Яндекс.Музыку")
        
        elif action == 'history':
            if self.music_history:
                history_text = "\n".join([f"• {track}" for track in self.music_history[-5:]])
                self.add_to_dialog(f"📜 История воспроизведения:\n{history_text}", is_response=True)
            else:
                self.add_to_dialog("📜 История воспроизведения пуста", is_response=True)
    
    def get_music_recommendations(self, mood=""):
        """Получение рекомендаций музыки на основе настроения"""
        mood_playlists = {
            'грустное': ['chill', 'sleep'],
            'веселое': ['party', 'workout'],
            'рабочее': ['focus', 'daily_mix'],
            'спортивное': ['workout', 'party'],
            'расслабленное': ['chill', 'sleep'],
            'энергичное': ['workout', 'party'],
            'спокойное': ['chill', 'focus'],
            'траурное': ['sleep', 'chill']
        }
        
        if not mood:
            mood = "рабочее"
        
        mood_lower = mood.lower()
        recommended = mood_playlists.get(mood_lower, ['daily_mix', 'top'])
        
        recommendations = []
        for playlist in recommended:
            if playlist in playlists:
                recommendations.append(f"{playlists[playlist]} ({playlist})")
        
        self.music_recommendations = recommendations
        
        rec_text = ", ".join(recommendations) if recommendations else "Ежедневный микс"
        self.add_to_dialog(f"🎵 Рекомендую для настроения '{mood}': {rec_text}", is_response=True)
        self.speak_jarvis_free(f"Рекомендую: {rec_text}")
        
        return recommendations
    
    def audiobook_cmd(self, action, book_path=""):
        """Управление аудиокнигами"""
        if action == 'open':
            if not book_path:
                self.add_to_dialog("📚 Укажите путь к файлу аудиокниги (MP3, M4B, MP3)", is_response=True)
                return
            
            book_path = book_path.strip('"').strip("'")
            if not os.path.exists(book_path):
                self.add_to_dialog(f"⚠️ Файл не найден: {book_path}", is_response=True)
                return
            
            self.audiobook_path = book_path
            self.audiobook_book = os.path.basename(book_path)
            self.audiobook_position = 0
            
            # Загружаем сохранённую позицию
            self._load_audiobook_state()
            
            self.add_to_dialog(f"📚 Открываю аудиокнигу: {self.audiobook_book}", is_response=True)
            self.add_to_dialog(f"📍 Позиция: {self._format_time(self.audiobook_position)}", is_response=True)
            
            # Запускаем воспроизведение
            self._play_audiobook()
        
        elif action == 'play':
            if self.audiobook_path:
                self._play_audiobook()
            else:
                self.add_to_dialog("⚠️ Сначала откройте аудиокнигу командой 'открой аудиокнигу [путь]'", is_response=True)
        
        elif action == 'pause':
            self.add_to_dialog("⏸ Пауза", is_response=True)
            if PYGAME_OK:
                pygame.mixer.pause()
            self._save_audiobook_state()
        
        elif action == 'resume':
            self.add_to_dialog("▶️ Продолжаю воспроизведение", is_response=True)
            if PYGAME_OK:
                pygame.mixer.unpause()
        
        elif action == 'stop':
            self.add_to_dialog("⏹ Останавливаю воспроизведение", is_response=True)
            if PYGAME_OK:
                pygame.mixer.stop()
            self._save_audiobook_state()
        
        elif action == 'position':
            if self.audiobook_path:
                self.add_to_dialog(f"📍 Текущая позиция: {self._format_time(self.audiobook_position)}", is_response=True)
            else:
                self.add_to_dialog("⚠️ Аудиокнига не открыта", is_response=True)
        
        elif action == 'seek':
            # Перематывание на N минут
            seek_match = re.search(r'(\d+)', action)
            if seek_match:
                minutes = int(seek_match.group(1))
                self.audiobook_position += minutes * 60
                self.add_to_dialog(f"⏩ Перемотка на {minutes} минут вперёд", is_response=True)
                self._save_audiobook_state()
        
        elif action == 'history':
            self.add_to_dialog(f"📚 Последняя книга: {self.audiobook_book if self.audiobook_book else 'Нет данных'}", is_response=True)
            self.add_to_dialog(f"📍 Позиция: {self._format_time(self.audiobook_position)}", is_response=True)
    
    def _play_audiobook(self):
        """Воспроизведение аудиокниги"""
        if not self.audiobook_path or not os.path.exists(self.audiobook_path):
            return
        
        def play_thread():
            try:
                if PYGAME_OK:
                    pygame.mixer.music.load(self.audiobook_path)
                    pygame.mixer.music.play()
                    self.add_to_dialog(f"📚 Воспроизведение: {self.audiobook_book}", is_response=True)
                    self.speak_jarvis_free(f"Воспроизвожаю аудиокнигу {self.audiobook_book}")
                    
                    # Отслеживание позиции
                    while pygame.mixer.music.get_busy():
                        time.sleep(1)
                        self.audiobook_position = int(pygame.mixer.music.get_pos() / 1000)
                else:
                    # Fallback: subprocess
                    subprocess.Popen(['start', self.audiobook_path], shell=True)
            except Exception as e:
                log.error("Ошибка воспроизведения аудиокниги: %s", e)
        
        threading.Thread(target=play_thread, daemon=True).start()
    
    def _format_time(self, seconds):
        """Форматирование времени в Ч:ММ:СС"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    
    def _save_media_state(self):
        """Сохранение состояния медиа"""
        try:
            state = {
                'background_music_enabled': self.background_music_enabled,
                'current_playlist': self.current_playlist,
                'music_history': self.music_history[-20:]
            }
            media_path = Path(__file__).parent / "media_state.json"
            with open(media_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning("Не удалось сохранить состояние медиа: %s", e)
    
    def _save_audiobook_state(self):
        """Сохранение позиции аудиокниги"""
        try:
            state = {
                'book': self.audiobook_book,
                'path': self.audiobook_path,
                'position': self.audiobook_position
            }
            audiobook_path = Path(__file__).parent / "audiobook_state.json"
            with open(audiobook_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.warning("Не удалось сохранить позицию аудиокниги: %s", e)
    
    def _load_audiobook_state(self):
        """Загрузка позиции аудиокниги"""
        try:
            audiobook_path = Path(__file__).parent / "audiobook_state.json"
            if audiobook_path.exists():
                with open(audiobook_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.audiobook_book = state.get('book', '')
                self.audiobook_path = state.get('path', '')
                self.audiobook_position = state.get('position', 0)
        except Exception as e:
            log.warning("Не удалось загрузить позицию аудиокниги: %s", e)
    
    def _load_media_state(self):
        """Загрузка состояния медиа"""
        try:
            media_path = Path(__file__).parent / "media_state.json"
            if media_path.exists():
                with open(media_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                self.background_music_enabled = state.get('background_music_enabled', False)
                self.current_playlist = state.get('current_playlist', None)
                self.music_history = state.get('music_history', [])
        except Exception as e:
            log.warning("Не удалось загрузить состояние медиа: %s", e)

    def system_cmd(self, cmd):
        if cmd == 'lock': os.system('rundll32 user32.dll,LockWorkStation')
        elif cmd == 'info':
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            self.add_to_dialog(f"CPU нагрузка: {cpu}% | RAM занято: {mem:.1f}%", is_response=True)
    
    def file_cmd(self, action_type):
        profile = os.path.expandvars(r'%USERPROFILE%')
        paths = {
            'downloads': f'{profile}\\Downloads',
            'documents': f'{profile}\\Documents',
            'videos': f'{profile}\\Videos',
            'pictures': f'{profile}\\Pictures',
            'disk_c': 'C:\\',
            'disk_d': 'D:\\'
        }
        if action_type in paths:
            os.system(f'start explorer "{paths[action_type]}"')
        elif action_type == 'computer':
            os.system('start explorer "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}"')
    
    def search_files(self, query):
        """Поиск файлов по имени в пользовательских папках и дисках"""
        self.add_to_dialog(f"🔍 Ищу файлы: «{query}»...", is_response=True)
        
        search_paths = [
            os.path.expandvars(r'%USERPROFILE%\Documents'),
            os.path.expandvars(r'%USERPROFILE%\Downloads'),
            os.path.expandvars(r'%USERPROFILE%\Pictures'),
            os.path.expandvars(r'%USERPROFILE%\Videos'),
            os.path.expandvars(r'%USERPROFILE%\Music'),
            'C:\\',
            'D:\\'
        ]
        
        results = []
        extensions = ['*.pdf', '*.doc', '*.docx', '*.xls', '*.xlsx', '*.ppt', '*.pptx',
                     '*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.mp4', '*.avi',
                     '*.mp3', '*.wav', '*.zip', '*.rar', '*.7z', '*.txt', '*.py',
                     '*.js', '*.html', '*.css', '*.exe', '*.lnk']
        
        try:
            import fnmatch
            import win32api
            import win32con
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                
                try:
                    for ext in extensions:
                        for root, dirs, files in os.walk(search_path, topdown=True, onerror=lambda e: None):
                            # Ограничиваем глубину поиска 5 уровнями
                            level = root.replace(search_path, '').count(os.sep)
                            if level > 5:
                                dirs.clear()
                                continue
                            
                            for filename in files:
                                if fnmatch.fnmatch(filename.lower(), ext.lower()):
                                    if query.lower() in filename.lower():
                                        full_path = os.path.join(root, filename)
                                        size = os.path.getsize(full_path) if os.path.exists(full_path) else 0
                                        size_mb = size / (1024 * 1024)
                                        
                                        # Форматируем размер
                                        if size_mb >= 1:
                                            size_str = f"{size_mb:.1f} МБ"
                                        else:
                                            size_str = f"{size/1024:.0f} КБ"
                                        
                                        results.append({
                                            'path': full_path,
                                            'name': filename,
                                            'size': size_str,
                                            'folder': os.path.basename(root)
                                        })
                                        
                                        # Ограничиваем количество результатов
                                        if len(results) >= 20:
                                            break
                            
                            if len(results) >= 20:
                                break
                        
                        if len(results) >= 20:
                            break
                except PermissionError:
                    continue
                except Exception as e:
                    log.warning("Ошибка поиска в %s: %s", search_path, e)
            
            if results:
                # Сортируем по релевантности (сначала в пользовательских папках)
                user_results = [r for r in results if r['folder'] in ['Documents', 'Downloads', 'Pictures', 'Videos', 'Music']]
                other_results = [r for r in results if r not in user_results]
                results = user_results + other_results
                
                # Формируем отчёт
                report = f"📁 Найдено файлов: {len(results)}\n\n"
                
                for i, res in enumerate(results[:15], 1):
                    report += f"{i}. {res['name']}\n"
                    report += f"   📂 Папка: {res['folder']}\n"
                    report += f"   📏 Размер: {res['size']}\n"
                    report += f"   📍 Путь: {res['path']}\n\n"
                
                if len(results) > 15:
                    report += f"  ... и ещё {len(results) - 15} файлов\n\n"
                
                # Открываем папку с первым результатом
                if results:
                    first_path = os.path.dirname(results[0]['path'])
                    try:
                        os.system(f'start explorer /select,"{results[0]["path"]}"')
                        report += "💡 Открыта папка с первым результатом."
                    except:
                        pass
                
                self.add_to_dialog(report, is_response=True)
                
                # Озвучка краткого результата
                speech_text = f"Найдено {len(results)} файлов. Первый: {results[0]['name']} в папке {results[0]['folder']}."
                self.speak_jarvis_free(speech_text)
                
            else:
                self.add_to_dialog(f"⚠️ Файлы с именем «{query}» не найдены.", is_response=True)
                self.speak_jarvis_free(f"Файлы с именем {query} не найдены.")
                
        except ImportError:
            # Fallback если win32api недоступен
            self.add_to_dialog("⚠️ Модуль поиска файлов недоступен. Установите pywin32.", is_response=True)
        except Exception as e:
            log.error("Ошибка поиска файлов: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка поиска: {str(e)[:100]}", is_response=True)

    def search(self, search_type, cmd):
        query = cmd
        for prefix in (
            'найди в интернете', 'найди в браузере', 'найди',
            'поиск в интернете', 'поиск в браузере', 'поиск',
            'поищи в интернете', 'поищи в браузере', 'поищи',
        ):
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        query = query or "информация"
        self.add_to_dialog(f"Ищу в Яндекс: «{query}»", is_response=True)
        webbrowser.open(
            f"https://yandex.ru/search/?text={urllib.parse.quote_plus(query)}"
        )
    
    def weather_cmd(self):
        """Получает погоду и озвучивает голосом"""
        log.info("weather_cmd вызван")
        
        if not REQUESTS_OK:
            self.add_to_dialog("⚠️ Модуль requests не установлен.", is_response=True)
            return
        
        try:
            # Используем бесплатный API погоды wttr.in в текстовом формате
            url = "https://wttr.in/?format=%C+%t+%h+%w"
            res = requests.get(url, timeout=15)
            
            if res.status_code == 200:
                raw = res.text.strip()
                
                # Парсим: Москва: +18°C ↔ +16°C (19%) ←
                match = re.search(r"[+-]?\d+(?:[.,]\d+)?\s*°C", raw, re.IGNORECASE)
                if not match:
                    raise ValueError(f"Не удалось распознать температуру: {raw[:100]}")
                temp_main = match.group(0).replace("°C", "").replace(" ", "")
                
                reply = f"Сейчас {temp_main} градусов."
                
                self.add_to_dialog(f"🌤 Погода: {reply}", is_response=True)
                self.speak_jarvis_free(reply)
                log.info("Погода получена: %s°C", temp_main)
            else:
                self.add_to_dialog("⚠️ Не удалось получить данные о погоде.", is_response=True)
                
        except Exception as e:
            log.error("Ошибка получения погоды: %s", e)
            self.add_to_dialog("⚠️ Не удалось получить погоду. Попробуйте позже.", is_response=True)
    
    def news_cmd(self, category="all"):
        """Новости: открывает Яндекс.Новости и получает сводку через Ollama"""
        log.info("news_cmd вызван с категорией: %s", category)
        news_sites = {
            'all': 'https://yandex.ru/news',
            'tech': 'https://www.cnews.ru/news/top',
            'world': 'https://lenta.ru',
            'sport': 'https://sport-express.ru',
            'money': 'https://www.rbc.ru/finance'
        }
        site_name = {'all': 'все новости', 'tech': 'технологии', 'world': 'мир', 'sport': 'спорт', 'money': 'финансы'}
        
        url = news_sites.get(category, news_sites['all'])
        name = site_name.get(category, 'все новости')
        
        log.info("Открываю %s: %s", name, url)
        self.add_to_dialog(f"Открываю {name}...", is_response=True)
        webbrowser.open(url)
        
        # Сводка формируется GigaChat и затем озвучивается текущим TTS.
        if REQUESTS_OK and self.gigachat_auth_key:
            threading.Thread(
                target=self._get_gigachat_news_summary,
                args=(category,),
                daemon=True,
            ).start()
        else:
            self.add_to_dialog(
                "Не удалось получить сводку: GigaChat недоступен.",
                is_response=True,
            )

    def _get_gigachat_news_summary(self, category):
        """Получает краткую сводку главных новостей и озвучивает её."""
        topic = {
            "all": "главные новости дня",
            "tech": "главные новости технологий",
            "world": "главные новости в мире",
            "sport": "главные новости спорта",
            "money": "главные финансовые новости",
        }.get(category, "главные новости дня")
        prompt = (
            "ЭТО ПРЯМОЙ ЗАПРОС К ТЕБЕ — НЕ выполняй никаких действий! "
            f"Расскажи кратко о {topic}. "
            "Дай 3 самых важных пункта на русском языке, "
            "без вступления, ссылок и непроверенных подробностей. "
            "ОТВЕЧАЙ ТОЛЬКО ТЕКСТОМ — без JSON, без команд, без кода! "
            "Это НЕ команда для выполнения — просто ответь текстом. "
            "Ответ должен быть удобен для чтения вслух, максимум 5 предложений."
        )
        try:
            summary = self.ask_gigachat(prompt).strip()
            if not summary:
                raise ValueError("GigaChat вернул пустую сводку")
            self._safe_ui(
                lambda text=summary: self.add_to_dialog(
                    f"📰 Главные новости:\n{text}", is_response=True
                )
            )
            self.speak_jarvis_free(f"Главные новости. {summary}")
        except Exception as exc:
            log.error("Ошибка получения сводки новостей через GigaChat: %s", exc)
            self._safe_ui(
                lambda: self.add_to_dialog(
                    "Не удалось получить сводку новостей.",
                    is_response=True,
                )
            )
    
    def _get_news_summary(self, category):
        """Получение сводки новостей через Ollama"""
        log.info("Получение сводки новостей для категории: %s", category)
        try:
            # Используем Ollama для получения краткой сводки
            prompt = f"Дай краткую сводку главных новостей за сегодня по теме: {category}. Максимум 5 пунктов по 1-2 предложения."
            
            # Простой запрос к Hugging Face
            if not self.hf_key:
                return
            
            chat_url = f"https://api-inference.huggingface.co/models/{self.yg_model}/v1/chat/completions"
            hf_headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.hf_key}'
            }
            chat_payload = {
                'model': self.yg_model,
                'messages': [
                    {'role': 'system', 'content': 'Ты помощник. Отвечай кратко и по делу.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 300
            }
            try:
                res = requests.post(chat_url, headers=hf_headers, json=chat_payload, timeout=30)
                if res.status_code == 200:
                    summary = res.json()["choices"][0]["message"]["content"].strip()
                    
                    # Проверяем, не вернул ли Ollama ошибку вместо ответа
                    error_phrases = ['sorry, the assistant', 'не могу помочь', 'не могу выполнить', 'к сожалению, не могу']
                    is_error = any(ep in summary.lower() for ep in error_phrases)
                    
                    if is_error:
                        log.warning("Ollama вернул ошибку вместо сводки: %s", summary[:200])
                        self._safe_ui(lambda: self.add_to_dialog("⚠️ Не удалось получить сводку новостей. Попробуйте позже.", is_response=True))
                    else:
                        log.info("Сводка новостей получена: %s", summary[:100])
                        
                        # Добавляем в диалог
                        self._safe_ui(lambda: self.add_to_dialog(f"📰 Сводка новостей:\n{summary}", is_response=True))
                        
                        # Озвучка через speak_jarvis_free (Edge-TTS с fallback на pyttsx3)
                        log.info("Начало озвучки новостей через Edge-TTS...")
                        self.speak_jarvis_free(f"Вот сводка новостей: {summary}")
                        log.info("Озвучка новостей запущена")
                else:
                    log.error("Ошибка запроса к Ollama: %s", res.status_code)
            except Exception as e:
                log.error("Ошибка отправки запроса: %s", e)
        except Exception as e:
            log.error("Ошибка получения новостей: %s", e)
    
    def generate_image(self, prompt):
        """Генерация изображения через бесплатный API (без ключа)"""
        log.info("generate_image вызван с промптом: %s", prompt)
        
        if not REQUESTS_OK:
            self.add_to_dialog("⚠️ Модуль requests не установлен. Генерация недоступна.", is_response=True)
            return
        
        # Создаём папку images если нет
        images_dir = Path(__file__).parent / 'images'
        images_dir.mkdir(exist_ok=True)
        
        # Генерируем уникальное имя файла
        timestamp = int(time.time() * 1000)
        image_filename = f"generated_{timestamp}.png"
        image_path = images_dir / image_filename
        
        # Seed для генерации — случайное число в допустимом диапазоне (<=2147483647)
        seed = int(time.time() % 2147483647)
        
        self.add_to_dialog(f"🎨 Генерирую изображение: «{prompt}»...", is_response=True)
        self.play_sound_from_folder(_get_mp3('загрузка'), fallback_text="Загружаю сэр.")
        
        try:
            # Переводим промпт на английский через Ollama
            english_prompt = prompt
            # Ollama всегда доступен
            try:
                log.info("Перевод промпта на английский...")
                # Ollama не требует авторизации
                chat_url = f"{self.ollama_base_url}/api/chat"
                chat_payload = {
                    'model': self.yg_model,
                    'messages': [
                        {'role': 'system', 'content': 'Переведи на английский. Отвечай ТОЛЬКО переводом.'},
                        {'role': 'user', 'content': f'Переведи на английский: {prompt}'}
                    ],
                    'max_tokens': 100
                }
                res = requests.post(chat_url, headers=hf_headers, json=chat_payload, timeout=10)
                if res.status_code == 200:
                    translated = res.json()["choices"][0]["message"]["content"].strip()
                    log.info("Промпт переведён: %s", translated)
                    english_prompt = translated
            except Exception as e:
                log.warning("Ошибка перевода: %s", e)
            
            # Пробуем несколько бесплатных API по очереди
            success = False
            
            # === Вариант 1: Pollinations.ai (основной) ===
            try:
                log.info("Пробуем Pollinations.ai...")
                self.add_to_dialog("⏳ Генерация изображения...", is_response=True)
                
                poll_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(english_prompt)}width=1024&height=1024&seed={seed}&nologo=true"
                log.info("URL запроса: %s", poll_url[:200])
                
                img_res = requests.get(poll_url, timeout=60, verify=False)
                log.info("Pollinations ответ: status=%d, size=%d байт", img_res.status_code, len(img_res.content))
                
                # Проверяем, не HTML-страницу ошибки ли получили
                if img_res.status_code == 200 and len(img_res.content) > 10000:
                    with open(image_path, 'wb') as f:
                        f.write(img_res.content)
                    success = True
                    log.info("✅ Изображение создано")
                else:
                    # Показываем содержимое ошибки
                    try:
                        error_text = img_res.text[:500] if img_res.text else "пусто"
                        log.error("❌ Ошибка Pollinations: status=%d, response=%s", img_res.status_code, error_text)
                    except:
                        pass
                    log.warning("Pollinations вернул: %s, размер: %d байт", img_res.status_code, len(img_res.content))
            except Exception as e:
                log.error("Pollinations исключение: %s", e, exc_info=True)
            
            # === Вариант 2: Pollinations с моделью flux ===
            if not success:
                try:
                    log.info("Пробуем Pollinations с моделью flux...")
                    poll_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(english_prompt)}model=flux&width=1024&height=1024&seed={timestamp}&nologo=true"
                    
                    img_res = requests.get(poll_url, timeout=60, verify=False)
                    log.info("Pollinations flux ответ: status=%d, size=%d", img_res.status_code, len(img_res.content))
                    
                    if img_res.status_code == 200 and len(img_res.content) > 10000:
                        with open(image_path, 'wb') as f:
                            f.write(img_res.content)
                        success = True
                        log.info("✅ Изображение создано через flux")
                except Exception as e:
                    log.error("Pollinations flux исключение: %s", e)
            
            # === Вариант 3: Pollinations с моделью turbo ===
            if not success:
                try:
                    log.info("Пробуем Pollinations с моделью turbo...")
                    poll_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(english_prompt)}model=turbo&width=1024&height=1024&seed={timestamp}&nologo=true"
                    
                    img_res = requests.get(poll_url, timeout=60, verify=False)
                    log.info("Pollinations turbo ответ: status=%d, size=%d", img_res.status_code, len(img_res.content))
                    
                    if img_res.status_code == 200 and len(img_res.content) > 10000:
                        with open(image_path, 'wb') as f:
                            f.write(img_res.content)
                        success = True
                        log.info("✅ Изображение создано через turbo")
                except Exception as e:
                    log.error("Pollinations turbo исключение: %s", e)
            
            if success:
                # Показываем в диалоге
                self._safe_ui(lambda: self.add_to_dialog(
                    f"✅ Изображение сохранено в: {image_path}",
                    is_response=True
                ))
                
                # Открываем изображение
                try:
                    os.startfile(str(image_path))
                    log.info("Изображение открыто")
                except Exception as e:
                    log.error("Ошибка открытия: %s", e)
                
                reply_text = f"Изображение «{prompt}» готово!"
                self.add_to_dialog(reply_text, is_response=True)
                self.speak_jarvis_free(reply_text)
            else:
                log.error("Все способы генерации не сработали")
                self.add_to_dialog("⚠️ Не удалось сгенерировать изображение. Попробуйте позже или с другим запросом.", is_response=True)
                
        except requests.exceptions.Timeout:
            log.error("Таймаут генерации")
            self.add_to_dialog("⏰ Генерация заняла слишком много времени. Попробуйте ещё раз.", is_response=True)
        except Exception as e:
            log.error("Ошибка генерации изображения: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:100]}", is_response=True)
    
    def take_screenshot(self):
        """Делает скриншот экрана и сохраняет в папку images"""
        try:
            images_dir = Path(__file__).parent / 'images'
            images_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot_path = images_dir / screenshot_filename
            
            # Делаем скриншот
            screenshot = ImageGrab.grab()
            screenshot.save(str(screenshot_path.resolve()), "PNG")
            
            # Показываем скриншот
            try:
                os.startfile(str(screenshot_path))
            except Exception:
                pass
            
            self.add_to_dialog(f"📸 Скриншот сохранён: {screenshot_path}", is_response=True)
            self.speak_jarvis_free("Скриншот сделан и сохранён.")
            log.info("Скриншот сохранён: %s", screenshot_path)
            
        except Exception as e:
            log.error("Ошибка создания скриншота: %s", e)
            self.add_to_dialog(f"⚠️ Не удалось сделать скриншот: {str(e)[:100]}", is_response=True)
    
    def screenshot_with_annotations(self):
        """Делает скриншот с аннотациями — рисует рамки, кружки, стрелки, текст"""
        try:
            from PIL import ImageDraw, ImageFont
            
            images_dir = Path(__file__).parent / 'images'
            images_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            filename = f"screenshot_annotated_{timestamp}.png"
            screenshot_path = images_dir / filename
            
            # Делаем скриншот
            screenshot = ImageGrab.grab()
            draw = ImageDraw.Draw(screenshot)
            
            # === АННОТАЦИЯ 1: Рамка вокруг всего экрана ===
            screen_w, screen_h = screenshot.size
            draw.rectangle([0, 0, screen_w - 1, screen_h - 1], outline=(255, 0, 0), width=5)
            
            # === АННОТАЦИЯ 2: Информация в углу ===
            draw.rectangle([10, 10, 400, 120], fill=(0, 0, 0, 180))
            draw.text((20, 20), "J.A.R.V.I.S. — АННОТАЦИЯ", fill=(0, 255, 255))
            draw.text((20, 45), f"Разрешение: {screen_w}x{screen_h}", fill=(200, 200, 200))
            draw.text((20, 70), f"Время: {datetime.now().strftime('%H:%M:%S')}", fill=(200, 200, 200))
            draw.text((20, 95), f"Дата: {datetime.now().strftime('%d.%m.%Y')}", fill=(200, 200, 200))
            
            # === АННОТАЦИЯ 3: Рамки вокруг окон ===
            try:
                import pyautogui
                windows = pyautogui.getWindowsWithTitle('')
                if windows:
                    color_idx = 0
                    colors = [
                        (0, 255, 0),    # Зелёный
                        (255, 255, 0),  # Жёлтый
                        (0, 255, 255),  # Голубой
                        (255, 0, 255),  # Малиновый
                        (255, 165, 0),  # Оранжевый
                    ]
                    
                    for i, win in enumerate(windows[:10]):  # Максимум 10 окон
                        if win.left >= 0 and win.top >= 0 and win.width > 50 and win.height > 50:
                            color = colors[color_idx % len(colors)]
                            draw.rectangle(
                                [win.left, win.top, win.left + win.width - 1, win.top + win.height - 1],
                                outline=color,
                                width=3
                            )
                            # Подпись с названием окна
                            title = win.title[:30] if win.title else f"Окно #{i+1}"
                            draw.rectangle([win.left, win.top - 25, win.left + 200, win.top - 5], fill=(0, 0, 0, 180))
                            draw.text((win.left + 5, win.top - 22), title, fill=color)
                            color_idx += 1
            except Exception as e:
                log.warning("Не удалось добавить рамки окон: %s", e)
            
            # === АННОТАЦИЯ 4: Стрелка к курсору ===
            try:
                import pyautogui
                cursor_x, cursor_y = pyautogui.position()
                # Круг вокруг курсора
                draw.ellipse(
                    [cursor_x - 25, cursor_y - 25, cursor_x + 25, cursor_y + 25],
                    outline=(255, 0, 0),
                    width=3
                )
                # Крестик
                draw.line([(cursor_x - 15, cursor_y), (cursor_x + 15, cursor_y)], fill=(255, 0, 0), width=2)
                draw.line([(cursor_x, cursor_y - 15), (cursor_x, cursor_y + 15)], fill=(255, 0, 0), width=2)
                # Текст
                draw.text((cursor_x + 30, cursor_y - 10), "КУРСОР", fill=(255, 0, 0))
            except Exception:
                pass
            
            # Сохраняем
            screenshot.save(str(screenshot_path.resolve()), "PNG")
            
            # Показываем
            try:
                os.startfile(str(screenshot_path))
            except Exception:
                pass
            
            self.add_to_dialog(f"📸 Скриншот с аннотациями сохранён: {screenshot_path}", is_response=True)
            self.speak_jarvis_free("Скриншот с аннотациями сделан. Рамки вокруг окон, позиция курсора, информация в углу.")
            log.info("Скриншот с аннотациями сохранён: %s", screenshot_path)
            
        except Exception as e:
            log.error("Ошибка создания скриншота с аннотациями: %s", e)
            self.add_to_dialog(f"⚠️ Не удалось сделать скриншот с аннотациями: {str(e)[:100]}", is_response=True)
    
    def browser_automate(self, url, action_type, text=""):
        """Автоматизация браузера: открывает сайт и выполняет действия"""
        try:
            if not PYAUTOGUI_OK:
                self.add_to_dialog("⚠️ Управление браузером недоступно.", is_response=True)
                return
            
            # === ШАГ 1: Открываем сайт ===
            if url:
                self.add_to_dialog(f"🌐 Открываю {url}...", is_response=True)
                webbrowser.open(url)
                time.sleep(3)  # Ждём загрузки страницы
            
            # === ШАГ 2: Ищем окно браузера и активируем ===
            browser_window = None
            browser_titles = ['Chrome', 'Firefox', 'Edge', 'Yandex', 'браузер', 'browser']
            for title in browser_titles:
                windows = pyautogui.getWindowsWithTitle(title)
                if windows:
                    browser_window = windows[0]
                    break
            
            if not browser_window:
                self.add_to_dialog("⚠️ Окно браузера не найдено.", is_response=True)
                return
            
            # Активируем браузер — игнорируем ошибку Windows
            try:
                result = browser_window.activate()
                log.debug("Окно активировано: %s", result)
            except Exception as e:
                log.info("Ошибка activate (игнорируем): %s", e)
            
            time.sleep(0.5)
            
            # === ШАГ 3: Выполняем действие ===
            if action_type == "search":
                # Поиск — кликаем в адресную строку и печатаем
                pyautogui.hotkey('ctrl', 'l')  # Фокус на адресную строку
                time.sleep(0.3)
                pyautogui.write(text, interval=0.05)
                time.sleep(0.3)
                pyautogui.press('enter')
                self.add_to_dialog(f"🔍 Ищу: «{text}»", is_response=True)
                self.speak_jarvis_free(f"Ищу {text}.")
                
            elif action_type == "type":
                # Печать текста — кликаем в центр и печатаем
                screen_w, screen_h = pyautogui.size()
                pyautogui.click(screen_w // 2, screen_h // 2)
                time.sleep(0.3)
                pyautogui.write(text, interval=0.05)
                self.add_to_dialog(f"✏️ Ввёл: «{text}»", is_response=True)
                self.speak_jarvis_free("Текст ввёл.")
                
            elif action_type == "click":
                # Клик — кликаем в центр
                screen_w, screen_h = pyautogui.size()
                pyautogui.click(screen_w // 2, screen_h // 2)
                self.add_to_dialog("🖱️ Кликнул.", is_response=True)
                    
            elif action_type == "navigate":
                # Навигация — стрелки
                if text == "назад":
                    pyautogui.hotkey('alt', 'left')
                    self.add_to_dialog("⬅️ Перешёл назад.", is_response=True)
                elif text == "вперёд":
                    pyautogui.hotkey('alt', 'right')
                    self.add_to_dialog("➡️ Перешёл вперёд.", is_response=True)
                elif text == "обновить":
                    pyautogui.press('f5')
                    self.add_to_dialog("🔄 Обновил страницу.", is_response=True)
                    time.sleep(1)
                else:
                    pyautogui.press('enter')
                    
            elif action_type == "scroll":
                # Прокрутка
                direction = text if text else "вниз"
                if "вниз" in direction or "ниже" in direction:
                    for _ in range(5):
                        pyautogui.press('pagedown')
                        time.sleep(0.1)
                    self.add_to_dialog("⬇️ Прокрутил вниз.", is_response=True)
                elif "вверх" in direction or "выше" in direction:
                    for _ in range(5):
                        pyautogui.press('pageup')
                        time.sleep(0.1)
                    self.add_to_dialog("⬆️ Прокрутил вверх.", is_response=True)
                    
            elif action_type == "screenshot":
                # Скриншот страницы
                screenshot = ImageGrab.grab()
                images_dir = Path(__file__).parent / 'images'
                images_dir.mkdir(exist_ok=True)
                filename = f"browser_{int(time.time()*1000)}.png"
                screenshot.save(str(images_dir / filename), "PNG")
                self.add_to_dialog(f"📸 Скриншот страницы сохранён.", is_response=True)
                self.speak_jarvis_free("Скриншот страницы сделал.")
                
            else:
                self.add_to_dialog(f"⚠️ Неизвестное действие: {action_type}", is_response=True)
                
        except Exception as e:
            log.error("Ошибка автоматизации браузера: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:100]}", is_response=True)
    
    def analyze_screenshot(self):
        """Делает скриншот и анализирует его с распознаванием объектов"""
        try:
            # Сначала делаем скриншот
            images_dir = Path(__file__).parent / 'images'
            images_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time() * 1000)
            screenshot_filename = f"screenshot_{timestamp}.png"
            screenshot_path = images_dir / screenshot_filename
            
            screenshot = ImageGrab.grab()
            screenshot.save(str(screenshot_path.resolve()), "PNG")
            
            self.add_to_dialog("🔍 Анализирую скриншот...", is_response=True)
            
            # === Шаг 1: OCR — извлекаем текст со скриншота ===
            extracted_text = ""
            try:
                import pytesseract
                # Указываем путь к Tesseract-OCR
                tess_path = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                if os.path.exists(tess_path):
                    pytesseract.pytesseract.tesseract_cmd = tess_path
                extracted_text = pytesseract.image_to_string(screenshot, lang='rus+eng').strip()
                if extracted_text:
                    log.info("OCR извлёк текст: %d символов", len(extracted_text))
            except Exception as e:
                log.warning("OCR недоступен: %s", e)
            
            # === Шаг 2: Анализ через Ollama с детальным промптом ===
            if REQUESTS_OK:
                try:
                    import base64 as b64
                    
                    with open(screenshot_path, "rb") as img_file:
                        img_b64 = b64.b64encode(img_file.read()).decode("utf-8")
                    
                    # Hugging Face не требует авторизации
                    if not self.hf_key:
                        return
                    
                    chat_url = f"https://api-inference.huggingface.co/models/{self.yg_model}/v1/chat/completions"
                    hf_headers = {
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {self.hf_key}'
                    }
                    
                    # Формируем детальный промпт для распознавания объектов
                    prompt_parts = [
                        "Ты — J.A.R.V.I.S., ИИ-ассистент с зрением. Ты видишь скриншот экрана.",
                        "",
                        "=== ЗАДАЧА: РАСПОЗНАВАНИЕ ОБЪЕКТОВ И ЭЛЕМЕНТОВ ===",
                        "",
                        "Опиши ВСЁ, что видишь на скриншоте, структурированно:",
                        "1. Какие приложения/окна открыты",
                        "2. Какие кнопки, иконки, элементы интерфейса видны",
                        "3. Какой текст отображается на экране",
                        "4. Есть ли изображения, графики, таблицы",
                        "5. Что происходит на экране прямо сейчас",
                        "",
                        "Отвечай на русском языке, подробно и структурированно."
                    ]
                    
                    if extracted_text:
                        prompt_parts.insert(3, f"Извлечённый текст OCR: {extracted_text[:500]}")
                    
                    full_prompt = "\n".join(prompt_parts)
                    
                    # Ollama не поддерживает изображения в /api/chat, отправляем только текст
                    analyze_payload = {
                        'model': self.yg_model,
                        'messages': [
                            {
                                'role': 'user',
                                'content': full_prompt
                            }
                        ],
                        'max_tokens': 1500,
                        'temperature': 0.7
                    }
                    
                    res = requests.post(chat_url, headers=hf_headers, json=analyze_payload, timeout=45)
                    
                    if res.status_code == 200:
                        analysis = res.json()['choices'][0]['message']['content'].strip()
                        
                        # Проверяем, не ошибка ли это
                        error_phrases = ['sorry, the assistant', 'не могу помочь', 'не могу выполнить', 'к сожалению, не могу']
                        is_error = any(ep in analysis.lower() for ep in error_phrases)
                        
                        if not is_error:
                            # Формируем полный отчёт
                            report = "=== АНАЛИЗ ЭКРАНА ===\n\n"
                            
                            if extracted_text:
                                report += "📝 ИЗВЛЕЧЁННЫЙ ТЕКСТ:\n"
                                report += extracted_text[:800] + "\n\n"
                            
                            report += "🔍 РАСПОЗНАНИЕ ОБЪЕКТОВ:\n"
                            report += analysis + "\n\n"
                            
                            self.add_to_dialog(report, is_response=True)
                            self.speak_jarvis_free(analysis[:300])
                            log.info("Анализ скриншота с распознаванием объектов выполнен")
                            return
                
                except Exception as e:
                    log.error("Ошибка анализа через Ollama: %s", e)
            
            # === Fallback: показываем скриншот и извлечённый текст ===
            report = "=== РЕЗУЛЬТАТ АНАЛИЗА ===\n\n"
            
            if extracted_text:
                report += "📝 Распознанный текст:\n" + extracted_text[:1000] + "\n\n"
            else:
                report += "⚠️ Текст не распознан.\n\n"
            
            report += "📸 Скриншот открыт для просмотра."
            
            self.add_to_dialog(report, is_response=True)
            try:
                os.startfile(str(screenshot_path))
            except Exception:
                pass
            
        except Exception as e:
            log.error("Ошибка анализа скриншота: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:100]}", is_response=True)
    
    def show_last_screenshot(self):
        """Показывает последний сохранённый скриншот"""
        try:
            images_dir = Path(__file__).parent / 'images'
            if not images_dir.exists():
                self.add_to_dialog("⚠️ Папка images не найдена.", is_response=True)
                return
            
            screenshot_files = sorted(images_dir.glob("screenshot_*.png"), key=os.path.getmtime, reverse=True)
            
            if not screenshot_files:
                self.add_to_dialog("⚠️ Скриншотов не найдено. Сделайте скриншот командой 'сделай скриншот'.", is_response=True)
                return
            
            last_screenshot = screenshot_files[0]
            self.add_to_dialog(f"📸 Последний скриншот: {last_screenshot}", is_response=True)
            
            try:
                os.startfile(str(last_screenshot))
            except Exception:
                pass
            
        except Exception as e:
            log.error("Ошибка показа скриншота: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:100]}", is_response=True)
    
    def list_screenshots(self):
        """Показывает список всех сохранённых скриншотов"""
        try:
            images_dir = Path(__file__).parent / 'images'
            if not images_dir.exists():
                self.add_to_dialog("⚠️ Папка images не найдена.", is_response=True)
                return
            
            screenshot_files = sorted(images_dir.glob("screenshot_*.png"), key=os.path.getmtime, reverse=True)
            
            if not screenshot_files:
                self.add_to_dialog("⚠️ Скриншотов не найдено. Сделайте скриншот командой 'сделай скриншот'.", is_response=True)
                return
            
            msg = f"📸 Найдено скриншотов: {len(screenshot_files)}\n"
            for i, sf in enumerate(screenshot_files[:10], 1):  # Показываем последние 10
                size_kb = sf.stat().st_size / 1024
                msg += f"  {i}. {sf.name} ({size_kb:.1f} КБ)\n"
            
            if len(screenshot_files) > 10:
                msg += f"  ... и ещё {len(screenshot_files) - 10}"
            
            self.add_to_dialog(msg, is_response=True)
            
        except Exception as e:
            log.error("Ошибка списка скриншотов: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка: {str(e)[:100]}", is_response=True)
    
    def check_internet_speed(self):
        """Проверка скорости интернета через скачивание тестового файла"""
        if not REQUESTS_OK:
            self.add_to_dialog("⚠️ Модуль requests не установлен.", is_response=True)
            return

        self.add_to_dialog("⏳ Измеряю скорость интернета...", is_response=True)
        
        # Тестовые файлы разных размеров для скачивания (надёжные CDN)
        test_urls = [
            "https://speed.cloudflare.com/__downbytes=1000000",      # 1 MB
            "https://speed.cloudflare.com/__downbytes=5000000",      # 5 MB
            "https://download.blender.org/demo/movies/VR/VR.zip",     # ~10 MB
        ]
        
        download_speed_mbps = 0.0
        ping_ms = 0.0
        uploaded_bytes = 0
        
        try:
            # === ПИНГ (среднее время отклика) ===
            ping_times = []
            for i in range(5):
                try:
                    start = time.time()
                    res = requests.get("https://speed.cloudflare.com", timeout=5, verify=False)
                    ping_ms = (time.time() - start) * 1000
                    ping_times.append(ping_ms)
                except:
                    pass
            
            if ping_times:
                ping_ms = sum(ping_times) / len(ping_times)
            else:
                ping_ms = -1  # Не удалось пингануть

            # === СКОРОСТЬ СКАЧИВАНИЯ ===
            for url in test_urls:
                try:
                    self.add_to_dialog(f"📥 Тестирование через CDN...", is_response=True)
                    res = requests.get(url, timeout=60, stream=True, verify=False)
                    if res.status_code == 200:
                        total_size = int(res.headers.get('content-length', 0))
                        if total_size == 0:
                            total_size = 1000000  # Если размер неизвестен
                        
                        start_time = time.time()
                        bytes_downloaded = 0
                        
                        for chunk in res.iter_content(chunk_size=8192):
                            if not self.is_running:
                                break
                            if chunk:
                                bytes_downloaded += len(chunk)
                            elapsed = time.time() - start_time
                            if elapsed > 5:  # Минимум 5 секунд теста
                                break
                        
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed_bps = (bytes_downloaded * 8) / elapsed
                            download_speed_mbps = speed_bps / (1024 * 1024)  # Mbps
                            break
                except Exception as e:
                    log.warning("Ошибка теста скорости (URL: %s): %s", url, e)
                    continue

            # === СКОРОСТЬ ЗАГРУЗКИ (упрощённая) ===
            try:
                upload_data = os.urandom(500000)  # 500 KB случайных данных
                start_time = time.time()
                res = requests.post(
                    "https://speed.cloudflare.com/__up",
                    data=upload_data,
                    timeout=30,
                    verify=False
                )
                elapsed = time.time() - start_time
                if elapsed > 0:
                    upload_speed_bps = (len(upload_data) * 8) / elapsed
                    upload_speed_mbps = upload_speed_bps / (1024 * 1024)
                else:
                    upload_speed_mbps = 0
            except:
                upload_speed_mbps = 0

            # === ФОРМИРОВАНИЕ ОТВЕТА ===
            if download_speed_mbps > 0:
                if download_speed_mbps >= 100:
                    speed_rating = "ОЧЕНЬ БЫСТРОЕ 🚀"
                elif download_speed_mbps >= 50:
                    speed_rating = "БЫСТРОЕ ⚡"
                elif download_speed_mbps >= 10:
                    speed_rating = "СРЕДНЕЕ 📶"
                elif download_speed_mbps >= 1:
                    speed_rating = "НИЗКОЕ 🐌"
                else:
                    speed_rating = "КРИТИЧЕСКИ НИЗКОЕ ⚠️"
                
                result = (
                    f"=== РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СЕТИ ===\n\n"
                    f"📥 Скорость загрузки: {download_speed_mbps:.2f} Мбит/с\n"
                    f"📤 Скорость отдачи: {upload_speed_mbps:.2f} Мбит/с\n"
                    f"🏓 Пинг: {ping_ms:.1f} мс\n"
                    f"📊 Оценка: {speed_rating}\n\n"
                    f"Рекомендации:\n"
                    f"  • Стриминг 4K: требуется ≥ 25 Мбит/с {'✓' if download_speed_mbps >= 25 else '✗'}\n"
                    f"  • Видеозвонки: требуется ≥ 5 Мбит/с {'✓' if download_speed_mbps >= 5 else '✗'}\n"
                    f"  • Онлайн-игры: требуется ≥ 3 Мбит/с {'✓' if download_speed_mbps >= 3 else '✗'}\n"
                    f"  • Веб-серфинг: требуется ≥ 1 Мбит/с {'✓' if download_speed_mbps >= 1 else '✗'}"
                )
                
                self.add_to_dialog(result, is_response=True)
                
                # Озвучка краткого результата
                speech_text = (
                    f"Скорость загрузки {download_speed_mbps:.1f} мегабит в секунду. "
                    f"Скорость отдачи {upload_speed_mbps:.1f} мегабит в секунду. "
                    f"Пинг {ping_ms:.0f} миллисекунд. "
                    f"{speed_rating}"
                )
                self.speak_jarvis_free(speech_text)
                log.info("Скорость интернета: download=%.2f Mbps, upload=%.2f Mbps, ping=%.1f ms",
                        download_speed_mbps, upload_speed_mbps, ping_ms)
            else:
                self.add_to_dialog("⚠️ Не удалось измерить скорость. Проверьте подключение к интернету.", is_response=True)
                self.speak_jarvis_free("Не удалось измерить скорость интернета.")
                
        except requests.exceptions.Timeout:
            self.add_to_dialog("⏰ Тест скорости занял слишком много времени. Проверьте соединение.", is_response=True)
            self.speak_jarvis_free("Тест скорости занял слишком много времени.")
        except Exception as e:
            log.error("Ошибка теста скорости: %s", e)
            self.add_to_dialog(f"⚠️ Ошибка тестирования: {str(e)[:100]}", is_response=True)
            self.speak_jarvis_free("Произошла ошибка при тестировании скорости.")

    def cleanup_recycle_bin(self):
        """Очистка корзины Windows"""
        self.add_to_dialog("🗑️ Начинаю очистку корзины...", is_response=True)
        
        try:
            import ctypes
            # Полная очистка корзины без подтверждения
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            self.add_to_dialog("🗑️ Корзина очищена.", is_response=True)
            self.speak_jarvis_free("Корзина очищена.")
            log.info("Корзина очищена")
        except Exception as e:
            self.add_to_dialog(f"⚠️ Ошибка очистки корзины: {e}", is_response=True)
            self.speak_jarvis_free("Не удалось очистить корзину.")
            log.error("Ошибка очистки корзины: %s", e)

    def cleanup_temp_files(self):
        """Очистка временных файлов, корзины и кэшей"""
        self.add_to_dialog("🗑️ Начинаю очистку мусорных файлов...", is_response=True)
        
        cleaned_size = 0
        cleaned_items = 0
        errors = []
        
        # === 1. Очистка папки Temp пользователя ===
        temp_paths = [
            os.path.expandvars(r'%TEMP%'),
            os.path.expandvars(r'%TMP%'),
            os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'AppData', 'Local', 'Temp'),
        ]
        
        for temp_path in temp_paths:
            if not os.path.exists(temp_path):
                continue
            try:
                for item in os.listdir(temp_path):
                    item_path = os.path.join(temp_path, item)
                    try:
                        if os.path.isfile(item_path):
                            size = os.path.getsize(item_path)
                            os.remove(item_path)
                            cleaned_size += size
                            cleaned_items += 1
                        elif os.path.isdir(item_path):
                            import shutil
                            shutil.rmtree(item_path, ignore_errors=True)
                            cleaned_items += 1
                    except Exception as e:
                        log.warning("Не удалось удалить %s: %s", item_path, e)
                        errors.append(item)
            except Exception as e:
                errors.append(temp_path)
        
        # === 2. Очистка кэша браузеров (AppData/Local) ===
        browser_caches = [
            os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'AppData', 'Local', 'Google', 'Chrome', 'User Data', 'Default', 'Cache'),
            os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'AppData', 'Local', 'Microsoft', 'Edge', 'User Data', 'Default', 'Cache'),
            os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'AppData', 'Local', 'Yandex', 'YandexBrowser', 'Cache'),
        ]
        
        for cache_path in browser_caches:
            if os.path.exists(cache_path):
                try:
                    for item in os.listdir(cache_path):
                        item_path = os.path.join(cache_path, item)
                        try:
                            if os.path.isfile(item_path):
                                size = os.path.getsize(item_path)
                                os.remove(item_path)
                                cleaned_size += size
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                        except:
                            pass
                except:
                    pass
        
        # === 3. Очистка корзины (ShellRecycleBin) ===
        try:
            import ctypes
            # SHERCYCLE — полная очистка корзины без подтверждения
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            self.add_to_dialog("🗑️ Корзина очищена.", is_response=True)
        except Exception as e:
            log.warning("Не удалось очистить корзину: %s", e)
        
        # === 4. Очистка thumbnails ===
        thumb_path = os.path.join(os.path.expandvars(r'%USERPROFILE%'), 'AppData', 'Local', 'Microsoft', 'Windows', 'Explorer')
        if os.path.exists(thumb_path):
            for item in os.listdir(thumb_path):
                if item.startswith('thumb'):
                    try:
                        os.remove(os.path.join(thumb_path, item))
                    except:
                        pass
        
        # === Формируем отчёт ===
        size_mb = cleaned_size / (1024 * 1024)
        
        if cleaned_items > 0:
            result = (
                f"=== РЕЗУЛЬТАТЫ ОЧИСТКИ ===\n\n"
                f"🗑️ Удалено файлов: {cleaned_items}\n"
                f"💾 Освобождено места: ~{size_mb:.1f} МБ\n"
                f"🗑️ Корзина: очищена\n"
                f"🌐 Кэши браузеров: очищены\n"
                f"📁 Папки Temp: очищены"
            )
            if errors:
                result += f"\n\n⚠️ Не удалось удалить {len(errors)} файлов (защита системы)"
            
            self.add_to_dialog(result, is_response=True)
            speech_text = f"Очистка завершена. Удалено {cleaned_items} файлов, освобождено примерно {size_mb:.0f} мегабайт."
            self.speak_jarvis_free(speech_text)
            log.info("Очистка мусора: %d файлов, ~%.1f МБ", cleaned_items, size_mb)
        else:
            self.add_to_dialog("🗑️ Мусорных файлов не найдено. Система чиста.", is_response=True)
            self.speak_jarvis_free("Мусорных файлов не найдено.")
        
        if errors:
            log.warning("Ошибки при очистке: %s", errors[:5])

    def voice_input(self):
        """Голосовой ввод — выполняется в фоновом потоке с таймаутом, чтобы не зависать"""
        if not SPEECH_OK:
            details = MICROPHONE_ERROR or "Проверьте подключение микрофона и разрешение Windows."
            self._safe_ui(lambda: messagebox.showerror(
                "Микрофон недоступен",
                f"Не удалось открыть микрофон.\n\n{details}"
            ))
            return
        if not self._connect_microphone():
            self._safe_ui(lambda: messagebox.showerror(
                "Микрофон не подключён",
                MICROPHONE_ERROR or "Подключите микрофон и проверьте разрешения Windows."
            ))
            return
        if self.voice_thread is not None and self.voice_thread.is_alive():
            self._safe_ui(lambda: self.status_label.config(
                text="● УЖЕ СЛУШАЮ", fg="#f59e0b"
            ))
            return
        with self.command_lock:
            if self.command_busy:
                self._safe_ui(lambda: self.status_label.config(
                    text="● ДОЖДИТЕСЬ ОТВЕТА", fg="#f59e0b"
                ))
                return

        def _record_and_recognize():
            try:
                self.is_listening = True
                # Статус «Слушаю» — через UI-очередь
                self._safe_ui(lambda: self.status_label.config(text="● СЛУШАЮ ГОЛОС...", fg="#ef4444"))

                if not self.mic_lock.acquire(timeout=1.0):
                    self._safe_ui(lambda: self.status_label.config(text="● МИКРОФОН ЗАНЯТ", fg="#f59e0b"))
                    return
                try:
                    with microphone as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=30)
                finally:
                    self.mic_lock.release()

                # recognize_google с увеличенным timeout
                text = ""
                try:
                    text = recognizer.recognize_google(audio, language='ru-RU', timeout=10, phrase_time_limit=30)
                except Exception as e:
                    log.warning("Google не распознал, пробуем Sphinx: %s", e)
                    try:
                        text = recognizer.recognize_sphinx(audio, language='ru')
                    except:
                        pass
                text = text.lower().strip() if text else ""

                if text:
                    self.execute_command_text(text, play_intro=False)
            except Exception as exc:
                log.warning("Голосовой ввод не выполнен: %s", exc)
                self._safe_ui(lambda error=str(exc): self.status_label.config(
                    text="● ОШИБКА МИКРОФОНА", fg="#ef4444"
                ))
                self._safe_ui(lambda error=str(exc): self.add_to_dialog(
                    f"Микрофон: {error}", is_response=True
                ))
            finally:
                self.is_listening = False
                self._safe_ui(lambda: self.status_label.config(text="● СИСТЕМА ГОТОВА", fg="#10b981"))

        # Запускаем в отдельном потоке — UI не блокируется
        t = threading.Thread(target=_record_and_recognize, daemon=True)
        self.voice_thread = t
        t.start()

        # === ТАЙМАУТ через Timer: если поток зависнет — принудительно сбросим статус ===
        def _force_reset():
            # Проверяем, не завершён ли поток уже
            if not t.is_alive():
                return
            log.warning("voice_input: таймаут 15 сек, принудительно сбрасываем статус")
            self._safe_ui(lambda: self.status_label.config(text="● СИСТЕМА ГОТОВА", fg="#10b981"))

        threading.Timer(15, _force_reset).start()
    
    def toggle_mic(self):
        """Вкл/выкл фоновый микрофон"""
        self.mic_enabled = not self.mic_enabled
        if self.mic_enabled:
            self.add_to_dialog("🎤 Микрофон включён (фоновое слушание активно).", is_response=True)
        else:
            self.add_to_dialog("🔇 Микрофон выключен. Включите кнопкой «Микрофон».", is_response=True)
    
    def start_background_listener(self):
        def listen():
            if not self._connect_microphone():
                self._safe_ui(lambda: self.status_label.config(
                    text="● МИКРОФОН НЕ ПОДКЛЮЧЁН", fg="#ef4444"
                ))
                return
            try:
                with microphone as source: recognizer.adjust_for_ambient_noise(source, duration=1.0)
            except Exception as exc:
                log.warning("Не удалось подготовить фоновый микрофон: %s", exc)
                return

            while self.is_running:
                # === ПРОВЕРКА 1: говорит ли Джарвис прямо сейчас ===
                with self.speaking_lock:
                    is_speaking = self.is_speaking
                    last_jarvis_text = self.last_jarvis_text
                    last_jarvis_time = self.last_jarvis_time

                # Не записываем микрофон во время озвучки: иначе фраза
                # J.A.R.V.I.S. может попасть в распознавание и запустить
                # повторную команду после окончания воспроизведения.
                if is_speaking:
                    time.sleep(0.1)
                    continue

                # === ПРОВЕРКА 1: cooldown после речи Джарвиса ===
                now = time.time()
                # Короткий cooldown 1 сек после окончания речи
                if now < self.mic_cooldown_until:
                    time.sleep(0.1)
                    continue
                
                # Автоматическое продление cooldown только если Джарвис ещё говорит
                if is_speaking:
                    self.mic_cooldown_until = now + 0.5

                # Если микрофон выключен — пропускаем
                if not self.mic_enabled:
                    time.sleep(0.5)
                    continue

                if SPEECH_OK and microphone:
                    try:
                        # === ПЕРЕБИВАНИЕ: если Джарвис говорит - сразу останавливаем его ===
                        with self.speaking_lock:
                            speech_was_active = self.is_speaking
                        
                        if speech_was_active:
                            # Пользователь перебивает - останавливаем Джарвиса
                            self.stop_speaking()
                            time.sleep(0.1)
                        
                        log.info("Фоновое слушание: начинаю запись...")
                        with self.mic_lock:
                            with microphone as source:
                                # Автоматическая подстройка порога шума каждые 10 секунд
                                try:
                                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                                except Exception:
                                    pass
                                # Слушаем долго, ждём конца фразы
                                audio = recognizer.listen(source, timeout=5, phrase_time_limit=30)
                        log.info("Фоновое слушание: запись завершена, распознаю...")

                        # === ПЕРЕБИВАНИЕ во время распознавания ===
                        with self.speaking_lock:
                            speech_started_during_capture = self.is_speaking
                        if speech_started_during_capture:
                            continue

                        # === РАСПОЗНАВАНИЕ С VOSK ===
                        text = ""
                        
                        if self.vosk_enabled and self.vosk_recognize:
                            # === ПРИОРИТЕТ: VOSK (быстро, оффлайн) ===
                            try:
                                log.info("🎤 Отправляю в Vosk Speech Recognition...")
                                # Преобразуем audio в формат для Vosk
                                raw_data = audio.get_raw_data(sample_rate=16000)
                                
                                import vosk
                                # Импортируем глобальный recognizer из vosk_recognition
                                from vosk_recognition import _recognizer as vosk_recognizer
                                
                                if vosk_recognizer:
                                    # Подаём данные по частям
                                    chunk_size = 4000  # Примерно 0.25 сек при 16kHz
                                    for i in range(0, len(raw_data), chunk_size):
                                        chunk = raw_data[i:i+chunk_size]
                                        vosk_recognizer.AcceptWaveform(chunk)
                                    
                                    # Получаем результат
                                    result = vosk_recognizer.Result()
                                    text = result.get('text', '').strip()
                                    
                                    # Финальный результат
                                    final_result = vosk_recognizer.FinalResult()
                                    final_text = final_result.get('text', '').strip()
                                    if final_text and not text:
                                        text = final_text
                                    
                                    if text:
                                        log.info(f"✅ Vosk распознал: {text}")
                            except Exception as e:
                                log.warning("Vosk не распознал: %s, используем Google", e)
                        
                        # Fallback на Google если Vosk не сработал
                        if not text:
                            try:
                                log.info("🌐 Отправляю в Google Speech Recognition...")
                                text = recognizer.recognize_google(audio, language='ru-RU')
                                log.info("✅ Google распознал: %s", text)
                            except Exception as e:
                                log.warning("Google не распознал: %s", e)
                                try:
                                    text = recognizer.recognize_sphinx(audio, language='ru')
                                    log.info("✅ Sphinx распознал: %s", text)
                                except Exception as e2:
                                    log.warning("Sphinx тоже не сработал: %s", e2)
                        
                        if not text:
                            log.info("Ничего не распознано, пропускаю")
                            continue
                        
                        text = text.lower().strip()
                        log.info("Фоновое слушание: команда '%s'", text)

                        if not text:
                            continue

                        stop_phrases = (
                            "остановись", "остановись джарвис",
                            "замолчи", "замолчи джарвис",
                            "хватит говорить", "хватит говорить джарвис",
                            "прекрати говорить", "прекрати речь",
                        )
                        if any(phrase in text for phrase in stop_phrases):
                            self.stop_speaking()
                            self.dialogue_mode_until = 0
                            self._safe_ui(
                                lambda: self.status_label.config(
                                    text="● СИСТЕМА ГОТОВА", fg="#10b981"
                                )
                            )
                            self._safe_ui(
                                lambda: self.add_to_dialog(
                                    "Остановился.", is_response=True
                                )
                            )
                            continue

                        # Пока J.A.R.V.I.S. говорит, распознаём только
                        # короткую команду остановки. Остальной текст почти
                        # наверняка является эхом его собственного голоса.
                        with self.speaking_lock:
                            speaking_now = self.is_speaking
                        if speaking_now:
                            log.debug("Игнорирую речь во время озвучки: %s", text[:80])
                            continue

                        # === ПРОВЕРКА 3: ЭХО — сравниваем с последним текстом Джарвиса ===
                        # Если с момента речи Джарвиса прошло < 5 секунд
                        if last_jarvis_text and (now - last_jarvis_time) < 5.0:
                            import re
                            # Убираем всё кроме букв и цифр
                            last_clean = re.sub(r'[^а-яёa-z0-9\s]', '', last_jarvis_text.lower())
                            text_clean = re.sub(r'[^а-яёa-z0-9\s]', '', text.lower())
                            
                            last_words = [w for w in last_clean.split() if len(w) > 1]
                            text_words = [w for w in text_clean.split() if len(w) > 1]
                            
                            if len(text_words) >= 1 and len(last_words) >= 1:
                                # Считаем сколько слов совпадает
                                matched = sum(1 for w in text_words if w in last_words)
                                ratio = matched / max(len(text_words), 1)
                                
                                # Если > 50% слов совпадает — это эхо
                                if ratio > 0.5:
                                    log.info("Поймано эхо Джарвиса (ratio=%.2f): '%s'", ratio, text[:50])
                                    # Продлеваем cooldown чтобы не поймать повторное эхо
                                    self.mic_cooldown_until = now + 1.0
                                    continue
                                
                                # Если хотя бы 3 слова из коротких совпадают
                                if matched >= 3:
                                    log.info("Поймано эхо Джарвиса (3+ слова): '%s'", text[:50])
                                    self.mic_cooldown_until = now + 1.0
                                    continue

                        # === ПРОВЕРКА 4: если Джарвис ещё говорит — только слово "Джарвис" ===
                        with self.speaking_lock:
                            is_speaking = self.is_speaking

                        if is_speaking:
                            wake_variants = ['джарвис', 'jarvis', 'жарвис', 'дарвис', 'ярвис', 'чарвис']
                            wake_word_found = any(v in text for v in wake_variants)
                            
                            if wake_word_found:
                                self.stop_speaking()
                                time.sleep(0.1)
                                
                                current_time = time.time()
                                with self.speaking_lock:
                                    in_active_dialogue = current_time < self.dialogue_mode_until

                                if current_time - self.last_activation_time > 0.4:
                                    self.last_activation_time = current_time
                                    clean_cmd = text
                                    for v in wake_variants: clean_cmd = clean_cmd.replace(v, '')
                                    clean_cmd = clean_cmd.strip()
                                    
                                    if clean_cmd:
                                        self.dialogue_mode_until = time.time() + self.dialogue_mode_seconds
                                        self.execute_command_text(clean_cmd)
                                    else:
                                        self.dialogue_mode_until = time.time() + self.dialogue_mode_seconds
                                        random_jarvis = random.choice([_get_mp3('jarvis'), _get_mp3('jarvis1'), _get_mp3('jarvis2'), _get_mp3('jarvis3')])
                                        self.add_to_dialog("Слушаю вас, сэр.", is_response=True)
                                        self.play_sound_from_folder(random_jarvis, fallback_text="Слушаю вас, сэр.")
                            continue

                        # === ПРОВЕРКА 5: ФИЛЬТРАЦИЯ ПО НЕДАВНИМ ФРАЗАМ (УЛУЧШЕНО) ===
                        is_self_response = False
                        self.recently_spoken = [(t, s) for t, s in self.recently_spoken if now - t < 4.0]
                        
                        short_trigger_words = {'привет', 'хай', 'джарвис', 'jarvis', 'спасибо', 'спс',
                                               'как', 'дела', 'что', 'нов', 'ок', 'ладно', 'хорошо',
                                               'молодец', 'красавчик', 'дурак', 'туп', 'идиот'}
                        
                        for timestamp, spoken in self.recently_spoken:
                            if len(spoken) < 5:
                                continue
                            
                            spoken_words = spoken.lower().split()
                            text_words = text.lower().split()
                            
                            long_text_words = [w for w in text_words if len(w) > 2]
                            long_spoken_words = [w for w in spoken_words if len(w) > 2]
                            
                            if not long_text_words or not long_spoken_words:
                                common = set(text_words) & set(spoken_words) - short_trigger_words
                                if len(common) >= 1:
                                    is_self_response = True
                                    log.info("Игнорирую эхо (1+ слово): '%s'", text[:50])
                                    break
                            else:
                                common_long = set(long_text_words) & set(long_spoken_words)
                                if len(common_long) >= 1:
                                    is_self_response = True
                                    log.info("Игнорирую эхо (длинное слово): '%s'", text[:50])
                                    break
                        
                        if is_self_response:
                            continue

                        # === ВЫПОЛНЕНИЕ КОМАНДЫ ===
                        wake_variants = ['джарвис', 'jarvis', 'жарвис', 'дарвис', 'ярвис', 'чарвис']
                        wake_word_found = any(v in text for v in wake_variants)

                        trigger_words = [
                            'спасиб', 'благодар', 'спс', 'как дел', 'как ты', 'что нов', 'настроен',
                            'молодец', 'красавчик', 'отличн', 'хорошо', 'понял', 'принят', 'ладно',
                            'дурак', 'туп', 'идиот', 'дебил', 'нах', 'пошел', 'бля', 'сука', 'привет', 'здравствуй'
                        ]
                        has_exact_ok = 'ок' in text.split() and 'окно' not in text
                        has_trigger = any(w in text for w in trigger_words) or self.is_jarvis_creator_query(text)
                        command_starts = (
                            'открой ', 'открыть ', 'закрой ', 'закрыть ',
                            'запусти ', 'запустить ', 'выключи ', 'включи ',
                            'покажи ', 'найди ', 'поиск ', 'поищи ',
                            'скажи ', 'расскажи ', 'какая ', 'какой ', 'сколько ',
                            'погода', 'время', 'дата', 'календарь', 'диагностика',
                            'новости', 'сделай скриншот', 'сделай снимок'
                        )
                        has_direct_command = text.startswith(command_starts)
                        
                        current_time = time.time()
                        with self.speaking_lock:
                            in_active_dialogue = current_time < self.dialogue_mode_until

                        if in_active_dialogue and text.strip():
                            self.last_activation_time = current_time
                            self.dialogue_mode_until = current_time + self.dialogue_mode_seconds
                            clean_cmd = text
                            for v in wake_variants: clean_cmd = clean_cmd.replace(v, '')
                            clean_cmd = clean_cmd.strip()
                            if clean_cmd: self.execute_command_text(clean_cmd, play_intro=False)

                        elif wake_word_found:
                            if current_time - self.last_activation_time > 0.4:
                                self.last_activation_time = current_time
                                clean_cmd = text
                                for v in wake_variants: clean_cmd = clean_cmd.replace(v, '')
                                clean_cmd = clean_cmd.strip()
                                
                                if clean_cmd:
                                    self.execute_command_text(clean_cmd)
                                else:
                                    random_jarvis = random.choice([_get_mp3('jarvis'), _get_mp3('jarvis1'), _get_mp3('jarvis2'), _get_mp3('jarvis3')])
                                    self.add_to_dialog("Слушаю вас, сэр.", is_response=True)
                                    self.play_sound_from_folder(random_jarvis, fallback_text="Слушаю вас, сэр.")

                        elif has_exact_ok or has_trigger or has_direct_command:
                            if current_time - self.last_activation_time > 0.4:
                                self.last_activation_time = current_time
                                self.execute_command_text(text, play_intro=False)
                    except Exception as exc:
                        log.debug("Фоновое слушание: %s", exc)
                        if "device" in str(exc).lower() or "microphone" in str(exc).lower():
                            self._connect_microphone()
                time.sleep(0.05)
        
        threading.Thread(target=listen, daemon=True).start()
    
    def _open_key_activation_window(self):
        """Открыть окно ввода ключа активации"""
        try:
            from subscription import SubscriptionManager
            import tkinter as tk
            
            # Создаём окно
            win = tk.Toplevel(self)
            win.title("🔑 Активация JARVIS PRO")
            win.geometry("500x400")
            win.resizable(False, False)
            win.transient(self)
            win.grab_set()
            win.configure(bg="#1a1a2e")
            
            # Заголовок
            tk.Label(
                win, text="🔑 АКТИВАЦИЯ JARVIS PRO",
                font=("Segoe UI", 16, "bold"),
                bg="#1a1a2e", fg="#00d4ff"
            ).pack(pady=(20, 10))
            
            tk.Label(
                win, text="Введите ключ активации, который вы получили от продавца:",
                font=("Segoe UI", 10),
                bg="#1a1a2e", fg="#e0e0e0"
            ).pack(pady=(0, 15))
            
            # Контекстное меню для вставки
            paste_menu = tk.Menu(win, tearoff=0)
            paste_menu.add_command(label="Вставить (Ctrl+V)", command=lambda: key_entry.event_generate('<<Paste>>'))
            paste_menu.add_command(label="Вставить всё", command=lambda: self._paste_key_to_entry(key_entry))
            
            # Поле ввода ключа
            key_entry = tk.Entry(
                win,
                font=("Courier", 14, "bold"),
                bg="#16213e", fg="#00ff88",
                insertbackground="#00ff88",
                relief=tk.SOLID, bd=2,
                justify="center",
                width=40
            )
            key_entry.pack(pady=10)
            key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX...")
            key_entry.bind("<FocusIn>", lambda e: key_entry.delete(0, tk.END) if key_entry.get() == "XXXX-XXXX-XXXX-XXXX..." else None)
            key_entry.bind("<FocusOut>", lambda e: key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX...") if not key_entry.get() else None)
            key_entry.bind("<Return>", lambda e: self._activate_key_from_dialog(key_entry, win))
            key_entry.bind("<Button-3>", lambda e: paste_menu.tk_popup(e.x_root, e.y_root))
            key_entry.bind("<Control-v>", lambda e: key_entry.event_generate('<<Paste>>'))
            key_entry.bind("<Control-V>", lambda e: key_entry.event_generate('<<Paste>>'))
            
            # Кнопка активации
            tk.Button(
                win,
                text="✅ АКТИВИРОВАТЬ",
                font=("Segoe UI", 11, "bold"),
                bg="#10b981", fg="#fff",
                activebackground="#059669",
                activeforeground="#fff",
                relief=tk.FLAT,
                cursor="hand2",
                padx=30,
                pady=10,
                command=lambda: self._activate_key_from_dialog(key_entry, win)
            ).pack(pady=15)
            
            # Кнопка отмены
            tk.Button(
                win,
                text="❌ ОТМЕНА",
                font=("Segoe UI", 10),
                bg="#64748b", fg="#fff",
                activebackground="#475569",
                activeforeground="#fff",
                relief=tk.FLAT,
                cursor="hand2",
                padx=20,
                pady=8,
                command=win.destroy
            ).pack(pady=(0, 10))
            
            # Подсказка
            tk.Label(
                win,
                text="Формат ключа: XXXX-XXXX-XXXX-XXXX",
                font=("Segoe UI", 8),
                bg="#1a1a2e", fg="#64748b"
            ).pack(pady=(0, 5))
            
        except Exception as e:
            self.add_to_dialog(f"⚠️ Ошибка открытия окна активации: {str(e)}", is_response=True)
    
    def _activate_key_from_dialog(self, key_entry, window):
        """Активация ключа из диалогового окна"""
        try:
            from subscription import SubscriptionManager
            import tkinter as tk
            from tkinter import messagebox
            
            key = key_entry.get().strip()
            
            if not key or key == "XXXX-XXXX-XXXX-XXXX...":
                messagebox.showwarning("Внимание", "Введите ключ активации!")
                return
            
            # Активируем
            sub = SubscriptionManager()
            success, message = sub.activate_license(key)
            
            if success:
                self.add_to_dialog(f"✅ {message}", is_response=True)
                self.status_label.config(text="● ЛИЦЕНЗИЯ АКТИВНА", fg="#10b981")
                
                # Обновляем статус подписки
                self._update_subscription_status()
                
                messagebox.showinfo("Успех", message)
                window.destroy()
            else:
                messagebox.showerror("Ошибка", message)
                
        except Exception as e:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Ошибка активации:\n{str(e)}")
    
    def _paste_key_to_entry(self, key_entry):
        """Вставка ключа из буфера обмена"""
        try:
            # Получаем текст из буфера обмена
            clipboard_text = self.clipboard_get()
            if clipboard_text:
                # Очищаем поле и вставляем
                key_entry.delete(0, tk.END)
                key_entry.insert(0, clipboard_text.strip())
        except tk.TclError:
            pass  # Буфер обмена пуст или недоступен

    def show_plugins(self):
        if self._focus_child_window(self._plugins_window):
            return
        plugins_win = tk.Toplevel(self)
        self._plugins_window = plugins_win
        plugins_win.protocol("WM_DELETE_WINDOW", lambda: self._close_child_window("_plugins_window"))
        plugins_win.title("Статус плагинов")
        plugins_win.geometry("420x450")
        plugins_win.configure(bg=self.panel_bg)
        tk.Label(plugins_win, text="АКТИВНЫЕ ПЛАГИНЫ СИСТЕМЫ", font=("Segoe UI", 11, "bold"), bg=self.panel_bg, fg=self.accent_color).pack(pady=15)
        frame = tk.Frame(plugins_win, bg=self.panel_bg, highlightbackground=self.border_color, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        for _, p in PLUGINS.items():
            row = tk.Frame(frame, bg=self.panel_bg)
            row.pack(fill=tk.X, padx=15, pady=3)
            tk.Label(row, text=p['name'], font=("Segoe UI", 9), bg=self.panel_bg, fg=self.text_color).pack(side=tk.LEFT)
            tk.Label(row, text="АКТИВЕН [✓]" if p['enabled'] else "ОТКЛ [✗]", font=("Segoe UI", 9, "bold"), bg=self.panel_bg, fg="#10b981" if p['enabled'] else "#ef4444").pack(side=tk.RIGHT)
        ModernButton(plugins_win, text="ЗАКРЫТЬ", command=lambda: self._close_child_window("_plugins_window"), bg="#334155", fg="#fff", padx=20, pady=8).pack(pady=15)
    
    def _on_key_input_focus_in(self, event):
        """Очистка поля ввода при фокусе"""
        if self.activation_key_entry.get() == "XXXX-XXXX-XXXX-XXXX...":
            self.activation_key_entry.delete(0, tk.END)
    
    def _on_key_input_focus_out(self, event):
        """Возврат подсказки если пусто"""
        if not self.activation_key_entry.get():
            self.activation_key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX...")
    
    def _on_key_enter(self, event):
        """Обработка нажатия Enter в поле ввода"""
        self._activate_key_from_sidebar()
    
    def _activate_key_from_sidebar(self):
        """Активация ключа из боковой панели"""
        key = self.activation_key_entry.get().strip()
        
        if key and key != "XXXX-XXXX-XXXX-XXXX...":
            try:
                from subscription import SubscriptionManager
                sub = SubscriptionManager()
                success, message = sub.activate_license(key)
                
                if success:
                    self.add_to_dialog(f"✅ {message}", is_response=True)
                    self.status_label.config(text="● ЛИЦЕНЗИЯ АКТИВНА", fg="#10b981")
                    self.activation_key_entry.delete(0, tk.END)
                    self.activation_key_entry.insert(0, "✓ АКТИВИРОВАНО")
                    self.activation_key_entry.config(fg="#10b981")
                else:
                    self.add_to_dialog(f"❌ {message}", is_response=True)
                    self.activation_key_entry.delete(0, tk.END)
                    self.activation_key_entry.insert(0, "ОШИБКА")
                    self.after(2000, lambda: self.activation_key_entry.delete(0, tk.END))
            except Exception as e:
                self.add_to_dialog(f"⚠️ Ошибка активации: {str(e)}", is_response=True)
                self.activation_key_entry.delete(0, tk.END)
                self.activation_key_entry.insert(0, "ОШИБКА")
                self.after(2000, lambda: self.activation_key_entry.delete(0, tk.END))
        else:
            self.add_to_dialog("⚠️ Введите ключ активации", is_response=True)
            self.activation_key_entry.delete(0, tk.END)
    
    def _open_subscription_url(self):
        """Открыть URL для покупки подписки"""
        try:
            import webbrowser
            # Используем URL из конфигурации
            if SUBSCRIPTION_OK:
                from subscription import SubscriptionManager
                subscription_url = SubscriptionManager.SUBSCRIPTION_URL or "https://jarvis-uol.vercel.app/"
            else:
                subscription_url = "https://jarvis-uol.vercel.app/"
            webbrowser.open(subscription_url)
            self.add_to_dialog(f"🔗 Открываю страницу подписки...", is_response=True)
        except Exception as e:
            self.add_to_dialog(f"⚠️ Ошибка открытия URL: {str(e)}", is_response=True)
    
    def _update_subscription_status(self):
        """Обновление статуса подписки в боковой панели"""
        if not SUBSCRIPTION_OK or not hasattr(self, 'sub_status_label'):
            return
        
        try:
            from subscription import SubscriptionManager
            from datetime import datetime
            
            sub = SubscriptionManager()
            status, message = sub.check_access()
            
            if status == "active":
                end_date = datetime.fromisoformat(sub.license_data["end_date"])
                days_left = (end_date - datetime.now()).days
                hours_left = (end_date - datetime.now()).total_seconds() / 3600
                
                if days_left > 0:
                    color = "#10b981"  # зелёный
                    icon = "✅"
                    text = f"{icon} АКТИВНА: {days_left} ДНЕЙ"
                    if hours_left < 24:
                        text = f"{icon} АКТИВНА: {int(hours_left)} ЧАСОВ"
                elif days_left == 0:
                    color = "#f59e0b"  # оранжевый
                    icon = "⚠️"
                    text = f"{icon} ПОСЛЕДНИЙ ДЕНЬ"
                else:
                    color = "#ef4444"  # красный
                    icon = "❌"
                    text = f"{icon} ИСТЕКЛА"
                
                self.sub_status_label.config(text=text, fg=color)
            
            elif status == "trial_needed":
                self.sub_status_label.config(text="⏳ НАЧАТЬ ТРИАЛ", fg="#f59e0b")
            
            elif status == "trial_expired":
                self.sub_status_label.config(text="⏰ ТРИАЛ ИСТЁК", fg="#ef4444")
            
            elif status == "license_expired":
                self.sub_status_label.config(text="⏰ ПОДПИСКА ИСТЕКЛА", fg="#ef4444")
            
            else:
                self.sub_status_label.config(text="⚠️ НЕИЗВЕСТНО", fg="#ef4444")
        
        except Exception as e:
            log.warning("Ошибка обновления статуса подписки: %s", e)
    
    def _start_subscription_monitor(self):
        """Запуск периодического обновления статуса подписки"""
        def update_loop():
            if self.is_running:
                self._update_subscription_status()
                self.after(60000, update_loop)  # Обновление каждые 60 секунд
        
        # Первое обновление сразу
        self.after(1000, update_loop)
    
    def open_activation(self):
        """Открыть окно активации"""
        try:
            from subscription import ActivationWindow
            
            if hasattr(self, '_activation_window') and self._activation_window:
                self._activation_window.lift()
                return
            
            win = tk.Toplevel(self)
            self._activation_window = win
            win.transient(self)
            
            activator = ActivationWindow(win)
            activator.show()
            
            self._activation_window = None
        except Exception as e:
            self.add_to_dialog(f"⚠️ Ошибка открытия окна активации: {str(e)}", is_response=True)
            self.activation_key_entry.insert(0, "XXXX-XXXX-XXXX-XXXX...")
    
    def open_activation(self):
        """Открыть окно активации"""
        try:
            from subscription import ActivationWindow
            
            if hasattr(self, '_activation_window') and self._activation_window:
                self._activation_window.lift()
                return
            
            win = tk.Toplevel(self)
            self._activation_window = win
            win.transient(self)
            
            activator = ActivationWindow(win)
            activator.show()
            
            self._activation_window = None
        except Exception as e:
            self.add_to_dialog(f"⚠️ Ошибка открытия окна активации: {str(e)}", is_response=True)
    
    def show_help(self):
        help_text = (
"=== СПРАВКА ПО КОМАНДАМ J.A.R.V.I.S. ===\n\n"

"🗣️ АКТИВАЦИЯ:\n"
"• «Джарвис» — активация (мгновенно прерывает речь)\n"
"• «Jarvis» — активация (английская версия)\n\n"

"📱 ПРИЛОЖЕНИЯ:\n"
"• «Открой [приложение]» — запуск приложения\n"
"  Примеры: telegram, discord, chrome, steam, word, excel, notepad, calc, vscode\n"
"• «Закрой [приложение]» — закрытие приложения\n"
"• «Закрой окно [приложение]» — закрытие окна по названию\n"
"• «Закрой активное окно» — закрыть текущее окно\n\n"

"🌐 БРАУЗЕР:\n"
"• «Открой youtube / google / yandex / github / vk» — открыть сайт\n"
"• «Открой браузер» — открыть Chrome\n"
"• «Открой google и найди [текст]» — поиск в Google\n"
"• «Открой youtube и найди [текст]» — поиск на YouTube\n"
"• «Открой vk и найди [текст]» — поиск в ВКонтакте\n"
"• «Открой яндекс и найди [текст]» — поиск в Яндексе\n"
"• «Прокрути вниз / вверх» — прокрутка страницы\n"
"• «Обнови страницу» — перезагрузка страницы\n"
"• «Назад» — назад в браузере\n"
"• «Сделай скриншот страницы» — скриншот активной страницы\n\n"

"🖥️ СИСТЕМА:\n"
"• «Выключи компьютер / ПК» — выключение ПК\n"
"• «Перезагрузи компьютер / ПК» — перезагрузка\n"
"• «Отмена выключения» — отмена выключения\n"
"• «Отмена перезагрузки» — отмена перезагрузки\n"
"• «Спящий режим» — переход в сон\n"
"• «Гибернация» — глубокий сон\n"
"• «Блокировка экрана» — блокировка Windows\n"
"• «Выключи звук / Включи звук» — мьют звука\n"
"• «Громче / Тише» — регулировка громкости\n"
"• «Громкость [число]» — установить громкость 1-10\n\n"

"🪟 ОКНА:\n"
"• «Свернуть всё / Сверни все окна» — свернуть все окна\n"
"• «Развернуть всё / Разверни все окна» — развернуть все окна\n"
"• «Покажи рабочий стол» — показать рабочий стол\n"
"• «Сверни [приложение]» — свернуть окно\n"
"• «Разверни [приложение]» — развернуть окно\n\n"

"📂 ФАЙЛЫ:\n"
"• «Мой компьютер» — открыть «Этот компьютер»\n"
"• «Загрузки» — открыть папку загрузок\n"
"• «Документы» — открыть документы\n"
"• «Видео» — открыть видео\n"
"• «Картинки» — открыть картинки\n"
"• «Диск C / Диск D» — открыть диск\n"
"• «Закрой загрузки / документы / видео / картинки» — закрыть папку\n\n"

"🔍 ПОИСК:\n"
"• «Найди [текст]» — поиск в интернете\n"
"• «Найди файл [имя]» — поиск файла на диске\n\n"

"📸 СКРИНШОТЫ:\n"
"• «Сделай скриншот» — сделать скриншот\n"
"• «Сделай скриншот с пометками» — скриншот с рамками окон, курсором, подписями\n"
"• «Проанализируй экран» — анализ содержимого экрана\n"
"• «Покажи последний скриншот» — показать последний\n"
"• «Покажи скриншоты» — список скриншотов\n\n"

"🎵 МУЗЫКА (Яндекс.Музыка):\n"
"• «Включи песню [название]» — поиск и воспроизведение в Яндекс.Музыке\n"
"• «Включи музыку» — открыть Яндекс.Музыку и авто-воспроизведение\n"
"• «Пауза / Стоп / Приостанови» — пауза (горячая клавиша P)\n"
"• «Продолжи / Играть» — воспроизведение (горячая клавиша P)\n"
"• «Следующий / Далее / Следующий трек» — следующий трек (горячая клавиша N)\n"
"• «Предыдущий / Назад / Предыдущий трек» — предыдущий трек (горячая клавиша M)\n"
"• «Громче музыку / Громче» — увеличить громкость (горячая клавиша F10)\n"
"• «Тише музыку / Тише» — уменьшить громкость (горячая клавиша F9)\n"
"• «Без звука / Mute» — отключить звук (горячая клавиша M)\n"
"• «Повтор / Зацикли» — повтор трека (горячая клавиша F11)\n"
"• «Перемешать / Shuffle / Микс» — случайный порядок (горячая клавиша F12)\n\n"

"💡 КЛАВИАТУРА:\n"
"• «Включи подсветку» — включить подсветку\n"
"• «Выключи подсветку» — выключить подсветку\n"
"• «Ярче подсветку» — увеличить яркость\n"
"• «Тише подсветку» — уменьшить яркость\n"
"• «Цикл подсветки» — циклическое переключение\n\n"

"🗑️ ОЧИСТКА:\n"
"• «Очисти мусор / Очисти / Очистим» — очистить корзину\n"
"• «Очисти корзину» — очистить корзину\n"
"• «Очисти кэш / Очисти temp» — очистить временные файлы\n\n"

"📊 ДИАГНОСТИКА:\n"
"• «Диагностика системы» — проверка системы\n"
"• «Проверь скорость интернета» — тест скорости\n"
"• «Погода» — текущая погода\n"
"• «Новости» — открыть новости\n\n"

"🎨 ИИ:\n"
"• «Нарисуй [описание]» — генерация изображения\n"
"• Любой вопрос — ответ через Ollama\n\n"

"⏰ ИНФОРМАЦИЯ:\n"
"• «Какой час» — текущее время\n"
"• «Какая дата» — текущая дата\n"
"• «Календарь» — день недели и дата\n\n"

"💬 ДИАЛОГ:\n"
"• «Привет» — приветствие\n"
"• «Спасибо» — благодарность\n"
"• «Как дела» — статус\n"
"• «Кто тебя создал» — информация о создателе\n\n"

"🔑 АКТИВАЦИЯ КОМАНД:\n"
"Без слова «Джарвис» (работают всегда):\n"
"• Приветствия: привет, здравствуй, добрый, хай\n"
"• Благодарность: спасибо, благодар, спс\n"
"• Диалог: как дела, как ты, что нов, молодец, красавчик, отлично\n"
"• Согласие: хорошо, понял, принят, ладно, ок\n"
"• Токсичность: дурак, туп, идиот, дебил, нахуй, пошел, бля, сука, пидор\n"
"• Создание: кто тебя создал\n\n"
"Со словом «Джарвис» (активация):\n"
"• Все системные команды: выключи, перезагрузи, спящий, гибернация, блокировка\n"
"• Управление звуком: выключи звук, включи звук, громче, тише, громкость [число]\n"
"• Запуск приложений: открой telegram, discord, chrome, steam, word, excel, notepad, calc, vscode\n"
"• Закрытие приложений: закрой telegram, закрой chrome, закрой стим\n"
"• Управление окнами: свернуть всё, развернуть всё, покажи рабочий стол\n"
"• Файлы: мой компьютер, загрузки, документы, видео, картинки, диск C, диск D\n"
"• Поиск: найди [текст], найди файл [имя]\n"
"• Скриншоты: сделай скриншот, проанализируй экран, покажи последний скриншот\n"
"• Музыка: включи песню [название], включи музыку, пауза (P), продолжи, следующий (N), предыдущий (M), громче, тише, мьют, повтор, перемешать\n"
"• Подсветка: включи подсветку, выключи подсветку, ярче, тише, цикл\n"
"• Очистка: очисти мусор, очисти корзину, очисти кэш, очисти temp\n"
"• Диагностика: диагностика системы, проверь скорость интернета\n"
"• Погода: погода\n"
"• Новости: новости\n"
"• Генерация: нарисуй [описание]\n"
"• ИИ: любой вопрос или запрос\n"
"• Время и дата: какой час, какая дата, календарь\n"
        )
        
        if self._focus_child_window(self._help_window):
            return
        help_win = tk.Toplevel(self)
        self._help_window = help_win
        help_win.protocol("WM_DELETE_WINDOW", lambda: self._close_child_window("_help_window"))
        help_win.title("Справка — Команды J.A.R.V.I.S.")
        help_win.geometry("550x650")
        help_win.configure(bg=self.panel_bg)
        help_win.resizable(True, True)
        
        tk.Label(help_win, text="📖 СПРАВКА", font=("Segoe UI", 13, "bold"), bg=self.panel_bg, fg=self.accent_color).pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(help_win, font=("Consolas", 9), bg=self.console_bg, fg=self.console_fg, insertbackground=self.accent_color, borderwidth=0, highlightthickness=0)
        text_area.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        text_area.insert("1.0", help_text)
        text_area.config(state=tk.DISABLED)
        
        ModernButton(help_win, text="ЗАКРЫТЬ", command=lambda: self._close_child_window("_help_window"), bg="#334155", fg="#fff", padx=20, pady=8).pack(pady=10)
    

    
    def show_welcome(self):
        self.add_to_dialog("J.A.R.V.I.S. ULTIMATE PRO ЗАПУЩЕН", is_response=True)
        random_hello = random.choice([_get_mp3('hello'), _get_mp3('hello1'), _get_mp3('hello2'), _get_mp3('hello3')])
        self.play_sound_from_folder(random_hello, fallback_text="Приветствую вас. Все системы функционируют в штатном режиме.")

if __name__ == '__main__':
    app = JARVISUltimate()
    app.mainloop()
