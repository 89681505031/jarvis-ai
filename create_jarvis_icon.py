#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание иконки JARVIS из изображения
"""
from PIL import Image
import os

# Путь к исходному изображению (загруженному пользователем)
input_path = "images/jarvis_icon_source.png"
output_path = "images/jarvis_icon.png"

# Создаём иконку если исходное изображение существует
if os.path.exists(input_path):
    img = Image.open(input_path)
    img = img.resize((256, 256), Image.Resampling.LANCZOS)
    img.save(output_path)
    print(f"Иконка создана: {output_path}")
else:
    print(f"Исходное изображение не найдено: {input_path}")
    print("Пожалуйста, сохраните изображение как images/jarvis_icon_source.png")
