#!/usr/bin/env python3
import base64

key = 'MDFhMDU5YjItYjhjNy03NGJjLWI4YWUtNDg5YTVjZTQ2Mzg5OjFmMjBkMmQ2LTIzMjItNGYzYS05OGE2LTdiNzA2YWExYmYxNg=='
decoded = base64.b64decode(key).decode('utf-8')
print(f"Decoded: {decoded}")
parts = decoded.split(':')
print(f"Login: {parts[0]}")
print(f"Password: {parts[1]}")
