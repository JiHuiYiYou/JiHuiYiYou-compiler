data $str0 = { b "JHYY stress test", b 0 }
data $str1 = { b "=== JHYY Stress Test ===", b 0 }
data $str2 = { b "t_add3: %d\n", b 0 }
data $str3 = { b "t_mul4: %d\n", b 0 }
data $str4 = { b "t_mixed: %d\n", b 0 }
data $str5 = { b "t_negate: %d\n", b 0 }
data $str6 = { b "t_abs_diff: %d\n", b 0 }
data $str7 = { b "t_clamp: %d\n", b 0 }
data $str8 = { b "t_fact: %d\n", b 0 }
data $str9 = { b "t_fib: %d\n", b 0 }
data $str10 = { b "t_gcd: %d\n", b 0 }
data $str11 = { b "t_sum_to: %d\n", b 0 }
data $str12 = { b "t_power: %d\n", b 0 }
data $str13 = { b "t_sum_digits: %d\n", b 0 }
data $str14 = { b "t_is_positive: %d\n", b 0 }
data $str15 = { b "t_in_range: %d\n", b 0 }
data $str16 = { b "t_max3: %d\n", b 0 }
data $str17 = { b "t_min3: %d\n", b 0 }
data $str18 = { b "t_sign: %d\n", b 0 }
data $str19 = { b "t_bit_pack: %d\n", b 0 }
data $str20 = { b "t_bit_unpack: %d\n", b 0 }
data $str21 = { b "t_count_set_bits: %d\n", b 0 }
data $str22 = { b "t_bit_xor: %d\n", b 0 }
data $str23 = { b "t_bit_or: %d\n", b 0 }
data $str24 = { b "t_bit_and: %d\n", b 0 }
data $str25 = { b "t_shifts: %d\n", b 0 }
data $str26 = { b "t_point_basic: %d\n", b 0 }
data $str27 = { b "t_point_ops: %d\n", b 0 }
data $str28 = { b "t_point_diff: %d\n", b 0 }
data $str29 = { b "t_rect_area: %d\n", b 0 }
data $str30 = { b "t_triple: %d\n", b 0 }
data $str31 = { b "t_array_sum: %d\n", b 0 }
data $str32 = { b "t_array_max: %d\n", b 0 }
data $str33 = { b "t_array_min: %d\n", b 0 }
data $str34 = { b "t_array_dot: %d\n", b 0 }
data $str35 = { b "t_ptr_field: %d\n", b 0 }
data $str36 = { b "t_ptr_array: %d\n", b 0 }
data $str37 = { b "t_swap_via_ptr: %d\n", b 0 }
data $str38 = { b "t_modify_via_ptr: %d\n", b 0 }
data $str39 = { b "t_sum_even: %d\n", b 0 }
data $str40 = { b "t_sum_odd: %d\n", b 0 }
data $str41 = { b "t_nested: %d\n", b 0 }
data $str42 = { b "t_for_sum: %d\n", b 0 }
data $str43 = { b "t_for_break: %d\n", b 0 }
data $str44 = { b "t_for_continue: %d\n", b 0 }
data $str45 = { b "t_while_break: %d\n", b 0 }
data $str46 = { b "t_harmonic: %d\n", b 0 }
data $str47 = { b "t_collatz: %d\n", b 0 }
data $str48 = { b "t_prime: %d\n", b 0 }
data $str49 = { b "t_count_primes: %d\n", b 0 }
data $str50 = { b "t_next_prime: %d\n", b 0 }
data $str51 = { b "t_compound_assign: %d\n", b 0 }
data $str52 = { b "t_complex_combo: %d\n", b 0 }
data $str53 = { b "t_early_return: %d\n", b 0 }
data $str54 = { b "t_nested_if: %d\n", b 0 }
data $str55 = { b "t_recursive_mix: %d\n", b 0 }
data $str56 = { b "t_logical_combinations: %d\n", b 0 }
data $str57 = { b "t_array_literal_basic: %d\n", b 0 }
data $str58 = { b "t_array_type_annot: %d\n", b 0 }
data $str59 = { b "t_string_literal: %d\n", b 0 }
data $str60 = { b "t_unary_ops: %d\n", b 0 }
data $str61 = { b "Test failures: %d\n", b 0 }
export function w $add3(w %a, w %b, w %c) {
@start0
    %t0 =w copy %a
    %t1 =w copy %b
    %t2 =w copy %c
    %t3 =w add %t0, %t1
    %t4 =w add %t3, %t2
    ret %t4
}

export function w $mul4(w %a, w %b, w %c, w %d) {
@start1
    %t5 =w copy %a
    %t6 =w copy %b
    %t7 =w copy %c
    %t8 =w copy %d
    %t9 =w mul %t5, %t6
    %t10 =w mul %t9, %t7
    %t11 =w mul %t10, %t8
    ret %t11
}

export function w $mixed_ops(w %x, w %y) {
@start2
    %t12 =w copy %x
    %t13 =w copy %y
    %t14 =w add %t12, %t13
    %t15 =w sub %t12, %t13
    %t16 =w mul %t12, %t13
    %t17 =w add %t12, %t13
    %t18 =w copy 2
    %t19 =w div %t17, %t18
    %t20 =w copy 3
    %t21 =w mul %t12, %t20
    %t22 =w copy 7
    %t23 =w rem %t21, %t22
    %t24 =w add %t14, %t15
    %t25 =w add %t24, %t16
    %t26 =w add %t25, %t19
    %t27 =w add %t26, %t23
    ret %t27
}

export function w $negate_via_sub(w %x) {
@start3
    %t28 =w copy %x
    %t29 =w copy 0
    %t30 =w sub %t29, %t28
    ret %t30
}

export function w $abs_diff(w %a, w %b) {
@start4
    %t31 =w copy %a
    %t32 =w copy %b
    %t33 =w csgtw %t31, %t32
    jnz %t33, @then5, @else6
@then5
    %t34 =w sub %t31, %t32
    ret %t34
@else6
    jmp @merge7
@merge7
    %t35 =w sub %t32, %t31
    ret %t35
}

export function w $clamp_pos(w %x) {
@start8
    %t36 =w copy %x
    %t37 =w copy 0
    %t38 =w csltw %t36, %t37
    jnz %t38, @then9, @else10
@then9
    %t39 =w copy 0
    ret %t39
@else10
    jmp @merge11
@merge11
    ret %t36
}

export function w $fact(w %n) {
@start12
    %t40 =w copy %n
    %t41 =w copy 1
    %t42 =w cslew %t40, %t41
    jnz %t42, @then13, @else14
@then13
    %t43 =w copy 1
    ret %t43
@else14
    jmp @merge15
@merge15
    %t44 =w copy 1
    %t45 =w sub %t40, %t44
    %t46 =w call $fact(w %t45)
    %t47 =w mul %t40, %t46
    ret %t47
}

export function w $fib(w %n) {
@start16
    %t48 =w copy %n
    %t49 =w copy 2
    %t50 =w csltw %t48, %t49
    jnz %t50, @then17, @else18
@then17
    ret %t48
@else18
    jmp @merge19
@merge19
    %t51 =w copy 1
    %t52 =w sub %t48, %t51
    %t53 =w call $fib(w %t52)
    %t54 =w copy 2
    %t55 =w sub %t48, %t54
    %t56 =w call $fib(w %t55)
    %t57 =w add %t53, %t56
    ret %t57
}

export function w $gcd(w %a, w %b) {
@start20
    %t58 =w copy %a
    %t59 =w copy %b
    %t60 =l alloc4 4
    storew %t58, %t60
    %t61 =l alloc4 4
    storew %t59, %t61
    jmp @loop21
@loop21
    %t62 =w loadw %t61
    %t63 =w copy 0
    %t64 =w cnew %t62, %t63
    jnz %t64, @body22, @exit23
@body22
    %t65 =w loadw %t61
    %t66 =w loadw %t60
    %t67 =w loadw %t61
    %t68 =w rem %t66, %t67
    storew %t68, %t61
    storew %t65, %t60
    jmp @loop21
@exit23
    %t69 =w loadw %t60
    ret %t69
}

export function w $sum_to(w %n) {
@start24
    %t70 =w copy %n
    %t71 =w copy 0
    %t72 =l alloc4 4
    storew %t71, %t72
    %t73 =w copy 1
    %t74 =l alloc4 4
    storew %t73, %t74
    jmp @loop25
@loop25
    %t75 =w loadw %t74
    %t76 =w cslew %t75, %t70
    jnz %t76, @body26, @exit27
@body26
    %t77 =w loadw %t72
    %t78 =w loadw %t74
    %t79 =w add %t77, %t78
    storew %t79, %t72
    %t80 =w loadw %t74
    %t81 =w copy 1
    %t82 =w add %t80, %t81
    storew %t82, %t74
    jmp @loop25
@exit27
    %t83 =w loadw %t72
    ret %t83
}

export function w $power(w %base, w %exp) {
@start28
    %t84 =w copy %base
    %t85 =w copy %exp
    %t86 =w copy 1
    %t87 =l alloc4 4
    storew %t86, %t87
    %t88 =w copy 0
    %t89 =l alloc4 4
    storew %t88, %t89
    jmp @loop29
@loop29
    %t90 =w loadw %t89
    %t91 =w csltw %t90, %t85
    jnz %t91, @body30, @exit31
@body30
    %t92 =w loadw %t87
    %t93 =w mul %t92, %t84
    storew %t93, %t87
    %t94 =w loadw %t89
    %t95 =w copy 1
    %t96 =w add %t94, %t95
    storew %t96, %t89
    jmp @loop29
@exit31
    %t97 =w loadw %t87
    ret %t97
}

export function w $sum_digits_iterative(w %n) {
@start32
    %t98 =w copy %n
    %t99 =l alloc4 4
    storew %t98, %t99
    %t100 =w copy 0
    %t101 =l alloc4 4
    storew %t100, %t101
    jmp @loop33
@loop33
    %t102 =w loadw %t99
    %t103 =w copy 0
    %t104 =w csgtw %t102, %t103
    jnz %t104, @body34, @exit35
@body34
    %t105 =w loadw %t101
    %t106 =w loadw %t99
    %t107 =w copy 10
    %t108 =w rem %t106, %t107
    %t109 =w add %t105, %t108
    storew %t109, %t101
    %t110 =w loadw %t99
    %t111 =w copy 10
    %t112 =w div %t110, %t111
    storew %t112, %t99
    jmp @loop33
@exit35
    %t113 =w loadw %t101
    ret %t113
}

export function w $is_positive(w %x) {
@start36
    %t114 =w copy %x
    %t115 =w copy 0
    %t116 =w csgtw %t114, %t115
    jnz %t116, @then37, @else38
@then37
    %t117 =w copy 1
    ret %t117
@else38
    jmp @merge39
@merge39
    %t118 =w copy 0
    ret %t118
}

export function w $is_in_range(w %x, w %lo, w %hi) {
@start40
    %t119 =w copy %x
    %t120 =w copy %lo
    %t121 =w copy %hi
    %t122 =w csltw %t119, %t120
    jnz %t122, @then41, @else42
@then41
    %t123 =w copy 0
    ret %t123
@else42
    jmp @merge43
@merge43
    %t124 =w csgtw %t119, %t121
    jnz %t124, @then44, @else45
@then44
    %t125 =w copy 0
    ret %t125
@else45
    jmp @merge46
@merge46
    %t126 =w copy 1
    ret %t126
}

export function w $bool_and(w %a, w %b) {
@start47
    %t127 =w copy %a
    %t128 =w copy %b
    %t129 =w copy 0
    %t130 =w ceqw %t127, %t129
    jnz %t130, @then48, @else49
@then48
    %t131 =w copy 0
    ret %t131
@else49
    jmp @merge50
@merge50
    %t132 =w copy 0
    %t133 =w ceqw %t128, %t132
    jnz %t133, @then51, @else52
@then51
    %t134 =w copy 0
    ret %t134
@else52
    jmp @merge53
@merge53
    %t135 =w copy 1
    ret %t135
}

export function w $bool_or(w %a, w %b) {
@start54
    %t136 =w copy %a
    %t137 =w copy %b
    %t138 =w copy 0
    %t139 =w cnew %t136, %t138
    jnz %t139, @then55, @else56
@then55
    %t140 =w copy 1
    ret %t140
@else56
    jmp @merge57
@merge57
    %t141 =w copy 0
    %t142 =w cnew %t137, %t141
    jnz %t142, @then58, @else59
@then58
    %t143 =w copy 1
    ret %t143
@else59
    jmp @merge60
@merge60
    %t144 =w copy 0
    ret %t144
}

export function w $max3(w %a, w %b, w %c) {
@start61
    %t145 =w copy %a
    %t146 =w copy %b
    %t147 =w copy %c
    %t148 =l alloc4 4
    storew %t145, %t148
    %t149 =w loadw %t148
    %t150 =w csgtw %t146, %t149
    jnz %t150, @then62, @else63
@then62
    storew %t146, %t148
    jmp @merge64
@else63
    jmp @merge64
@merge64
    %t151 =w loadw %t148
    %t152 =w csgtw %t147, %t151
    jnz %t152, @then65, @else66
@then65
    storew %t147, %t148
    jmp @merge67
@else66
    jmp @merge67
@merge67
    %t153 =w loadw %t148
    ret %t153
}

export function w $min3(w %a, w %b, w %c) {
@start68
    %t154 =w copy %a
    %t155 =w copy %b
    %t156 =w copy %c
    %t157 =l alloc4 4
    storew %t154, %t157
    %t158 =w loadw %t157
    %t159 =w csltw %t155, %t158
    jnz %t159, @then69, @else70
@then69
    storew %t155, %t157
    jmp @merge71
@else70
    jmp @merge71
@merge71
    %t160 =w loadw %t157
    %t161 =w csltw %t156, %t160
    jnz %t161, @then72, @else73
@then72
    storew %t156, %t157
    jmp @merge74
@else73
    jmp @merge74
@merge74
    %t162 =w loadw %t157
    ret %t162
}

