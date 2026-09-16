#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка JARVIS со всеми зависимостями
"""

import subprocess
import os
import shutil

def build_complete():
    """Полная сборка со всеми зависимостями"""
    
    project_dir = r'C:\Users\Пользователь\Desktop\Jarvis'
    dist_dir = os.path.join(project_dir, 'dist')
    build_dir = os.path.join(project_dir, 'build')
    
    print("=" * 70)
    print("ПОЛНАЯ СБОРКА JARVIS СО ВСЕМИ ЗАВИСИМОСТЯМИ")
    print("=" * 70)
    
    # Очищаем старые файлы
    print("\n[1/4] Очистка старых файлов...")
    for folder in [build_dir, os.path.join(dist_dir, 'JARVIS_Full')]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"  [OK] Удалено: {folder}")
    
    # Проверяем что все файлы на месте
    print("\n[2/4] Проверка файлов...")
    required_files = {
        'jarvis_fixed.py': 'Основной файл',
        'sounds': 'Папка sounds/',
        'images': 'Папка images/',
        'config.json': 'Конфигурация',
        'memory.json': 'Память'
    }
    
    for path, desc in required_files.items():
        full_path = os.path.join(project_dir, path)
        if os.path.exists(full_path):
            print(f"  [OK] {desc}: {path}")
        else:
            print(f"  [FAIL] {desc}: {path} - НЕ НАЙДЕНО!")
    
    # Команда сборки
    print("\n[3/4] Сборка...")
    cmd = [
        'pyinstaller',
        '--onedir',
        '--name', 'JARVIS_Full',
        '--windowed',
        '--add-data', 'sounds;sounds',
        '--add-data', 'images;images',
        '--add-data', 'config.json;.',
        '--add-data', 'memory.json;.',
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
        output_dir = os.path.join(dist_dir, 'JARVIS_Full')
        
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
            print("СБОРКА ЗАВЕРШЕНА!")
            print("=" * 70)
            print(f"\n[INFO] Папка: {output_dir}")
            print(f"[INFO] Размер: {size_mb:.1f} МБ")
            print(f"[INFO] Файлов: {file_count}")
            print(f"\n[INFO] Содержимое:")
            
            for item in ['JARVIS_Full.exe', 'sounds', 'images', 'config.json', 'memory.json']:
                item_path = os.path.join(output_dir, item)
                if os.path.exists(item_path):
                    if os.path.isdir(item_path):
                        print(f"  [OK] {item}/ (папка)")
                    else:
                        print(f"  [OK] {item}")
            
            print(f"\n[INFO] ДЛЯ УСТАНОВКИ НА ДРУГОЙ ПК:")
            print(f"  1. Скопируйте ВСЮ папку: {output_dir}")
            print(f"  2. На другом ПК: запустите JARVIS_Full.exe")
            print("=" * 70)
            
        else:
            print("\n[ERROR] Папка результата не создана")
    else:
        print("\n[ERROR] Ошибка сборки!")
    
    return result.returncode == 0

if __name__ == '__main__':
    build_complete()
