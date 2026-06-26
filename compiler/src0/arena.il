export function l $ARENA_DEFAULT_SIZE() {
@start0
    %t0 =w copy 1048576
    %t1 =l extsw %t0
    ret %t1
}

export function l $align_up(l %x, l %align) {
@start1
    %t2 =l copy %x
    %t3 =l copy %align
    %t4 =w copy 1
    %t5 =l extsw %t4
    %t6 =l sub %t3, %t5
    %t7 =l add %t2, %t6
    %t9 =l copy -1
    %t8 =l xor %t6, %t9
    %t10 =l and %t7, %t8
    ret %t10
}

export function l $ptr_add(l %p, l %off) {
@start2
    %t11 =l copy %p
    %t12 =l copy %off
    %t13 =l copy %t11
    %t14 =l add %t13, %t12
    %t15 =l copy %t14
    ret %t15
}

export function w $arena_new_block(l %a, l %min_size) {
@start3
    %t16 =l copy %a
    %t17 =l copy %min_size
    %t18 =l add %t16, 32
    %t19 =l loadl %t18
    %t20 =l alloc8 8
    storel %t19, %t20
    %t21 =l loadl %t20
    %t22 =w csltl %t21, %t17
    jnz %t22, @then4, @else5
@then4
    storel %t17, %t20
    jmp @merge6
@else5
    jmp @merge6
@merge6
    %t23 =w copy 16
    %t24 =l extsw %t23
    %t25 =l loadl %t20
    %t26 =l add %t24, %t25
    %t27 =l call $malloc(l %t26)
    %t28 =w copy 0
    %t29 =l extsw %t28
    %t30 =w ceql %t27, %t29
    jnz %t30, @then7, @else8
@then7
    %t31 =w copy 0
    ret %t31
@else8
    jmp @merge9
@merge9
    %t32 =l copy %t27
    %t33 =l add %t16, 24
    %t34 =l loadl %t33
    storel %t34, %t32
    %t35 =l copy %t32
    %t36 =l add %t16, 24
    storel %t35, %t36
    %t37 =w copy 16
    %t38 =l extsw %t37
    %t39 =l call $ptr_add(l %t27, l %t38)
    storel %t39, %t16
    %t40 =l add %t16, 8
    storel %t39, %t40
    %t41 =l loadl %t20
    %t42 =l call $ptr_add(l %t39, l %t41)
    %t43 =l add %t16, 16
    storel %t42, %t43
    %t44 =w copy 1
    ret %t44
}

export function w $arena_init(l %a, l %default_size) {
@start10
    %t45 =l copy %a
    %t46 =l copy %default_size
    %t47 =w copy 0
    %t48 =l extsw %t47
    %t49 =w csgtl %t46, %t48
    jnz %t49, @then11, @else12
@then11
    %t50 =l add %t45, 32
    storel %t46, %t50
    jmp @merge13
@else12
    %t51 =l call $ARENA_DEFAULT_SIZE()
    %t52 =l add %t45, 32
    storel %t51, %t52
    jmp @ep14
@ep14
    jmp @merge13
@merge13
    %t53 =w copy 0
    %t54 =l extsw %t53
    %t55 =l add %t45, 24
    storel %t54, %t55
    %t56 =w copy 0
    %t57 =l extsw %t56
    storel %t57, %t45
    %t58 =w copy 0
    %t59 =l extsw %t58
    %t60 =l add %t45, 8
    storel %t59, %t60
    %t61 =w copy 0
    %t62 =l extsw %t61
    %t63 =l add %t45, 16
    storel %t62, %t63
    %t64 =w copy 1
    ret %t64
}

export function l $arena_alloc_aligned(l %a, l %size, l %align) {
@start15
    %t65 =l copy %a
    %t66 =l copy %size
    %t67 =l copy %align
    %t68 =w copy 0
    %t69 =l extsw %t68
    %t70 =w ceql %t66, %t69
    jnz %t70, @then16, @else17
@then16
    %t71 =w copy 0
    %t72 =l extsw %t71
    ret %t72
@else17
    jmp @merge18
@merge18
    %t73 =l add %t65, 8
    %t74 =l loadl %t73
    %t75 =w copy 0
    %t76 =l extsw %t75
    %t77 =w cnel %t74, %t76
    jnz %t77, @then19, @else20
@then19
    %t78 =l add %t65, 8
    %t79 =l loadl %t78
    %t80 =l copy %t79
    %t81 =l call $align_up(l %t80, l %t67)
    %t82 =l copy %t81
    %t83 =l add %t65, 16
    %t84 =l loadl %t83
    %t85 =l copy %t84
    %t86 =l add %t81, %t66
    %t87 =w cslel %t86, %t85
    jnz %t87, @then22, @else23
@then22
    %t88 =l add %t81, %t66
    %t89 =l copy %t88
    %t90 =l add %t65, 8
    storel %t89, %t90
    ret %t82
@else23
    jmp @merge24
@merge24
    jmp @merge21
@else20
    jmp @merge21
@merge21
    %t91 =l add %t66, %t67
    %t92 =w call $arena_new_block(l %t65, l %t91)
    %t93 =w copy 0
    %t94 =w ceqw %t92, %t93
    jnz %t94, @then25, @else26
@then25
    %t95 =w copy 0
    %t96 =l extsw %t95
    ret %t96
@else26
    jmp @merge27
@merge27
    %t97 =l call $arena_alloc_aligned(l %t65, l %t66, l %t67)
    ret %t97
}

