with open('frontend/src/pages/Login.tsx', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'emailRegex' in line and '\\\\s' in line:
        lines[i] = '        const emailRegex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/\n'

with open('frontend/src/pages/Login.tsx', 'w', encoding='utf-8', newline='') as f:
    f.writelines(lines)

print('Email regex fixed!')
