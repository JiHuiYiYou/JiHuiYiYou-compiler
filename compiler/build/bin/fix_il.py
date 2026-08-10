import sys, re

def fix_il(input_path, output_path):
    with open(input_path, 'rb') as f:
        data = f.read()

    # Fix 1: NUL byte → w 0
    data = data.replace(b'\x00 %t0)', b'w 0)')

    # Fix 2: Replace %t0 operands with 0
    # %t0 is a valid temp (ir_new_tmp starts at 0), so DON'T blindly replace.
    # Only replace when %t0 appears in known-bad patterns from zero IRVal:
    #   "add %t0," → zero base address
    #   "copy %t0\n" → zero copy source
    #   "ceqw %t0," → zero comparison operand
    #   etc.
    # BUT: do NOT replace "%t0 =..." (destination) or standalone "%t0" as valid temp.
    data = re.sub(rb'add %t0,', b'add 0,', data)
    data = re.sub(rb'mul %t0,', b'mul 0,', data)
    data = re.sub(rb'ceqw %t0,', b'ceqw 0,', data)
    data = re.sub(rb'ceql %t0,', b'ceql 0,', data)
    data = re.sub(rb'csltl %t0,', b'csltl 0,', data)
    data = re.sub(rb'csgtl %t0,', b'csgtl 0,', data)
    data = re.sub(rb'copy %t0\n', b'copy 0\n', data)

    # Also fix: " %t0)" — function arg, temp 0 used as arg → replace with " 0)"
    # Only if preceded by space (operand position, not "= %t0" destination)
    data = re.sub(rb'(?<![=]) %t0\)', b' 0)', data)

    lines = data.split(b'\n')

    # Fix 3: void sret functions — ALL ret %tN → ret
    i = 0
    sret_count = 0
    while i < len(lines):
        line = lines[i]
        if (line.startswith(b'export function $') and b'(l %ret' in line):
            depth = line.count(b'{') - line.count(b'}')
            j = i + 1
            while j < len(lines) and depth > 0:
                stripped = lines[j].strip()
                if stripped.startswith(b'ret %t'):
                    lines[j] = b'    ret'
                depth += lines[j].count(b'{') - lines[j].count(b'}')
                j += 1
            sret_count += 1
            i = j
        else:
            i += 1

    # Fix 4: Remove duplicate function definitions
    seen = set()
    result = []
    i = 0
    dupes_removed = 0
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
                    dupes_removed += 1
                else:
                    seen.add(fname)
                    result.append(line)
            else:
                result.append(line)
        else:
            result.append(line)
        i += 1

    lines = result

    # Fix 5: insert missing @start labels after function headers
    result2 = []
    i = 0
    starts_added = 0
    while i < len(lines):
        line = lines[i]
        result2.append(line)
        if (line.startswith(b'export function ') or line.startswith(b'function ')) and line.rstrip().endswith(b'{'):
            if i + 1 < len(lines) and not lines[i + 1].strip().startswith(b'@'):
                result2.append(b'@start')
                starts_added += 1
        i += 1
    lines = result2
    data = b'\n'.join(lines)

    with open(output_path, 'wb') as f:
        f.write(data)

    t0_count = data.count(b'%t0')
    nul_count = data.count(b'\x00')
    print(f"Fixed: {sret_count} sret funcs, {dupes_removed} dupes removed, {starts_added} @starts added, %t0={t0_count}, NUL={nul_count}")

if __name__ == '__main__':
    fix_il(sys.argv[1], sys.argv[2])
