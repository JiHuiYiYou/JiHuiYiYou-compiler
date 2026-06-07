data $str0 = { b "你的 HP: %d/%d\n", b 0 }
data $str1 = { b "怪物 HP: %d\n", b 0 }
data $str2 = { b "1. 攻击", b 0 }
data $str3 = { b "2. 喝药 (+6 HP)", b 0 }
data $str4 = { b "3. 逃跑", b 0 }
data $str5 = { b "选择行动:", b 0 }
data $str6 = { b "%d", b 0 }
data $str7 = { b "你造成了 %d 点伤害。\n", b 0 }
data $str8 = { b "你喝下一瓶药。", b 0 }
data $str9 = { b "你没有药水！", b 0 }
data $str10 = { b "逃跑失败！", b 0 }
data $str11 = { b "你逃跑了。", b 0 }
data $str12 = { b "你击败了怪物！", b 0 }
data $str13 = { b "怪物造成了 %d 点伤害。\n", b 0 }
data $str14 = { b "你站在地牢入口。", b 0 }
data $str15 = { b "一只怪物冲了出来！", b 0 }
data $str16 = { b "你发现了治疗泉水。", b 0 }
data $str17 = { b "你找到了一个宝箱。", b 0 }
data $str18 = { b "前方是最终 BOSS 房间。", b 0 }
data $str19 = { b "你看到了出口。", b 0 }
data $str20 = { b "你恢复了生命值。", b 0 }
data $str21 = { b "获得金币和药水。", b 0 }
data $str22 = { b "=== 地下城文字 Rogue ===", b 0 }
data $str23 = { b "前往下一层？(1=是 0=退出):", b 0 }
data $str24 = { b "%d", b 0 }
data $str25 = { b "你成功逃出地牢！", b 0 }
data $str26 = { b "你死在了地牢深处。", b 0 }
data $str27 = { b "最终金币：%d\n", b 0 }
export function w $randRange(l %seed, w %min, w %max) {
@start0
    %t0 =l copy %seed
    %t1 =w copy %min
    %t2 =w copy %max
    %t3 =w loadw %t0
    %t4 =w copy 1103515245
    %t5 =w mul %t3, %t4
    %t6 =w copy 12345
    %t7 =w add %t5, %t6
    %t8 =w copy 2147483647
    %t9 =w and %t7, %t8
    storew %t3, %t0
    %t10 =w sub %t2, %t1
    %t11 =w copy 1
    %t12 =w add %t10, %t11
    %t13 =w rem %t3, %t12
    %t14 =w add %t1, %t13
    ret %t14
}

export function w $clamp(w %x, w %min, w %max) {
@start1
    %t15 =w copy %x
    %t16 =w copy %min
    %t17 =w copy %max
    %t18 =w csltw %t15, %t16
    jnz %t18, @then2, @else3
@then2
    ret %t16
@else3
    jmp @merge4
@merge4
    %t19 =w csgtw %t15, %t17
    jnz %t19, @then5, @else6
@then5
    ret %t17
@else6
    jmp @merge7
@merge7
    ret %t15
}

export function w $monsterHp(w %tag) {
@start8
    %t20 =w copy %tag
    %t21 =w copy 0
    %t22 =w ceqw %t20, %t21
    jnz %t22, @then9, @else10
@then9
    %t23 =w copy 8
    ret %t23
@else10
    jmp @merge11
@merge11
    %t24 =w copy 1
    %t25 =w ceqw %t20, %t24
    jnz %t25, @then12, @else13
@then12
    %t26 =w copy 14
    ret %t26
@else13
    jmp @merge14
@merge14
    %t27 =w copy 30
    ret %t27
}

export function w $monsterAtk(w %tag) {
@start15
    %t28 =w copy %tag
    %t29 =w copy 0
    %t30 =w ceqw %t28, %t29
    jnz %t30, @then16, @else17
@then16
    %t31 =w copy 2
    ret %t31
@else17
    jmp @merge18
@merge18
    %t32 =w copy 1
    %t33 =w ceqw %t28, %t32
    jnz %t33, @then19, @else20
@then19
    %t34 =w copy 4
    ret %t34
@else20
    jmp @merge21
@merge21
    %t35 =w copy 7
    ret %t35
}

export function w $monsterGold(w %tag) {
@start22
    %t36 =w copy %tag
    %t37 =w copy 0
    %t38 =w ceqw %t36, %t37
    jnz %t38, @then23, @else24
@then23
    %t39 =w copy 5
    ret %t39
@else24
    jmp @merge25
@merge25
    %t40 =w copy 1
    %t41 =w ceqw %t36, %t40
    jnz %t41, @then26, @else27
@then26
    %t42 =w copy 10
    ret %t42
@else27
    jmp @merge28
@merge28
    %t43 =w copy 50
    ret %t43
}