export function w $sign(w %x) {
@start75
    %t163 =w copy %x
    %t164 =w copy 0
    %t165 =w csgtw %t163, %t164
    jnz %t165, @then76, @else77
@then76
    %t166 =w copy 1
    ret %t166
@else77
    jmp @merge78
@merge78
    %t167 =w copy 0
    %t168 =w csltw %t163, %t167
    jnz %t168, @then79, @else80
@then79
    %t169 =w copy 1
    %t171 =w copy 0
    %t170 =w sub %t171, %t169
    ret %t170
@else80
    jmp @merge81
@merge81
    %t172 =w copy 0
    ret %t172
}

export function w $bit_pack(w %a, w %b, w %c, w %d) {
@start82
    %t173 =w copy %a
    %t174 =w copy %b
    %t175 =w copy %c
    %t176 =w copy %d
    %t177 =w copy 255
    %t178 =w and %t173, %t177
    %t179 =w copy 255
    %t180 =w and %t174, %t179
    %t181 =w copy 8
    %t182 =w shl %t180, %t181
    %t183 =w or %t178, %t182
    %t184 =w copy 255
    %t185 =w and %t175, %t184
    %t186 =w copy 16
    %t187 =w shl %t185, %t186
    %t188 =w or %t183, %t187
    %t189 =w copy 255
    %t190 =w and %t176, %t189
    %t191 =w copy 24
    %t192 =w shl %t190, %t191
    %t193 =w or %t188, %t192
    ret %t193
}

export function w $bit_unpack_byte(w %x, w %n) {
@start83
    %t194 =w copy %x
    %t195 =w copy %n
    %t196 =w copy 8
    %t197 =w mul %t195, %t196
    %t198 =w shr %t194, %t197
    %t199 =w copy 255
    %t200 =w and %t198, %t199
    ret %t200
}

export function w $count_set_bits(w %x_in) {
@start84
    %t201 =w copy %x_in
    %t202 =l alloc4 4
    storew %t201, %t202
    %t203 =w copy 0
    %t204 =l alloc4 4
    storew %t203, %t204
    jmp @loop85
@loop85
    %t205 =w loadw %t202
    %t206 =w copy 0
    %t207 =w csgtw %t205, %t206
    jnz %t207, @body86, @exit87
@body86
    %t208 =w loadw %t202
    %t209 =w copy 1
    %t210 =w and %t208, %t209
    %t211 =w copy 0
    %t212 =w cnew %t210, %t211
    jnz %t212, @then88, @else89
@then88
    %t213 =w loadw %t204
    %t214 =w copy 1
    %t215 =w add %t213, %t214
    storew %t215, %t204
    jmp @merge90
@else89
    jmp @merge90
@merge90
    %t216 =w loadw %t202
    %t217 =w copy 1
    %t218 =w shr %t216, %t217
    storew %t218, %t202
    jmp @loop85
@exit87
    %t219 =w loadw %t204
    ret %t219
}

export function w $bit_xor_pattern(w %a, w %b) {
@start91
    %t220 =w copy %a
    %t221 =w copy %b
    %t222 =w xor %t220, %t221
    ret %t222
}

export function w $bit_or_pattern(w %a, w %b) {
@start92
    %t223 =w copy %a
    %t224 =w copy %b
    %t225 =w or %t223, %t224
    ret %t225
}

export function w $bit_and_pattern(w %a, w %b) {
@start93
    %t226 =w copy %a
    %t227 =w copy %b
    %t228 =w and %t226, %t227
    ret %t228
}

export function w $shift_left(w %x, w %n) {
@start94
    %t229 =w copy %x
    %t230 =w copy %n
    %t231 =w shl %t229, %t230
    ret %t231
}

export function w $shift_right(w %x, w %n) {
@start95
    %t232 =w copy %x
    %t233 =w copy %n
    %t234 =w shr %t232, %t233
    ret %t234
}

export function $make_point(l %ret, w %x, w %y) {
@start96
    %t235 =l copy %ret
    %t236 =w copy %x
    %t237 =w copy %y
    %t238 =l alloc8 8
    %t239 =l add %t238, 0
    storew %t236, %t239
    %t240 =l add %t238, 4
    storew %t237, %t240
    %t241 =l copy %t238
    %t242 =l copy %t235
    %t243 =w loadw %t241
    storew %t243, %t242
    %t244 =l add %t238, 4
    %t245 =l add %t235, 4
    %t246 =w loadw %t244
    storew %t246, %t245
    ret
}

export function w $point_sum(l %p) {
@start97
    %t247 =l copy %p
    %t248 =w loadw %t247
    %t249 =l add %t247, 4
    %t250 =w loadw %t249
    %t251 =w add %t248, %t250
    ret %t251
}

export function w $point_diff(l %p) {
@start98
    %t252 =l copy %p
    %t253 =w loadw %t252
    %t254 =l add %t252, 4
    %t255 =w loadw %t254
    %t256 =w sub %t253, %t255
    ret %t256
}

export function $point_scale(l %ret, l %p, w %k) {
@start99
    %t257 =l copy %ret
    %t258 =l copy %p
    %t259 =w copy %k
    %t260 =l alloc8 8
    %t261 =w loadw %t258
    %t262 =w mul %t261, %t259
    %t263 =l add %t260, 0
    storew %t262, %t263
    %t264 =l add %t258, 4
    %t265 =w loadw %t264
    %t266 =w mul %t265, %t259
    %t267 =l add %t260, 4
    storew %t266, %t267
    %t268 =l copy %t260
    %t269 =l copy %t257
    %t270 =w loadw %t268
    storew %t270, %t269
    %t271 =l add %t260, 4
    %t272 =l add %t257, 4
    %t273 =w loadw %t271
    storew %t273, %t272
    ret
}

export function $point_translate(l %ret, l %p, w %dx, w %dy) {
@start100
    %t274 =l copy %ret
    %t275 =l copy %p
    %t276 =w copy %dx
    %t277 =w copy %dy
    %t278 =l alloc8 8
    %t279 =w loadw %t275
    %t280 =w add %t279, %t276
    %t281 =l add %t278, 0
    storew %t280, %t281
    %t282 =l add %t275, 4
    %t283 =w loadw %t282
    %t284 =w add %t283, %t277
    %t285 =l add %t278, 4
    storew %t284, %t285
    %t286 =l copy %t278
    %t287 =l copy %t274
    %t288 =w loadw %t286
    storew %t288, %t287
    %t289 =l add %t278, 4
    %t290 =l add %t274, 4
    %t291 =w loadw %t289
    storew %t291, %t290
    ret
}

export function w $rect_area(l %b) {
@start101
    %t292 =l copy %b
    %t293 =l add %t292, 8
    %t294 =w loadw %t293
    %t295 =l add %t292, 12
    %t296 =w loadw %t295
    %t297 =w mul %t294, %t296
    ret %t297
}

export function w $triple_sum(l %t) {
@start102
    %t298 =l copy %t
    %t299 =w loadw %t298
    %t300 =l add %t298, 4
    %t301 =w loadw %t300
    %t302 =w add %t299, %t301
    %t303 =l add %t298, 8
    %t304 =w loadw %t303
    %t305 =w add %t302, %t304
    ret %t305
}

export function w $triple_max(l %t) {
@start103
    %t306 =l copy %t
    %t307 =w loadw %t306
    %t308 =l alloc4 4
    storew %t307, %t308
    %t309 =l add %t306, 4
    %t310 =w loadw %t309
    %t311 =w loadw %t308
    %t312 =w csgtw %t310, %t311
    jnz %t312, @then104, @else105
@then104
    %t313 =l add %t306, 4
    %t314 =w loadw %t313
    storew %t314, %t308
    jmp @merge106
@else105
    jmp @merge106
@merge106
    %t315 =l add %t306, 8
    %t316 =w loadw %t315
    %t317 =w loadw %t308
    %t318 =w csgtw %t316, %t317
    jnz %t318, @then107, @else108
@then107
    %t319 =l add %t306, 8
    %t320 =w loadw %t319
    storew %t320, %t308
    jmp @merge109
@else108
    jmp @merge109
@merge109
    %t321 =w loadw %t308
    ret %t321
}

export function w $sum_4(w %a0, w %a1, w %a2, w %a3) {
@start110
    %t322 =w copy %a0
    %t323 =w copy %a1
    %t324 =w copy %a2
    %t325 =w copy %a3
    %t326 =w add %t322, %t323
    %t327 =w add %t326, %t324
    %t328 =w add %t327, %t325
    ret %t328
}

export function w $max4(w %a0, w %a1, w %a2, w %a3) {
@start111
    %t329 =w copy %a0
    %t330 =w copy %a1
    %t331 =w copy %a2
    %t332 =w copy %a3
    %t333 =l alloc4 4
    storew %t329, %t333
    %t334 =w loadw %t333
    %t335 =w csgtw %t330, %t334
    jnz %t335, @then112, @else113
@then112
    storew %t330, %t333
    jmp @merge114
@else113
    jmp @merge114
@merge114
    %t336 =w loadw %t333
    %t337 =w csgtw %t331, %t336
    jnz %t337, @then115, @else116
@then115
    storew %t331, %t333
    jmp @merge117
@else116
    jmp @merge117
@merge117
    %t338 =w loadw %t333
    %t339 =w csgtw %t332, %t338
    jnz %t339, @then118, @else119
@then118
    storew %t332, %t333
    jmp @merge120
@else119
    jmp @merge120
@merge120
    %t340 =w loadw %t333
    ret %t340
}

export function w $min4(w %a0, w %a1, w %a2, w %a3) {
@start121
    %t341 =w copy %a0
    %t342 =w copy %a1
    %t343 =w copy %a2
    %t344 =w copy %a3
    %t345 =l alloc4 4
    storew %t341, %t345
    %t346 =w loadw %t345
    %t347 =w csltw %t342, %t346
    jnz %t347, @then122, @else123
@then122
    storew %t342, %t345
    jmp @merge124
@else123
    jmp @merge124
@merge124
    %t348 =w loadw %t345
    %t349 =w csltw %t343, %t348
    jnz %t349, @then125, @else126
@then125
    storew %t343, %t345
    jmp @merge127
@else126
    jmp @merge127
@merge127
    %t350 =w loadw %t345
    %t351 =w csltw %t344, %t350
    jnz %t351, @then128, @else129
@then128
    storew %t344, %t345
    jmp @merge130
@else129
    jmp @merge130
@merge130
    %t352 =w loadw %t345
    ret %t352
}

export function w $dot3(w %a0, w %a1, w %a2, w %b0, w %b1, w %b2) {
@start131
    %t353 =w copy %a0
    %t354 =w copy %a1
    %t355 =w copy %a2
    %t356 =w copy %b0
    %t357 =w copy %b1
    %t358 =w copy %b2
    %t359 =w mul %t353, %t356
    %t360 =w mul %t354, %t357
    %t361 =w add %t359, %t360
    %t362 =w mul %t355, %t358
    %t363 =w add %t361, %t362
    ret %t363
}

export function w $array_reverse_partial() {
@start132
    %t364 =l alloc16 16
    %t365 =w copy 10
    storew %t365, %t364
    %t366 =w copy 20
    %t367 =l copy 4
    %t368 =l add %t364, %t367
    storew %t366, %t368
    %t369 =w copy 30
    %t370 =l copy 8
    %t371 =l add %t364, %t370
    storew %t369, %t371
    %t372 =w copy 40
    %t373 =l copy 12
    %t374 =l add %t364, %t373
    storew %t372, %t374
    %t375 =w copy 0
    %t376 =l copy 0
    %t377 =l add %t364, %t376
    %t378 =w loadw %t377
    %t379 =w copy 1
    %t380 =l copy 4
    %t381 =l add %t364, %t380
    %t382 =w loadw %t381
    %t383 =w copy 2
    %t384 =l copy 8
    %t385 =l add %t364, %t384
    %t386 =w loadw %t385
    %t387 =w copy 3
    %t388 =l copy 12
    %t389 =l add %t364, %t388
    %t390 =w loadw %t389
    %t391 =w add %t378, %t382
    %t392 =w add %t391, %t386
    %t393 =w add %t392, %t390
    ret %t393
}

export function w $swap_via_ptr(l %a, l %b) {
@start133
    %t394 =l copy %a
    %t395 =l copy %b
    %t396 =w loadw %t394
    %t397 =w loadw %t395
    storew %t397, %t394
    storew %t396, %t395
    %t398 =w loadw %t394
    %t399 =w loadw %t395
    %t400 =w add %t398, %t399
    ret %t400
}

export function w $modify_via_ptr(l %p, w %delta) {
@start134
    %t401 =l copy %p
    %t402 =w copy %delta
    %t403 =w loadw %t401
    %t404 =w add %t403, %t402
    storew %t404, %t401
    %t405 =w loadw %t401
    ret %t405
}

export function w $ptr_field_writes() {
@start135
    %t406 =l alloc8 8
    %t407 =w copy 5
    %t408 =l add %t406, 0
    storew %t407, %t408
    %t409 =w copy 7
    %t410 =l add %t406, 4
    storew %t409, %t410
    %t411 =l copy 0
    %t412 =w loadw %t406
    %t413 =l add %t406, 4
    %t414 =w loadw %t413
    %t415 =w add %t412, %t414
    ret %t415
}

export function w $ptr_array_writes() {
@start136
    %t416 =l alloc16 16
    %t417 =w copy 1
    storew %t417, %t416
    %t418 =w copy 2
    %t419 =l copy 4
    %t420 =l add %t416, %t419
    storew %t418, %t420
    %t421 =w copy 3
    %t422 =l copy 8
    %t423 =l add %t416, %t422
    storew %t421, %t423
    %t424 =w copy 4
    %t425 =l copy 12
    %t426 =l add %t416, %t425
    storew %t424, %t426
    %t427 =l copy 0
    %t428 =w copy 10
    %t429 =w copy 0
    %t430 =l copy 0
    %t431 =l add %t416, %t430
    storew %t428, %t431
    %t432 =w copy 30
    %t433 =w copy 2
    %t434 =l copy 8
    %t435 =l add %t416, %t434
    storew %t432, %t435
    %t436 =w copy 0
    %t437 =l copy 0
    %t438 =l add %t416, %t437
    %t439 =w loadw %t438
    %t440 =w copy 1
    %t441 =l copy 4
    %t442 =l add %t416, %t441
    %t443 =w loadw %t442
    %t444 =w add %t439, %t443
    %t445 =w copy 2
    %t446 =l copy 8
    %t447 =l add %t416, %t446
    %t448 =w loadw %t447
    %t449 =w add %t444, %t448
    %t450 =w copy 3
    %t451 =l copy 12
    %t452 =l add %t416, %t451
    %t453 =w loadw %t452
    %t454 =w add %t449, %t453
    ret %t454
}

