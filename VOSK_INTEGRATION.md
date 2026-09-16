# === ПОЛНАЯ ИНТЕГРАЦИЯ VOSK + PORCUPINE ===

## 🎯 Что будет работать:

1. **Porcupine** (wake word) → всегда слушает "Jarvis"
2. **Vosk** (распознавание) → распознаёт команду оффлайн
3. **Fish Audio** (TTS) → озвучивает голосом персонажа

## 📦 Установка:

```bash
# 1. Установите все зависимости
pip install vosk pvporcupine pvrecorder playsound

# 2. Скачайте модели
# - Vosk: https://github.com/alibaba-damo-academy/Vosk/releases
#   vosk-model-small-ru-0.22.zip → распакуйте в config/
# - Porcupine: https://console.picovoice.ai/
#   Получите API ключ и .ppn файл
```

## 🚀 Как использовать:

### Вариант 1: Только Vosk (без Porcupine)
```python
# Jarvis будет работать как обычно
# Говорите команды напрямую без "Jarvis"
```

### Вариант 2: Porcupine + Vosk (рекомендуется)
```python
# 1. Запустите wake word детектор
from wake_word.porcupine_detector import init_porcupine, start_wake_word_listener

if init_porcupine():
    start_wake_word_listener()

# 2. Теперь Jarvis:
#    - Всегда слушает "Jarvis" (Porcupine)
#    - Когда слышит "Jarvis" → включает микрофон
#    - Распознаёт команду (Vosk)
#    - Выполняет и отвечает (Fish Audio)
```

## ⚡ Преимущества:

| Характеристика | Без Vosk | С Vosk |
|---|---|---|
| Интернет | ✅ Нужен | ❌ Не нужен |
| Лимит Google | 50 раз/мин | Нет лимита |
| Скорость | Зависит от сети | ⚡ Быстро |
| Приватность | Данные в облако | 🔒 Полностью локально |

## 🔧 Решение проблем:

### Vosk не запускается:
```
❌ Ошибка: Model not found
✅ Решение: Распакуйте vosk-model-small-ru-0.22 в config/
```

```
❌ Ошибка: vosk not installed
✅ Решение: pip install vosk
```

### Porcupine не работает:
```
❌ Ошибка: Invalid access key
✅ Решение: Получите ключ на https://console.picovoice.ai/
```

```
❌ Ошибка: Keyword file not found
✅ Решение: Положите .ppn файл в config/keywords/
```
