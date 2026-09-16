#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тест скорости запуска JARVIS
"""

import subprocess
import time
import os

def test_launch_speed(exe_path, name):
    """Тестирует скорость запуска"""
    if not os.path.exists(exe_path):
        print(f"[SKIP] {name}: Файл не найден - {exe_path}")
        return
    
    size_mb = os.path.getsize(exe_path) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"ТЕСТ: {name}")
    print(f"{'='*60}")
    print(f"Путь: {exe_path}")
    print(f"Размер: {size_mb:.2f} МБ")
    
    # Запускаем и измеряем время
    print(f"\nЗапуск...")
    start = time.time()
    
    try:
        # Запускаем с замером времени
        proc = subprocess.Popen(
            [exe_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Ждём немного и завершаем
        time.sleep(3)
        proc.terminate()
        proc.wait(timeout=5)
        
        elapsed = time.time() - start
        print(f"Время запуска и инициализации: {elapsed:.2f} сек")
        
    except Exception as e:
        print(f"[ERROR] Ошибка теста: {e}")
        elapsed = -1

if __name__ == '__main__':
    base = r'C:\Users\Пользователь\Desktop\Jarvis\dist'
    
    print("=" * 60)
    print("ТЕСТ СКОРОСТИ ЗАПУСКА JARVIS")
    print("=" * 60)
    
    # Тестируем ONEDIR версию
    test_launch_speed(
        os.path.join(base, 'JARVIS', 'JARVIS.exe'),
        "JARVIS ONEDIR (быстрый запуск)"
    )
    
    print(f"\n{'='*60}")
    print("РЕЗУЛЬТАТЫ:")
    print(f"{'='*60}")
    
    # Показываем размер папки
    jarvis_folder = os.path.join(base, 'JARVIS')
    if os.path.exists(jarvis_folder):
        total_size = 0
        count = 0
        for root, dirs, files in os.walk(jarvis_folder):
            for file in files:
                total_size += os.path.getsize(os.path.join(root, file))
                count += 1
        print(f"\n[INFO] JARVIS ONEDIR:")
        print(f"  Размер: {total_size / (1024*1024):.2f} МБ")
        print(f"  Файлов: {count}")
        print(f"  Путь: {jarvis_folder}")
