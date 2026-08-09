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

    # Fix 7: repair corrupted QBE type chars in instructions
    # W-005 #2 corrupts the qbe_type byte after "=" in "%tN =X op ..."
    valid_types = {ord('w'), ord('l'), ord('s'), ord('d'), ord('b'), ord('h')}
    type_fixes = 0
    for i in range(len(lines)):
        line = lines[i]
        # Match: "    %tN =X ..." where X is the result type
        m = re.match(rb'(    %t\d+ =)(.)(.+)', line)
        if m:
            prefix = m.group(1)
            type_byte = m.group(2)
            rest = m.group(3)
            if type_byte[0] not in valid_types:
                # Determine correct type from instruction
                rest_stripped = rest.lstrip()
                if rest_stripped.startswith(b'copy'):
                    new_type = b'w'
                elif rest_stripped.startswith(b'loadw') or rest_stripped.startswith(b'storew'):
                    new_type = b'w'
                elif rest_stripped.startswith(b'loadl') or rest_stripped.startswith(b'storel'):
                    new_type = b'l'
                elif rest_stripped.startswith(b'loads') or rest_stripped.startswith(b'stores'):
                    new_type = b's'
                elif rest_stripped.startswith(b'loadd') or rest_stripped.startswith(b'stored'):
                    new_type = b'd'
                elif rest_stripped.startswith(b'ceqw') or rest_stripped.startswith(b'csltw') or rest_stripped.startswith(b'cultw'):
                    new_type = b'w'
                elif rest_stripped.startswith(b'ceql') or rest_stripped.startswith(b'csltl') or rest_stripped.startswith(b'cultl') or rest_stripped.startswith(b'csgtl'):
                    new_type = b'l'
                elif rest_stripped.startswith(b'alloc'):
                    new_type = b'l'
                elif rest_stripped.startswith(b'call') or rest_stripped.startswith(b'phi'):
                    new_type = b'w'
                elif rest_stripped.startswith(b'extsw') or rest_stripped.startswith(b'extsb') or rest_stripped.startswith(b'extsh'):
                    new_type = b'l'
                elif rest_stripped.startswith(b'add') or rest_stripped.startswith(b'sub') or rest_stripped.startswith(b'mul') or rest_stripped.startswith(b'div'):
                    new_type = b'w'
                else:
                    new_type = b'w'  # default
                lines[i] = prefix + new_type + rest
                type_fixes += 1

    # Fix 8: SSA-like temp dedup + renumbering
    # W-005 #2 can assign same corrupted temp ID to different values.
    # First pass: find duplicate definitions and split them into unique temps.
    import re as re2
    seen_defs = {}  # old_id → first_def_line
    dupe_splits = []  # (line_idx, old_id, new_unique_id)
    next_new_id = 1000000  # high sentinel to avoid collisions
    for i in range(len(lines)):
        m_def = re2.match(rb'    %t(\d+) =', lines[i])
        if m_def:
            tid = int(m_def.group(1))
            if tid in seen_defs:
                # Duplicate definition — give it a new unique ID
                dupe_splits.append((i, tid, next_new_id))
                next_new_id += 1
            else:
                seen_defs[tid] = i

    # Apply duplicate splits: rename the duplicate definition + all refs after it
    # until the temp is redefined again
    for line_idx, old_id, new_id in dupe_splits:
        # Rename the definition
        lines[line_idx] = re2.sub(
            rb'    %t' + str(old_id).encode() + rb' =',
            ('    %t' + str(new_id) + ' =').encode(),
            lines[line_idx]
        )
        # Rename subsequent uses until next redefinition of this old_id
        for j in range(line_idx + 1, len(lines)):
            # Stop at next redefinition of old_id
            if re2.match(rb'    %t' + str(old_id).encode() + rb' =', lines[j]):
                break
            # Replace all references to old_id with new_id
            lines[j] = re2.sub(
                rb'%t' + str(old_id).encode() + rb'\b',
                ('%t' + str(new_id)).encode(),
                lines[j]
            )

    # Now renumber all temps sequentially
    all_temps = set()
    def_order = []
    for line in lines:
        m_def = re2.match(rb'    %t(\d+) =', line)
        if m_def:
            tid = int(m_def.group(1))
            if tid not in all_temps:
                all_temps.add(tid)
                def_order.append(tid)
        for m_ref in re2.finditer(rb'%t(\d+)', line):
            all_temps.add(int(m_ref.group(1)))

    renum = {}
    next_id = 0
    for old_id in def_order:
        renum[old_id] = next_id
        next_id += 1
    for old_id in sorted(all_temps):
        if old_id not in renum:
            renum[old_id] = next_id
            next_id += 1

    def replace_temp(m):
        old_id = int(m.group(1))
        return ('%t' + str(renum.get(old_id, old_id))).encode()

    for i in range(len(lines)):
        lines[i] = re2.sub(rb'%t(\d+)', replace_temp, lines[i])

    renum_count = len(renum)
    data = b'\n'.join(lines)

    with open(output_path, 'wb') as f:
        f.write(data)

    t0 = data.count(b'%t0')
    nul = data.count(b'\x00')
    print(f"Output fix: {ret_fixes} ret fixes, {type_fixes} type fixes, {renum_count} temps renumbered, %t0={t0}, NUL={nul}")

if __name__ == '__main__':
    fix_output_il(sys.argv[1], sys.argv[2])
