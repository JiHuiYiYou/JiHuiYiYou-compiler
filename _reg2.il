export function w $factorial(w %n) {
@start0
    %t0 =w copy %n
    %t1 =w copy 1
    %t2 =l alloc4 4
    storew %t1, %t2
    %t3 =w copy 1
    %t4 =l alloc4 4
    storew %t3, %t4
    jmp @loop1
@loop1
    %t5 =w loadw %t4
    %t6 =w cslew %t5, %t0
    jnz %t6, @body2, @exit3
@body2
    %t7 =w loadw %t2
    %t8 =w loadw %t4
    %t9 =w mul %t7, %t8
    storew %t9, %t2
    %t10 =w loadw %t4
    %t11 =w copy 1
    %t12 =w add %t10, %t11
    storew %t12, %t4
    jmp @loop1
@exit3
    %t13 =w loadw %t2
    ret %t13
}

export function w $fibonacci(w %n) {
@start4
    %t14 =w copy %n
    %t15 =w copy 1
    %t16 =w cslew %t14, %t15
    jnz %t16, @then5, @else6
@then5
    ret %t14
@else6
    jmp @merge7
@merge7
    %t17 =w copy 1
    %t18 =w sub %t14, %t17
    %t19 =w call $fibonacci(w %t18)
    %t20 =w copy 2
    %t21 =w sub %t14, %t20
    %t22 =w call $fibonacci(w %t21)
    %t23 =w add %t19, %t22
    ret %t23
}

export function w $gcd(w %a, w %b) {
@start8
    %t24 =w copy %a
    %t25 =w copy %b
    %t26 =l alloc4 4
    storew %t24, %t26
    %t27 =l alloc4 4
    storew %t25, %t27
    jmp @loop9
@loop9
    %t28 =w loadw %t27
    %t29 =w copy 0
    %t30 =w cnew %t28, %t29
    jnz %t30, @body10, @exit11
@body10
    %t31 =w loadw %t27
    %t32 =w loadw %t26
    %t33 =w loadw %t27
    %t34 =w rem %t32, %t33
    storew %t34, %t27
    storew %t31, %t26
    jmp @loop9
@exit11
    %t35 =w loadw %t26
    ret %t35
}

export function w $sum_range(w %start, w %end) {
@start12
    %t36 =w copy %start
    %t37 =w copy %end
    %t38 =w copy 0
    %t39 =l alloc4 4
    storew %t38, %t39
    %t40 =l alloc4 4
    storew %t36, %t40
    jmp @loop13
@loop13
    %t41 =w loadw %t40
    %t42 =w cslew %t41, %t37
    jnz %t42, @body14, @exit15
@body14
    %t43 =w loadw %t39
    %t44 =w loadw %t40
    %t45 =w add %t43, %t44
    storew %t45, %t39
    %t46 =w loadw %t40
    %t47 =w copy 1
    %t48 =w add %t46, %t47
    storew %t48, %t40
    jmp @loop13
@exit15
    %t49 =w loadw %t39
    ret %t49
}

export function w $main_jhyy() {
@start16
    %t50 =w copy 5
    %t51 =w call $factorial(w %t50)
    %t52 =w copy 10
    %t53 =w call $fibonacci(w %t52)
    %t54 =w add %t51, %t53
    %t55 =w copy 48
    %t56 =w copy 18
    %t57 =w call $gcd(w %t55, w %t56)
    %t58 =w copy 1
    %t59 =w copy 10
    %t60 =w call $sum_range(w %t58, w %t59)
    %t61 =w add %t57, %t60
    %t62 =w add %t54, %t61
    %t63 =w sub %t54, %t61
    %t64 =w mul %t62, %t63
    %t65 =w copy 10
    %t66 =w div %t64, %t65
    %t67 =w copy 7
    %t68 =w rem %t66, %t67
    %t69 =w ceqw %t62, %t64
    %t70 =w csltw %t62, %t64
    %t71 =w csgtw %t62, %t66
    jnz %t69, @sc_eval17, @sc_false19
@sc_false19
    %t73 =w copy 0
    jmp @sc_merge18
@sc_eval17
    %t74 =w cnew %t70, 0
    jmp @sc_merge18
@sc_merge18
    %t72 =w phi @sc_false19 %t73, @sc_eval17 %t74
    jnz %t71, @sc_true22, @sc_eval20
@sc_true22
    %t76 =w copy 1
    jmp @sc_merge21
@sc_eval20
    %t78 =w copy 0
    %t77 =w ceqw %t69, %t78
    %t79 =w cnew %t77, 0
    jmp @sc_merge21
@sc_merge21
    %t75 =w phi @sc_true22 %t76, @sc_eval20 %t79
    %t80 =w copy 255
    %t81 =w copy 15
    %t82 =w and %t80, %t81
    %t83 =w copy 4
    %t84 =w shl %t82, %t83
    %t85 =w copy 1
    %t86 =l alloc4 4
    storew %t85, %t86
    %t87 =w loadw %t86
    %t88 =w copy 2
    %t89 =w add %t87, %t88
    storew %t89, %t86
    %t90 =w loadw %t86
    %t91 =w copy 3
    %t92 =w mul %t90, %t91
    storew %t92, %t86
    %t93 =w loadw %t86
    %t94 =w copy 1
    %t95 =w sub %t93, %t94
    storew %t95, %t86
    %t96 =w loadw %t86
    %t97 =w copy 0
    ret %t97
}

