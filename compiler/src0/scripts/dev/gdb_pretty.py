"""JHYY gdb pretty printer (v1.4.3).

Reads .jhyy source to register type layouts (struct / enum / slice),
then pretty-prints values at addresses via the `jhyy-pretty` command.
Also auto-registers a pretty-printer for any DWARF-typed variable that
matches a registered jhyy type name (limited use — jhyy codegen doesn't
emit type DWARF, so this only fires for cross-language interop).

Usage:
    gdb ./foo.exe                                  # auto-sources via .gdbinit
    (gdb) jhyy-load-types path/to/foo.jhyy
    (gdb) b foo.jhyy:42
    (gdb) r
    (gdb) jhyy-pretty $rbp-72 Point
    (gdb) jhyy-pretty $rsp+8  Color
    (gdb) jhyy-pretty $rsp+16 [*]i32

ABI layouts (per docs/abis/jhyy-abi-v1.0.0.md):
  struct (§ 2.5): aligned fields, max_align tail pad
  enum   (§ 2.6): i32 tag at 0, payload at align_up(4, max_payload_align)
  slice  (§ 2.3): *T (8B) at 0, u64 len at 8
"""
import re
import gdb
import gdb.printing

# type registry: name -> dict (kind=struct|enum|slice, plus layout)
_types = {}

_PRIM = {  # name -> (size, fmt letter for gdb `x` cmd)
    'i8': (1, 'b'), 'u8': (1, 'B'), 'bool': (1, 'B'), 'char': (1, 'c'),
    'i16': (2, 'h'), 'u16': (2, 'H'),
    'i32': (4, 'i'), 'u32': (4, 'I'), 'f32': (4, 'f'),
    'i64': (8, 'q'), 'u64': (8, 'Q'), 'f64': (8, 'g'),
    'isize': (8, 'q'), 'usize': (8, 'Q'),
}


def _align(x, a): return (x + a - 1) & ~(a - 1)


def _size(t):
    if t in _PRIM: return _PRIM[t][0]
    if t.startswith('*'): return 8
    if t.startswith('[!'):  # [!T; N]
        m = re.match(r'\[!([^;]+);\s*(\d+)\]', t)
        if m: return _size(m.group(1).strip()) * int(m.group(2))
    if t.startswith('['): return 16  # slice
    if t in _types: return _types[t].get('total_size', 0)
    return 0


def _alignof(t):
    if t in _PRIM: return _PRIM[t][0]
    if t.startswith('*'): return 8
    if t.startswith('[!'):
        m = re.match(r'\[!([^;]+);\s*(\d+)\]', t)
        if m: return _alignof(m.group(1).strip())
    if t.startswith('['): return 8
    if t in _types and _types[t]['kind'] == 'struct': return _types[t].get('align', 1)
    if t in _types and _types[t]['kind'] == 'enum': return _types[t].get('align', 4)
    return 1


# ── parser ────────────────────────────────────────────────────────────
_STRUCT = re.compile(r'type\s+(\w+)\s*=\s*struct\s*\{([^}]*)\}', re.M)
_ENUM = re.compile(r'type\s+(\w+)\s*=\s*enum\s*\{([^}]*)\}', re.M)
_LET_SLICE = re.compile(r'let\s+\w+\s*:\s*(\[\*\][^\s=;,]+)\s*=', re.M)


def _split_top(s, sep=','):
    depth, cur, parts = 0, '', []
    for ch in s:
        if ch in '([{': depth += 1
        elif ch in ')]}': depth -= 1
        if ch == sep and depth == 0:
            parts.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip(): parts.append(cur.strip())
    return parts


def _parse_struct_layout(name, body):
    fields, offset, max_a = [], 0, 1
    for raw in _split_top(body):
        m = re.match(r'(\w+)\s*:\s*(.+)', raw)
        if not m: continue
        fname, ftype = m.group(1), m.group(2).strip()
        a, s = _alignof(ftype), _size(ftype)
        offset = _align(offset, a)
        fields.append({'name': fname, 'offset': offset, 'size': s, 'type': ftype})
        offset += s
        max_a = max(max_a, a)
    return {'kind': 'struct', 'name': name, 'fields': fields,
            'total_size': _align(offset, max_a), 'align': max_a}


def _parse_enum_layout(name, body):
    variants, ps, pa = [], [], []
    for raw in _split_top(body):
        if '(' in raw:
            m = re.match(r'(\w+)\s*\(\s*(.+?)\s*\)', raw)
            vname, ptype = m.group(1), m.group(2).strip()
        else:
            vname, ptype = raw, None
        if ptype:
            ps.append(_size(ptype)); pa.append(_alignof(ptype))
        variants.append({'name': vname, 'payload': ptype})
    mps = max(ps) if ps else 0
    mpa = max(pa) if pa else 1
    po = _align(4, mpa)
    total_a = max(mpa, 4)
    total_s = _align(po + mps, total_a)
    out = []
    for i, v in enumerate(variants):
        out.append({'name': v['name'], 'tag': i,
                    'has_payload': v['payload'] is not None,
                    'payload': v['payload'], 'payload_offset': po})
    return {'kind': 'enum', 'name': name, 'variants': out,
            'total_size': total_s, 'align': total_a,
            'tag_size': 4, 'payload_offset': po, 'payload_size': mps}