export function $battle(l %hp, w %maxHp, w %atk, l %potions, l %mHp, w %mAtk, w %mGold, l %seed, l %state, l %gold) {
@start29
    %t44 =l copy %hp
    %t45 =w copy %maxHp
    %t46 =w copy %atk
    %t47 =l copy %potions
    %t48 =l copy %mHp
    %t49 =w copy %mAtk
    %t50 =w copy %mGold
    %t51 =l copy %seed
    %t52 =l copy %state
    %t53 =l copy %gold
    jmp @loop30
@loop30
    %t54 =w loadw %t44
    %t55 =w copy 0
    %t56 =w csgtw %t54, %t55
    jnz %t56, @body31, @exit32
@body31
    %t57 =l copy $str0
    %t58 =w loadw %t44
    %t59 =w call $printf(l %t57, w %t58, w %t45)
    %t60 =l copy $str1
    %t61 =w loadw %t48
    %t62 =w call $printf(l %t60, w %t61)
    %t63 =l copy $str2
    %t64 =w call $puts(l %t63)
    %t65 =l copy $str3
    %t66 =w call $puts(l %t65)
    %t67 =l copy $str4
    %t68 =w call $puts(l %t67)
    %t69 =l copy $str5
    %t70 =w call $puts(l %t69)
    %t71 =w copy 0
    %t72 =l alloc4 4
    storew %t71, %t72
    %t73 =l copy $str6
    %t74 =l copy 0
    %t75 =w call $scanf(l %t73, l %t72)
    %t76 =w loadw %t72
    %t77 =w copy 1
    %t78 =w ceqw %t76, %t77
    jnz %t78, @then33, @else34
@then33
    %t79 =w copy 1
    %t81 =w copy 0
    %t80 =w sub %t81, %t79
    %t82 =w copy 1
    %t83 =w call $randRange(l %t51, w %t80, w %t82)
    %t84 =w add %t46, %t83
    %t85 =w loadw %t48
    %t86 =w sub %t85, %t84
    storew %t86, %t48
    %t87 =l copy $str7
    %t88 =w call $printf(l %t87, w %t84)
    jmp @merge35
@else34
    jmp @merge35
@merge35
    %t89 =w loadw %t72
    %t90 =w copy 2
    %t91 =w ceqw %t89, %t90
    jnz %t91, @then36, @else37
@then36
    %t92 =w loadw %t47
    %t93 =w copy 0
    %t94 =w csgtw %t92, %t93
    jnz %t94, @then39, @else40
@then39
    %t95 =w loadw %t44
    %t96 =w copy 6
    %t97 =w add %t95, %t96
    storew %t97, %t44
    %t98 =w loadw %t44
    %t99 =w copy 0
    %t100 =w call $clamp(w %t98, w %t99, w %t45)
    storew %t100, %t44
    %t101 =w loadw %t47
    %t102 =w copy 1
    %t103 =w sub %t101, %t102
    storew %t103, %t47
    %t104 =l copy $str8
    %t105 =w call $puts(l %t104)
    jmp @merge41
@else40
    %t106 =l copy $str9
    %t107 =w call $puts(l %t106)
    jmp @merge41
@merge41
    %t108 =w phi @then39 %t105, @else40 %t107
    jmp @merge38
@else37
    jmp @merge38
@merge38
    %t109 =w loadw %t72
    %t110 =w copy 3
    %t111 =w ceqw %t109, %t110
    jnz %t111, @then42, @else43
@then42
    %t112 =w copy 0
    %t113 =w copy 1
    %t114 =w call $randRange(l %t51, w %t112, w %t113)
    %t115 =w copy 0
    %t116 =w ceqw %t114, %t115
    jnz %t116, @then45, @else46
@then45
    %t117 =l copy $str10
    %t118 =w call $puts(l %t117)
    jmp @merge47
@else46
    %t119 =l copy $str11
    %t120 =w call $puts(l %t119)
    jmp @merge47
@merge47
    %t121 =w phi @then45 %t118, @else46 %t120
    %t122 =w copy 0
    %t123 =w cnew %t114, %t122
    jnz %t123, @then48, @else49
@then48
    ret
@else49
    jmp @merge50
@merge50
    jmp @merge44
@else43
    jmp @merge44
@merge44
    %t124 =w loadw %t48
    %t125 =w copy 0
    %t126 =w cslew %t124, %t125
    jnz %t126, @then51, @else52
@then51
    %t127 =l copy $str12
    %t128 =w call $puts(l %t127)
    %t129 =w loadw %t53
    %t130 =w add %t129, %t50
    storew %t130, %t53
    ret
@else52
    jmp @merge53
@merge53
    %t131 =w copy 1
    %t133 =w copy 0
    %t132 =w sub %t133, %t131
    %t134 =w copy 1
    %t135 =w call $randRange(l %t51, w %t132, w %t134)
    %t136 =w add %t49, %t135
    %t137 =w loadw %t44
    %t138 =w sub %t137, %t136
    storew %t138, %t44
    %t139 =l copy $str13
    %t140 =w call $printf(l %t139, w %t136)
    jmp @loop30
@exit32
    %t141 =w copy 2
    storew %t141, %t52
    ret
}

