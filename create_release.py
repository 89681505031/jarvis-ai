#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание GitHub Release с .exe файлом
"""

import os
import sys
import subprocess
from pathlib import Path

def create_release():
    print("=" * 60)
    print("СОЗДАНИЕ GITHUB RELEASE")
    print("=" * 60)
    
    # Проверяем .exe
    exe_path = Path("dist/JARVIS_PRO.exe")
    if not exe_path.exists():
        print("\n❌ JARVIS_PRO.exe не найден!")
        print("Запустите сначала: python build_exe.py")
        return False
    
    # Получаем размер
    size = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n📦 Файл: {exe_path}")
    print(f"📊 Размер: {size:.2f} MB")
    
    # Версия
    version = "2.0.0"
    
    print(f"\n🚀 Создание Release v{version}...")
    print("\nИнструкция:")
    print("1. Убедитесь что установлен gh CLI:")
    print("   pip install gh")
    print("2. Войдите в GitHub:")
    print("   gh auth login")
    print("3. Запустите этот скрипт снова")
    print("\nИли загрузите вручную через GitHub web:")
    print(f"https://github.com/89681505031/jarvis-ai/releases/new?tag=v{version}")
    
    # Пробуем через gh CLI
    try:
        result = subprocess.run(
            ['gh', 'release', 'create', f'v{version}',
             str(exe_path),
             '--title', f'JARVIS PRO v{version}',
             '--notes', f'''## JARVIS PRO v{version}

### Новые возможности:
- 🎤 Fish Audio TTS - голоса разных персонажей
- 🗣️ Vosk STT - оффлайн распознавание речи
- 🤖 Gemini AI - умный диалог
- 🔄 Автообновление при запуске
- 🎭 5 персонажей: Jarvis, Astra, Luna, Terra, Cyber

### Установка:
Просто замените старый JARVIS_PRO.exe на новый!

### Системные требования:
- Windows 10/11
- Python не нужен (.exe автономный)

### Изменения:
- Версия: {version}
- Размер: {size:.2f} MB
- Дата: {Path(__file__).parent.name}
'''],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✅ Release v{version} создан!")
            print(f"🔗 https://github.com/89681505031/jarvis-ai/releases/tag/v{version}")
            return True
        else:
            print(f"\n⚠️ gh CLI ошибка: {result.stderr}")
            print("\nЗагрузите вручную:")
            print(f"https://github.com/89681505031/jarvis-ai/releases/new?tag=v{version}")
    except FileNotFoundError:
        print("\n⚠️ gh CLI не установлен")
        print("\nЗагрузите вручную:")
        print(f"https://github.com/89681505031/jarvis-ai/releases/new?tag=v{version}")
    
    return False

if __name__ == '__main__':
    success = create_release()
    sys.exit(0 if success else 1)
