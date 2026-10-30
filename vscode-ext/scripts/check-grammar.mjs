#!/usr/bin/env node
/**
 * 语法高亮 grammar 的**自检**。
 *
 * ⚠️ 为什么要有这个：`syntaxes/jhyy.tmLanguage.json` 是**手写**的，
 * 很容易跟真实的语言规则对不上（用户报过一批：漏关键字、数字字面量规则
 * 不准、字符字面量不高亮……）。这里把「语言真实规则 → grammar 必须命中」
 * 钉成一张表，改坏了就红。
 *
 * 规则的出处：`docs/abis/jhyy-lang-spec-v4.0.0.md` §2.5（字面量）
 * 与 `compiler/src0/{lexer,parser,sema}.jhyy`（关键字 / 类型）。
 *
 * 用法：`node scripts/check-grammar.mjs`（或 `npm run check:grammar`）
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const grammarPath = join(here, '..', 'syntaxes', 'jhyy.tmLanguage.json')
const grammar = JSON.parse(readFileSync(grammarPath, 'utf8'))
const repo = grammar.repository

const failures = []
function check(ok, message) {
  if (!ok) failures.push(message)
}

/* ── 1. 所有正则都要能编译 ────────────────────────────────────── */
for (const [name, entry] of Object.entries(repo)) {
  const patterns = entry.patterns ?? [entry]
  for (const p of patterns) {
    if (!p.match) continue
    try {
      new RegExp(p.match)
    } catch (err) {
      failures.push(`${name}: 正则编译失败 ${p.match} —— ${err.message}`)
    }
  }
}

/* ── 2. token → scope 的匹配（模拟 TextMate：按 patterns 顺序，先匹配先赢） ── */
function scopeOf(text) {
  for (const { include } of grammar.patterns) {
    const entry = repo[include.replace('#', '')]
    if (!entry) continue
    for (const p of entry.patterns ?? [entry]) {
      if (!p.match) continue
      const m = new RegExp(p.match).exec(text)
      if (m && m.index === 0 && m[0].length > 0) return p.name
    }
  }
  return null
}

const BS = String.fromCharCode(92)

/** [字面量文本, 期望的 scope 前缀] */
const EXPECT = [
  // 关键字（跟 lexer.jhyy 的 token 表对齐）
  ['break', 'keyword.control'],
  ['continue', 'keyword.control'],
  ['defer', 'keyword.control'],
  ['const', 'keyword.declaration'],
  ['volatile', 'storage.modifier'],
  ['null', 'constant.language.null'],
  ['true', 'constant.language.boolean'],
  ['false', 'constant.language.boolean'],
  // 类型（sema.jhyy 的 primitive 表 —— i8 是**合法**类型）
  ['i8', 'storage.type'],
  ['i16', 'storage.type'],
  ['i32', 'storage.type'],
  ['u64', 'storage.type'],
  ['f64', 'storage.type'],
  ['bool', 'storage.type'],
  // 整数字面量（规范 §2.5）
  ['42', 'constant.numeric.integer'],
  ['42i32', 'constant.numeric.integer'],
  ['0xFF', 'constant.numeric.hex'],
  ['0Xff', 'constant.numeric.hex'],
  ['0b1010', 'constant.numeric.bin'],
  ['0o77', 'constant.numeric.oct'],
  ['077', 'constant.numeric.oct'], // ⚠️ 前导零按八进制解释（= 63）
  // 浮点（规范 §2.5：只有 N.M 形式，没有指数）
  ['3.14', 'constant.numeric.float'],
  ['2.5f32', 'constant.numeric.float'],
  // 字符字面量（要能吃转义）
  ["'a'", 'string.quoted.single'],
  ["'" + BS + "n'", 'string.quoted.single'],
  ["'" + BS + "'" + "'", 'string.quoted.single'],
  // 运算符
  ['::', 'keyword.operator'],
  ['..', 'keyword.operator'],
  ['->', 'keyword.operator'],
  ['==', 'keyword.operator'],
]

for (const [text, want] of EXPECT) {
  const got = scopeOf(text)
  check(
    (got ?? '').startsWith(want),
    `${JSON.stringify(text)} 期望 scope 前缀 ${want}，实际 ${got}`,
  )
}

/* ── 3. 语言**不接受**的东西，grammar 不该高亮成字面量 ────────── */
{
  /* ⚠️ 这里**不能**用数组下标取规则（`repo.numbers.patterns[3]` 之类）。
   * 下标会因数组重排而**静默指向别的规则** ⇒ 下面 4 条检查全部变成空转，
   * 而且照样报「✓ 通过」—— 正是本项目栽过好几次的「门绿着但没在验它
   * 声称在验的东西」。改为**按 name 定位**，重排免疫。 */

  const numRules = repo.numbers.patterns ?? []

  /** 按 scope name 找规则；找不到 ⇒ 响亮失败（不静默跳过） */
  function numRule(name) {
    const r = numRules.find((p) => p.name === name)
    check(r !== undefined, `grammar 里找不到 scope ${name} —— 规则被改名/删掉了？`)
    return r
  }

  const intRule = numRule('constant.numeric.integer.jhyy')
  const floatRule = numRule('constant.numeric.float.jhyy')

  /* 显式 `0o77` 与前导零 `077` **共用** scope `constant.numeric.oct.jhyy`
   * ⇒ 按 name 找到两条 ⇒ 再按**行为**区分：前导零那条认 '077' 但不认 '08'。 */
  const octRules = numRules.filter((p) => p.name === 'constant.numeric.oct.jhyy')
  const leadingZeroRule = octRules.find((p) => {
    const re = new RegExp(p.match)
    return re.test('077') && !re.test('08')
  })
  check(
    leadingZeroRule !== undefined,
    '找不到「前导零八进制」规则 —— 应当有一条认 "077" 但不认 "08" 的 oct 规则',
  )

  // 下划线分隔是解析错误（规范 §2.5）⇒ 不能整段当数字
  if (intRule) {
    const re = new RegExp(intRule.match)
    check(
      !re.test('1_000'),
      '"1_000" 被当成了合法整数字面量 —— 语言里它是解析错误',
    )
  }
  // 指数写法不是合法浮点
  if (floatRule) {
    const re = new RegExp(floatRule.match)
    check(
      !re.test('1.0e10'),
      '"1.0e10" 被当成了合法浮点 —— 语言里它解析失败',
    )
  }
  // 前导零那条规则只认八进制数字 ⇒ "08" 里那个 8 不是八进制数字
  if (leadingZeroRule) {
    const re = new RegExp(leadingZeroRule.match)
    check(
      !re.test('08'),
      '前导零规则把 "08" 也当八进制了 —— 8 不是八进制数字',
    )
    // 前导零必须是**八进制**的 scope，不能跟普通十进制整数一个色
    check(
      leadingZeroRule.name !== intRule?.name,
      '前导零（八进制）和普通整数的 scope 一样 —— 配色上分不出八进制',
    )
  }
}

/* ── 结果 ─────────────────────────────────────────────────────── */
if (failures.length) {
  console.error('✗ grammar 自检失败：')
  for (const f of failures) console.error('  · ' + f)
  process.exit(1)
}
console.log(`✓ grammar 自检通过（${EXPECT.length} 条字面量规则 + 反例）`)