export function w $sum_even_to(w %n) {
@start137
    %t455 =w copy %n
    %t456 =w copy 0
    %t457 =l alloc4 4
    storew %t456, %t457
    %t458 =w copy 0
    %t459 =l alloc4 4
    storew %t458, %t459
    jmp @loop138
@loop138
    %t460 =w loadw %t459
    %t461 =w cslew %t460, %t455
    jnz %t461, @body139, @exit140
@body139
    %t462 =w loadw %t459
    %t463 =w copy 2
    %t464 =w rem %t462, %t463
    %t465 =w copy 0
    %t466 =w ceqw %t464, %t465
    jnz %t466, @then141, @else142
@then141
    %t467 =w loadw %t457
    %t468 =w loadw %t459
    %t469 =w add %t467, %t468
    storew %t469, %t457
    jmp @merge143
@else142
    jmp @merge143
@merge143
    %t470 =w loadw %t459
    %t471 =w copy 1
    %t472 =w add %t470, %t471
    storew %t472, %t459
    jmp @loop138
@exit140
    %t473 =w loadw %t457
    ret %t473
}

export function w $sum_odd_to(w %n) {
@start144
    %t474 =w copy %n
    %t475 =w copy 0
    %t476 =l alloc4 4
    storew %t475, %t476
    %t477 =w copy 1
    %t478 =l alloc4 4
    storew %t477, %t478
    jmp @loop145
@loop145
    %t479 =w loadw %t478
    %t480 =w cslew %t479, %t474
    jnz %t480, @body146, @exit147
@body146
    %t481 =w loadw %t476
    %t482 =w loadw %t478
    %t483 =w add %t481, %t482
    storew %t483, %t476
    %t484 =w loadw %t478
    %t485 =w copy 2
    %t486 =w add %t484, %t485
    storew %t486, %t478
    jmp @loop145
@exit147
    %t487 =w loadw %t476
    ret %t487
}

export function w $nested_loop_sum(w %rows, w %cols) {
@start148
    %t488 =w copy %rows
    %t489 =w copy %cols
    %t490 =w copy 0
    %t491 =l alloc4 4
    storew %t490, %t491
    %t492 =w copy 0
    %t493 =l alloc4 4
    storew %t492, %t493
    jmp @loop149
@loop149
    %t494 =w loadw %t493
    %t495 =w csltw %t494, %t488
    jnz %t495, @body150, @exit151
@body150
    %t496 =w copy 0
    %t497 =l alloc4 4
    storew %t496, %t497
    jmp @loop152
@loop152
    %t498 =w loadw %t497
    %t499 =w csltw %t498, %t489
    jnz %t499, @body153, @exit154
@body153
    %t500 =w loadw %t491
    %t501 =w copy 1
    %t502 =w add %t500, %t501
    storew %t502, %t491
    %t503 =w loadw %t497
    %t504 =w copy 1
    %t505 =w add %t503, %t504
    storew %t505, %t497
    jmp @loop152
@exit154
    %t506 =w loadw %t493
    %t507 =w copy 1
    %t508 =w add %t506, %t507
    storew %t508, %t493
    jmp @loop149
@exit151
    %t509 =w loadw %t491
    ret %t509
}

export function w $for_sum(w %start, w %end) {
@start155
    %t510 =w copy %start
    %t511 =w copy %end
    %t512 =w copy 0
    %t513 =l alloc4 4
    storew %t512, %t513
    %t514 =l alloc4 4
    storew %t510, %t514
    jmp @loop156
@loop156
    %t515 =w loadw %t514
    %t516 =w csltw %t515, %t511
    jnz %t516, @body157, @exit159
@body157
    %t517 =w loadw %t513
    %t518 =w loadw %t514
    %t519 =w add %t517, %t518
    storew %t519, %t513
@incr158
    %t520 =w loadw %t514
    %t521 =w add %t520, 1
    storew %t521, %t514
    jmp @loop156
@exit159
    %t522 =w loadw %t513
    ret %t522
}

export function w $for_break_at(w %target) {
@start160
    %t523 =w copy %target
    %t524 =w copy 0
    %t525 =l alloc4 4
    storew %t524, %t525
    %t526 =w copy 0
    %t527 =w copy 100
    %t528 =l alloc4 4
    storew %t526, %t528
    jmp @loop161
@loop161
    %t529 =w loadw %t528
    %t530 =w csltw %t529, %t527
    jnz %t530, @body162, @exit164
@body162
    %t531 =w loadw %t528
    %t532 =w ceqw %t531, %t523
    jnz %t532, @then165, @else166
@then165
    %t533 =w loadw %t528
    storew %t533, %t525
    jmp @exit164
@else166
    jmp @merge167
@merge167
    %t534 =w loadw %t528
    storew %t534, %t525
@incr163
    %t535 =w loadw %t528
    %t536 =w add %t535, 1
    storew %t536, %t528
    jmp @loop161
@exit164
    %t537 =w loadw %t525
    ret %t537
}

export function w $for_continue_sum_evens(w %end) {
@start168
    %t538 =w copy %end
    %t539 =w copy 0
    %t540 =l alloc4 4
    storew %t539, %t540
    %t541 =w copy 0
    %t542 =l alloc4 4
    storew %t541, %t542
    jmp @loop169
@loop169
    %t543 =w loadw %t542
    %t544 =w csltw %t543, %t538
    jnz %t544, @body170, @exit172
@body170
    %t545 =w loadw %t542
    %t546 =w copy 2
    %t547 =w rem %t545, %t546
    %t548 =w copy 0
    %t549 =w cnew %t547, %t548
    jnz %t549, @then173, @else174
@then173
    jmp @incr171
@else174
    jmp @merge175
@merge175
    %t550 =w loadw %t540
    %t551 =w loadw %t542
    %t552 =w add %t550, %t551
    storew %t552, %t540
@incr171
    %t553 =w loadw %t542
    %t554 =w add %t553, 1
    storew %t554, %t542
    jmp @loop169
@exit172
    %t555 =w loadw %t540
    ret %t555
}

export function w $while_break_when_found(w %target) {
@start176
    %t556 =w copy %target
    %t557 =w copy 0
    %t558 =l alloc4 4
    storew %t557, %t558
    %t559 =w copy 0
    %t560 =l alloc4 4
    storew %t559, %t560
    jmp @loop177
@loop177
    %t561 =w loadw %t560
    %t562 =w copy 100
    %t563 =w csltw %t561, %t562
    jnz %t563, @body178, @exit179
@body178
    %t564 =w loadw %t560
    %t565 =w ceqw %t564, %t556
    jnz %t565, @then180, @else181
@then180
    %t566 =w loadw %t560
    storew %t566, %t558
    jmp @exit179
@else181
    jmp @merge182
@merge182
    %t567 =w loadw %t560
    %t568 =w copy 1
    %t569 =w add %t567, %t568
    storew %t569, %t560
    jmp @loop177
@exit179
    %t570 =w loadw %t558
    ret %t570
}

export function w $harmonic_sum(w %n) {
@start183
    %t571 =w copy %n
    %t572 =w copy 0
    %t573 =l alloc4 4
    storew %t572, %t573
    %t574 =w copy 1
    %t575 =l alloc4 4
    storew %t574, %t575
    jmp @loop184
@loop184
    %t576 =w loadw %t575
    %t577 =w cslew %t576, %t571
    jnz %t577, @body185, @exit186
@body185
    %t578 =w loadw %t573
    %t579 =w copy 1000
    %t580 =w loadw %t575
    %t581 =w div %t579, %t580
    %t582 =w add %t578, %t581
    storew %t582, %t573
    %t583 =w loadw %t575
    %t584 =w copy 1
    %t585 =w add %t583, %t584
    storew %t585, %t575
    jmp @loop184
@exit186
    %t586 =w loadw %t573
    ret %t586
}

export function w $collatz_steps(w %n) {
@start187
    %t587 =w copy %n
    %t588 =l alloc4 4
    storew %t587, %t588
    %t589 =w copy 0
    %t590 =l alloc4 4
    storew %t589, %t590
    jmp @loop188
@loop188
    %t591 =w loadw %t588
    %t592 =w copy 1
    %t593 =w cnew %t591, %t592
    jnz %t593, @body189, @exit190
@body189
    %t594 =w loadw %t588
    %t595 =w copy 2
    %t596 =w rem %t594, %t595
    %t597 =w copy 0
    %t598 =w ceqw %t596, %t597
    jnz %t598, @then191, @else192
@then191
    %t599 =w loadw %t588
    %t600 =w copy 2
    %t601 =w div %t599, %t600
    storew %t601, %t588
    jmp @merge193
@else192
    %t602 =w loadw %t588
    %t603 =w copy 3
    %t604 =w mul %t602, %t603
    %t605 =w copy 1
    %t606 =w add %t604, %t605
    storew %t606, %t588
    jmp @ep194
@ep194
    jmp @merge193
@merge193
    %t607 =w loadw %t590
    %t608 =w copy 1
    %t609 =w add %t607, %t608
    storew %t609, %t590
    jmp @loop188
@exit190
    %t610 =w loadw %t590
    ret %t610
}

export function w $is_prime(w %n) {
@start195
    %t611 =w copy %n
    %t612 =w copy 2
    %t613 =w csltw %t611, %t612
    jnz %t613, @then196, @else197
@then196
    %t614 =w copy 0
    ret %t614
@else197
    jmp @merge198
@merge198
    %t615 =w copy 2
    %t616 =w ceqw %t611, %t615
    jnz %t616, @then199, @else200
@then199
    %t617 =w copy 1
    ret %t617
@else200
    jmp @merge201
@merge201
    %t618 =w copy 2
    %t619 =w rem %t611, %t618
    %t620 =w copy 0
    %t621 =w ceqw %t619, %t620
    jnz %t621, @then202, @else203
@then202
    %t622 =w copy 0
    ret %t622
@else203
    jmp @merge204
@merge204
    %t623 =w copy 3
    %t624 =l alloc4 4
    storew %t623, %t624
    jmp @loop205
@loop205
    %t625 =w loadw %t624
    %t626 =w loadw %t624
    %t627 =w mul %t625, %t626
    %t628 =w cslew %t627, %t611
    jnz %t628, @body206, @exit207
@body206
    %t629 =w loadw %t624
    %t630 =w rem %t611, %t629
    %t631 =w copy 0
    %t632 =w ceqw %t630, %t631
    jnz %t632, @then208, @else209
@then208
    %t633 =w copy 0
    ret %t633
@else209
    jmp @merge210
@merge210
    %t634 =w loadw %t624
    %t635 =w copy 2
    %t636 =w add %t634, %t635
    storew %t636, %t624
    jmp @loop205
@exit207
    %t637 =w copy 1
    ret %t637
}

export function w $count_primes_up_to(w %n) {
@start211
    %t638 =w copy %n
    %t639 =w copy 0
    %t640 =l alloc4 4
    storew %t639, %t640
    %t641 =w copy 2
    %t642 =l alloc4 4
    storew %t641, %t642
    jmp @loop212
@loop212
    %t643 =w loadw %t642
    %t644 =w cslew %t643, %t638
    jnz %t644, @body213, @exit214
@body213
    %t645 =w loadw %t642
    %t646 =w call $is_prime(w %t645)
    %t647 =w copy 0
    %t648 =w cnew %t646, %t647
    jnz %t648, @then215, @else216
@then215
    %t649 =w loadw %t640
    %t650 =w copy 1
    %t651 =w add %t649, %t650
    storew %t651, %t640
    jmp @merge217
@else216
    jmp @merge217
@merge217
    %t652 =w loadw %t642
    %t653 =w copy 1
    %t654 =w add %t652, %t653
    storew %t654, %t642
    jmp @loop212
@exit214
    %t655 =w loadw %t640
    ret %t655
}

export function w $next_prime_after(w %n) {
@start218
    %t656 =w copy %n
    %t657 =w copy 1
    %t658 =w add %t656, %t657
    %t659 =l alloc4 4
    storew %t658, %t659
    %t660 =w copy 0
    %t661 =l alloc4 4
    storew %t660, %t661
    %t662 =w copy 0
    %t663 =l alloc4 4
    storew %t662, %t663
    jmp @loop219
@loop219
    %t664 =w loadw %t661
    %t665 =w copy 0
    %t666 =w ceqw %t664, %t665
    jnz %t666, @body220, @exit221
@body220
    %t667 =w loadw %t659
    %t668 =w call $is_prime(w %t667)
    %t669 =w copy 0
    %t670 =w cnew %t668, %t669
    jnz %t670, @then222, @else223
@then222
    %t671 =w copy 1
    storew %t671, %t661
    %t672 =w loadw %t659
    storew %t672, %t663
    jmp @merge224
@else223
    %t673 =w loadw %t659
    %t674 =w copy 1
    %t675 =w add %t673, %t674
    storew %t675, %t659
    jmp @ep225
@ep225
    jmp @merge224
@merge224
    jmp @loop219
@exit221
    %t676 =w loadw %t663
    ret %t676
}

export function w $check_eq(w %actual, w %expected) {
@start226
    %t677 =w copy %actual
    %t678 =w copy %expected
    %t679 =w copy 0
    %t680 =l alloc4 4
    storew %t679, %t680
    %t681 =w cnew %t677, %t678
    jnz %t681, @then227, @else228
@then227
    %t682 =w copy 1
    storew %t682, %t680
    jmp @merge229
@else228
    jmp @merge229
@merge229
    %t683 =w loadw %t680
    ret %t683
}

