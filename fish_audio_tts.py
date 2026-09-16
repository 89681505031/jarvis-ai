#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
J.A.R.V.I.S. - Fish.TTS Voice Converter
Использует fish.audio API для генерации речи голосом Джарвиса
"""

import logging
import requests
import time
import os

log = logging.getLogger("jarvis.fish_audio")

# === PROXY НАСТРОЙКИ ===
_PROXY_URL = os.environ.get('HTTP_PROXY', os.environ.get('HTTPS_PROXY', ''))
if not _PROXY_URL:
    _PROXY_URL = 'http://127.0.0.1:10808'  # Fallback proxy

_proxy_available = None  # Будет проверено при первом использовании

def _get_proxies():
    """Возвращает словарь прокси или None для прямого подключения"""
    global _proxy_available
    
    # Если уже проверили — возвращаем результат
    if _proxy_available is not None:
        if _proxy_available:
            return {'http': _PROXY_URL, 'https': _PROXY_URL}
        return None
    
    # Пробуем проверить proxy
    try:
        import requests as req
        r = req.get('https://api.fish.audio', timeout=5, proxies={'http': _PROXY_URL, 'https': _PROXY_URL}, verify=False)
        _proxy_available = True
        log.info(f"✅ Proxy доступен: {_PROXY_URL}")
        return {'http': _PROXY_URL, 'https': _PROXY_URL}
    except Exception as e:
        log.warning(f"⚠️ Proxy недоступен, используется прямое подключение")
        _proxy_available = False
        return None

# Глобальные переменные
_fish_api_key = ""
_fish_enabled = False
_fish_model_id = "jarvis"  # ID модели голоса

class FishAudioTTS:
    """
    Text-to-Speech через fish.audio API
    Генерирует речь с клонированием голоса
    """
    
    def __init__(self, api_key="", model_id="jarvis"):
        """
        Args:
            api_key: API ключ от fish.audio
            model_id: ID модели голоса (например "jarvis", "ironman")
        """
        self.api_key = api_key
        self.model_id = model_id
        self.enabled = False
        self.available = False
        self.base_url = "https://api.fish.audio"
        self.custom_voice_id = None  # Кастомный ID голоса для персонажей
        
        if api_key:
            self.test_connection()
        
        log.info(f"FishAudioTTS инициализирован: model={model_id}")
    
    def test_connection(self):
        """Проверить подключение к fish.audio API"""
        if not self.api_key:
            log.warning("API ключ не установлен")
            return False
        
        try:
            # Пробуем разные endpoints
            endpoints = [
                (f"{self.base_url}/v1/tts", "POST"),
                (f"{self.base_url}/tts", "POST"),
                (f"{self.base_url}/api/tts", "POST"),
                (f"{self.base_url}/voice/synthesize", "POST"),
            ]
            
            for endpoint, method in endpoints:
                try:
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    
                    proxies = _get_proxies()
                    
                    if method == "POST":
                        response = requests.post(
                            endpoint,
                            headers=headers,
                            json={"text": "test", "reference_id": self.model_id},
                            timeout=10,
                            proxies=proxies,
                            verify=False
                        )
                    else:
                        response = requests.get(endpoint, headers=headers, timeout=10, proxies=proxies, verify=False)
                    
                    # Если получили любой ответ (не timeout/connection error) - ключ работает
                    if response.status_code in [200, 400, 401, 403, 404, 422, 429]:
                        if response.status_code == 200:
                            self.available = True
                            self.enabled = True
                            log.info("fish.audio API доступен!")
                            return True
                        elif response.status_code == 401 or response.status_code == 403:
                            log.error("Неверный API ключ fish.audio")
                            self.available = False
                            return False
                        else:
                            # 400, 404, 422, 429 - ключ работает, просто неверный формат запроса
                            self.available = True
                            self.enabled = True
                            log.info(f"fish.audio API доступен! (status: {response.status_code})")
                            return True
                except Exception as e:
                    log.debug(f"Endpoint {endpoint} ошибка: {e}")
                    continue
            
            log.error("Все endpoints fish.audio недоступны")
            self.available = False
        except Exception as e:
            log.error(f"Ошибка подключения к fish.audio: {e}")
            self.available = False
        
        return False
    
    def generate_speech(self, text, output_path=None, reference_audio=None, whisper=False):
        """
        Сгенерировать речь через fish.audio
        
        Args:
            text: Текст для озвучки
            output_path: Путь к выходному файлу (опционально)
            reference_audio: Путь к референсному аудио (опционально)
            whisper: Режим шепота (тихий голос)
            
        Returns:
            str: Путь к сгенерированному файлу или None
        """
        if not self.available:
            log.error("fish.audio API недоступен")
            return None
        
        if not self.api_key:
            log.error("API ключ не установлен")
            return None
        
        try:
            # Подготавливаем путь к выходному файлу
            if output_path is None:
                from pathlib import Path
                timestamp = int(time.time() * 1000)
                output_path = f"sounds/temp_fish_{timestamp}.mp3"
            
            # Формируем запрос - используем кастомный голос если установлен
            reference_id = self.custom_voice_id if self.custom_voice_id else self.model_id
            
            log.info(f"🎤 [FISH API] reference_id: {reference_id}")
            log.info(f"🎤 [FISH API] custom_voice_id: {self.custom_voice_id}")
            log.info(f"🎤 [FISH API] model_id: {self.model_id}")
            
            data = {
                "text": text,
                "reference_id": reference_id,
                "format": "mp3",
            }
            
            # === РЕЖИМ ШЕПОТА ===
            if whisper:
                # Добавляем инструкцию для тихого голоса
                whisper_prefix = "[whispering] "
                data["text"] = whisper_prefix + text
                log.info("🤫 Fish Audio: генерация тихого голоса (шепот)...")
            else:
                log.info(f"Отправка запроса к fish.audio: {text[:50]}...")
            
            proxies = _get_proxies()
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "model": "s2.1-pro-free",  # Модель как header
            }
            
            response = requests.post(
                f"{self.base_url}/v1/tts",
                headers=headers,
                json=data,
                timeout=60,
                proxies=proxies,
                verify=False
            )
            
            if response.status_code == 200:
                # fish.audio возвращает аудиофайл
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                log.info(f"Речь сгенерирована: {output_path}")
                return output_path
            elif response.status_code == 401:
                log.error("Неверный API ключ fish.audio")
            elif response.status_code == 429:
                log.error("Превышен лимит запросов fish.audio")
            else:
                log.error(f"Ошибка генерации: {response.status_code} - {response.text[:300]}")
                return None
            
        except Exception as e:
            log.error(f"Ошибка при генерации speech: {e}")
            return None
    
    def list_models(self):
        """Получить список доступных моделей голоса"""
        if not self.api_key:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.base_url}/model",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                log.info(f"Доступные модели: {models}")
                return models
        except Exception as e:
            log.error(f"Ошибка получения моделей: {e}")
        
        return []
    
    def set_api_key(self, api_key):
        """Установить API ключ"""
        self.api_key = api_key
        return self.test_connection()
    
    def set_model(self, model_id):
        """Установить модель голоса"""
        self.model_id = model_id
        log.info(f"Модель голоса установлена: {model_id}")
        return True
    
    def set_custom_voice_id(self, voice_id):
        """Установить кастомный ID голоса для персонажа"""
        if voice_id:
            self.custom_voice_id = voice_id
            log.info(f"🎤 Кастомный голос установлен: {voice_id}")
            return True
        else:
            self.custom_voice_id = None
            log.info("Кастомный голос удалён")
            return True


# Глобальный экземпляр
_fish_tts = None


def init_fish_tts(api_key="", model_id="jarvis"):
    """Инициализация глобального TTS через fish.audio"""
    global _fish_tts
    _fish_tts = FishAudioTTS(api_key=api_key, model_id=model_id)
    return _fish_tts


def get_fish_tts():
    """Получить глобальный TTS"""
    return _fish_tts


def fish_enabled():
    """Проверить, включён ли fish.audio"""
    global _fish_tts
    return _fish_tts is not None and _fish_tts.enabled


# Экспорт
FISH_AUDIO_OK = False
try:
    import requests
    FISH_AUDIO_OK = True
    log.info("FishAudio модуль загружен")
except ImportError:
    FISH_AUDIO_OK = False
    log.warning("requests не доступен, FishAudio будет недоступен")
