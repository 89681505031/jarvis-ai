#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Гибридный AI модуль для JARVIS
Приоритет: GigaChat (основной) → Gemini (резервный)
Автоматическое переключение при недоступности
"""

import os
import time
import logging

log = logging.getLogger("jarvis.hybrid_ai")

# Глобальные настройки
GIGACHAT_ENABLED = False
GEMINI_ENABLED = False
AI_PRIORITY = "gigachat"  # "gigachat", "gemini", "auto"

def hybrid_ask(user_message, history=None, system_prompt=None):
    """
    Гибридный запрос к AI с автоматическим fallback
    
    Приоритет:
    1. GigaChat (основной - лучший для русского языка)
    2. Gemini (резервный - бесплатный)
    
    Args:
        user_message: текст вопроса
        history: история диалога
        system_prompt: системный промпт
        
    Returns:
        str: ответ AI или None если оба недоступны
    """
    global GIGACHAT_ENABLED, GEMINI_ENABLED
    
    # Попытка 1: GigaChat (если включён)
    if AI_PRIORITY == "gigachat" and GIGACHAT_ENABLED:
        try:
            log.info("🔄 [HYBRID] Пробуем GigaChat...")
            from jarvis_fixed import JarvisUltimate
            # Создаём временный экземпляр только для запроса
            # Используем функцию ask_gigachat напрямую
            import sys
            jarvis_path = os.path.dirname(os.path.abspath(__file__))
            sys.path.insert(0, jarvis_path)
            
            # Импортируем функцию GigaChat
            try:
                from jarvis_fixed import _gigachat_request
                response = _gigachat_request(user_message, system_prompt)
                if response:
                    log.info(f"✅ [HYBRID] GigaChat ответил: {len(response)} символов")
                    return response
            except ImportError:
                log.warning("⚠️ [HYBRID] Функция _gigachat_request не найдена")
            except Exception as e:
                log.warning(f"⚠️ [HYBRID] GigaChat ошибка: {e}")
        except Exception as e:
            log.debug(f"[HYBRID] GigaChat ошибка: {e}")
    
    # Попытка 2: Gemini (если GigaChat не сработал или отключён)
    if GEMINI_ENABLED:
        try:
            log.info("🔄 [HYBRID] Пробуем Gemini...")
            from gemini_ai import ask_gemini
            response = ask_gemini(user_message, history=history, system_prompt=system_prompt)
            if response:
                log.info(f"✅ [HYBRID] Gemini ответил: {len(response)} символов")
                return response
        except Exception as e:
            log.warning(f"⚠️ [HYBRID] Gemini ошибка: {e}")
    
    # Оба не сработали
    log.error("❌ [HYBRID] Оба AI недоступны!")
    return "Извините, я сейчас недоступен. Проверьте подключение к интернету или попробуйте позже."

def set_ai_priority(priority):
    """
    Установить приоритет AI
    
    Args:
        priority: "gigachat", "gemini", "auto"
    """
    global AI_PRIORITY
    AI_PRIORITY = priority
    log.info(f"🔄 [HYBRID] Приоритет AI установлен: {priority}")

def get_ai_status():
    """Получить статус AI систем"""
    status = "🤖 [HYBRID AI STATUS]\n"
    status += f"  Приоритет: {AI_PRIORITY}\n"
    status += f"  GigaChat: {'✅ Активен' if GIGACHAT_ENABLED else '❌ Неактивен'}\n"
    status += f"  Gemini: {'✅ Активен' if GEMINI_ENABLED else '❌ Неактивен'}\n"
    return status
