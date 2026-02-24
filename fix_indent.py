import sys

def fix():
    with open('automaton/apply_jobs.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open('automaton/apply_jobs.py', 'w', encoding='utf-8') as f:
        for i in range(len(lines)):
            if 664 <= i < 914 and lines[i].strip(): # lines are 0-indexed, so 0 to 913
                f.write('    ' + lines[i])
            else:
                f.write(lines[i])

if __name__ == "__main__":
    fix()
    print("Fixed!")
