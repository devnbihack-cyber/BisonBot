filepath = r'C:\Users\HP\anaconda3\envs\env_name\lib\site-packages\rasa\engine\storage\local_model_storage.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

# Find and print the extractall line so we can see exactly what it says
for i, line in enumerate(lines):
    if 'extractall' in line:
        print(f"Line {i+1}: {repr(line)}")

# Fix: replace any extractall line that uses the \\?\ prefix
fixed_lines = []
changed = False
for line in lines:
    if 'extractall' in line and '\\\\?\\\\' in line:
        # Replace the whole extractall call with a simple version
        indent = len(line) - len(line.lstrip())
        fixed_line = ' ' * indent + 'tar.extractall(temporary_directory)\n'
        fixed_lines.append(fixed_line)
        changed = True
        print(f"Fixed line: {repr(fixed_line)}")
    else:
        fixed_lines.append(line)

if changed:
    with open(filepath, 'w') as f:
        f.writelines(fixed_lines)
    print("Patched successfully!")
else:
    print("No matching line found - printing all extractall lines above for inspection.")