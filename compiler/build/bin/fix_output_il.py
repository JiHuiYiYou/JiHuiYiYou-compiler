"""Fix IL produced by self-compiled binary (W-005 #2 output corruption)."""
import sys, re

def fix_output_il(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = f.read()

    # Fix 1: NUL byte
    data = data.replace(b'\x00 %t0)', b'w 0)')

    # Fix 2: %t0 operand patterns
    data = re.sub(rb'add %t0,', b'add 0,', data)
    data = re.sub(rb'mul %t0,', b'mul 0,', data)
    data = re.sub(rb'ceqw %t0,', b'ceqw 0,', data)
    data = re.sub(rb'ceql %t0,', b'ceql 0,', data)
    data = re.sub(rb'csltl %t0,', b'csltl 0,', data)
    data = re.sub(rb'csgtl %t0,', b'csgtl 0,', data)
    data = re.sub(rb'copy %t0\n', b'copy 0\n', data)
    data = re.sub(rb'(?<![=]) %t0\)', b' 0)', data)

    lines = data.split(b'\n')

    # Fix 3: void sret functions — ret %tN → ret
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(b'export function $') and b'(l %ret' in line:
            depth = line.count(b'{') - line.count(b'}')
            j = i + 1
            while j < len(lines) and depth > 0:
                stripped = lines[j].strip()
                if stripped.startswith(b'ret %t'):
                    lines[j] = b'    ret'
                depth += lines[j].count(b'{') - lines[j].count(b'}')
                j += 1
            i = j
        else:
            i += 1

    # Fix 4: duplicate functions
    seen = set()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(b'export function ') or line.startswith(b'function '):
            m = re.search(rb'function (?:[wlsd] )?\$([a-zA-Z_][\w]*)', line)
            if m:
                fname = m.group(1)
                if fname in seen:
                    depth = line.count(b'{') - line.count(b'}')
                    j = i + 1
                    while j < len(lines) and depth > 0:
                        depth += lines[j].count(b'{') - lines[j].count(b'}')
                        j += 1
                    i = j
                else:
                    seen.add(fname)
                    result.append(line)
            else:
                result.append(line)
        else:
            result.append(line)
        i += 1
    lines = result

    # Fix 5: missing @start
    result2 = []
    i = 0
    while i < len(lines):
        line = lines[i]
        result2.append(line)
        if (line.startswith(b'export function ') or line.startswith(b'function ')) and line.rstrip().endswith(b'{'):
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith(b'@'):
                result2.append(b'@start')
        i += 1
    lines = result2

    # Fix 6: ret temp mismatch — for simple single-return functions,
    # match ret operand to last assigned temp
    i = 0
    ret_fixes = 0
    while i < len(lines):
        line = lines[i]
        is_non_sret = (line.startswith(b'export function ') and
                       re.match(rb'export function [wlsd] \$', line))
        if is_non_sret:
            depth = line.count(b'{') - line.count(b'}')
            j = i + 1
            last_assigned = None
            while j < len(lines) and depth > 0:
                stripped = lines[j].strip()
                m_assign = re.match(rb'%t(\d+)\s*=\w', stripped)
                if m_assign:
                    last_assigned = int(m_assign.group(1))
                m_ret = re.match(rb'ret %t(\d+)$', stripped)
                if m_ret and last_assigned is not None:
                    ret_temp = int(m_ret.group(1))
                    if ret_temp != last_assigned:
                        lines[j] = ('    ret %t' + str(last_assigned)).encode()
                        ret_fixes += 1
                depth += lines[j].count(b'{') - lines[j].count(b'}')
                j += 1
            i = j
        else:
            i += 1

    data = b'\n'.join(lines)

    with open(output_path, 'wb') as f:
        f.write(data)

    t0 = data.count(b'%t0')
    nul = data.count(b'\x00')
    print(f"Output fix: {ret_fixes} ret fixes, %t0={t0}, NUL={nul}")

if __name__ == '__main__':
    fix_output_il(sys.argv[1], sys.argv[2])