def load_types(path):
    src = open(path, encoding='utf-8').read()
    n = 0
    for m in _STRUCT.finditer(src):
        nm = m.group(1)
        _types[nm] = _parse_struct_layout(nm, m.group(2))
        print(f"[jhyy-pretty] struct {nm} (size={_types[nm]['total_size']})")
        n += 1
    for m in _ENUM.finditer(src):
        nm = m.group(1)
        _types[nm] = _parse_enum_layout(nm, m.group(2))
        vs = [v['name'] for v in _types[nm]['variants']]
        print(f"[jhyy-pretty] enum   {nm} (variants={vs})")
        n += 1
    seen = set()
    for m in _LET_SLICE.finditer(src):
        st = m.group(1).strip()
        if st in seen: continue
        seen.add(st)
        _types[st] = {'kind': 'slice', 'name': st, 'elem': st[3:]}
        print(f"[jhyy-pretty] slice  {st}")
        n += 1
    print(f"[jhyy-pretty] loaded {n} types from {path}")
    return n


# ── memory reader ─────────────────────────────────────────────────────
def _read(addr, nbytes, signed=False):
    raw = gdb.selected_inferior().read_memory(addr, nbytes).tobytes()
    return int.from_bytes(raw, 'little', signed=signed)


def _fmt_prim(addr, t):
    if t not in _PRIM: return f'<unknown primitive {t}>'
    sz, _ = _PRIM[t]
    return str(_read(addr, sz, signed=True))


def _fmt_enum(addr, info):
    tag = _read(addr, info['tag_size'], signed=True)
    for v in info['variants']:
        if v['tag'] == tag:
            if not v['has_payload']: return v['name']
            paddr = addr + info['payload_offset']
            pt = v['payload']
            if pt in _PRIM: return f"{v['name']}({_fmt_prim(paddr, pt)})"
            if pt in _types and _types[pt]['kind'] == 'struct':
                inner = _fmt_struct(paddr, _types[pt])
                return f"{v['name']}({inner})"
            return f"{v['name']}(<payload {pt}>)"
    return f'<invalid tag {tag}>'


def _fmt_struct(addr, info, depth=0):
    parts = []
    for f in info['fields']:
        fa = addr + f['offset']
        t = f['type']
        if t.startswith('['):
            parts.append(f"{f['name']}={_fmt_slice(fa, t)}")
        elif t in _types and _types[t]['kind'] == 'struct':
            if depth >= 8: parts.append(f"{f['name']}=<max depth>")
            else: parts.append(f"{f['name']}={{{_fmt_struct(fa, _types[t], depth+1)}}}")
        elif t in _types and _types[t]['kind'] == 'enum':
            parts.append(f"{f['name']}={_fmt_enum(fa, _types[t])}")
        elif t in _PRIM:
            parts.append(f"{f['name']}={_fmt_prim(fa, t)}")
        else:
            parts.append(f"{f['name']}=<unknown {t}>")
    return ', '.join(parts)


def _fmt_slice(addr, t):
    info = _types.get(t)
    elem = info['elem'] if (info and info['kind'] == 'slice') else t[3:]
    dp = _read(addr, 8); ln = _read(addr + 8, 8)
    return f"{t}{{data=0x{dp:x}, len={ln}}}"


# ── gdb commands + auto-pretty-printer ────────────────────────────────
class _LoadCmd(gdb.Command):
    """jhyy-load-types <path-to-source.jhyy>"""
    def __init__(self): super().__init__('jhyy-load-types', gdb.COMMAND_USER)
    def invoke(self, arg, from_tty):
        if arg: load_types(arg)
        else: print("Usage: jhyy-load-types <path-to-source.jhyy>")


class _PrettyCmd(gdb.Command):
    """jhyy-pretty <addr-expr> <typename>"""
    def __init__(self): super().__init__('jhyy-pretty', gdb.COMMAND_USER)
    def invoke(self, arg, from_tty):
        p = arg.split()
        if len(p) != 2:
            print("Usage: jhyy-pretty <addr-expr> <typename>"); return
        try: addr = int(gdb.parse_and_eval(p[0])) & 0xffffffffffffffff
        except Exception as e: print(f"Invalid address {p[0]!r}: {e}"); return
        info = _types.get(p[1])
        if not info: print(f"Unknown type {p[1]} (run jhyy-load-types first)"); return
        if info['kind'] == 'struct':
            print(f"{p[1]}{{{_fmt_struct(addr, info)}}}")
        elif info['kind'] == 'enum':
            print(_fmt_enum(addr, info))
        else:
            print(_fmt_slice(addr, p[1]))


class _PP:
    """Best-effort DWARF-type pretty-printer (only fires if DWARF names a
    type identically to a registered jhyy type — usually doesn't trigger
    because jhyy codegen doesn't emit type DWARF). Main path is the
    jhyy-pretty command above."""
    def __init__(self): self.name = 'jhyy'; self.enabled = True
    def __call__(self, val):
        try: tname = str(val.type)
        except Exception: return None
        for key in _types:
            if key in tname:
                info = _types[key]
                return _AddrFmt(val, info)
        return None


class _AddrFmt:
    def __init__(self, val, info): self.val, self.info = val, info
    def to_string(self):
        try:
            addr = int(self.val.address)
            if self.info['kind'] == 'struct':
                return f"{self.info['name']}{{{_fmt_struct(addr, self.info)}}}"
            if self.info['kind'] == 'enum':
                return _fmt_enum(addr, self.info)
            return _fmt_slice(addr, self.info['name'])
        except Exception as e:
            return f'<jhyy-pretty error: {e}>'


_LoadCmd()
_PrettyCmd()
try:
    gdb.printing.register_pretty_printer(gdb.current_objfile(), _PP())
except RuntimeError:
    pass  # already registered (e.g. user manually re-sourced)