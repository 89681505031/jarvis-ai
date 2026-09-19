#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Оптимизированная сборка JARVIS — режим ONEDIR
Преимущества:
- Мгновенный запуск (нет распаковки)
- Меньший размер (исключаем ненужные модули)
- Легче обновлять отдельные файлы
"""

import subprocess
import sys
import os
import shutil

def build_onedir():
    """Сборка в режиме папки (быстрый запуск)"""
    print("=" * 60)
    print("СБОРКА ONEDIR — БЫСТРЫЙ ЗАПУСК")
    print("=" * 60)
    print(f"[INFO] Текущая папка: {os.getcwd()}")
    
    # Очищаем старые файлы сборки
    for folder in ['build', 'dist', 'JARVIS_onedir.spec']:
        if os.path.exists(folder):
            print(f"Удаляю: {folder}")
            if os.path.isdir(folder):
                shutil.rmtree(folder)
    
    # Команда PyInstaller с максимальной оптимизацией
    cmd = [
        'pyinstaller',
        '--onedir',
        '--name', 'JARVIS',
        '--add-data', 'sounds;sounds',
        '--add-data', 'images;images',
        '--add-data', 'config.json;.',
        '--add-data', 'memory.json;.',
        '--noconsole',
        # Исключаем тяжёлые и ненужные модули
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt5.QtWidgets',
        '--exclude-module', 'PyQt5.QtCore',
        '--exclude-module', 'PyQt5.QtGui',
        '--exclude-module', 'PySide2',
        '--exclude-module', 'PySide6',
        '--exclude-module', 'torch',
        '--exclude-module', 'torchvision',
        '--exclude-module', 'tensorflow',
        '--exclude-module', 'transformers',
        '--exclude-module', 'sklearn',
        '--exclude-module', 'scipy',
        '--exclude-module', 'PIL',  # Загрузим лениво
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
        '--exclude-module', 'encodings.cp720',
        '--exclude-module', 'encodings.cp737',
        '--exclude-module', 'encodings.cp775',
        '--exclude-module', 'encodings.cp852',
        '--exclude-module', 'encodings.cp855',
        '--exclude-module', 'encodings.cp857',
        '--exclude-module', 'encodings.cp858',
        '--exclude-module', 'encodings.cp860',
        '--exclude-module', 'encodings.cp861',
        '--exclude-module', 'encodings.cp862',
        '--exclude-module', 'encodings.cp863',
        '--exclude-module', 'encodings.cp864',
        '--exclude-module', 'encodings.cp865',
        '--exclude-module', 'encodings.cp866',
        '--exclude-module', 'encodings.cp869',
        '--exclude-module', 'encodings.cp874',
        '--exclude-module', 'encodings.cp875',
        '--exclude-module', 'encodings.cp932',
        '--exclude-module', 'encodings.cp936',
        '--exclude-module', 'encodings.cp949',
        '--exclude-module', 'encodings.cp950',
        '--exclude-module', 'encodings.euc_jp',
        '--exclude-module', 'encodings.euc_kr',
        '--exclude-module', 'encodings.gb2312',
        '--exclude-module', 'encodings.gbk',
        '--exclude-module', 'encodings.big5',
        '--exclude-module', 'encodings.koi8_r',
        '--exclude-module', 'encodings.ko_cp949',
        '--exclude-module', 'encodings.utf_8_sig',
        '--exclude-module', 'lib2to3',
        '--exclude-module', 'pydoc',
        '--clean',
        '--noconfirm',
        'jarvis_fixed.py'
    ]
    
    print(f"\nЗапуск команды:")
    print(' '.join(cmd))
    print()
    
    result = subprocess.run(cmd, cwd='C:/Users/Пользователь/Desktop/Jarvis')
    
    if result.returncode == 0:
        print("\n[OK] Сборка ONEDIR завершена успешно!")
        exe_path = 'C:/Users/Пользователь/Desktop/Jarvis/dist/JARVIS/JARVIS.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"[INFO] EXE файл: {exe_path}")
            print(f"[INFO] Размер EXE: {size_mb:.1f} МБ")
            
            dist_folder = 'C:/Users/Пользователь/Desktop/Jarvis/dist/JARVIS'
            total_size = 0
            for root, dirs, files in os.walk(dist_folder):
                for file in files:
                    total_size += os.path.getsize(os.path.join(root, file))
            print(f"[INFO] Общий размер папки: {total_size / (1024*1024):.1f} МБ")
    else:
        print("\n❌ Ошибка сборки. Проверьте команду выше.")
    
    return result.returncode == 0

if __name__ == '__main__':
    build_onedir()
