# === НАСТРОЙКА WAKE WORD (PORCUPINE) ===

# 1. ПОЛУЧИТЕ API КЛЮЧ:
#    Перейдите на https://console.picovoice.ai/
#    Зарегистрируйтесь и получите API ключ (бесплатно до 1000 часов/мес)

# 2. СКАЧАЙТЕ КЛЮЧЕВОЕ СЛОВО:
#    Перейдите на https://console.picovoice.ai/
#    Выберите "Keywords" → "Build" → "English/Russian"
#    Скачайте модель "Jarvis" или создайте свою
#    Файл будет иметь расширение .ppn

# 3. РАЗМЕСТИТЕ ФАЙЛЫ:
#    Положите .ppn файл в папку:
#    C:/Users/Пользователь/Desktop/Jarvis/config/keywords/jarvis_windows.pp

# 4. ОТРЕДАКТИРУЙТЕ КОНФИГ:
#    Файл: C:/Users/Пользователь/Desktop/Jarvis/config/porcupine_config.py
#    Замените 'ВАШ_API_KLJUCH_PORCUPINE' на ваш реальный ключ
#    Укажите правильный путь к .ppn файлу

# 5. УСТАНОВИТЕ ЗАВИСИМОСТИ:
#    pip install pvporcupine pvrecorder playsound

# 6. ПРОТЕСТИРУЙТЕ:
#    python -c "from wake_word.porcupine_detector import init_porcupine; print('OK' if init_porcupine() else 'FAIL')"