export function w $t_add3() {
@start230
    %t684 =w copy 1
    %t685 =w copy 2
    %t686 =w copy 3
    %t687 =w call $add3(w %t684, w %t685, w %t686)
    %t688 =w copy 6
    %t689 =w call $check_eq(w %t687, w %t688)
    ret %t689
}

export function w $t_mul4() {
@start231
    %t690 =w copy 1
    %t691 =w copy 2
    %t692 =w copy 3
    %t693 =w copy 4
    %t694 =w call $mul4(w %t690, w %t691, w %t692, w %t693)
    %t695 =w copy 24
    %t696 =w call $check_eq(w %t694, w %t695)
    ret %t696
}

export function w $t_mixed() {
@start232
    %t697 =w copy 10
    %t698 =w copy 4
    %t699 =w call $mixed_ops(w %t697, w %t698)
    %t700 =w copy 69
    %t701 =w call $check_eq(w %t699, w %t700)
    ret %t701
}

export function w $t_negate() {
@start233
    %t702 =w copy 13
    %t703 =w call $negate_via_sub(w %t702)
    %t704 =w copy 0
    %t705 =w copy 13
    %t706 =w sub %t704, %t705
    %t707 =w call $check_eq(w %t703, w %t706)
    ret %t707
}

export function w $t_abs_diff() {
@start234
    %t708 =w copy 7
    %t709 =w copy 12
    %t710 =w call $abs_diff(w %t708, w %t709)
    %t711 =w copy 5
    %t712 =w call $check_eq(w %t710, w %t711)
    ret %t712
}

export function w $t_clamp() {
@start235
    %t713 =w copy 0
    %t714 =l alloc4 4
    storew %t713, %t714
    %t715 =w copy 0
    %t716 =w copy 3
    %t717 =w sub %t715, %t716
    %t718 =w call $clamp_pos(w %t717)
    %t719 =w copy 0
    %t720 =w cnew %t718, %t719
    jnz %t720, @then236, @else237
@then236
    %t721 =w copy 1
    storew %t721, %t714
    jmp @merge238
@else237
    jmp @merge238
@merge238
    %t722 =w copy 7
    %t723 =w call $clamp_pos(w %t722)
    %t724 =w copy 7
    %t725 =w cnew %t723, %t724
    jnz %t725, @then239, @else240
@then239
    %t726 =w copy 1
    storew %t726, %t714
    jmp @merge241
@else240
    jmp @merge241
@merge241
    %t727 =w loadw %t714
    ret %t727
}

export function w $t_fact() {
@start242
    %t728 =w copy 5
    %t729 =w call $fact(w %t728)
    %t730 =w copy 120
    %t731 =w call $check_eq(w %t729, w %t730)
    ret %t731
}

export function w $t_fib() {
@start243
    %t732 =w copy 10
    %t733 =w call $fib(w %t732)
    %t734 =w copy 55
    %t735 =w call $check_eq(w %t733, w %t734)
    ret %t735
}

export function w $t_gcd() {
@start244
    %t736 =w copy 48
    %t737 =w copy 18
    %t738 =w call $gcd(w %t736, w %t737)
    %t739 =w copy 6
    %t740 =w call $check_eq(w %t738, w %t739)
    ret %t740
}

export function w $t_sum_to() {
@start245
    %t741 =w copy 10
    %t742 =w call $sum_to(w %t741)
    %t743 =w copy 55
    %t744 =w call $check_eq(w %t742, w %t743)
    ret %t744
}

export function w $t_power() {
@start246
    %t745 =w copy 2
    %t746 =w copy 10
    %t747 =w call $power(w %t745, w %t746)
    %t748 =w copy 1024
    %t749 =w call $check_eq(w %t747, w %t748)
    ret %t749
}

export function w $t_sum_digits() {
@start247
    %t750 =w copy 1234
    %t751 =w call $sum_digits_iterative(w %t750)
    %t752 =w copy 10
    %t753 =w call $check_eq(w %t751, w %t752)
    ret %t753
}

export function w $t_is_positive() {
@start248
    %t754 =w copy 0
    %t755 =l alloc4 4
    storew %t754, %t755
    %t756 =w copy 5
    %t757 =w call $is_positive(w %t756)
    %t758 =w copy 1
    %t759 =w cnew %t757, %t758
    jnz %t759, @then249, @else250
@then249
    %t760 =w copy 1
    storew %t760, %t755
    jmp @merge251
@else250
    jmp @merge251
@merge251
    %t761 =w copy 0
    %t762 =w copy 3
    %t763 =w sub %t761, %t762
    %t764 =w call $is_positive(w %t763)
    %t765 =w copy 0
    %t766 =w cnew %t764, %t765
    jnz %t766, @then252, @else253
@then252
    %t767 =w copy 1
    storew %t767, %t755
    jmp @merge254
@else253
    jmp @merge254
@merge254
    %t768 =w loadw %t755
    ret %t768
}

export function w $t_in_range() {
@start255
    %t769 =w copy 0
    %t770 =l alloc4 4
    storew %t769, %t770
    %t771 =w copy 5
    %t772 =w copy 1
    %t773 =w copy 10
    %t774 =w call $is_in_range(w %t771, w %t772, w %t773)
    %t775 =w copy 1
    %t776 =w cnew %t774, %t775
    jnz %t776, @then256, @else257
@then256
    %t777 =w copy 1
    storew %t777, %t770
    jmp @merge258
@else257
    jmp @merge258
@merge258
    %t778 =w copy 15
    %t779 =w copy 1
    %t780 =w copy 10
    %t781 =w call $is_in_range(w %t778, w %t779, w %t780)
    %t782 =w copy 0
    %t783 =w cnew %t781, %t782
    jnz %t783, @then259, @else260
@then259
    %t784 =w copy 1
    storew %t784, %t770
    jmp @merge261
@else260
    jmp @merge261
@merge261
    %t785 =w loadw %t770
    ret %t785
}

export function w $t_max3() {
@start262
    %t786 =w copy 3
    %t787 =w copy 7
    %t788 =w copy 5
    %t789 =w call $max3(w %t786, w %t787, w %t788)
    %t790 =w copy 7
    %t791 =w call $check_eq(w %t789, w %t790)
    ret %t791
}

export function w $t_min3() {
@start263
    %t792 =w copy 3
    %t793 =w copy 7
    %t794 =w copy 5
    %t795 =w call $min3(w %t792, w %t793, w %t794)
    %t796 =w copy 3
    %t797 =w call $check_eq(w %t795, w %t796)
    ret %t797
}

export function w $t_sign() {
@start264
    %t798 =w copy 0
    %t799 =l alloc4 4
    storew %t798, %t799
    %t800 =w copy 5
    %t801 =w call $sign(w %t800)
    %t802 =w copy 1
    %t803 =w cnew %t801, %t802
    jnz %t803, @then265, @else266
@then265
    %t804 =w copy 1
    storew %t804, %t799
    jmp @merge267
@else266
    jmp @merge267
@merge267
    %t805 =w copy 0
    %t806 =w copy 3
    %t807 =w sub %t805, %t806
    %t808 =w call $sign(w %t807)
    %t809 =w copy 0
    %t810 =w copy 1
    %t811 =w sub %t809, %t810
    %t812 =w cnew %t808, %t811
    jnz %t812, @then268, @else269
@then268
    %t813 =w copy 1
    storew %t813, %t799
    jmp @merge270
@else269
    jmp @merge270
@merge270
    %t814 =w copy 0
    %t815 =w call $sign(w %t814)
    %t816 =w copy 0
    %t817 =w cnew %t815, %t816
    jnz %t817, @then271, @else272
@then271
    %t818 =w copy 1
    storew %t818, %t799
    jmp @merge273
@else272
    jmp @merge273
@merge273
    %t819 =w loadw %t799
    ret %t819
}

export function w $t_bit_pack() {
@start274
    %t820 =w copy 18
    %t821 =w copy 52
    %t822 =w copy 86
    %t823 =w copy 120
    %t824 =w call $bit_pack(w %t820, w %t821, w %t822, w %t823)
    %t825 =w copy 2018915346
    %t826 =w call $check_eq(w %t824, w %t825)
    ret %t826
}

export function w $t_bit_unpack() {
@start275
    %t827 =w copy 170
    %t828 =w copy 187
    %t829 =w copy 204
    %t830 =w copy 221
    %t831 =w call $bit_pack(w %t827, w %t828, w %t829, w %t830)
    %t832 =w copy 0
    %t833 =w call $bit_unpack_byte(w %t831, w %t832)
    %t834 =w copy 1
    %t835 =w call $bit_unpack_byte(w %t831, w %t834)
    %t836 =w copy 2
    %t837 =w call $bit_unpack_byte(w %t831, w %t836)
    %t838 =w copy 3
    %t839 =w call $bit_unpack_byte(w %t831, w %t838)
    %t840 =w copy 0
    %t841 =l alloc4 4
    storew %t840, %t841
    %t842 =w copy 170
    %t843 =w cnew %t833, %t842
    jnz %t843, @then276, @else277
@then276
    %t844 =w copy 1
    storew %t844, %t841
    jmp @merge278
@else277
    jmp @merge278
@merge278
    %t845 =w copy 187
    %t846 =w cnew %t835, %t845
    jnz %t846, @then279, @else280
@then279
    %t847 =w copy 1
    storew %t847, %t841
    jmp @merge281
@else280
    jmp @merge281
@merge281
    %t848 =w copy 204
    %t849 =w cnew %t837, %t848
    jnz %t849, @then282, @else283
@then282
    %t850 =w copy 1
    storew %t850, %t841
    jmp @merge284
@else283
    jmp @merge284
@merge284
    %t851 =w copy 221
    %t852 =w cnew %t839, %t851
    jnz %t852, @then285, @else286
@then285
    %t853 =w copy 1
    storew %t853, %t841
    jmp @merge287
@else286
    jmp @merge287
@merge287
    %t854 =w loadw %t841
    ret %t854
}

export function w $t_count_set_bits() {
@start288
    %t855 =w copy 181
    %t856 =w call $count_set_bits(w %t855)
    %t857 =w copy 5
    %t858 =w call $check_eq(w %t856, w %t857)
    ret %t858
}

export function w $t_bit_xor() {
@start289
    %t859 =w copy 15
    %t860 =w copy 240
    %t861 =w call $bit_xor_pattern(w %t859, w %t860)
    %t862 =w copy 255
    %t863 =w call $check_eq(w %t861, w %t862)
    ret %t863
}

export function w $t_bit_or() {
@start290
    %t864 =w copy 15
    %t865 =w copy 240
    %t866 =w call $bit_or_pattern(w %t864, w %t865)
    %t867 =w copy 255
    %t868 =w call $check_eq(w %t866, w %t867)
    ret %t868
}

export function w $t_bit_and() {
@start291
    %t869 =w copy 255
    %t870 =w copy 15
    %t871 =w call $bit_and_pattern(w %t869, w %t870)
    %t872 =w copy 15
    %t873 =w call $check_eq(w %t871, w %t872)
    ret %t873
}

export function w $t_shifts() {
@start292
    %t874 =w copy 0
    %t875 =l alloc4 4
    storew %t874, %t875
    %t876 =w copy 1
    %t877 =w copy 8
    %t878 =w call $shift_left(w %t876, w %t877)
    %t879 =w copy 256
    %t880 =w cnew %t878, %t879
    jnz %t880, @then293, @else294
@then293
    %t881 =w copy 1
    storew %t881, %t875
    jmp @merge295
@else294
    jmp @merge295
@merge295
    %t882 =w copy 256
    %t883 =w copy 4
    %t884 =w call $shift_right(w %t882, w %t883)
    %t885 =w copy 16
    %t886 =w cnew %t884, %t885
    jnz %t886, @then296, @else297
@then296
    %t887 =w copy 1
    storew %t887, %t875
    jmp @merge298
@else297
    jmp @merge298
@merge298
    %t888 =w loadw %t875
    ret %t888
}

export function w $t_point_basic() {
@start299
    %t889 =l alloc8 8
    %t890 =w copy 3
    %t891 =w copy 4
    call $make_point(l %t889, w %t890, w %t891)
    %t892 =l alloc8 8
    %t893 =l copy %t889
    %t894 =l copy %t892
    %t895 =w loadw %t893
    storew %t895, %t894
    %t896 =l add %t889, 4
    %t897 =l add %t892, 4
    %t898 =w loadw %t896
    storew %t898, %t897
    %t899 =w copy 0
    %t900 =l alloc4 4
    storew %t899, %t900
    %t901 =w loadw %t892
    %t902 =w copy 3
    %t903 =w cnew %t901, %t902
    jnz %t903, @then300, @else301
@then300
    %t904 =w copy 1
    storew %t904, %t900
    jmp @merge302
@else301
    jmp @merge302
@merge302
    %t905 =l add %t892, 4
    %t906 =w loadw %t905
    %t907 =w copy 4
    %t908 =w cnew %t906, %t907
    jnz %t908, @then303, @else304
@then303
    %t909 =w copy 1
    storew %t909, %t900
    jmp @merge305
@else304
    jmp @merge305
@merge305
    %t910 =l alloc8 8
    %t911 =l copy %t892
    %t912 =l copy %t910
    %t913 =w loadw %t911
    storew %t913, %t912
    %t914 =l add %t892, 4
    %t915 =l add %t910, 4
    %t916 =w loadw %t914
    storew %t916, %t915
    %t917 =w call $point_sum(l %t910)
    %t918 =w copy 7
    %t919 =w cnew %t917, %t918
    jnz %t919, @then306, @else307
@then306
    %t920 =w copy 1
    storew %t920, %t900
    jmp @merge308
@else307
    jmp @merge308
@merge308
    %t921 =w loadw %t900
    ret %t921
}

