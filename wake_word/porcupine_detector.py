#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Porcupine Wake Word Detection
Обнаружение ключевого слова (например "Jarvis")
"""

import pvporcupine
from pvrecorder import PvRecorder
import logging

log = logging.getLogger("jarvis.wake_word")

# Глобальные переменные
_porcupine = None
_recorder = None
_is_listening = False
_wake_word_callback = None


def init_porcupine(access_key=None, keyword_paths=None):
    """
    Инициализация Porcupine для обнаружения wake word
    
    Args:
        access_key: API ключ от Picovoice
        keyword_paths: Список путей к .ppn файлам
    
    Returns:
        bool: True если успешно
    """
    global _porcupine, _recorder, _is_listening
    
    try:
        # Импортируем конфигурацию
        from config.porcupine_config import access_key as config_key
        from config.porcupine_config import keyword_paths as config_paths
        from config.porcupine_config import MICROPHONE_DEVICE_INDEX
        
        if access_key is None:
            access_key = config_key
        if keyword_paths is None:
            keyword_paths = config_paths
        
        if access_key == 'ВАШ_API_KLJUCH_PORCUPINE':
            log.warning("⚠️ Porcupine: Не установлен API ключ!")
            log.warning("   Получить бесплатно: https://console.picovoice.ai/")
            return False
        
        # Инициализация Porcupine
        _porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=keyword_paths
        )
        
        log.info(f"✅ Porcupine инициализирован: {len(keyword_paths)} ключевых слов")
        log.info(f"   Frame length: {_porcupine.frame_length}")
        
        # Инициализация микрофона
        device_index = MICROPHONE_DEVICE_INDEX
        if device_index == -1:
            # Автоматический выбор первого доступного микрофона
            import pvrecorder
            device_index = pvrecorder.get_audio_device_count() - 1
            if device_index < 0:
                log.error("❌ Микрофон не найден!")
                return False
        
        _recorder = PvRecorder(
            device_index=device_index,
            frame_length=_porcupine.frame_length
        )
        
        log.info(f"🎤 Микрофон подключён: устройство {device_index}")
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка инициализации Porcupine: {e}")
        return False


def start_listening(callback=None):
    """
    Запуск прослушивания микрофона для обнаружения wake word
    
    Args:
        callback: Функция, вызываемая при обнаружении ключевого слова
                 callback(keyword_index, keyword_name)
    """
    global _is_listening, _wake_word_callback
    
    if _porcupine is None or _recorder is None:
        log.error("❌ Porcupine не инициализирован!")
        return False
    
    _wake_word_callback = callback
    _is_listening = True
    
    try:
        _recorder.start()
        log.info("👂 Porcupine слушает... (скажите 'Jarvis')")
        return True
    except Exception as e:
        log.error(f"❌ Ошибка запуска микрофона: {e}")
        return False


def stop_listening():
    """Остановка прослушивания"""
    global _is_listening
    
    if _recorder is not None:
        try:
            _recorder.stop()
            log.info("🔇 Porcupine остановлен")
        except Exception as e:
            log.error(f"❌ Ошибка остановки: {e}")
    
    _is_listening = False


def process_audio_frame(audio_frame):
    """
    Обработка одного аудио фрейма
    
    Args:
        audio_frame: Аудио фрейм от микрофона
    
    Returns:
        int: Индекс обнаруженного ключевого слова или -1
    """
    if _porcupine is None:
        return -1
    
    try:
        return _porcupine.process(audio_frame)
    except Exception as e:
        log.error(f"❌ Ошибка обработки аудио: {e}")
        return -1


def run_wake_word_loop(callback=None):
    """
    Основной цикл обнаружения wake word
    
    Args:
        callback: Функция, вызываемая при обнаружении
    """
    if not start_listening(callback):
        return
    
    log.info("🎤 Ожидание 'Jarvis'...")
    
    try:
        while _is_listening:
            audio_frame = _recorder.read()
            keyword_index = process_audio_frame(audio_frame)
            
            if keyword_index >= 0:
                keyword_name = _porcupine.keywords[keyword_index]
                log.info(f"🎯 Обнаружено ключевое слово: '{keyword_name}'")
                
                if callback:
                    callback(keyword_index, keyword_name)
                
                # Пауза перед повторным прослушиванием
                import time
                time.sleep(0.5)
    
    except KeyboardInterrupt:
        log.info("⏹ Остановлено пользователем")
    
    finally:
        stop_listening()
        cleanup()


def cleanup():
    """Очистка ресурсов"""
    global _porcupine, _recorder
    
    try:
        if _recorder is not None:
            _recorder.stop()
            _recorder.delete()
    except Exception:
        pass
    
    if _porcupine is not None:
        _porcupine.delete()
    
    log.info("🧹 Ресурсы Porcupine освобождены")


def is_listening():
    """Проверить, слушает ли Porcupine"""
    return _is_listening
