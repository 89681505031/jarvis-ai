#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Конфигурация Porcupine (Wake Word Detection)
"""

# === ВАШ API КЛЮЧ PORCUPINE ===
# Получить бесплатно: https://console.picovoice.ai/
# Бесплатно до 1000 часов в месяц
access_key = 'ВАШ_API_KLJUCH_PORCUPINE'

# === ПУТИ К КЛЮЧЕВЫМ СЛОВАМ ===
# Поместите .ppn файлы в папку config/keywords/
keyword_paths = [
    r'config\keywords\jarvis_windows.pp',  # Ключевое слово "Jarvis"
    # Можно добавить другие: r'config/keywords/alexa.pp',
]

# === НАСТРОЙКИ МИКРОФОНА ===
MICROPHONE_DEVICE_INDEX = 0  # -1 = автоматический выбор
AUDIO_FRAME_LENGTH = 512     # Не менять, устанавливается porcupine
AUDIO_SAMPLE_RATE = 16000    # Стандартный采样率
