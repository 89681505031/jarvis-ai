#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vosk Speech Recognition Module
Локальное распознавание речи без интернета
"""

import os
import sys
import threading
import queue
import logging
import time

log = logging.getLogger("jarvis.vosk")

# Глобальные переменные
_vosk_available = False
_recognizer = None
_microphone = None
_audio_queue = None
_is_recognizing = False
_recognition_callback = None


def init_vosk(model_path=None):
    """
    Инициализация Vosk для распознавания речи
    
    Args:
        model_path: Путь к модели Vosk (например 'config/vosk-model-ru-0.10')
    
    Returns:
        bool: True если успешно
    """
    global _vosk_available, _recognizer
    
    try:
        import vosk
        log.info("✅ Vosk модуль загружен")
        
        # Определяем путь к модели
        if model_path is None:
            # Пробуем стандартные пути
            # ВАЖНО: Vosk (C-библиотека) НЕ поддерживает кириллицу в путях на Windows!
            possible_paths = [
                r'C:\vosk_models\vosk-model-small-ru-0.22',  # Основной путь без кириллицы
                os.path.join(os.path.dirname(__file__), 'config', 'vosk-model-small-ru-0.22'),
                os.path.join(os.getcwd(), 'config', 'vosk-model-small-ru-0.22'),
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    log.info(f"📁 Модель Vosk найдена: {model_path}")
                    break
        
        if model_path is None:
            log.warning("⚠️ Модель Vosk не найдена!")
            log.warning("   Скачайте: https://github.com/alibaba-damo-academy/Vosk/releases")
            log.warning("   Положите в: config/vosk-model-small-ru-0.22")
            log.warning("   Используем speech_recognition как fallback")
            return False
        
        # Проверяем что путь существует
        if not os.path.exists(model_path):
            log.error(f"❌ Путь к модели не существует: {model_path}")
            return False
        
        # Проверяем что это папка
        if not os.path.isdir(model_path):
            log.error(f"❌ Путь к модели должен быть папкой: {model_path}")
            return False
        
        # Проверяем что есть нужные файлы
        required_files = ['am', 'conf']
        for req in required_files:
            req_path = os.path.join(model_path, req)
            if not os.path.exists(req_path):
                log.error(f"❌ Отсутствует required folder: {req_path}")
                return False
        
        log.info(f"✅ Модель найдена и проверена: {model_path}")
        
        # Преобразуем в абсолютный путь
        model_path = os.path.abspath(model_path)
        log.info(f"📍 Абсолютный путь: {model_path}")
        
        # Инициализация Recognizer
        # ВАЖНО: Сначала создаём объект модели, потом Recognizer!
        try:
            log.info(f"🔧 Инициализация vosk.Model...")
            
            # Сначала создаём модель
            _vosk_model = vosk.Model(model_path)
            log.info("✅ Модель загружена в память")
            
            # Потом создаём Recognizer с объектом модели
            log.info(f"🔧 Инициализация vosk.KaldiRecognizer...")
            _recognizer = vosk.KaldiRecognizer(_vosk_model, 16000)
            _vosk_available = True
            log.info("✅ Vosk инициализирован успешно!")
            log.info(f"   Модель: {model_path}")
            log.info("   Sample rate: 16000 Hz")
            return True
        except Exception as init_error:
            log.error(f"❌ Ошибка инициализации Vosk: {init_error}")
            log.error(f"   Модель: {model_path}")
            import traceback
            log.error(traceback.format_exc())
            return False
        
        log.info("✅ Vosk инициализирован успешно!")
        log.info("   Модель: русская (small)")
        log.info("  采样率: 16000 Hz")
        return True
        
    except ImportError:
        log.error("❌ Vosk не установлен!")
        log.error("   Установите: pip install vosk")
        return False
    except Exception as e:
        log.error(f"❌ Ошибка инициализации Vosk: {e}")
        return False


def start_recognition(callback=None, timeout=10):
    """
    Запуск распознавания речи
    
    Args:
        callback: Функция, вызываемая при распознавании
                 callback(text, confidence)
        timeout: Таймаут в секундах (по умолчанию 10)
    
    Returns:
        bool: True если успешно запущено
    """
    global _is_recognizing, _recognition_callback, _audio_queue
    
    if not _vosk_available or _recognizer is None:
        log.error("❌ Vosk не инициализирован!")
        return False
    
    _recognition_callback = callback
    _is_recognizing = True
    _audio_queue = queue.Queue()
    
    try:
        # Импортируем microphone
        import speech_recognition as sr
        
        # Находим микрофон
        microphone = sr.Microphone(sample_rate=16000)
        
        log.info("🎤 Распознавание речи запущено...")
        log.info(f"   Таймаут: {timeout} секунд")
        
        def recognize_loop():
            nonlocal microphone
            try:
                with microphone as source:
                    # Настраиваем на фоновый шум
                    sr.Recognizer().adjust_for_ambient_noise(source, duration=0.5)
                    log.info("🎤 Готов к записи...")
                    
                    # Записываем аудио
                    audio = sr.Recognizer().listen(source, timeout=timeout, phrase_time_limit=8)
                    
                    # Получаем сырые данные
                    raw_data = audio.get_raw_data()
                    
                    # Передаём в Vosk
                    if _recognizer.AcceptWaveform(raw_data):
                        result = _recognizer.Result()
                        text = result.get('text', '').strip()
                        confidence = result.get('confidence', 0.0)
                        
                        if text:
                            log.info(f"📝 Распознано: '{text}' (уверенность: {confidence:.2%})")
                            
                            if _recognition_callback:
                                _recognition_callback(text, confidence)
                        else:
                            log.info("⚠️ Ничего не распознано")
                    
                    # Финальный результат
                    final_result = _recognizer.FinalResult()
                    text = final_result.get('text', '').strip()
                    if text:
                        log.info(f"📝 Финальный результат: '{text}'")
                        if _recognition_callback:
                            _recognition_callback(text, 0.8)
                    
            except Exception as e:
                log.error(f"❌ Ошибка распознавания: {e}")
            finally:
                _is_recognizing = False
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=recognize_loop, daemon=True)
        thread.start()
        return True
        
    except Exception as e:
        log.error(f"❌ Ошибка запуска распознавания: {e}")
        _is_recognizing = False
        return False


def stop_recognition():
    """Остановка распознавания"""
    global _is_recognizing
    _is_recognizing = False
    log.info("🔇 Распознавание остановлено")


def is_recognizing():
    """Проверить, идёт ли распознавание"""
    return _is_recognizing


def get_vosk_status():
    """Получить статус Vosk"""
    if _vosk_available:
        return "✅ Активен"
    else:
        return "❌ Неактивен (используется speech_recognition)"


# === ИНТЕГРАЦИЯ С JARVIS ===

def create_vosk_recognizer():
    """
    Создать функцию распознавания для интеграции в Jarvis
    
    Использует Vosk если доступен, иначе speech_recognition
    """
    def recognize_command(timeout=10):
        """
        Распознаёт команду пользователя
        
        Args:
            timeout: Таймаут в секундах
        
        Returns:
            str: Распознанный текст или None
        """
        if _vosk_available and _recognizer:
            # Используем Vosk
            result = start_recognition(timeout=timeout)
            if result:
                # Ждём завершения
                time.sleep(timeout)
                # Возвращаем последний результат (упрощённо)
                return "command_from_vosk"
            else:
                return None
        else:
            # Fallback на speech_recognition
            log.info("⚠️ Vosk недоступен, используем speech_recognition")
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()
                microphone = sr.Microphone(sample_rate=16000)
                
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)
                
                text = recognizer.recognize_google(audio, language='ru-RU')
                log.info(f"📝 Распознано (Google): '{text}'")
                return text
                
            except Exception as e:
                log.error(f"❌ Ошибка распознавания: {e}")
                return None
    
    return recognize_command


# === ПРОВЕРКА РАБОТОСПОСОБНОСТИ ===

if __name__ == "__main__":
    print("=== ПРОВЕРКА VOSK ===\n")
    
    # Инициализация
    if init_vosk():
        print("✅ Vosk инициализирован\n")
        
        # Callback функция
        def on_recognized(text, confidence):
            print(f"🎤 Распознано: '{text}' (уверенность: {confidence:.2%})")
        
        print("🎤 Скажите фразу...\n")
        
        # Распознавание
        start_recognition(callback=on_recognized, timeout=10)
        
        # Ждём
        try:
            while is_recognizing():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n⏹ Остановлено")
        
        print("\n✅ Проверка завершена")
    else:
        print("❌ Vosk не инициализирован")
        print("   1. Установите: pip install vosk")
        print("   2. Скачайте модель: config/vosk-model-small-ru-0.22")
        print("   3. Проверьте путь в init_vosk()")
