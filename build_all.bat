@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo J.A.R.V.I.S. - ОПТИМИЗАЦИЯ СБОРКИ
echo ============================================================
echo.

:menu
echo ВЫБЕРИТЕ ВАРИАНТ СБОРКИ:
echo.
echo [1] Оптимизированная ONEFILE (маленький размер)
echo [2] Быстрый ONEDIR (мгновенный запуск)
echo [3] ОБЕ сборки сразу
echo [4] Только оптимизировать импорты
echo [Q] Выход
echo.
set /p choice="Ваш выбор: "

if /i "%choice%"=="1" (
    echo.
    echo СБОРКА ONEFILE...
    python build_optimized.py
) else if /i "%choice%"=="2" (
    echo.
    СБОРКА ONEDIR...
    python build_onedir.py
) else if /i "%choice%"=="3" (
    echo.
    echo ============================================
    echo ШАГ 1: Оптимизация импортов
    echo ============================================
    python optimize_imports.py
    echo.
    echo ============================================
    echo ШАГ 2: Сборка ONEFILE
    echo ============================================
    python build_optimized.py
    echo.
    echo ============================================
    echo ШАГ 3: Сборка ONEDIR
    echo ============================================
    python build_onedir.py
) else if /i "%choice%"=="4" (
    echo.
    echo ОПТИМИЗАЦИЯ ИМПОРТОВ...
    python optimize_imports.py
) else if /i "%choice%"=="Q" (
    exit /b
) else (
    echo.
    echo ❌ Неверный выбор!
    goto :menu
)

echo.
echo ============================================================
echo ГОТОВО!
echo ============================================================
echo.
echo Файлы сборки:
echo   - C:\Users\Пользователь\Desktop\Jarvis\dist\
echo.
echo JARVIS.exe - оригинальная сборка (2.5 ГБ)
echo JARVIS_Optimized.exe - оптимизированная ONEFILE
echo JARVIS\ (папка) - сборка ONEDIR для быстрого запуска
echo.
pause
goto :menu