export function w $t_point_ops() {
@start309
    %t922 =l alloc8 8
    %t923 =w copy 2
    %t924 =w copy 3
    call $make_point(l %t922, w %t923, w %t924)
    %t925 =l alloc8 8
    %t926 =l copy %t922
    %t927 =l copy %t925
    %t928 =w loadw %t926
    storew %t928, %t927
    %t929 =l add %t922, 4
    %t930 =l add %t925, 4
    %t931 =w loadw %t929
    storew %t931, %t930
    %t932 =l alloc8 8
    %t933 =l alloc8 8
    %t934 =l copy %t925
    %t935 =l copy %t933
    %t936 =w loadw %t934
    storew %t936, %t935
    %t937 =l add %t925, 4
    %t938 =l add %t933, 4
    %t939 =w loadw %t937
    storew %t939, %t938
    %t940 =w copy 5
    call $point_scale(l %t932, l %t933, w %t940)
    %t941 =l alloc8 8
    %t942 =l copy %t932
    %t943 =l copy %t941
    %t944 =w loadw %t942
    storew %t944, %t943
    %t945 =l add %t932, 4
    %t946 =l add %t941, 4
    %t947 =w loadw %t945
    storew %t947, %t946
    %t948 =l alloc8 8
    %t949 =l alloc8 8
    %t950 =l copy %t925
    %t951 =l copy %t949
    %t952 =w loadw %t950
    storew %t952, %t951
    %t953 =l add %t925, 4
    %t954 =l add %t949, 4
    %t955 =w loadw %t953
    storew %t955, %t954
    %t956 =w copy 10
    %t957 =w copy 20
    call $point_translate(l %t948, l %t949, w %t956, w %t957)
    %t958 =l alloc8 8
    %t959 =l copy %t948
    %t960 =l copy %t958
    %t961 =w loadw %t959
    storew %t961, %t960
    %t962 =l add %t948, 4
    %t963 =l add %t958, 4
    %t964 =w loadw %t962
    storew %t964, %t963
    %t965 =w copy 0
    %t966 =l alloc4 4
    storew %t965, %t966
    %t967 =l alloc8 8
    %t968 =l copy %t941
    %t969 =l copy %t967
    %t970 =w loadw %t968
    storew %t970, %t969
    %t971 =l add %t941, 4
    %t972 =l add %t967, 4
    %t973 =w loadw %t971
    storew %t973, %t972
    %t974 =w call $point_sum(l %t967)
    %t975 =w copy 25
    %t976 =w cnew %t974, %t975
    jnz %t976, @then310, @else311
@then310
    %t977 =w copy 1
    storew %t977, %t966
    jmp @merge312
@else311
    jmp @merge312
@merge312
    %t978 =l alloc8 8
    %t979 =l copy %t958
    %t980 =l copy %t978
    %t981 =w loadw %t979
    storew %t981, %t980
    %t982 =l add %t958, 4
    %t983 =l add %t978, 4
    %t984 =w loadw %t982
    storew %t984, %t983
    %t985 =w call $point_sum(l %t978)
    %t986 =w copy 35
    %t987 =w cnew %t985, %t986
    jnz %t987, @then313, @else314
@then313
    %t988 =w copy 1
    storew %t988, %t966
    jmp @merge315
@else314
    jmp @merge315
@merge315
    %t989 =w loadw %t966
    ret %t989
}

export function w $t_point_diff() {
@start316
    %t990 =l alloc8 8
    %t991 =w copy 10
    %t992 =w copy 3
    call $make_point(l %t990, w %t991, w %t992)
    %t993 =l alloc8 8
    %t994 =l copy %t990
    %t995 =l copy %t993
    %t996 =w loadw %t994
    storew %t996, %t995
    %t997 =l add %t990, 4
    %t998 =l add %t993, 4
    %t999 =w loadw %t997
    storew %t999, %t998
    %t1000 =l alloc8 8
    %t1001 =l copy %t993
    %t1002 =l copy %t1000
    %t1003 =w loadw %t1001
    storew %t1003, %t1002
    %t1004 =l add %t993, 4
    %t1005 =l add %t1000, 4
    %t1006 =w loadw %t1004
    storew %t1006, %t1005
    %t1007 =w call $point_diff(l %t1000)
    %t1008 =w copy 7
    %t1009 =w call $check_eq(w %t1007, w %t1008)
    ret %t1009
}

export function w $t_rect_area() {
@start317
    %t1010 =l alloc16 16
    %t1011 =w copy 0
    %t1012 =l add %t1010, 0
    storew %t1011, %t1012
    %t1013 =w copy 0
    %t1014 =l add %t1010, 4
    storew %t1013, %t1014
    %t1015 =w copy 5
    %t1016 =l add %t1010, 8
    storew %t1015, %t1016
    %t1017 =w copy 4
    %t1018 =l add %t1010, 12
    storew %t1017, %t1018
    %t1019 =l alloc16 16
    %t1020 =l copy %t1010
    %t1021 =l copy %t1019
    %t1022 =w loadw %t1020
    storew %t1022, %t1021
    %t1023 =l add %t1010, 4
    %t1024 =l add %t1019, 4
    %t1025 =w loadw %t1023
    storew %t1025, %t1024
    %t1026 =l add %t1010, 8
    %t1027 =l add %t1019, 8
    %t1028 =w loadw %t1026
    storew %t1028, %t1027
    %t1029 =l add %t1010, 12
    %t1030 =l add %t1019, 12
    %t1031 =w loadw %t1029
    storew %t1031, %t1030
    %t1032 =w call $rect_area(l %t1019)
    %t1033 =w copy 20
    %t1034 =w call $check_eq(w %t1032, w %t1033)
    ret %t1034
}

export function w $t_triple() {
@start318
    %t1035 =l alloc16 16
    %t1036 =w copy 5
    %t1037 =l add %t1035, 0
    storew %t1036, %t1037
    %t1038 =w copy 12
    %t1039 =l add %t1035, 4
    storew %t1038, %t1039
    %t1040 =w copy 7
    %t1041 =l add %t1035, 8
    storew %t1040, %t1041
    %t1042 =w copy 0
    %t1043 =l alloc4 4
    storew %t1042, %t1043
    %t1044 =l alloc16 16
    %t1045 =l copy %t1035
    %t1046 =l copy %t1044
    %t1047 =w loadw %t1045
    storew %t1047, %t1046
    %t1048 =l add %t1035, 4
    %t1049 =l add %t1044, 4
    %t1050 =w loadw %t1048
    storew %t1050, %t1049
    %t1051 =l add %t1035, 8
    %t1052 =l add %t1044, 8
    %t1053 =w loadw %t1051
    storew %t1053, %t1052
    %t1054 =w call $triple_sum(l %t1044)
    %t1055 =w copy 24
    %t1056 =w cnew %t1054, %t1055
    jnz %t1056, @then319, @else320
@then319
    %t1057 =w copy 1
    storew %t1057, %t1043
    jmp @merge321
@else320
    jmp @merge321
@merge321
    %t1058 =l alloc16 16
    %t1059 =l copy %t1035
    %t1060 =l copy %t1058
    %t1061 =w loadw %t1059
    storew %t1061, %t1060
    %t1062 =l add %t1035, 4
    %t1063 =l add %t1058, 4
    %t1064 =w loadw %t1062
    storew %t1064, %t1063
    %t1065 =l add %t1035, 8
    %t1066 =l add %t1058, 8
    %t1067 =w loadw %t1065
    storew %t1067, %t1066
    %t1068 =w call $triple_max(l %t1058)
    %t1069 =w copy 12
    %t1070 =w cnew %t1068, %t1069
    jnz %t1070, @then322, @else323
@then322
    %t1071 =w copy 1
    storew %t1071, %t1043
    jmp @merge324
@else323
    jmp @merge324
@merge324
    %t1072 =w loadw %t1043
    ret %t1072
}

export function w $t_array_sum() {
@start325
    %t1073 =l alloc16 16
    %t1074 =w copy 1
    storew %t1074, %t1073
    %t1075 =w copy 2
    %t1076 =l copy 4
    %t1077 =l add %t1073, %t1076
    storew %t1075, %t1077
    %t1078 =w copy 3
    %t1079 =l copy 8
    %t1080 =l add %t1073, %t1079
    storew %t1078, %t1080
    %t1081 =w copy 4
    %t1082 =l copy 12
    %t1083 =l add %t1073, %t1082
    storew %t1081, %t1083
    %t1084 =w copy 0
    %t1085 =l copy 0
    %t1086 =l add %t1073, %t1085
    %t1087 =w loadw %t1086
    %t1088 =w copy 1
    %t1089 =l copy 4
    %t1090 =l add %t1073, %t1089
    %t1091 =w loadw %t1090
    %t1092 =w copy 2
    %t1093 =l copy 8
    %t1094 =l add %t1073, %t1093
    %t1095 =w loadw %t1094
    %t1096 =w copy 3
    %t1097 =l copy 12
    %t1098 =l add %t1073, %t1097
    %t1099 =w loadw %t1098
    %t1100 =w call $sum_4(w %t1087, w %t1091, w %t1095, w %t1099)
    %t1101 =w copy 10
    %t1102 =w call $check_eq(w %t1100, w %t1101)
    ret %t1102
}

export function w $t_array_max() {
@start326
    %t1103 =l alloc16 16
    %t1104 =w copy 3
    storew %t1104, %t1103
    %t1105 =w copy 9
    %t1106 =l copy 4
    %t1107 =l add %t1103, %t1106
    storew %t1105, %t1107
    %t1108 =w copy 1
    %t1109 =l copy 8
    %t1110 =l add %t1103, %t1109
    storew %t1108, %t1110
    %t1111 =w copy 7
    %t1112 =l copy 12
    %t1113 =l add %t1103, %t1112
    storew %t1111, %t1113
    %t1114 =w copy 0
    %t1115 =l copy 0
    %t1116 =l add %t1103, %t1115
    %t1117 =w loadw %t1116
    %t1118 =w copy 1
    %t1119 =l copy 4
    %t1120 =l add %t1103, %t1119
    %t1121 =w loadw %t1120
    %t1122 =w copy 2
    %t1123 =l copy 8
    %t1124 =l add %t1103, %t1123
    %t1125 =w loadw %t1124
    %t1126 =w copy 3
    %t1127 =l copy 12
    %t1128 =l add %t1103, %t1127
    %t1129 =w loadw %t1128
    %t1130 =w call $max4(w %t1117, w %t1121, w %t1125, w %t1129)
    %t1131 =w copy 9
    %t1132 =w call $check_eq(w %t1130, w %t1131)
    ret %t1132
}

export function w $t_array_min() {
@start327
    %t1133 =l alloc16 16
    %t1134 =w copy 3
    storew %t1134, %t1133
    %t1135 =w copy 9
    %t1136 =l copy 4
    %t1137 =l add %t1133, %t1136
    storew %t1135, %t1137
    %t1138 =w copy 1
    %t1139 =l copy 8
    %t1140 =l add %t1133, %t1139
    storew %t1138, %t1140
    %t1141 =w copy 7
    %t1142 =l copy 12
    %t1143 =l add %t1133, %t1142
    storew %t1141, %t1143
    %t1144 =w copy 0
    %t1145 =l copy 0
    %t1146 =l add %t1133, %t1145
    %t1147 =w loadw %t1146
    %t1148 =w copy 1
    %t1149 =l copy 4
    %t1150 =l add %t1133, %t1149
    %t1151 =w loadw %t1150
    %t1152 =w copy 2
    %t1153 =l copy 8
    %t1154 =l add %t1133, %t1153
    %t1155 =w loadw %t1154
    %t1156 =w copy 3
    %t1157 =l copy 12
    %t1158 =l add %t1133, %t1157
    %t1159 =w loadw %t1158
    %t1160 =w call $min4(w %t1147, w %t1151, w %t1155, w %t1159)
    %t1161 =w copy 1
    %t1162 =w call $check_eq(w %t1160, w %t1161)
    ret %t1162
}

export function w $t_array_dot() {
@start328
    %t1163 =l alloc16 16
    %t1164 =w copy 1
    storew %t1164, %t1163
    %t1165 =w copy 2
    %t1166 =l copy 4
    %t1167 =l add %t1163, %t1166
    storew %t1165, %t1167
    %t1168 =w copy 3
    %t1169 =l copy 8
    %t1170 =l add %t1163, %t1169
    storew %t1168, %t1170
    %t1171 =l alloc16 16
    %t1172 =w copy 4
    storew %t1172, %t1171
    %t1173 =w copy 5
    %t1174 =l copy 4
    %t1175 =l add %t1171, %t1174
    storew %t1173, %t1175
    %t1176 =w copy 6
    %t1177 =l copy 8
    %t1178 =l add %t1171, %t1177
    storew %t1176, %t1178
    %t1179 =w copy 0
    %t1180 =l copy 0
    %t1181 =l add %t1163, %t1180
    %t1182 =w loadw %t1181
    %t1183 =w copy 1
    %t1184 =l copy 4
    %t1185 =l add %t1163, %t1184
    %t1186 =w loadw %t1185
    %t1187 =w copy 2
    %t1188 =l copy 8
    %t1189 =l add %t1163, %t1188
    %t1190 =w loadw %t1189
    %t1191 =w copy 0
    %t1192 =l copy 0
    %t1193 =l add %t1171, %t1192
    %t1194 =w loadw %t1193
    %t1195 =w copy 1
    %t1196 =l copy 4
    %t1197 =l add %t1171, %t1196
    %t1198 =w loadw %t1197
    %t1199 =w copy 2
    %t1200 =l copy 8
    %t1201 =l add %t1171, %t1200
    %t1202 =w loadw %t1201
    %t1203 =w call $dot3(w %t1182, w %t1186, w %t1190, w %t1194, w %t1198, w %t1202)
    %t1204 =w copy 32
    %t1205 =w call $check_eq(w %t1203, w %t1204)
    ret %t1205
}

export function w $t_ptr_field() {
@start329
    %t1206 =w call $ptr_field_writes()
    %t1207 =w copy 12
    %t1208 =w call $check_eq(w %t1206, w %t1207)
    ret %t1208
}

