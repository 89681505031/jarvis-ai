#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Тест Fish Audio TTS"""

import sys
sys.path.insert(0, '.')

from fish_audio_tts import FishAudioTTS

API_KEY = "AQ.Ab8RN6JZNmnFKgsHRnWI9-riAbXaq9-XCPQn0L1VwIeWcg1WQw"

print("=== ТЕСТ FISH AUDIO TTS ===")
print()

tts = FishAudioTTS(api_key=API_KEY, model_id="4c3eaacc1a0545cdb0295bfddf3e3785")
print(f"Enabled: {tts.enabled}")
print(f"Available: {tts.available}")
print()

if tts.available:
    print("Тестовый запрос...")
    result = tts.generate_speech("Привет, я Джарвис.", "sounds/test_fish.mp3")
    if result:
        print(f"✅ Успех! Файл: {result}")
    else:
        print("❌ Ошибка генерации")
else:
    print("❌ API недоступен")
