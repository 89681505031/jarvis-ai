#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. — умный как ChatGPT, голос как Пол Беттани.
Один файл. Мозг = интернет (Pollinations AI + Wikipedia).
"""

import sys, os, json, re, time, math, random, queue, threading, asyncio, logging, subprocess
import urllib.parse, webbrowser
from pathlib import Path
from datetime import datetime

# ============================================================
# ЛОГИ
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(Path(__file__).parent / "jarvis.log", encoding="utf-8", mode="a"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("jarvis")

# ============================================================
# ЗАВИСИМОСТИ
# ============================================================
try:
    import requests
    import urllib3
    urllib3.disable_warnings()
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    log.error("pip install requests")

try:
    import tkinter as tk
    from tkinter import scrolledtext, messagebox
    TK_OK = True
except ImportError:
    TK_OK = False

try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except Exception:
    PYGAME_OK = False

try:
    import edge_tts
    EDGE_TTS_OK = True
except ImportError:
    EDGE_TTS_OK = False

try:
    import pyttsx3
    VOICE_OK = True
except ImportError:
    VOICE_OK = False

try:
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 400
    recognizer.pause_threshold = 0.8
    microphone = sr.Microphone()
    SPEECH_OK = True
except Exception:
    SPEECH_OK = False
    recognizer = None
    microphone = None

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAG_OK = True
except Exception:
    PYAG_OK = False

try:
    import psutil
    PSUTIL_OK = True
except ImportError:
    PSUTIL_OK = False


# ============================================================
# МОЗГ — CHATGPT ЧЕРЕЗ ИНТЕРНЕТ
# ============================================================
class Brain:
    """Мозг Джарвиса. Обращается к Pollinations AI (настоящий LLM, без ключа),
    при неудаче — Wikipedia. Отвечает как ChatGPT."""

    SYSTEM = (
        "Ты — J.A.R.V.I.S., умный ИИ-ассистент на ПК, как в фильме Железный человек. "
        "Ты знаешь всё: науку, историю, программирование, культуру, математику, языки. "
        "Отвечай на русском языке, обращайся к пользователю 'сэр'. "
        "Будь точным, полезным, дружелюбным и кратким (1-5 предложений, если не просят подробнее). "
        "Не используй markdown, звёздочки, решётки — только обычный текст. "
        "Если не знаешь — честно скажи."
    )

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 JarvisBrain/5.0'})
        self.history = []

    def think(self, question):
        q = question.strip()
        if not q:
            return {'action': 'none', 'param': '', 'reply': 'Слушаю, сэр.'}

        low = q.lower()

        # --- Быстрые локальные ответы (мгновенно) ---
        if re.search(r'который час|сколько времени|какое (сейчас )?время', low):
            n = datetime.now()
            return self._r(f"Сейчас {n.hour} часов {n.minute:02d} минут.")

        if re.search(r'какое (сегодня )?число|какая (сегодня )?дата', low):
            n = datetime.now()
            days = ['понедельник','вторник','среда','четверг','пятница','суббота','воскресенье']
            months = ['января','февраля','марта','апреля','мая','июня',
                      'июля','августа','сентября','октября','ноября','декабря']
            return self._r(f"Сегодня {days[n.weekday()]}, {n.day} {months[n.month-1]} {n.year} года.")

        # --- Калькулятор ---
        if re.search(r'(посчитай|вычисли|сколько будет|реши)\s+(.+)', low):
            expr = re.search(r'(посчитай|вычисли|сколько будет|реши)\s+(.+)', low).group(2)
            r = self._calc(expr)
            if r is not None:
                return self._r(f"Ответ: {r}")

        if re.fullmatch(r'\s*[\d\s+\-*/().]+\s*', q):
            r = self._calc(q)
            if r is not None:
                return self._r(f"Ответ: {r}")

        # --- Основное: ChatGPT через Pollinations ---
        answer = self._ask_llm(q)
        if answer:
            return self._r(answer)

        # --- Fallback: Wikipedia ---
        answer = self._wikipedia(q)
        if answer:
            return self._r(answer)

        return self._r("Прошу прощения, сэр, не удалось найти ответ. Попробуйте сформулировать иначе.")

    def _ask_llm(self, question):
        """Pollinations AI — реальный LLM (GPT-4o-mini, Mistral, Llama) без ключа."""
        # Собираем контекст диалога (последние 6 сообщений)
        self.history.append({'role': 'user', 'content': question})
        if len(self.history) > 12:
            self.history = self.history[-12:]

        messages = [{'role': 'system', 'content': self.SYSTEM}] + self.history

        # Пробуем разные модели
        for model in ('openai', 'mistral', 'llama'):
            try:
                r = self.session.post(
                    "https://text.pollinations.ai/openai",
                    json={'model': model, 'messages': messages,
                          'temperature': 0.7, 'private': True},
                    timeout=60, verify=False
                )
                if r.status_code == 200:
                    data = r.json()
                    content = data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
                    if content and len(content) > 3:
                        # Чистим от markdown
                        content = re.sub(r'```[\s\S]*?```', '', content)
                        content = re.sub(r'[#*`>_~]+', '', content)
                        content = re.sub(r'\s+', ' ', content).strip()
                        self.history.append({'role': 'assistant', 'content': content})
                        if len(self.history) > 12:
                            self.history = self.history[-12:]
                        return content
            except Exception as e:
                log.warning("Pollinations %s: %s", model, str(e)[:80])
                continue
        return None

    def _wikipedia(self, question):
        """Wikipedia — если LLM недоступен."""
        try:
            q = re.sub(r'^(кто такой|кто такая|что такое|что значит|расскажи про|расскажи о)\s+',
                       '', question.lower()).strip(' ?.!')
            if len(q) < 2:
                return None
            r = self.session.get("https://ru.wikipedia.org/w/api.php", params={
                'action': 'query', 'format': 'json',
                'list': 'search', 'srsearch': q, 'srlimit': 1
            }, timeout=10, verify=False)
            data = r.json()
            if not data.get('query', {}).get('search'):
                return None
            title = data['query']['search'][0]['title']
            r2 = self.session.get(
                f"https://ru.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}",
                timeout=10, verify=False)
            if r2.status_code == 200:
                extract = r2.json().get('extract', '').strip()
                if extract:
                    sents = re.split(r'(?<=[.!?])\s+', extract)
                    return ' '.join(sents[:3])[:700]
        except Exception:
            pass
        return None

    def _calc(self, expr):
        e = expr.lower()
        for k, v in {'плюс': '+', 'минус': '-', 'умножить на': '*', 'умножить': '*',
                     'разделить на': '/', 'разделить': '/', 'делить на': '/',
                     'в квадрате': '**2', 'в кубе': '**3', 'корень из': 'sqrt',
                     'х': '*', 'x': '*'}.items():
            e = e.replace(k, v)
        e = e.replace(',', '.').replace('%', '/100').replace('^', '**')
        e = re.sub(r'[^0-9+\-*/(). a-z]', '', e)
        e = re.sub(r'sqrt\s*(\d+(?:\.\d+)?)', r'math.sqrt(\1)', e)
        if not e.strip():
            return None
        try:
            return eval(e, {'__builtins__': None, 'math': math, 'abs': abs, 'round': round}, {})
        except Exception:
            return None

    def _r(self, text):
        return {'action': 'none', 'param': '', 'reply': text}


BRAIN = Brain()


# ============================================================
# ГОЛОС JARVIS — ru-RU-DmitryNeural, pitch -15Hz, rate -8%
# ============================================================
class Voice:
    VOICE = "ru-RU-DmitryNeural"
    RATE = "-8%"
    PITCH = "-15Hz"

    def __init__(self, app=None):
        self.app = app
        self.lock = threading.Lock()
        self.speaking = False
        self.sounds_dir = Path(__file__).parent / 'sounds'
        self.sounds_dir.mkdir(exist_ok=True)

    def stop(self):
        with self.lock:
            self.speaking = False
        if PYGAME_OK:
            try:
                pygame.mixer.music.stop()
                pygame.mixer.stop()
            except Exception:
                pass

    def say(self, text, block=False):
        if block:
            self._speak(text)
        else:
            threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    def _speak(self, text):
        with self.lock:
            self.speaking = True
        text = text.replace('"', "'").replace('\n', ' ').strip()
        if not text:
            return
        temp = self.sounds_dir / f"jarvis_{int(time.time()*1000)}.mp3"
        success = False

        # --- Edge-TTS ---
        if EDGE_TTS_OK:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    async def gen():
                        c = edge_tts.Communicate(text, self.VOICE,
                                                 rate=self.RATE, pitch=self.PITCH)
                        await c.save(str(temp))
                    loop.run_until_complete(gen())
                finally:
                    loop.close()
            except Exception as e:
                log.error("Edge-TTS: %s", str(e)[:120])
                # CLI fallback
                try:
                    cmd = [sys.executable, '-m', 'edge_tts',
                           '--voice', self.VOICE, '--rate', self.RATE, '--pitch', self.PITCH,
                           '--text', text, '--write-media', str(temp)]
                    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    subprocess.run(cmd, capture_output=True, timeout=30, creationflags=flags)
                except Exception as e2:
                    log.error("Edge-TTS CLI: %s", e2)

        # --- Воспроизведение ---
        if temp.exists() and PYGAME_OK:
            try:
                pygame.mixer.music.load(str(temp))
                pygame.mixer.music.play()
                while self.speaking and pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                if not self.speaking:
                    pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                success = True
            except Exception as e:
                log.error("Pygame: %s", e)

        try:
            if temp.exists():
                temp.unlink()
        except Exception:
            pass

        # --- pyttsx3 fallback ---
        if not success and VOICE_OK:
            try:
                import pyttsx3
                e = pyttsx3.init()
                e.setProperty('rate', 165)
                for v in e.getProperty('voices'):
                    if 'male' in v.name.lower() or 'муж' in v.name.lower():
                        e.setProperty('voice', v.id)
                        break
                e.say(text)
                e.runAndWait()
            except Exception as ex:
                log.error("pyttsx3: %s", ex)

        with self.lock:
            self.speaking = False


# ============================================================
# КОМАНДЫ ПК
# ============================================================
def execute_pc_command(cmd):
    """Возвращает True если команда распознана как системная."""
    low = cmd.lower().strip()
    words = low.split()

    # Питание
    if any(k in low for k in ['выключи компьютер', 'выключить компьютер', 'выключи пк', 'выключи комп']):
        os.system('shutdown -s -t 30')
        return "Выключаю компьютер через 30 секунд, сэр."
    if any(k in low for k in ['отмена выключения', 'не выключай']):
        os.system('shutdown -a')
        return "Отменено."
    if any(k in low for k in ['перезагрузи компьютер', 'перезагрузить пк', 'перезагрузка пк']):
        os.system('shutdown -r -t 30')
        return "Перезагружаю через 30 секунд."
    if any(k in low for k in ['спящий режим', 'режим сна']):
        os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
        return "Спящий режим."
    if any(k in low for k in ['заблокируй', 'блокировка экрана']) or 'lock' in words:
        os.system('rundll32 user32.dll,LockWorkStation')
        return "Экран заблокирован."

    # Звук
    if any(k in low for k in ['выключи звук', 'без звука', 'заглуши', 'мьют']):
        if PYAG_OK:
            pyautogui.press('volumemute')
        return "Звук выключен."
    if any(k in low for k in ['включи звук', 'верни звук']):
        if PYAG_OK:
            pyautogui.press('volumemute')
        return "Звук включён."
    if any(k in low for k in ['громче', 'увеличь звук']) and 'музык' not in low:
        if PYAG_OK:
            for _ in range(5): pyautogui.press('volumeup')
        return "Громче."
    if any(k in low for k in ['тише', 'уменьши звук']) and 'музык' not in low:
        if PYAG_OK:
            for _ in range(5): pyautogui.press('volumedown')
        return "Тише."

    # Запуск приложений
    if any(w in words for w in ['открой', 'запусти']):
        target = low
        for w in ['открой', 'запусти', 'пожалуйста']:
            target = target.replace(w, '')
        target = target.strip()

        sites = {
            'ютуб': 'https://youtube.com', 'youtube': 'https://youtube.com',
            'гугл': 'https://google.com', 'google': 'https://google.com',
            'яндекс': 'https://yandex.ru', 'yandex': 'https://yandex.ru',
            'вк': 'https://vk.com', 'vk': 'https://vk.com',
            'github': 'https://github.com', 'гитхаб': 'https://github.com',
        }
        if target in sites:
            webbrowser.open(sites[target])
            return f"Открываю {target}."

        apps = {
            'хром': 'chrome', 'chrome': 'chrome',
            'блокнот': 'notepad', 'notepad': 'notepad',
            'калькулятор': 'calc', 'калькулятор': 'calc',
            'проводник': 'explorer', 'steam': 'steam', 'стим': 'steam',
            'telegram': 'telegram', 'телеграм': 'telegram',
            'discord': 'discord', 'дискорд': 'discord',
            'vscode': 'code', 'вскод': 'code',
        }
        for name, exe in apps.items():
            if name in target:
                try:
                    subprocess.Popen(exe, shell=True)
                    return f"Запускаю {name}."
                except Exception:
                    pass

    # Закрытие
    if any(w in words for w in ['закрой', 'закрыть']) and 'окно' not in low:
        target = low
        for w in ['закрой', 'закрыть']:
            target = target.replace(w, '')
        target = target.strip()
        procs = {
            'хром': 'chrome', 'chrome': 'chrome', 'стим': 'steam',
            'telegram': 'telegram', 'телеграм': 'telegram',
            'discord': 'discord', 'дискорд': 'discord',
            'блокнот': 'notepad', 'проводник': 'explorer',
        }
        for name, exe in procs.items():
            if name in target and PSUTIL_OK:
                killed = 0
                for p in psutil.process_iter(['name']):
                    try:
                        if exe in p.info['name'].lower():
                            p.kill(); killed += 1
                    except Exception:
                        pass
                return f"Закрыл {killed} процессов {name}."

    if 'закрой окно' in low or 'закрой активное' in low:
        if PYAG_OK:
            pyautogui.hotkey('alt', 'f4')
        return "Окно закрыто."

    # Скриншот
    if 'скриншот' in low or 'скрин' in low:
        try:
            from PIL import ImageGrab
            d = Path(__file__).parent / 'images'
            d.mkdir(exist_ok=True)
            f = d / f"shot_{int(time.time())}.png"
            ImageGrab.grab().save(str(f))
            os.startfile(str(f))
            return f"Скриншот сохранён: {f.name}"
        except Exception as e:
            return f"Ошибка скриншота: {e}"

    # Свернуть всё
    if 'сверни все' in low or 'свернуть все' in low or 'рабочий стол' in low:
        os.system('powershell -command "(New-Object -ComObject Shell.Application).MinimizeAll()"')
        return "Свернул все окна."

    # Диагностика
    if 'диагностик' in low or ('система' in low and ('проверь' in low or 'статус' in low)):
        if PSUTIL_OK:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory().percent
            return f"Процессор: {cpu}%, память: {ram}%."
        return "Модуль диагностики недоступен."

    # Очистка корзины
    if 'очисти корзину' in low or 'очистка корзины' in low:
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0)
            return "Корзина очищена."
        except Exception:
            return "Не удалось очистить корзину."

    # Погода
    if 'погода' in low:
        try:
            r = requests.get("https://wttr.in/?format=%C+%t", timeout=10, verify=False)
            if r.status_code == 200:
                return f"Погода: {r.text.strip()}"
        except Exception:
            pass
        return "Погоду получить не удалось."

    return None


# ============================================================
# GUI
# ============================================================
class JarvisGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("J.A.R.V.I.S. — Internet Brain + JARVIS Voice")
        self.geometry("1200x800")
        self.configure(bg="#0a0a0a")
        self.voice = Voice(self)
        self.ui_queue = queue.Queue()
        self.is_speaking = False
        self.last_speech_time = 0
        self.dialogue_until = 0
        self.mic_enabled = True
        self.running = True
        self._build_ui()
        self.after(100, self._drain)
        if SPEECH_OK:
            threading.Thread(target=self._listen, daemon=True).start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._welcome()

    def _build_ui(self):
        # Верхняя панель
        top = tk.Frame(self, bg="#0a0a0a", height=60)
        top.pack(fill=tk.X)
        tk.Label(top, text="J.A.R.V.I.S.", font=("Segoe UI", 20, "bold"),
                 bg="#0a0a0a", fg="#38bdf8").pack(side=tk.LEFT, padx=20, pady=15)
        self.status = tk.Label(top, text="● ГОТОВ", font=("Segoe UI", 10, "bold"),
                                bg="#0a0a0a", fg="#10b981")
        self.status.pack(side=tk.RIGHT, padx=20)

        # Область диалога
        dialog_frame = tk.Frame(self, bg="#0a0a0a")
        dialog_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        self.chat = scrolledtext.ScrolledText(dialog_frame, font=("Consolas", 10),
                                                bg="#0f0f0f", fg="#d4d4d4",
                                                insertbackground="#38bdf8",
                                                borderwidth=0, highlightthickness=0,
                                                wrap=tk.WORD)
        self.chat.pack(fill=tk.BOTH, expand=True)
        self.chat.config(state=tk.DISABLED)

        # Поле ввода
        inp_frame = tk.Frame(self, bg="#0f0f0f", highlightbackground="#1f1f1f", highlightthickness=1)
        inp_frame.pack(fill=tk.X, padx=15, pady=(0, 10), ipady=6)

        self.entry = tk.Entry(inp_frame, font=("Segoe UI", 12), bg="#0f0f0f",
                                fg="#e0f2fe", insertbackground="#38bdf8",
                                relief=tk.FLAT, bd=0)
        self.entry.pack(fill=tk.X, padx=12, pady=6)
        self.entry.bind("<Return>", lambda e: self._send())

        # Кнопки
        btn_frame = tk.Frame(self, bg="#0a0a0a")
        btn_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        self._btn(btn_frame, "ОТПРАВИТЬ", "#2563eb", self._send)
        self._btn(btn_frame, "🎤 СЛУШАТЬ", "#059669", self._voice_input)
        self._btn(btn_frame, "🔇 МИКРОФОН", "#dc2626", self._toggle_mic)
        self._btn(btn_frame, "❓ СПРАВКА", "#475569", self._help)
        self._btn(btn_frame, "🗑 ОЧИСТИТЬ", "#7c3aed", self._clear_chat)

        self.entry.focus()

    def _btn(self, parent, text, color, cmd):
        b = tk.Button(parent, text=text, command=cmd, bg=color, fg="#fff",
                       font=("Segoe UI", 10, "bold"), relief=tk.FLAT,
                       bd=0, padx=14, pady=8, cursor="hand2")
        b.pack(side=tk.LEFT, padx=4)
        return b

    def _drain(self):
        try:
            while True:
                fn = self.ui_queue.get_nowait()
                try:
                    fn()
                except Exception:
                    pass
        except queue.Empty:
            pass
        self.after(100, self._drain)

    def _log(self, text):
        try:
            self.chat.config(state=tk.NORMAL)
            self.chat.insert(tk.END, text)
            self.chat.see(tk.END)
            self.chat.config(state=tk.DISABLED)
        except Exception:
            pass

    def _add(self, text, kind="jarvis"):
        ts = datetime.now().strftime("%H:%M:%S")
        if kind == "user":
            line = f"[{ts}] 👤 СЭР: {text}\n"
        elif kind == "jarvis":
            line = f"[{ts}] 🤖 JARVIS: {text}\n\n"
        else:
            line = f"[{ts}] {text}\n"
        self.ui_queue.put(lambda: self._log(line))

    def _send(self):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, tk.END)
        self._add(text, "user")
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text):
        # Пробуем команду ПК
        pc = execute_pc_command(text)
        if pc:
            self._add(pc, "jarvis")
            self._speak(pc)
            return

        # Иначе — мозг
        try:
            self.status.config(text="● ДУМАЮ...", fg="#f59e0b")
        except Exception:
            pass
        result = BRAIN.think(text)
        reply = result.get('reply', '').strip() or "Не могу ответить."
        self._add(reply, "jarvis")
        self._speak(reply)
        try:
            self.status.config(text="● ГОТОВ", fg="#10b981")
        except Exception:
            pass

    def _speak(self, text):
        self.is_speaking = True
        self.voice.say(text, block=True)
        self.is_speaking = False
        self.last_speech_time = time.time()
        self.dialogue_until = time.time() + 15.0

    def _voice_input(self):
        if not SPEECH_OK:
            messagebox.showerror("Ошибка", "Микрофон недоступен")
            return

        def rec():
            try:
                self.ui_queue.put(lambda: self.status.config(text="● СЛУШАЮ...", fg="#ef4444"))
                with microphone as src:
                    recognizer.adjust_for_ambient_noise(src, duration=0.4)
                    audio = recognizer.listen(src, timeout=10, phrase_time_limit=10)
                txt = recognizer.recognize_google(audio, language='ru-RU').lower().strip()
                if txt:
                    self._add(txt, "user")
                    self._process(txt)
            except Exception as e:
                log.warning("STT: %s", e)
            finally:
                self.ui_queue.put(lambda: self.status.config(text="● ГОТОВ", fg="#10b981"))

        threading.Thread(target=rec, daemon=True).start()

    def _toggle_mic(self):
        self.mic_enabled = not self.mic_enabled
        self._add(f"Микрофон {'включён' if self.mic_enabled else 'выключен'}.", "jarvis")

    def _listen(self):
        try:
            with microphone as src:
                recognizer.adjust_for_ambient_noise(src, duration=1.0)
        except Exception:
            pass
        while self.running:
            if self.is_speaking or not self.mic_enabled:
                time.sleep(0.2)
                continue
            if time.time() < self.last_speech_time + 1.5:
                time.sleep(0.1)
                continue
            try:
                with microphone as src:
                    audio = recognizer.listen(src, timeout=None, phrase_time_limit=12)
                txt = recognizer.recognize_google(audio, language='ru-RU').lower().strip()
                if not txt:
                    continue
                wake = any(v in txt for v in ['джарвис', 'jarvis', 'жарвис', 'дарвис'])
                active = time.time() < self.dialogue_until
                if wake:
                    self.voice.stop()
                    clean = txt
                    for v in ['джарвис', 'jarvis', 'жарвис', 'дарвис']:
                        clean = clean.replace(v, '')
                    clean = clean.strip()
                    if clean:
                        self._add(txt, "user")
                        self._process(clean)
                    else:
                        msg = "Слушаю вас, сэр."
                        self._add(msg, "jarvis")
                        self._speak(msg)
                elif active:
                    self._add(txt, "user")
                    self._process(txt)
            except Exception:
                time.sleep(0.1)

    def _help(self):
        h = (
"📖 СПРАВКА J.A.R.V.I.S.\n\n"
"🧠 Просто спроси что угодно — отвечу как ChatGPT\n"
"   • «Кто такой Тесла?»\n"
"   • «Объясни квантовую механику»\n"
"   • «Напиши код на Python»\n"
"   • «Сколько будет 234 * 567?»\n\n"
"🖥️ КОМАНДЫ ПК\n"
"   • «Открой хром / блокнот / стим»\n"
"   • «Закрой хром»\n"
"   • «Выключи компьютер»\n"
"   • «Спящий режим»\n"
"   • «Скриншот»\n"
"   • «Сверни все окна»\n"
"   • «Громче / тише / без звука»\n"
"   • «Погода»\n"
"   • «Диагностика»\n"
"   • «Очисти корзину»\n\n"
"🎤 АКТИВАЦИЯ\n"
"   • Скажи «Джарвис» — включится слушание\n"
"   • В течение 15 секунд можно говорить без повтора\n\n"
"🎩 Голос: ru-RU-DmitryNeural (как Пол Беттани)"
        )
        w = tk.Toplevel(self)
        w.title("Справка")
        w.geometry("600x600")
        w.configure(bg="#0a0a0a")
        t = scrolledtext.ScrolledText(w, font=("Consolas", 10), bg="#0f0f0f",
                                        fg="#d4d4d4", borderwidth=0, highlightthickness=0)
        t.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        t.insert("1.0", h)
        t.config(state=tk.DISABLED)

    def _clear_chat(self):
        self.chat.config(state=tk.NORMAL)
        self.chat.delete("1.0", tk.END)
        self.chat.config(state=tk.DISABLED)

    def _on_close(self):
        self.running = False
        try:
            self.voice.stop()
        except Exception:
            pass
        self.destroy()

    def _welcome(self):
        msg = "Все системы готовы, сэр. Чем могу помочь?"
        self._add(msg, "jarvis")
        self._speak(msg)


# ============================================================
# MAIN
# ============================================================
def main():
    if not REQUESTS_OK:
        print("❌ Установите: pip install requests")
        sys.exit(1)
    if not TK_OK:
        # CLI режим
        print("🌐 JARVIS CLI (без GUI). Введите вопрос или 'выход'.")
        while True:
            try:
                q = input("Вы: ").strip()
                if q.lower() in ('выход', 'exit', 'quit'):
                    break
                pc = execute_pc_command(q)
                if pc:
                    print(f"JARVIS: {pc}")
                    Voice().say(pc, block=True)
                    continue
                r = BRAIN.think(q)
                reply = r.get('reply', '...')
                print(f"JARVIS: {reply}")
                Voice().say(reply, block=True)
            except (KeyboardInterrupt, EOFError):
                break
        return

    app = JarvisGUI()
    app.mainloop()


if __name__ == "__main__":
    main()