export function w $t_ptr_array() {
@start330
    %t1209 =w call $ptr_array_writes()
    %t1210 =w copy 46
    %t1211 =w call $check_eq(w %t1209, w %t1210)
    ret %t1211
}

export function w $t_swap_via_ptr() {
@start331
    %t1212 =w copy 5
    %t1213 =l alloc4 4
    storew %t1212, %t1213
    %t1214 =w copy 10
    %t1215 =l alloc4 4
    storew %t1214, %t1215
    %t1216 =l copy 0
    %t1217 =l copy 0
    %t1218 =w call $swap_via_ptr(l %t1213, l %t1215)
    %t1219 =w copy 0
    %t1220 =l alloc4 4
    storew %t1219, %t1220
    %t1221 =w copy 15
    %t1222 =w cnew %t1218, %t1221
    jnz %t1222, @then332, @else333
@then332
    %t1223 =w copy 1
    storew %t1223, %t1220
    jmp @merge334
@else333
    jmp @merge334
@merge334
    %t1224 =w loadw %t1213
    %t1225 =w copy 10
    %t1226 =w cnew %t1224, %t1225
    jnz %t1226, @then335, @else336
@then335
    %t1227 =w copy 1
    storew %t1227, %t1220
    jmp @merge337
@else336
    jmp @merge337
@merge337
    %t1228 =w loadw %t1215
    %t1229 =w copy 5
    %t1230 =w cnew %t1228, %t1229
    jnz %t1230, @then338, @else339
@then338
    %t1231 =w copy 1
    storew %t1231, %t1220
    jmp @merge340
@else339
    jmp @merge340
@merge340
    %t1232 =w loadw %t1220
    ret %t1232
}

export function w $t_modify_via_ptr() {
@start341
    %t1233 =w copy 100
    %t1234 =l alloc4 4
    storew %t1233, %t1234
    %t1235 =l copy 0
    %t1236 =w copy 25
    %t1237 =w call $modify_via_ptr(l %t1234, w %t1236)
    %t1238 =w copy 0
    %t1239 =l alloc4 4
    storew %t1238, %t1239
    %t1240 =w copy 125
    %t1241 =w cnew %t1237, %t1240
    jnz %t1241, @then342, @else343
@then342
    %t1242 =w copy 1
    storew %t1242, %t1239
    jmp @merge344
@else343
    jmp @merge344
@merge344
    %t1243 =w loadw %t1234
    %t1244 =w copy 125
    %t1245 =w cnew %t1243, %t1244
    jnz %t1245, @then345, @else346
@then345
    %t1246 =w copy 1
    storew %t1246, %t1239
    jmp @merge347
@else346
    jmp @merge347
@merge347
    %t1247 =w loadw %t1239
    ret %t1247
}

export function w $t_sum_even() {
@start348
    %t1248 =w copy 10
    %t1249 =w call $sum_even_to(w %t1248)
    %t1250 =w copy 30
    %t1251 =w call $check_eq(w %t1249, w %t1250)
    ret %t1251
}

export function w $t_sum_odd() {
@start349
    %t1252 =w copy 9
    %t1253 =w call $sum_odd_to(w %t1252)
    %t1254 =w copy 25
    %t1255 =w call $check_eq(w %t1253, w %t1254)
    ret %t1255
}

export function w $t_nested() {
@start350
    %t1256 =w copy 4
    %t1257 =w copy 5
    %t1258 =w call $nested_loop_sum(w %t1256, w %t1257)
    %t1259 =w copy 20
    %t1260 =w call $check_eq(w %t1258, w %t1259)
    ret %t1260
}

export function w $t_for_sum() {
@start351
    %t1261 =w copy 0
    %t1262 =w copy 10
    %t1263 =w call $for_sum(w %t1261, w %t1262)
    %t1264 =w copy 45
    %t1265 =w call $check_eq(w %t1263, w %t1264)
    ret %t1265
}

export function w $t_for_break() {
@start352
    %t1266 =w copy 7
    %t1267 =w call $for_break_at(w %t1266)
    %t1268 =w copy 7
    %t1269 =w call $check_eq(w %t1267, w %t1268)
    ret %t1269
}

export function w $t_for_continue() {
@start353
    %t1270 =w copy 11
    %t1271 =w call $for_continue_sum_evens(w %t1270)
    %t1272 =w copy 30
    %t1273 =w call $check_eq(w %t1271, w %t1272)
    ret %t1273
}

export function w $t_while_break() {
@start354
    %t1274 =w copy 13
    %t1275 =w call $while_break_when_found(w %t1274)
    %t1276 =w copy 13
    %t1277 =w call $check_eq(w %t1275, w %t1276)
    ret %t1277
}

export function w $t_harmonic() {
@start355
    %t1278 =w copy 10
    %t1279 =w call $harmonic_sum(w %t1278)
    %t1280 =w copy 2927
    %t1281 =w call $check_eq(w %t1279, w %t1280)
    ret %t1281
}

export function w $t_collatz() {
@start356
    %t1282 =w copy 6
    %t1283 =w call $collatz_steps(w %t1282)
    %t1284 =w copy 8
    %t1285 =w call $check_eq(w %t1283, w %t1284)
    ret %t1285
}

export function w $t_prime() {
@start357
    %t1286 =w copy 0
    %t1287 =l alloc4 4
    storew %t1286, %t1287
    %t1288 =w copy 2
    %t1289 =w call $is_prime(w %t1288)
    %t1290 =w copy 1
    %t1291 =w cnew %t1289, %t1290
    jnz %t1291, @then358, @else359
@then358
    %t1292 =w copy 1
    storew %t1292, %t1287
    jmp @merge360
@else359
    jmp @merge360
@merge360
    %t1293 =w copy 17
    %t1294 =w call $is_prime(w %t1293)
    %t1295 =w copy 1
    %t1296 =w cnew %t1294, %t1295
    jnz %t1296, @then361, @else362
@then361
    %t1297 =w copy 1
    storew %t1297, %t1287
    jmp @merge363
@else362
    jmp @merge363
@merge363
    %t1298 =w copy 15
    %t1299 =w call $is_prime(w %t1298)
    %t1300 =w copy 0
    %t1301 =w cnew %t1299, %t1300
    jnz %t1301, @then364, @else365
@then364
    %t1302 =w copy 1
    storew %t1302, %t1287
    jmp @merge366
@else365
    jmp @merge366
@merge366
    %t1303 =w loadw %t1287
    ret %t1303
}

export function w $t_count_primes() {
@start367
    %t1304 =w copy 10
    %t1305 =w call $count_primes_up_to(w %t1304)
    %t1306 =w copy 4
    %t1307 =w call $check_eq(w %t1305, w %t1306)
    ret %t1307
}

export function w $t_next_prime() {
@start368
    %t1308 =w copy 10
    %t1309 =w call $next_prime_after(w %t1308)
    %t1310 =w copy 11
    %t1311 =w call $check_eq(w %t1309, w %t1310)
    ret %t1311
}

export function w $t_compound_assign() {
@start369
    %t1312 =w copy 10
    %t1313 =l alloc4 4
    storew %t1312, %t1313
    %t1314 =w loadw %t1313
    %t1315 =w copy 5
    %t1316 =w add %t1314, %t1315
    storew %t1316, %t1313
    %t1317 =w loadw %t1313
    %t1318 =w copy 3
    %t1319 =w sub %t1317, %t1318
    storew %t1319, %t1313
    %t1320 =w loadw %t1313
    %t1321 =w copy 2
    %t1322 =w mul %t1320, %t1321
    storew %t1322, %t1313
    %t1323 =w loadw %t1313
    %t1324 =w copy 4
    %t1325 =w div %t1323, %t1324
    storew %t1325, %t1313
    %t1326 =w loadw %t1313
    %t1327 =w copy 5
    %t1328 =w rem %t1326, %t1327
    storew %t1328, %t1313
    %t1329 =w loadw %t1313
    %t1330 =w copy 1
    %t1331 =w call $check_eq(w %t1329, w %t1330)
    ret %t1331
}

export function w $t_complex_combo() {
@start370
    %t1332 =l alloc8 8
    %t1333 =w copy 3
    %t1334 =l add %t1332, 0
    storew %t1333, %t1334
    %t1335 =w copy 4
    %t1336 =l add %t1332, 4
    storew %t1335, %t1336
    %t1337 =w loadw %t1332
    %t1338 =l add %t1332, 4
    %t1339 =w loadw %t1338
    %t1340 =w loadw %t1332
    %t1341 =l add %t1332, 4
    %t1342 =w loadw %t1341
    %t1343 =w mul %t1340, %t1342
    %t1344 =w loadw %t1332
    %t1345 =l add %t1332, 4
    %t1346 =w loadw %t1345
    %t1347 =w add %t1344, %t1346
    %t1348 =w call $sum_4(w %t1337, w %t1339, w %t1343, w %t1347)
    %t1349 =w copy 26
    %t1350 =w call $check_eq(w %t1348, w %t1349)
    ret %t1350
}

export function w $inner_triple_op(w %x) {
@start371
    %t1351 =w copy %x
    %t1352 =w copy 0
    %t1353 =w csltw %t1351, %t1352
    jnz %t1353, @then372, @else373
@then372
    %t1354 =w copy 0
    %t1355 =w copy 1
    %t1356 =w sub %t1354, %t1355
    ret %t1356
@else373
    jmp @merge374
@merge374
    %t1357 =w copy 0
    %t1358 =w ceqw %t1351, %t1357
    jnz %t1358, @then375, @else376
@then375
    %t1359 =w copy 0
    ret %t1359
@else376
    jmp @merge377
@merge377
    %t1360 =w copy 2
    %t1361 =w mul %t1351, %t1360
    ret %t1361
}

export function w $t_early_return() {
@start378
    %t1362 =w copy 0
    %t1363 =w copy 5
    %t1364 =w sub %t1362, %t1363
    %t1365 =w call $inner_triple_op(w %t1364)
    %t1366 =w copy 0
    %t1367 =w call $inner_triple_op(w %t1366)
    %t1368 =w copy 7
    %t1369 =w call $inner_triple_op(w %t1368)
    %t1370 =w copy 0
    %t1371 =l alloc4 4
    storew %t1370, %t1371
    %t1372 =w copy 0
    %t1373 =w copy 1
    %t1374 =w sub %t1372, %t1373
    %t1375 =w cnew %t1365, %t1374
    jnz %t1375, @then379, @else380
@then379
    %t1376 =w copy 1
    storew %t1376, %t1371
    jmp @merge381
@else380
    jmp @merge381
@merge381
    %t1377 =w copy 0
    %t1378 =w cnew %t1367, %t1377
    jnz %t1378, @then382, @else383
@then382
    %t1379 =w copy 1
    storew %t1379, %t1371
    jmp @merge384
@else383
    jmp @merge384
@merge384
    %t1380 =w copy 14
    %t1381 =w cnew %t1369, %t1380
    jnz %t1381, @then385, @else386
@then385
    %t1382 =w copy 1
    storew %t1382, %t1371
    jmp @merge387
@else386
    jmp @merge387
@merge387
    %t1383 =w loadw %t1371
    ret %t1383
}

export function w $t_nested_if() {
@start388
    %t1384 =w copy 5
    %t1385 =w copy 10
    %t1386 =w copy 0
    %t1387 =l alloc4 4
    storew %t1386, %t1387
    %t1388 =w copy 0
    %t1389 =w csgtw %t1384, %t1388
    jnz %t1389, @then389, @else390
@then389
    %t1390 =w copy 5
    %t1391 =w csgtw %t1385, %t1390
    jnz %t1391, @then392, @else393
@then392
    %t1392 =w add %t1384, %t1385
    storew %t1392, %t1387
    jmp @merge394
@else393
    %t1393 =w sub %t1384, %t1385
    storew %t1393, %t1387
    jmp @ep395
@ep395
    jmp @merge394
@merge394
    jmp @merge391
@else390
    %t1394 =w copy 0
    %t1395 =w sub %t1394, %t1384
    storew %t1395, %t1387
    jmp @ep396
@ep396
    jmp @merge391
@merge391
    %t1396 =w loadw %t1387
    %t1397 =w copy 15
    %t1398 =w call $check_eq(w %t1396, w %t1397)
    ret %t1398
}

export function w $t_recursive_mix() {
@start397
    %t1399 =w copy 8
    %t1400 =w call $fib(w %t1399)
    %t1401 =w copy 6
    %t1402 =w call $fact(w %t1401)
    %t1403 =w copy 100
    %t1404 =w copy 75
    %t1405 =w call $gcd(w %t1403, w %t1404)
    %t1406 =w add %t1400, %t1402
    %t1407 =w add %t1406, %t1405
    %t1408 =w copy 766
    %t1409 =w call $check_eq(w %t1407, w %t1408)
    ret %t1409
}

export function w $t_logical_combinations() {
@start398
    %t1410 =w copy 1
    %t1411 =w copy 0
    %t1412 =w copy 1
    %t1413 =w call $bool_and(w %t1410, w %t1412)
    %t1414 =w call $bool_or(w %t1413, w %t1411)
    %t1415 =w copy 0
    %t1416 =l alloc4 4
    storew %t1415, %t1416
    %t1417 =w copy 1
    %t1418 =w cnew %t1413, %t1417
    jnz %t1418, @then399, @else400
@then399
    %t1419 =w copy 1
    storew %t1419, %t1416
    jmp @merge401
@else400
    jmp @merge401
@merge401
    %t1420 =w copy 1
    %t1421 =w cnew %t1414, %t1420
    jnz %t1421, @then402, @else403
@then402
    %t1422 =w copy 1
    storew %t1422, %t1416
    jmp @merge404
@else403
    jmp @merge404
@merge404
    %t1423 =w loadw %t1416
    ret %t1423
}

