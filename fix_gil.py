import os

files = [
    "core/conversion.py",
    "core/editing.py",
    "core/extraction.py",
    "core/optimization.py",
    "core/page_manipulation.py",
    "core/security.py"
]

target = 'if cancel_event and cancel_event.is_set(): raise Exception("Cancelled by user")'

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if target in line:
                indent = line[:len(line) - len(line.lstrip())]
                new_lines.append(indent + 'if cancel_event:')
                new_lines.append(indent + '    if cancel_event.is_set(): raise Exception("Cancelled by user")')
                new_lines.append(indent + '    import time; time.sleep(0.005)')
            else:
                new_lines.append(line)
                
        with open(f, 'w', encoding='utf-8') as file:
            file.write('\n'.join(new_lines))
        print(f"Updated {f}")
    except Exception as e:
        print(f"Failed on {f}: {e}")