export function l $arena_alloc(l %a, l %size) {
@start28
    %t98 =l copy %a
    %t99 =l copy %size
    %t100 =w copy 8
    %t101 =l extsw %t100
    %t102 =l call $arena_alloc_aligned(l %t98, l %t99, l %t101)
    ret %t102
}

export function l $arena_calloc(l %a, l %size) {
@start29
    %t103 =l copy %a
    %t104 =l copy %size
    %t105 =l call $arena_alloc(l %t103, l %t104)
    %t106 =w copy 0
    %t107 =l extsw %t106
    %t108 =w cnel %t105, %t107
    jnz %t108, @then30, @else31
@then30
    %t109 =w copy 0
    %t110 =l call $memset(l %t105, w %t109, l %t104)
    jmp @merge32
@else31
    jmp @merge32
@merge32
    ret %t105
}

export function l $arena_strdup(l %a, l %s, l %len) {
@start33
    %t111 =l copy %a
    %t112 =l copy %s
    %t113 =l copy %len
    %t114 =w copy 1
    %t115 =l extsw %t114
    %t116 =l add %t113, %t115
    %t117 =l call $arena_alloc(l %t111, l %t116)
    %t118 =w copy 0
    %t119 =l extsw %t118
    %t120 =w ceql %t117, %t119
    jnz %t120, @then34, @else35
@then34
    %t121 =w copy 0
    %t122 =l extsw %t121
    ret %t122
@else35
    jmp @merge36
@merge36
    %t123 =l call $memcpy(l %t117, l %t112, l %t113)
    %t124 =l call $ptr_add(l %t117, l %t113)
    %t125 =w copy 0
    %t126 =w copy 1
    %t127 =l extsw %t126
    %t128 =l call $memset(l %t124, w %t125, l %t127)
    ret %t117
}

export function w $arena_reset(l %a) {
@start37
    %t129 =l copy %a
    %t130 =l add %t129, 24
    %t131 =l loadl %t130
    %t132 =w copy 0
    %t133 =l extsw %t132
    %t134 =w cnel %t131, %t133
    jnz %t134, @then38, @else39
@then38
    %t135 =l add %t129, 24
    %t136 =l loadl %t135
    %t137 =w copy 16
    %t138 =l extsw %t137
    %t139 =l call $ptr_add(l %t136, l %t138)
    storel %t139, %t129
    %t140 =l add %t129, 8
    storel %t139, %t140
    %t141 =l add %t129, 32
    %t142 =l loadl %t141
    %t143 =l call $ptr_add(l %t139, l %t142)
    %t144 =l add %t129, 16
    storel %t143, %t144
    jmp @merge40
@else39
    jmp @merge40
@merge40
    %t145 =w copy 1
    ret %t145
}

export function w $arena_free(l %a) {
@start41
    %t146 =l copy %a
    %t147 =l add %t146, 24
    %t148 =l loadl %t147
    %t149 =l alloc8 8
    storel %t148, %t149
    jmp @loop42
@loop42
    %t150 =l loadl %t149
    %t151 =w copy 0
    %t152 =l extsw %t151
    %t153 =w cnel %t150, %t152
    jnz %t153, @body43, @exit44
@body43
    %t154 =l loadl %t149
    %t155 =l copy %t154
    %t156 =l loadl %t155
    %t157 =l loadl %t149
    %t158 =w call $free(l %t157)
    storel %t156, %t149
    jmp @loop42
@exit44
    %t159 =w copy 0
    %t160 =l extsw %t159
    %t161 =l add %t146, 24
    storel %t160, %t161
    %t162 =w copy 0
    %t163 =l extsw %t162
    storel %t163, %t146
    %t164 =w copy 0
    %t165 =l extsw %t164
    %t166 =l add %t146, 8
    storel %t165, %t166
    %t167 =w copy 0
    %t168 =l extsw %t167
    %t169 =l add %t146, 16
    storel %t168, %t169
    %t170 =w copy 1
    ret %t170
}