export function $describeRoom(w %tag) {
@start54
    %t142 =w copy %tag
    %t143 =w copy 0
    %t144 =w ceqw %t142, %t143
    jnz %t144, @then55, @else56
@then55
    %t145 =l copy $str14
    %t146 =w call $puts(l %t145)
    jmp @merge57
@else56
    jmp @merge57
@merge57
    %t147 =w copy 1
    %t148 =w ceqw %t142, %t147
    jnz %t148, @then58, @else59
@then58
    %t149 =l copy $str15
    %t150 =w call $puts(l %t149)
    jmp @merge60
@else59
    jmp @merge60
@merge60
    %t151 =w copy 2
    %t152 =w ceqw %t142, %t151
    jnz %t152, @then61, @else62
@then61
    %t153 =l copy $str16
    %t154 =w call $puts(l %t153)
    jmp @merge63
@else62
    jmp @merge63
@merge63
    %t155 =w copy 3
    %t156 =w ceqw %t142, %t155
    jnz %t156, @then64, @else65
@then64
    %t157 =l copy $str17
    %t158 =w call $puts(l %t157)
    jmp @merge66
@else65
    jmp @merge66
@merge66
    %t159 =w copy 4
    %t160 =w ceqw %t142, %t159
    jnz %t160, @then67, @else68
@then67
    %t161 =l copy $str18
    %t162 =w call $puts(l %t161)
    jmp @merge69
@else68
    jmp @merge69
@merge69
    %t163 =w copy 5
    %t164 =w ceqw %t142, %t163
    jnz %t164, @then70, @else71
@then70
    %t165 =l copy $str19
    %t166 =w call $puts(l %t165)
    jmp @merge72
@else71
    jmp @merge72
@merge72
    ret
}

export function $processRoom(l %hp, w %maxHp, w %atk, l %potions, l %seed, l %state, l %gold, w %roomTag) {
@start73
    %t167 =l copy %hp
    %t168 =w copy %maxHp
    %t169 =w copy %atk
    %t170 =l copy %potions
    %t171 =l copy %seed
    %t172 =l copy %state
    %t173 =l copy %gold
    %t174 =w copy %roomTag
    %t175 =w call $describeRoom(w %t174)
    %t176 =w copy 2
    %t177 =w ceqw %t174, %t176
    jnz %t177, @then74, @else75
@then74
    %t178 =w loadw %t167
    %t179 =w copy 8
    %t180 =w add %t178, %t179
    storew %t180, %t167
    %t181 =w loadw %t167
    %t182 =w copy 0
    %t183 =w call $clamp(w %t181, w %t182, w %t168)
    storew %t183, %t167
    %t184 =l copy $str20
    %t185 =w call $puts(l %t184)
    jmp @merge76
@else75
    jmp @merge76
@merge76
    %t186 =w copy 3
    %t187 =w ceqw %t174, %t186
    jnz %t187, @then77, @else78
@then77
    %t188 =w loadw %t173
    %t189 =w copy 20
    %t190 =w add %t188, %t189
    storew %t190, %t173
    %t191 =w loadw %t170
    %t192 =w copy 1
    %t193 =w add %t191, %t192
    storew %t193, %t170
    %t194 =l copy $str21
    %t195 =w call $puts(l %t194)
    jmp @merge79
@else78
    jmp @merge79
@merge79
    %t196 =w copy 1
    %t197 =w ceqw %t174, %t196
    jnz %t197, @then80, @else81
@then80
    %t198 =w copy 0
    %t199 =w call $monsterHp(w %t198)
    %t200 =w call $monsterAtk(w %t198)
    %t201 =w call $monsterGold(w %t198)
    %t202 =l alloc4 4
    storew %t199, %t202
    %t203 =l copy 0
    %t204 =w call $battle(l %t167, w %t168, w %t169, l %t170, l %t202, w %t200, w %t201, l %t171, l %t172, l %t173)
    jmp @merge82
@else81
    jmp @merge82
@merge82
    %t205 =w copy 4
    %t206 =w ceqw %t174, %t205
    jnz %t206, @then83, @else84
@then83
    %t207 =w copy 2
    %t208 =w call $monsterHp(w %t207)
    %t209 =w call $monsterAtk(w %t207)
    %t210 =w call $monsterGold(w %t207)
    %t211 =l alloc4 4
    storew %t208, %t211
    %t212 =l copy 0
    %t213 =w call $battle(l %t167, w %t168, w %t169, l %t170, l %t211, w %t209, w %t210, l %t171, l %t172, l %t173)
    jmp @merge85
@else84
    jmp @merge85
@merge85
    %t214 =w copy 5
    %t215 =w ceqw %t174, %t214
    jnz %t215, @then86, @else87
@then86
    %t216 =w copy 1
    storew %t216, %t172
    jmp @merge88
@else87
    jmp @merge88
@merge88
    ret
}

