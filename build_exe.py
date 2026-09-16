#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка JARVIS PRO в .exe через PyInstaller
Автоматически собирает всё в один файл
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_exe():
    print("=" * 60)
    print("J.A.R.V.I.S. PRO - Сборка EXE")
    print("=" * 60)
    
    base_dir = Path(__file__).parent
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"
    spec_file = base_dir / "jarvis_pro.spec"
    
    # Очищаем старые файлы сборки
    print("\n[1/4] Очистка старых файлов сборки...")
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if spec_file.exists():
        spec_file.unlink()
    
    # Создаём spec файл
    print("[2/4] Создание spec файла...")
    spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['jarvis_fixed.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config/vosk-model-small-ru-0.22', 'config/vosk-model-small-ru-0.22'),
        ('sounds', 'sounds'),
        ('templates', 'templates'),
        ('jarvis_icon.ico', '.'),
        ('C:\\Program Files\\WindowsApps\\PythonSoftwareFoundation.Python.3.13_3.13.3824.0_x64__qbz5n2kfra8p0\\Lib\\tkinter', 'tkinter'),
    ],
    hiddenimports=[
        'vosk',
        'edge_tts',
        'google.genai',
        'pyttsx3',
        'pygame',
        'psutil',
        'PIL',
        'docx',
        'pyautogui',
        'comtypes',
        'win32gui',
        'win32con',
        'win32api',
        'requests',
        'fish_audio_tts',
        'gemini_ai',
        'vosk_recognition',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'notebook',
        'test',
        'docs',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='JARVIS_PRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,   # Показать консоль для отладки
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='jarvis_icon.ico',
)
'''
    
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Запускаем PyInstaller
    print("\n[3/4] Сборка .exe файла...")
    print("=" * 60)
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    result = subprocess.run(cmd, cwd=base_dir)
    
    if result.returncode != 0:
        print("\n❌ Ошибка сборки!")
        return False
    
    # Проверяем результат
    exe_path = dist_dir / 'JARVIS_PRO' / 'JARVIS_PRO.exe'
    
    if exe_path.exists():
        file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print("\n" + "=" * 60)
        print("УСПЕШНО! Сборка завершена.")
        print("=" * 60)
        print(f"\nФайл: {exe_path}")
        print(f"Размер: {file_size:.2f} MB")
        print("=" * 60)
        print("\nСтруктура dist/:")
        print("   dist/JARVIS_PRO/")
        print("   ├── JARVIS_PRO.exe  <- Основной файл")
        print("   └── _internal/      <- Зависимости")
        print("\nГотово к распространению!")
        return True
    else:
        print("\n❌ .exe файл не найден!")
        return False

if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1)
