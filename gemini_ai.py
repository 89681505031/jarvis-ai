#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini AI Module
Модуль для работы с Google Gemini API (google.genai)
"""

import os
import json
import time
import logging
import google.genai as genai_client

# Настройка proxy для Google API
_PROXY_URL = 'http://127.0.0.1:10808'

log = logging.getLogger("jarvis.gemini")

# Глобальные переменные
_gemini_available = False
_gemini_client = None
_gemini_chat = None
_gemini_model_name = 'gemini-3.6-flash'


def init_gemini(api_key=None):
    """
    Инициализация Gemini AI
    
    Args:
        api_key: API ключ Gemini
    
    Returns:
        bool: True если успешно
    """
    global _gemini_available, _gemini_client, _gemini_model_name
    
    try:
        if not api_key:
            log.error("[ERR] Gemini API key not specified")
            return False
        
        # Инициализация клиента с proxy
        _gemini_client = genai_client.Client(
            api_key=api_key,
            http_options={'client_args': {'proxy': _PROXY_URL}}
        )
        log.info("[OK] Gemini client initialized with proxy")
        log.info(f"   API key: {api_key[:10]}...{api_key[-5:]}")
        
        # Пробуем разные модели
        model_names = ['gemini-3.6-flash', 'gemini-3.1-pro-preview', 'gemini-2.5-flash']
        
        for name in model_names:
            try:
                chat = _gemini_client.chats.create(model=name)
                # Тестовый запрос
                test_resp = chat.send_message("test")
                if test_resp.text:
                    _gemini_model_name = name
                    _gemini_available = True
                    log.info(f"[OK] Gemini initialized: {name}")
                    return True
            except Exception as e:
                log.debug(f"Model {name} unavailable: {e}")
                continue
        
        log.error("[ERR] No available Gemini model")
        return False
        
    except ImportError:
        log.error("[ERR] google-genai not installed!")
        log.error("   Install: pip install google-genai")
        return False
    except Exception as e:
        log.error(f"[ERR] Gemini init error: {e}")
        return False


def ask_gemini(user_message, history=None, system_prompt=None):
    """
    Запрос к Gemini AI с retry и fallback
    """
    global _gemini_available, _gemini_client, _gemini_chat, _gemini_model_name
    
    if not _gemini_available or _gemini_client is None:
        log.error("[ERR] Gemini not initialized")
        return None
    
    try:
        # Конфигурация модели
        config = {
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.95,
            "max_output_tokens": 1024,
        }
        
        if system_prompt:
            config["system_instruction"] = system_prompt
        
        # Восстанавливаем историю если есть
        if history and len(history) > 0:
            history_contents = []
            for msg in history[-10:]:
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    history_contents.append({"role": "user", "parts": [content]})
                elif role in ("assistant", "model"):
                    history_contents.append({"role": "model", "parts": [content]})
            
            _gemini_chat = _gemini_client.chats.create(
                model=_gemini_model_name,
                config=config,
                history=history_contents if history_contents else None
            )
        else:
            _gemini_chat = _gemini_client.chats.create(
                model=_gemini_model_name,
                config=config
            )
        
        # Retry с разными моделями при ошибке
        retry_models = ['gemini-3.6-flash', 'gemini-3.1-pro-preview', 'gemini-2.5-flash']
        
        for attempt, model in enumerate(retry_models):
            try:
                if attempt > 0:
                    log.info(f"🔄 [GEMINI] Retry #{attempt} с моделью {model}")
                    _gemini_chat = _gemini_client.chats.create(model=model, config=config)
                
                response = _gemini_chat.send_message(user_message)
                
                if response.text:
                    _gemini_model_name = model  # Запоминаем рабочую модель
                    log.info(f"[OK] Gemini responded ({model}): {len(response.text)} chars")
                    return response.text
                else:
                    log.warning("[WARN] Gemini returned empty response")
                    
            except Exception as e:
                error_str = str(e)
                log.debug(f"Retry {model} failed: {error_str[:100]}")
                last_error = e
                continue
        
        # Все модели не сработали
        log.error(f"[ERR] All Gemini models failed: {last_error}")
        return None
            
    except Exception as e:
        log.error(f"[ERR] Gemini request error: {e}")
        return None


def is_gemini_available():
    """Проверить, доступен ли Gemini"""
    return _gemini_available


def get_gemini_status():
    """Получить статус Gemini"""
    if _gemini_available:
        return f"[OK] Gemini active ({_gemini_model_name})"
    else:
        return "[ERR] Gemini inactive"


# === ИНТЕГРАЦИЯ С JARVIS ===

def create_gemini_request():
    """Создать функцию запроса для интеграции в Jarvis"""
    def request_ai(user_message, history=None, system_prompt=None):
        return ask_gemini(user_message, history=history, system_prompt=system_prompt)
    return request_ai


# === ПРОВЕРКА ===

if __name__ == "__main__":
    print("=== GEMINI TEST ===\n")
    api_key = input("Enter Gemini API key: ").strip()
    
    if init_gemini(api_key):
        print(f"[OK] Gemini initialized\n")
        test_prompt = "Ты Джарвис - ИИ-ассистент. Отвечай кратко на русском."
        test_message = "Привет! Расскажи о себе."
        
        print(f"Question: {test_message}\n")
        response = ask_gemini(test_message, system_prompt=test_prompt)
        
        if response:
            print(f"\nAnswer:\n{response}")
        else:
            print("\n[ERR] Failed to get response")
        
        print("\n[Test completed]")
    else:
        print("[ERR] Gemini not initialized")
