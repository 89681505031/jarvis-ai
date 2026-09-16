#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Создание иконки для JARVIS PRO
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_jarvis_icon(size=256):
    """Создание иконки JARVIS в стиле Iron Man"""
    
    # Создаём изображение
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Цвета
    primary_blue = (0, 150, 255)  # Синий
    dark_blue = (0, 100, 200)
    cyan = (0, 212, 255)  # Голубой неон
    dark_bg = (10, 15, 30)  # Тёмный фон
    arc_center = (size // 2, size // 2)
    radius = size // 2 - 10
    
    # Тёмный круг (фон)
    draw.ellipse([10, 10, size-10, size-10], fill=dark_bg, outline=cyan, width=4)
    
    # Дуги ARC Reactor
    arc_width = 8
    
    # Внешняя дуга (верх)
    draw.arc([20, 20, size-20, size-20], 
             start=200, end=340, 
             fill=cyan, width=arc_width)
    
    # Внешняя дуга (низ)
    draw.arc([20, 20, size-20, size-20], 
             start=20, end=160, 
             fill=cyan, width=arc_width)
    
    # Внутренняя дуга (верх)
    inner_radius = radius - 30
    draw.arc([30, 30, size-30, size-30], 
             start=220, end=320, 
             fill=primary_blue, width=6)
    
    # Внутренняя дуга (низ)
    draw.arc([30, 30, size-30, size-30], 
             start=40, end=140, 
             fill=primary_blue, width=6)
    
    # Центральный круг (ARC)
    center_radius = 35
    draw.ellipse([
        arc_center[0] - center_radius,
        arc_center[1] - center_radius,
        arc_center[0] + center_radius,
        arc_center[1] + center_radius
    ], fill=cyan, outline=primary_blue, width=3)
    
    # Внутренний круг
    inner_center = 20
    draw.ellipse([
        arc_center[0] - inner_center,
        arc_center[1] - inner_center,
        arc_center[0] + inner_center,
        arc_center[1] + inner_center
    ], fill=primary_blue)
    
    # Точки-соединения
    dot_radius = 6
    angles = [0, 60, 120, 180, 240, 300]
    for angle in angles:
        import math
        rad = math.radians(angle)
        x = arc_center[0] + int((radius - 15) * math.cos(rad))
        y = arc_center[1] + int((radius - 15) * math.sin(rad))
        draw.ellipse([x-dot_radius, y-dot_radius, x+dot_radius, y+dot_radius], 
                     fill=cyan)
    
    # Сохраняем иконку
    icon_path = os.path.join(os.path.dirname(__file__), 'jarvis_icon.ico')
    img.save(icon_path, 'ico')
    
    print(f"[OK] Иконка создана: {icon_path}")
    print(f"[OK] Размер: {size}x{size}")
    
    return icon_path

if __name__ == '__main__':
    create_jarvis_icon()
