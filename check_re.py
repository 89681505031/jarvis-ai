import sys
sys.stdout.reconfigure(encoding='utf-8')
import re as regex_module

with open(r'C:\Users\Пользователь\Desktop\Jarvis\jarvis_fixed.py', 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# Search for ALL occurrences of 're' being used as module
print("=== All 're.' usages (module access) ===\n")
for i, line in enumerate(lines, 1):
    if regex_module.search(r'\bre\.(search|match|findall|sub|find|split|compile|fullmatch|IGNORECASE|DOTALL|MULTILINE)', line):
        print(f"Line {i}: {line.rstrip()}")

# Search for ALL occurrences of 're' being assigned (shadowing)
print("\n=== All 're' assignment patterns ===\n")
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if stripped.startswith('#'):
        continue
    
    # Check for re = (various patterns)
    if regex_module.search(r'\bre\s*=', line):
        print(f"Line {i}: {line.rstrip()}")
    elif regex_module.search(r'\bre\s*\+=', line):
        print(f"Line {i}: {line.rstrip()}")
    elif regex_module.search(r'\bre\s*\|=', line):
        print(f"Line {i}: {line.rstrip()}")
    elif regex_module.search(r'\bre\s*\*=', line):
        print(f"Line {i}: {line.rstrip()}")
    elif regex_module.search(r'\bre\s*\-=', line):
        print(f"Line {i}: {line.rstrip()}")

# Check for 're' in lambda or comprehension assignments
print("\n=== Lambda/comprehension with 're' ===\n")
for i, line in enumerate(lines, 1):
    if regex_module.search(r'lambda.*\bre\b', line):
        print(f"Line {i}: {line.rstrip()}")

# Check for 're' in for loops
print("\n=== For loop with 're' as target ===\n")
for i, line in enumerate(lines, 1):
    if regex_module.search(r'\bfor\s+re\s+', line):
        print(f"Line {i}: {line.rstrip()}")

# Check for 're' in with statements
print("\n=== With statement with 're' as target ===\n")
for i, line in enumerate(lines, 1):
    if regex_module.search(r'\bwith\s+.*\bre\b', line):
        print(f"Line {i}: {line.rstrip()}")

# Check for 're' in function parameters
print("\n=== Function/method with 're' as parameter ===\n")
for i, line in enumerate(lines, 1):
    if regex_module.search(r'def\s+\w+\([^)]*\bre\b', line):
        print(f"Line {i}: {line.rstrip()}")