export function w $main_jhyy() {
@start89
    %t217 =l copy $str22
    %t218 =w call $puts(l %t217)
    %t219 =w copy 20
    %t220 =l alloc4 4
    storew %t219, %t220
    %t221 =w copy 20
    %t222 =w copy 4
    %t223 =w copy 2
    %t224 =l alloc4 4
    storew %t223, %t224
    %t225 =w copy 0
    %t226 =l alloc4 4
    storew %t225, %t226
    %t227 =w copy 0
    %t228 =l alloc4 4
    storew %t227, %t228
    %t229 =w copy 0
    %t230 =l alloc4 4
    storew %t229, %t230
    %t231 =w copy 12345
    %t232 =l alloc4 4
    storew %t231, %t232
    jmp @loop90
@loop90
    %t233 =w loadw %t226
    %t234 =w copy 0
    %t235 =w ceqw %t233, %t234
    jnz %t235, @body91, @exit92
@body91
    %t236 =w loadw %t228
    %t237 =w copy 0
    %t238 =w ceqw %t236, %t237
    jnz %t238, @arm94, @next95
@arm94
    %t239 =w copy 0
    jmp @merge93
@next95
    %t240 =w copy 1
    %t241 =w ceqw %t236, %t240
    jnz %t241, @arm96, @next97
@arm96
    %t242 =w copy 2
    jmp @merge93
@next97
    %t243 =w copy 2
    %t244 =w ceqw %t236, %t243
    jnz %t244, @arm98, @next99
@arm98
    %t245 =w copy 1
    jmp @merge93
@next99
    %t246 =w copy 3
    %t247 =w ceqw %t236, %t246
    jnz %t247, @arm100, @next101
@arm100
    %t248 =w copy 3
    jmp @merge93
@next101
    %t249 =w copy 4
    %t250 =w ceqw %t236, %t249
    jnz %t250, @arm102, @next103
@arm102
    %t251 =w copy 4
    jmp @merge93
@next103
    jmp @arm104
@arm104
    %t252 =w copy 5
    jmp @merge93
@merge93
    %t253 =w phi @arm94 %t239, @arm96 %t242, @arm98 %t245, @arm100 %t248, @arm102 %t251, @arm104 %t252
    %t254 =l copy 0
    %t255 =l copy 0
    %t256 =l copy 0
    %t257 =l copy 0
    %t258 =l copy 0
    %t259 =w call $processRoom(l %t220, w %t221, w %t222, l %t224, l %t232, l %t226, l %t230, w %t253)
    %t260 =w loadw %t226
    %t261 =w copy 0
    %t262 =w ceqw %t260, %t261
    jnz %t262, @then105, @else106
@then105
    %t263 =l copy $str23
    %t264 =w call $puts(l %t263)
    %t265 =w copy 0
    %t266 =l alloc4 4
    storew %t265, %t266
    %t267 =l copy $str24
    %t268 =l copy 0
    %t269 =w call $scanf(l %t267, l %t266)
    %t270 =w loadw %t266
    %t271 =w copy 0
    %t272 =w ceqw %t270, %t271
    jnz %t272, @then108, @else109
@then108
    %t273 =w copy 1
    storew %t273, %t226
    %t274 =w copy 0
    jmp @merge110
@else109
    %t275 =w loadw %t228
    %t276 =w copy 1
    %t277 =w add %t275, %t276
    storew %t277, %t228
    %t278 =w copy 0
    jmp @merge110
@merge110
    %t279 =w phi @then108 %t274, @else109 %t278
    jmp @merge107
@else106
    jmp @merge107
@merge107
    jmp @loop90
@exit92
    %t280 =w loadw %t226
    %t281 =w copy 1
    %t282 =w ceqw %t280, %t281
    jnz %t282, @then111, @else112
@then111
    %t283 =l copy $str25
    %t284 =w call $puts(l %t283)
    jmp @merge113
@else112
    %t285 =l copy $str26
    %t286 =w call $puts(l %t285)
    jmp @merge113
@merge113
    %t287 =w phi @then111 %t284, @else112 %t286
    %t288 =l copy $str27
    %t289 =w loadw %t230
    %t290 =w call $printf(l %t288, w %t289)
    %t291 =w copy 0
    ret %t291
}

