#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизированная сборка JARVIS — режим ONEFILE (улучшенный)
Улучшения:
- Максимальное исключение модулей
- Оптимизация размера
- Быстрая распаковка
"""

import subprocess
import sys
import os
import shutil

def build_optimized_onefile():
    """Оптимизированная сборка в один EXE"""
    print("=" * 60)
    print("ОПТИМИЗИРОВАННАЯ СБОРКА ONEFILE")
    print("=" * 60)
    
    # Очищаем старые файлы сборки
    for folder in ['build', 'dist', 'JARVIS_optimized.spec']:
        if os.path.exists(folder):
            print(f"Удаляю: {folder}")
            if os.path.isdir(folder):
                shutil.rmtree(folder)
    
    # Команда PyInstaller с оптимизацией
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'JARVIS_Optimized',
        '--add-data', 'sounds;sounds',
        '--add-data', 'images;images',
        '--add-data', 'config.json;.',
        '--add-data', 'memory.json;.',
        '--noconsole',
        # Исключаем ВСЁ ненужное
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt5.QtWidgets',
        '--exclude-module', 'PyQt5.QtCore',
        '--exclude-module', 'PyQt5.QtGui',
        '--exclude-module', 'PySide2',
        '--exclude-module', 'PySide6',
        '--exclude-module', 'torch',
        '--exclude-module', 'torchvision',
        '--exclude-module', 'torchaudio',
        '--exclude-module', 'tensorflow',
        '--exclude-module', 'transformers',
        '--exclude-module', 'sklearn',
        '--exclude-module', 'scipy',
        '--exclude-module', 'cv2',
        '--exclude-module', 'selenium',
        '--exclude-module', 'playwright',
        '--exclude-module', 'IPython',
        '--exclude-module', 'jupyter',
        '--exclude-module', 'notebook',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'plotly',
        '--exclude-module', 'pytest',
        '--exclude-module', 'debugpy',
        '--exclude-module', 'pdb',
        '--exclude-module', 'tkinter.test',
        '--exclude-module', 'unittest',
        '--exclude-module', 'doctest',
        '--exclude-module', 'xml.etree.ElementTree.test',
        '--exclude-module', 'lib2to3',
        '--exclude-module', 'pydoc',


        '--exclude-module', 'test',
        '--exclude-module', 'tests',
        '--exclude-module', '__pycache__',
        '--exclude-module', 'typing.io',
        '--exclude-module', 'typing.re',
        '--exclude-module', 'numpy.testing',
        '--exclude-module', 'numpy.ma',
        '--exclude-module', 'scipy.testing',
        '--exclude-module', 'pkg_resources',
        '--clean',
        '--noconfirm',
        '--upx-exclude', '*.pyd',  # Не сжимать бинарники
        'jarvis_fixed.py'
    ]
    
    print(f"\nЗапуск команды:")
    print(' '.join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd='C:/Users/Пользователь/Desktop/Jarvis')
    
    if result.returncode == 0:
        print("\n[OK] Оптимизированная сборка завершена успешно!")
        exe_path = 'C:/Users/Пользователь/Desktop/Jarvis/dist/JARVIS_Optimized.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"[INFO] EXE файл: {exe_path}")
            print(f"[INFO] Размер EXE: {size_mb:.1f} МБ")
            
            # Сравнение с оригиналом
            original_path = 'C:/Users/Пользователь/Desktop/Jarvis/dist/JARVIS.exe'
            if os.path.exists(original_path):
                original_size = os.path.getsize(original_path) / (1024 * 1024)
                reduction = (1 - os.path.getsize(exe_path) / os.path.getsize(original_path)) * 100
                print(f"\n[INFO] Сравнение:")
                print(f"   Оригинал: {original_size:.1f} МБ")
                print(f"   Оптимизированный: {size_mb:.1f} МБ")
                print(f"   Сокращение: {reduction:.1f}%")
    else:
        print("\n[ERROR] Ошибка сборки.")
    
    return result.returncode == 0

if __name__ == '__main__':
    build_optimized_onefile()
