#!/usr/bin/env python3
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'C:/Users/Пользователь/Desktop/Jarvis')

try:
    from jarvis_fixed import GIGACHAT_OK, GEMINI_OK
    print('✅ Инициализация прошла успешно')
    print(f'  GigaChat: {"✅ Активен" if GIGACHAT_OK else "❌ Неактивен"}')
    print(f'  Gemini: {"✅ Активен" if GEMINI_OK else "❌ Неактивен"}')
except Exception as e:
    print(f'❌ Ошибка: {e}')
    import traceback
    traceback.print_exc()
