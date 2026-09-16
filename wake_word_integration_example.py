#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Пример интеграции Porcupine Wake Word в jarvis_fixed.py

Вставьте ЭТОТ КОД в jarvis_fixed.py после импортов:
"""

# === WAKE WORD INTEGRATION ===
import sys
sys.path.insert(0, '.')

from wake_word.porcupine_detector import (
    init_porcupine,
    run_wake_word_loop,
    is_listening,
    stop_listening
)
from sound.play import play

def on_wake_word_detected(keyword_index, keyword_name):
    """
    Callback при обнаружении wake word
    Вызывается когда Porcupine слышит "Jarvis"
    """
    print(f"🎯 [{keyword_name}] Обнаружено!")
    
    # Воспроизводим звук обнаружения
    play("Shazam-ON")
    
    # Здесь можно запустить голосовое управление
    # Например: start_voice_recognition()
    # Или: switch_to_listening_mode()
    
    print("🎤 Готов к команде...")
    
    # Воспроизводим звук готовности
    play("Shazam-OFF")


def start_wake_word_listener():
    """Запуск wake word детектора в фоновом потоке"""
    import threading
    
    def run_loop():
        try:
            run_wake_word_loop(callback=on_wake_word_detected)
        except Exception as e:
            print(f"❌ Ошибка wake word: {e}")
    
    # Запускаем в отдельном потоке
    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()
    print("👂 Wake word детектор запущен в фоновом режиме")


# === ИСПОЛЬЗОВАНИЕ В JARVIS: ===

# 1. В __init__ после инициализации:
#    if init_porcupine():
#        self.wake_word_enabled = True
#        start_wake_word_listener()
#    else:
#        self.wake_word_enabled = False
#        print("⚠️ Porcupine не доступен, используем speech_recognition")

# 2. В open_settings добавьте кнопку для включения/выключения:
#    ModernButton(settings_win, text="🎤 Wake Word", 
#                 command=lambda: start_wake_word_listener(),
#                 bg="#059669", fg="#fff").pack()


# === ПРОВЕРКА РАБОТОСПОСОБНОСТИ: ===
if __name__ == "__main__":
    print("=== ПРОВЕРКА WAKE WORD ===\n")
    
    # Инициализация
    if init_porcupine():
        print("✅ Porcupine инициализирован\n")
        print("🎤 Скажите 'Jarvis'...\n")
        
        # Запуск цикла
        run_wake_word_loop(callback=on_wake_word_detected)
    else:
        print("❌ Porcupine не инициализирован")
        print("   Проверьте API ключ в config/porcupine_config.py")
