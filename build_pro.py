#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка JARVIS PRO с системой подписки
"""

import subprocess
import os
import shutil

def build_pro():
    """Сборка JARVIS PRO"""
    
    project_dir = r'C:\Users\Пользователь\Desktop\Jarvis'
    dist_dir = os.path.join(project_dir, 'dist')
    build_dir = os.path.join(project_dir, 'build')
    
    print("=" * 70)
    print("СБОРКА JARVIS PRO С СИСТЕМОЙ ПОДПИСКИ")
    print("=" * 70)
    
    # Очищаем
    print("\n[1/4] Очистка...")
    for folder in [build_dir, os.path.join(dist_dir, 'JARVIS_PRO')]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  [OK] Удалено: {folder}")
    
    # Проверяем файлы
    print("\n[2/4] Проверка файлов...")
    required = {
        'jarvis_fixed.py': 'Основной файл',
        'subscription.py': 'Модуль подписки',
        'sounds': 'Папка sounds/',
        'images': 'Папка images/',
        'config.json': 'Конфигурация',
        'memory.json': 'Память'
    }
    
    for path, desc in required.items():
        full_path = os.path.join(project_dir, path)
        if os.path.exists(full_path):
            print(f"  [OK] {desc}")
        else:
            print(f"  [FAIL] {desc} - НЕ НАЙДЕНО!")
    
    # Сборка
    print("\n[3/4] Сборка JARVIS PRO...")
    cmd = [
        'pyinstaller',
        '--onedir',
        '--name', 'JARVIS_PRO',
        '--windowed',
        '--icon', 'jarvis_icon.ico',
        '--add-data', 'sounds;sounds',
        '--add-data', 'images;images',
        '--add-data', 'config.json;.',
        '--add-data', 'memory.json;.',
        '--add-data', 'subscription.py;.',
        '--noconfirm',
        '--clean',
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PySide2',
        '--exclude-module', 'PySide6',
        '--exclude-module', 'torch',
        '--exclude-module', 'torchvision',
        '--exclude-module', 'tensorflow',
        '--exclude-module', 'transformers',
        '--exclude-module', 'sklearn',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'selenium',
        '--exclude-module', 'IPython',
        '--exclude-module', 'jupyter',
        'jarvis_fixed.py'
    ]
    
    print("  Запуск PyInstaller...")
    print()
    
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode == 0:
        print("\n[4/4] Проверка результата...")
        output_dir = os.path.join(dist_dir, 'JARVIS_PRO')
        
        if os.path.exists(output_dir):
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
                    file_count += 1
            
            size_mb = total_size / (1024 * 1024)
            
            print("\n" + "=" * 70)
            print("JARVIS PRO СБОРКА ЗАВЕРШЕНА!")
            print("=" * 70)
            print(f"\n[INFO] Папка: {output_dir}")
            print(f"[INFO] Размер: {size_mb:.1f} МБ")
            print(f"[INFO] Файлов: {file_count}")
            print(f"\n[INFO] Включено:")
            print(f"  ✓ Система подписки (7 дней триал)")
            print(f"  ✓ Генератор ключей")
            print(f"  ✓ Окно активации с WhatsApp")
            print(f"  ✓ Все звуки и изображения")
            
            print(f"\n[INFO] ДЛЯ ПРОДАЖИ:")
            print(f"  1. Скопируйте папку JARVIS_PRO")
            print(f"  2. Отправьте покупателю")
            print(f"  3. Сгенерируйте ключ через меню (Ctrl+Shift+K)")
            print(f"  4. Отправьте ключ покупателю")
            print("=" * 70)
            
        else:
            print("\n[ERROR] Папка результата не создана")
    else:
        print("\n[ERROR] Ошибка сборки!")
    
    return result.returncode == 0

if __name__ == '__main__':
    build_pro()
