# 📦 Распространение JARVIS PRO

## Создание .exe файла

### 1. Сборка

```bash
python build_exe.py
```

Результат: `dist/JARVIS_PRO.exe` (347 MB)

### 2. Создание GitHub Release

**Вариант А: Через gh CLI**
```bash
pip install gh
gh auth login
python create_release.py
```

**Вариант Б: Вручную**
1. Открой: https://github.com/89681505031/jarvis-ai/releases/new?tag=v2.0.0
2. Tag: `v2.0.0`
3. Title: `JARVIS PRO v2.0.0`
4. Attach: `dist/JARVIS_PRO.exe`
5. Publish

### 3. Обновление

Когда есть новые изменения:
```bash
# Обновить код
git pull

# Собрать новый .exe
python build_exe.py

# Создать новый Release
# Версия: 2.1.0, 2.2.0 и т.д.
```

## Для пользователей

### Установка

1. Скачать `JARVIS_PRO.exe` из Releases
2. Запустить
3. Приложение само проверит обновления при запуске

### Обновление

При наличии новой версии появится окно:
- "Скачать обновление" → откроются Releases
- Заменить старый `.exe` на новый

## Структура релиза

```
JARVIS_PRO.exe          ← Автономный файл (347 MB)
```

Пользователям НЕ нужен Python!

## Версионирование

- `v2.0.0` — основной релиз
- `v2.0.1` — багфиксы
- `v2.1.0` — новые функции