export function w $t_array_literal_basic() {
@start405
    %t1424 =l alloc16 16
    %t1425 =w copy 10
    storew %t1425, %t1424
    %t1426 =w copy 20
    %t1427 =l copy 4
    %t1428 =l add %t1424, %t1427
    storew %t1426, %t1428
    %t1429 =w copy 30
    %t1430 =l copy 8
    %t1431 =l add %t1424, %t1430
    storew %t1429, %t1431
    %t1432 =w copy 40
    %t1433 =l copy 12
    %t1434 =l add %t1424, %t1433
    storew %t1432, %t1434
    %t1435 =w copy 0
    %t1436 =l alloc4 4
    storew %t1435, %t1436
    %t1437 =w copy 0
    %t1438 =l copy 0
    %t1439 =l add %t1424, %t1438
    %t1440 =w loadw %t1439
    %t1441 =w copy 10
    %t1442 =w cnew %t1440, %t1441
    jnz %t1442, @then406, @else407
@then406
    %t1443 =w copy 1
    storew %t1443, %t1436
    jmp @merge408
@else407
    jmp @merge408
@merge408
    %t1444 =w copy 1
    %t1445 =l copy 4
    %t1446 =l add %t1424, %t1445
    %t1447 =w loadw %t1446
    %t1448 =w copy 20
    %t1449 =w cnew %t1447, %t1448
    jnz %t1449, @then409, @else410
@then409
    %t1450 =w copy 1
    storew %t1450, %t1436
    jmp @merge411
@else410
    jmp @merge411
@merge411
    %t1451 =w copy 2
    %t1452 =l copy 8
    %t1453 =l add %t1424, %t1452
    %t1454 =w loadw %t1453
    %t1455 =w copy 30
    %t1456 =w cnew %t1454, %t1455
    jnz %t1456, @then412, @else413
@then412
    %t1457 =w copy 1
    storew %t1457, %t1436
    jmp @merge414
@else413
    jmp @merge414
@merge414
    %t1458 =w copy 3
    %t1459 =l copy 12
    %t1460 =l add %t1424, %t1459
    %t1461 =w loadw %t1460
    %t1462 =w copy 40
    %t1463 =w cnew %t1461, %t1462
    jnz %t1463, @then415, @else416
@then415
    %t1464 =w copy 1
    storew %t1464, %t1436
    jmp @merge417
@else416
    jmp @merge417
@merge417
    %t1465 =w loadw %t1436
    ret %t1465
}

export function w $t_array_type_annot() {
@start418
    %t1466 =l alloc16 16
    %t1467 =w copy 7
    storew %t1467, %t1466
    %t1468 =w copy 8
    %t1469 =l copy 4
    %t1470 =l add %t1466, %t1469
    storew %t1468, %t1470
    %t1471 =w copy 9
    %t1472 =l copy 8
    %t1473 =l add %t1466, %t1472
    storew %t1471, %t1473
    %t1474 =w copy 10
    %t1475 =l copy 12
    %t1476 =l add %t1466, %t1475
    storew %t1474, %t1476
    %t1477 =w copy 0
    %t1478 =l alloc4 4
    storew %t1477, %t1478
    %t1479 =w copy 0
    %t1480 =l copy 0
    %t1481 =l add %t1466, %t1480
    %t1482 =w loadw %t1481
    %t1483 =w copy 7
    %t1484 =w cnew %t1482, %t1483
    jnz %t1484, @then419, @else420
@then419
    %t1485 =w copy 1
    storew %t1485, %t1478
    jmp @merge421
@else420
    jmp @merge421
@merge421
    %t1486 =w copy 1
    %t1487 =l copy 4
    %t1488 =l add %t1466, %t1487
    %t1489 =w loadw %t1488
    %t1490 =w copy 8
    %t1491 =w cnew %t1489, %t1490
    jnz %t1491, @then422, @else423
@then422
    %t1492 =w copy 1
    storew %t1492, %t1478
    jmp @merge424
@else423
    jmp @merge424
@merge424
    %t1493 =w copy 2
    %t1494 =l copy 8
    %t1495 =l add %t1466, %t1494
    %t1496 =w loadw %t1495
    %t1497 =w copy 9
    %t1498 =w cnew %t1496, %t1497
    jnz %t1498, @then425, @else426
@then425
    %t1499 =w copy 1
    storew %t1499, %t1478
    jmp @merge427
@else426
    jmp @merge427
@merge427
    %t1500 =w copy 3
    %t1501 =l copy 12
    %t1502 =l add %t1466, %t1501
    %t1503 =w loadw %t1502
    %t1504 =w copy 10
    %t1505 =w cnew %t1503, %t1504
    jnz %t1505, @then428, @else429
@then428
    %t1506 =w copy 1
    storew %t1506, %t1478
    jmp @merge430
@else429
    jmp @merge430
@merge430
    %t1507 =w loadw %t1478
    ret %t1507
}

export function w $t_string_literal() {
@start431
    %t1508 =l copy $str0
    %t1509 =w call $puts(l %t1508)
    %t1510 =w copy 0
    ret %t1510
}

export function w $t_unary_ops() {
@start432
    %t1511 =w copy 7
    %t1512 =w copy 0
    %t1513 =w sub %t1512, %t1511
    %t1515 =w copy -1
    %t1514 =w xor %t1511, %t1515
    %t1516 =w copy 0
    %t1517 =l alloc4 4
    storew %t1516, %t1517
    %t1518 =w copy 0
    %t1519 =w copy 7
    %t1520 =w sub %t1518, %t1519
    %t1521 =w cnew %t1513, %t1520
    jnz %t1521, @then433, @else434
@then433
    %t1522 =w copy 1
    storew %t1522, %t1517
    jmp @merge435
@else434
    jmp @merge435
@merge435
    %t1523 =w copy 0
    %t1524 =w copy 8
    %t1525 =w sub %t1523, %t1524
    %t1526 =w cnew %t1514, %t1525
    jnz %t1526, @then436, @else437
@then436
    %t1527 =w copy 1
    storew %t1527, %t1517
    jmp @merge438
@else437
    jmp @merge438
@merge438
    %t1528 =w loadw %t1517
    ret %t1528
}

