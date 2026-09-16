#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест переключения голоса для персонажа Astra
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fish_audio_tts import init_fish_tts, FishAudioTTS

def test_astra_voice():
    """Тестирует установку голоса Astra"""
    
    print("=" * 60)
    print("🎤 ТЕСТ ГОЛОСА ASTRA")
    print("=" * 60)
    
    # Инициализация Fish Audio
    api_key = "sk-fish-D3gFp999pPGDH1kWJFyqB4k81FH4AoeEYDpLSebCZwE"
    model_id = "4c3eaacc1a0545cdb0295bfddf3e3785"
    
    print(f"\n🔑 API Key: {api_key[:20]}...")
    print(f"🎵 Model ID: {model_id}")
    
    fish_tts = init_fish_tts(api_key=api_key, model_id=model_id)
    
    if not fish_tts:
        print("❌ Ошибка: Fish TTS не инициализирован")
        return False
    
    print(f"\n✅ Fish TTS создан")
    print(f"   Available: {fish_tts.available}")
    print(f"   Enabled: {fish_tts.enabled}")
    
    # Тестируем стандартный голос
    print("\n" + "=" * 60)
    print("ТЕСТ 1: Стандартный голос")
    print("=" * 60)
    
    fish_tts.custom_voice_id = None
    print(f"Custom Voice ID: {fish_tts.custom_voice_id}")
    print(f"Reference ID будет: {fish_tts.model_id}")
    
    # Устанавливаем голос Astra
    print("\n" + "=" * 60)
    print("ТЕСТ 2: Голос Astra")
    print("=" * 60)
    
    astra_voice_id = "f6a0ee8b5fa743eca0e931405f319940"
    fish_tts.set_custom_voice_id(astra_voice_id)
    
    print(f"Custom Voice ID: {fish_tts.custom_voice_id}")
    print(f"Reference ID будет: {astra_voice_id}")
    
    # Тестируем генерацию
    print("\n" + "=" * 60)
    print("ТЕСТ 3: Генерация речи")
    print("=" * 60)
    
    test_text = "Привет! Я Astra - твой креативный ИИ-ассистент."
    print(f"Текст: {test_text}")
    
    try:
        output = "test_astra_voice.mp3"
        result = fish_tts.generate_speech(test_text, output)
        
        if result:
            print(f"\n✅ Успех! Файл создан: {result}")
            print(f"   Размер: {os.path.getsize(result)} байт")
        else:
            print(f"\n❌ Ошибка генерации")
    except Exception as e:
        print(f"\n❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 60)

if __name__ == "__main__":
    test_astra_voice()
