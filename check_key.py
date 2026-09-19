#!/usr/bin/env python3
import base64

key = 'MDFhMDU5YjItYjhjNy03ODRhLTk0MmItZjI2YzNmNjA4NzI0'
print(f"Key: {key}")
print(f"Length: {len(key)}")

# Проверяем base64
is_b64 = all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in key)
print(f"Is valid base64 chars: {is_b64}")

try:
    decoded = base64.b64decode(key)
    print(f"Decoded (base64): {decoded}")
    print(f"Decoded (text): {decoded.decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"Not valid base64: {e}")

# Проверяем hex
try:
    decoded_hex = bytes.fromhex(key)
    print(f"Decoded (hex): {decoded_hex}")
    print(f"Decoded (hex text): {decoded_hex.decode('utf-8', errors='replace')}")
except Exception as e:
    print(f"Not valid hex: {e}")