export function w $main_jhyy() {
@start439
    %t1529 =l copy $str1
    %t1530 =w call $puts(l %t1529)
    %t1531 =w copy 0
    %t1532 =l alloc4 4
    storew %t1531, %t1532
    %t1533 =w copy 0
    %t1534 =l alloc4 4
    storew %t1533, %t1534
    %t1535 =w call $t_add3()
    storew %t1535, %t1534
    %t1536 =w loadw %t1532
    %t1537 =w loadw %t1534
    %t1538 =w add %t1536, %t1537
    storew %t1538, %t1532
    %t1539 =l copy $str2
    %t1540 =w loadw %t1534
    %t1541 =w call $printf(l %t1539, w %t1540)
    %t1542 =w call $t_mul4()
    storew %t1542, %t1534
    %t1543 =w loadw %t1532
    %t1544 =w loadw %t1534
    %t1545 =w add %t1543, %t1544
    storew %t1545, %t1532
    %t1546 =l copy $str3
    %t1547 =w loadw %t1534
    %t1548 =w call $printf(l %t1546, w %t1547)
    %t1549 =w call $t_mixed()
    storew %t1549, %t1534
    %t1550 =w loadw %t1532
    %t1551 =w loadw %t1534
    %t1552 =w add %t1550, %t1551
    storew %t1552, %t1532
    %t1553 =l copy $str4
    %t1554 =w loadw %t1534
    %t1555 =w call $printf(l %t1553, w %t1554)
    %t1556 =w call $t_negate()
    storew %t1556, %t1534
    %t1557 =w loadw %t1532
    %t1558 =w loadw %t1534
    %t1559 =w add %t1557, %t1558
    storew %t1559, %t1532
    %t1560 =l copy $str5
    %t1561 =w loadw %t1534
    %t1562 =w call $printf(l %t1560, w %t1561)
    %t1563 =w call $t_abs_diff()
    storew %t1563, %t1534
    %t1564 =w loadw %t1532
    %t1565 =w loadw %t1534
    %t1566 =w add %t1564, %t1565
    storew %t1566, %t1532
    %t1567 =l copy $str6
    %t1568 =w loadw %t1534
    %t1569 =w call $printf(l %t1567, w %t1568)
    %t1570 =w call $t_clamp()
    storew %t1570, %t1534
    %t1571 =w loadw %t1532
    %t1572 =w loadw %t1534
    %t1573 =w add %t1571, %t1572
    storew %t1573, %t1532
    %t1574 =l copy $str7
    %t1575 =w loadw %t1534
    %t1576 =w call $printf(l %t1574, w %t1575)
    %t1577 =w call $t_fact()
    storew %t1577, %t1534
    %t1578 =w loadw %t1532
    %t1579 =w loadw %t1534
    %t1580 =w add %t1578, %t1579
    storew %t1580, %t1532
    %t1581 =l copy $str8
    %t1582 =w loadw %t1534
    %t1583 =w call $printf(l %t1581, w %t1582)
    %t1584 =w call $t_fib()
    storew %t1584, %t1534
    %t1585 =w loadw %t1532
    %t1586 =w loadw %t1534
    %t1587 =w add %t1585, %t1586
    storew %t1587, %t1532
    %t1588 =l copy $str9
    %t1589 =w loadw %t1534
    %t1590 =w call $printf(l %t1588, w %t1589)
    %t1591 =w call $t_gcd()
    storew %t1591, %t1534
    %t1592 =w loadw %t1532
    %t1593 =w loadw %t1534
    %t1594 =w add %t1592, %t1593
    storew %t1594, %t1532
    %t1595 =l copy $str10
    %t1596 =w loadw %t1534
    %t1597 =w call $printf(l %t1595, w %t1596)
    %t1598 =w call $t_sum_to()
    storew %t1598, %t1534
    %t1599 =w loadw %t1532
    %t1600 =w loadw %t1534
    %t1601 =w add %t1599, %t1600
    storew %t1601, %t1532
    %t1602 =l copy $str11
    %t1603 =w loadw %t1534
    %t1604 =w call $printf(l %t1602, w %t1603)
    %t1605 =w call $t_power()
    storew %t1605, %t1534
    %t1606 =w loadw %t1532
    %t1607 =w loadw %t1534
    %t1608 =w add %t1606, %t1607
    storew %t1608, %t1532
    %t1609 =l copy $str12
    %t1610 =w loadw %t1534
    %t1611 =w call $printf(l %t1609, w %t1610)
    %t1612 =w call $t_sum_digits()
    storew %t1612, %t1534
    %t1613 =w loadw %t1532
    %t1614 =w loadw %t1534
    %t1615 =w add %t1613, %t1614
    storew %t1615, %t1532
    %t1616 =l copy $str13
    %t1617 =w loadw %t1534
    %t1618 =w call $printf(l %t1616, w %t1617)
    %t1619 =w call $t_is_positive()
    storew %t1619, %t1534
    %t1620 =w loadw %t1532
    %t1621 =w loadw %t1534
    %t1622 =w add %t1620, %t1621
    storew %t1622, %t1532
    %t1623 =l copy $str14
    %t1624 =w loadw %t1534
    %t1625 =w call $printf(l %t1623, w %t1624)
    %t1626 =w call $t_in_range()
    storew %t1626, %t1534
    %t1627 =w loadw %t1532
    %t1628 =w loadw %t1534
    %t1629 =w add %t1627, %t1628
    storew %t1629, %t1532
    %t1630 =l copy $str15
    %t1631 =w loadw %t1534
    %t1632 =w call $printf(l %t1630, w %t1631)
    %t1633 =w call $t_max3()
    storew %t1633, %t1534
    %t1634 =w loadw %t1532
    %t1635 =w loadw %t1534
    %t1636 =w add %t1634, %t1635
    storew %t1636, %t1532
    %t1637 =l copy $str16
    %t1638 =w loadw %t1534
    %t1639 =w call $printf(l %t1637, w %t1638)
    %t1640 =w call $t_min3()
    storew %t1640, %t1534
    %t1641 =w loadw %t1532
    %t1642 =w loadw %t1534
    %t1643 =w add %t1641, %t1642
    storew %t1643, %t1532
    %t1644 =l copy $str17
    %t1645 =w loadw %t1534
    %t1646 =w call $printf(l %t1644, w %t1645)
    %t1647 =w call $t_sign()
    storew %t1647, %t1534
    %t1648 =w loadw %t1532
    %t1649 =w loadw %t1534
    %t1650 =w add %t1648, %t1649
    storew %t1650, %t1532
    %t1651 =l copy $str18
    %t1652 =w loadw %t1534
    %t1653 =w call $printf(l %t1651, w %t1652)
    %t1654 =w call $t_bit_pack()
    storew %t1654, %t1534
    %t1655 =w loadw %t1532
    %t1656 =w loadw %t1534
    %t1657 =w add %t1655, %t1656
    storew %t1657, %t1532
    %t1658 =l copy $str19
    %t1659 =w loadw %t1534
    %t1660 =w call $printf(l %t1658, w %t1659)
    %t1661 =w call $t_bit_unpack()
    storew %t1661, %t1534
    %t1662 =w loadw %t1532
    %t1663 =w loadw %t1534
    %t1664 =w add %t1662, %t1663
    storew %t1664, %t1532
    %t1665 =l copy $str20
    %t1666 =w loadw %t1534
    %t1667 =w call $printf(l %t1665, w %t1666)
    %t1668 =w call $t_count_set_bits()
    storew %t1668, %t1534
    %t1669 =w loadw %t1532
    %t1670 =w loadw %t1534
    %t1671 =w add %t1669, %t1670
    storew %t1671, %t1532
    %t1672 =l copy $str21
    %t1673 =w loadw %t1534
    %t1674 =w call $printf(l %t1672, w %t1673)
    %t1675 =w call $t_bit_xor()
    storew %t1675, %t1534
    %t1676 =w loadw %t1532
    %t1677 =w loadw %t1534
    %t1678 =w add %t1676, %t1677
    storew %t1678, %t1532
    %t1679 =l copy $str22
    %t1680 =w loadw %t1534
    %t1681 =w call $printf(l %t1679, w %t1680)
    %t1682 =w call $t_bit_or()
    storew %t1682, %t1534
    %t1683 =w loadw %t1532
    %t1684 =w loadw %t1534
    %t1685 =w add %t1683, %t1684
    storew %t1685, %t1532
    %t1686 =l copy $str23
    %t1687 =w loadw %t1534
    %t1688 =w call $printf(l %t1686, w %t1687)
    %t1689 =w call $t_bit_and()
    storew %t1689, %t1534
    %t1690 =w loadw %t1532
    %t1691 =w loadw %t1534
    %t1692 =w add %t1690, %t1691
    storew %t1692, %t1532
    %t1693 =l copy $str24
    %t1694 =w loadw %t1534
    %t1695 =w call $printf(l %t1693, w %t1694)
    %t1696 =w call $t_shifts()
    storew %t1696, %t1534
    %t1697 =w loadw %t1532
    %t1698 =w loadw %t1534
    %t1699 =w add %t1697, %t1698
    storew %t1699, %t1532
    %t1700 =l copy $str25
    %t1701 =w loadw %t1534
    %t1702 =w call $printf(l %t1700, w %t1701)
    %t1703 =w call $t_point_basic()
    storew %t1703, %t1534
    %t1704 =w loadw %t1532
    %t1705 =w loadw %t1534
    %t1706 =w add %t1704, %t1705
    storew %t1706, %t1532
    %t1707 =l copy $str26
    %t1708 =w loadw %t1534
    %t1709 =w call $printf(l %t1707, w %t1708)
    %t1710 =w call $t_point_ops()
    storew %t1710, %t1534
    %t1711 =w loadw %t1532
    %t1712 =w loadw %t1534
    %t1713 =w add %t1711, %t1712
    storew %t1713, %t1532
    %t1714 =l copy $str27
    %t1715 =w loadw %t1534
    %t1716 =w call $printf(l %t1714, w %t1715)
    %t1717 =w call $t_point_diff()
    storew %t1717, %t1534
    %t1718 =w loadw %t1532
    %t1719 =w loadw %t1534
    %t1720 =w add %t1718, %t1719
    storew %t1720, %t1532
    %t1721 =l copy $str28
    %t1722 =w loadw %t1534
    %t1723 =w call $printf(l %t1721, w %t1722)
    %t1724 =w call $t_rect_area()
    storew %t1724, %t1534
    %t1725 =w loadw %t1532
    %t1726 =w loadw %t1534
    %t1727 =w add %t1725, %t1726
    storew %t1727, %t1532
    %t1728 =l copy $str29
    %t1729 =w loadw %t1534
    %t1730 =w call $printf(l %t1728, w %t1729)
    %t1731 =w call $t_triple()
    storew %t1731, %t1534
    %t1732 =w loadw %t1532
    %t1733 =w loadw %t1534
    %t1734 =w add %t1732, %t1733
    storew %t1734, %t1532
    %t1735 =l copy $str30
    %t1736 =w loadw %t1534
    %t1737 =w call $printf(l %t1735, w %t1736)
    %t1738 =w call $t_array_sum()
    storew %t1738, %t1534
    %t1739 =w loadw %t1532
    %t1740 =w loadw %t1534
    %t1741 =w add %t1739, %t1740
    storew %t1741, %t1532
    %t1742 =l copy $str31
    %t1743 =w loadw %t1534
    %t1744 =w call $printf(l %t1742, w %t1743)
    %t1745 =w call $t_array_max()
    storew %t1745, %t1534
    %t1746 =w loadw %t1532
    %t1747 =w loadw %t1534
    %t1748 =w add %t1746, %t1747
    storew %t1748, %t1532
    %t1749 =l copy $str32
    %t1750 =w loadw %t1534
    %t1751 =w call $printf(l %t1749, w %t1750)
    %t1752 =w call $t_array_min()
    storew %t1752, %t1534
    %t1753 =w loadw %t1532
    %t1754 =w loadw %t1534
    %t1755 =w add %t1753, %t1754
    storew %t1755, %t1532
    %t1756 =l copy $str33
    %t1757 =w loadw %t1534
    %t1758 =w call $printf(l %t1756, w %t1757)
    %t1759 =w call $t_array_dot()
    storew %t1759, %t1534
    %t1760 =w loadw %t1532
    %t1761 =w loadw %t1534
    %t1762 =w add %t1760, %t1761
    storew %t1762, %t1532
    %t1763 =l copy $str34
    %t1764 =w loadw %t1534
    %t1765 =w call $printf(l %t1763, w %t1764)
    %t1766 =w call $t_ptr_field()
    storew %t1766, %t1534
    %t1767 =w loadw %t1532
    %t1768 =w loadw %t1534
    %t1769 =w add %t1767, %t1768
    storew %t1769, %t1532
    %t1770 =l copy $str35
    %t1771 =w loadw %t1534
    %t1772 =w call $printf(l %t1770, w %t1771)
    %t1773 =w call $t_ptr_array()
    storew %t1773, %t1534
    %t1774 =w loadw %t1532
    %t1775 =w loadw %t1534
    %t1776 =w add %t1774, %t1775
    storew %t1776, %t1532
    %t1777 =l copy $str36
    %t1778 =w loadw %t1534
    %t1779 =w call $printf(l %t1777, w %t1778)
    %t1780 =w call $t_swap_via_ptr()
    storew %t1780, %t1534
    %t1781 =w loadw %t1532
    %t1782 =w loadw %t1534
    %t1783 =w add %t1781, %t1782
    storew %t1783, %t1532
    %t1784 =l copy $str37
    %t1785 =w loadw %t1534
    %t1786 =w call $printf(l %t1784, w %t1785)
    %t1787 =w call $t_modify_via_ptr()
    storew %t1787, %t1534
    %t1788 =w loadw %t1532
    %t1789 =w loadw %t1534
    %t1790 =w add %t1788, %t1789
    storew %t1790, %t1532
    %t1791 =l copy $str38
    %t1792 =w loadw %t1534
    %t1793 =w call $printf(l %t1791, w %t1792)
    %t1794 =w call $t_sum_even()
    storew %t1794, %t1534
    %t1795 =w loadw %t1532
    %t1796 =w loadw %t1534
    %t1797 =w add %t1795, %t1796
    storew %t1797, %t1532
    %t1798 =l copy $str39
    %t1799 =w loadw %t1534
    %t1800 =w call $printf(l %t1798, w %t1799)
    %t1801 =w call $t_sum_odd()
    storew %t1801, %t1534
    %t1802 =w loadw %t1532
    %t1803 =w loadw %t1534
    %t1804 =w add %t1802, %t1803
    storew %t1804, %t1532
    %t1805 =l copy $str40
    %t1806 =w loadw %t1534
    %t1807 =w call $printf(l %t1805, w %t1806)
    %t1808 =w call $t_nested()
    storew %t1808, %t1534
    %t1809 =w loadw %t1532
    %t1810 =w loadw %t1534
    %t1811 =w add %t1809, %t1810
    storew %t1811, %t1532
    %t1812 =l copy $str41
    %t1813 =w loadw %t1534
    %t1814 =w call $printf(l %t1812, w %t1813)
    %t1815 =w call $t_for_sum()
    storew %t1815, %t1534
    %t1816 =w loadw %t1532
    %t1817 =w loadw %t1534
    %t1818 =w add %t1816, %t1817
    storew %t1818, %t1532
    %t1819 =l copy $str42
    %t1820 =w loadw %t1534
    %t1821 =w call $printf(l %t1819, w %t1820)
    %t1822 =w call $t_for_break()
    storew %t1822, %t1534
    %t1823 =w loadw %t1532
    %t1824 =w loadw %t1534
    %t1825 =w add %t1823, %t1824
    storew %t1825, %t1532
    %t1826 =l copy $str43
    %t1827 =w loadw %t1534
    %t1828 =w call $printf(l %t1826, w %t1827)
    %t1829 =w call $t_for_continue()
    storew %t1829, %t1534
    %t1830 =w loadw %t1532
    %t1831 =w loadw %t1534
    %t1832 =w add %t1830, %t1831
    storew %t1832, %t1532
    %t1833 =l copy $str44
    %t1834 =w loadw %t1534
    %t1835 =w call $printf(l %t1833, w %t1834)
    %t1836 =w call $t_while_break()
    storew %t1836, %t1534
    %t1837 =w loadw %t1532
    %t1838 =w loadw %t1534
    %t1839 =w add %t1837, %t1838
    storew %t1839, %t1532
    %t1840 =l copy $str45
    %t1841 =w loadw %t1534
    %t1842 =w call $printf(l %t1840, w %t1841)
    %t1843 =w call $t_harmonic()
    storew %t1843, %t1534
    %t1844 =w loadw %t1532
    %t1845 =w loadw %t1534
    %t1846 =w add %t1844, %t1845
    storew %t1846, %t1532
    %t1847 =l copy $str46
    %t1848 =w loadw %t1534
    %t1849 =w call $printf(l %t1847, w %t1848)
    %t1850 =w call $t_collatz()
    storew %t1850, %t1534
    %t1851 =w loadw %t1532
    %t1852 =w loadw %t1534
    %t1853 =w add %t1851, %t1852
    storew %t1853, %t1532
    %t1854 =l copy $str47
    %t1855 =w loadw %t1534
    %t1856 =w call $printf(l %t1854, w %t1855)
    %t1857 =w call $t_prime()
    storew %t1857, %t1534
    %t1858 =w loadw %t1532
    %t1859 =w loadw %t1534
    %t1860 =w add %t1858, %t1859
    storew %t1860, %t1532
    %t1861 =l copy $str48
    %t1862 =w loadw %t1534
    %t1863 =w call $printf(l %t1861, w %t1862)
    %t1864 =w call $t_count_primes()
    storew %t1864, %t1534
    %t1865 =w loadw %t1532
    %t1866 =w loadw %t1534
    %t1867 =w add %t1865, %t1866
    storew %t1867, %t1532
    %t1868 =l copy $str49
    %t1869 =w loadw %t1534
    %t1870 =w call $printf(l %t1868, w %t1869)
    %t1871 =w call $t_next_prime()
    storew %t1871, %t1534
    %t1872 =w loadw %t1532
    %t1873 =w loadw %t1534
    %t1874 =w add %t1872, %t1873
    storew %t1874, %t1532
    %t1875 =l copy $str50
    %t1876 =w loadw %t1534
    %t1877 =w call $printf(l %t1875, w %t1876)
    %t1878 =w call $t_compound_assign()
    storew %t1878, %t1534
    %t1879 =w loadw %t1532
    %t1880 =w loadw %t1534
    %t1881 =w add %t1879, %t1880
    storew %t1881, %t1532
    %t1882 =l copy $str51
    %t1883 =w loadw %t1534
    %t1884 =w call $printf(l %t1882, w %t1883)
    %t1885 =w call $t_complex_combo()
    storew %t1885, %t1534
    %t1886 =w loadw %t1532
    %t1887 =w loadw %t1534
    %t1888 =w add %t1886, %t1887
    storew %t1888, %t1532
    %t1889 =l copy $str52
    %t1890 =w loadw %t1534
    %t1891 =w call $printf(l %t1889, w %t1890)
    %t1892 =w call $t_early_return()
    storew %t1892, %t1534
    %t1893 =w loadw %t1532
    %t1894 =w loadw %t1534
    %t1895 =w add %t1893, %t1894
    storew %t1895, %t1532
    %t1896 =l copy $str53
    %t1897 =w loadw %t1534
    %t1898 =w call $printf(l %t1896, w %t1897)
    %t1899 =w call $t_nested_if()
    storew %t1899, %t1534
    %t1900 =w loadw %t1532
    %t1901 =w loadw %t1534
    %t1902 =w add %t1900, %t1901
    storew %t1902, %t1532
    %t1903 =l copy $str54
    %t1904 =w loadw %t1534
    %t1905 =w call $printf(l %t1903, w %t1904)
    %t1906 =w call $t_recursive_mix()
    storew %t1906, %t1534
    %t1907 =w loadw %t1532
    %t1908 =w loadw %t1534
    %t1909 =w add %t1907, %t1908
    storew %t1909, %t1532
    %t1910 =l copy $str55
    %t1911 =w loadw %t1534
    %t1912 =w call $printf(l %t1910, w %t1911)
    %t1913 =w call $t_logical_combinations()
    storew %t1913, %t1534
    %t1914 =w loadw %t1532
    %t1915 =w loadw %t1534
    %t1916 =w add %t1914, %t1915
    storew %t1916, %t1532
    %t1917 =l copy $str56
    %t1918 =w loadw %t1534
    %t1919 =w call $printf(l %t1917, w %t1918)
    %t1920 =w call $t_array_literal_basic()
    storew %t1920, %t1534
    %t1921 =w loadw %t1532
    %t1922 =w loadw %t1534
    %t1923 =w add %t1921, %t1922
    storew %t1923, %t1532
    %t1924 =l copy $str57
    %t1925 =w loadw %t1534
    %t1926 =w call $printf(l %t1924, w %t1925)
    %t1927 =w call $t_array_type_annot()
    storew %t1927, %t1534
    %t1928 =w loadw %t1532
    %t1929 =w loadw %t1534
    %t1930 =w add %t1928, %t1929
    storew %t1930, %t1532
    %t1931 =l copy $str58
    %t1932 =w loadw %t1534
    %t1933 =w call $printf(l %t1931, w %t1932)
    %t1934 =w call $t_string_literal()
    storew %t1934, %t1534
    %t1935 =w loadw %t1532
    %t1936 =w loadw %t1534
    %t1937 =w add %t1935, %t1936
    storew %t1937, %t1532
    %t1938 =l copy $str59
    %t1939 =w loadw %t1534
    %t1940 =w call $printf(l %t1938, w %t1939)
    %t1941 =w call $t_unary_ops()
    storew %t1941, %t1534
    %t1942 =w loadw %t1532
    %t1943 =w loadw %t1534
    %t1944 =w add %t1942, %t1943
    storew %t1944, %t1532
    %t1945 =l copy $str60
    %t1946 =w loadw %t1534
    %t1947 =w call $printf(l %t1945, w %t1946)
    %t1948 =l copy $str61
    %t1949 =w loadw %t1532
    %t1950 =w call $printf(l %t1948, w %t1949)
    %t1951 =w copy 12345
    ret %t1951
}

