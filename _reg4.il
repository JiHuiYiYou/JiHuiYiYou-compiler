data $str0 = { b "=== Array Test ===", b 0 }
data $str1 = { b "arr[0] = %d\n", b 0 }
data $str2 = { b "arr[2] = %d\n", b 0 }
data $str3 = { b "arr[4] = %d\n", b 0 }
data $str4 = { b "arr2[0] before: %d\n", b 0 }
data $str5 = { b "arr2[0] after: %d\n", b 0 }
data $str6 = { b "sum = %d\n", b 0 }
data $str7 = { b "typed[1] = %d\n", b 0 }
data $str8 = { b "All array tests passed!", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =l copy $str0
    %t1 =w call $puts(l %t0)
    %t2 =l alloc16 32
    %t3 =w copy 10
    storew %t3, %t2
    %t4 =w copy 20
    %t5 =l copy 4
    %t6 =l add %t2, %t5
    storew %t4, %t6
    %t7 =w copy 30
    %t8 =l copy 8
    %t9 =l add %t2, %t8
    storew %t7, %t9
    %t10 =w copy 40
    %t11 =l copy 12
    %t12 =l add %t2, %t11
    storew %t10, %t12
    %t13 =w copy 50
    %t14 =l copy 16
    %t15 =l add %t2, %t14
    storew %t13, %t15
    %t16 =l copy $str1
    %t17 =w copy 0
    %t18 =l copy 0
    %t19 =l add %t2, %t18
    %t20 =w loadw %t19
    %t21 =w call $printf(l %t16, w %t20)
    %t22 =l copy $str2
    %t23 =w copy 2
    %t24 =l copy 8
    %t25 =l add %t2, %t24
    %t26 =w loadw %t25
    %t27 =w call $printf(l %t22, w %t26)
    %t28 =l copy $str3
    %t29 =w copy 4
    %t30 =l copy 16
    %t31 =l add %t2, %t30
    %t32 =w loadw %t31
    %t33 =w call $printf(l %t28, w %t32)
    %t34 =l alloc16 16
    %t35 =w copy 1
    storew %t35, %t34
    %t36 =w copy 2
    %t37 =l copy 4
    %t38 =l add %t34, %t37
    storew %t36, %t38
    %t39 =w copy 3
    %t40 =l copy 8
    %t41 =l add %t34, %t40
    storew %t39, %t41
    %t42 =l copy $str4
    %t43 =w copy 0
    %t44 =l copy 0
    %t45 =l add %t34, %t44
    %t46 =w loadw %t45
    %t47 =w call $printf(l %t42, w %t46)
    %t48 =w copy 100
    %t49 =w copy 0
    %t50 =l copy 0
    %t51 =l add %t34, %t50
    storew %t48, %t51
    %t52 =l copy $str5
    %t53 =w copy 0
    %t54 =l copy 0
    %t55 =l add %t34, %t54
    %t56 =w loadw %t55
    %t57 =w call $printf(l %t52, w %t56)
    %t58 =l alloc16 16
    %t59 =w copy 5
    storew %t59, %t58
    %t60 =w copy 10
    %t61 =l copy 4
    %t62 =l add %t58, %t61
    storew %t60, %t62
    %t63 =w copy 15
    %t64 =l copy 8
    %t65 =l add %t58, %t64
    storew %t63, %t65
    %t66 =w copy 0
    %t67 =l copy 0
    %t68 =l add %t58, %t67
    %t69 =w loadw %t68
    %t70 =w copy 1
    %t71 =l copy 4
    %t72 =l add %t58, %t71
    %t73 =w loadw %t72
    %t74 =w copy 2
    %t75 =l copy 8
    %t76 =l add %t58, %t75
    %t77 =w loadw %t76
    %t78 =l copy $str6
    %t79 =w add %t69, %t73
    %t80 =w add %t79, %t77
    %t81 =w call $printf(l %t78, w %t80)
    %t82 =l alloc16 16
    %t83 =w copy 7
    storew %t83, %t82
    %t84 =w copy 8
    %t85 =l copy 4
    %t86 =l add %t82, %t85
    storew %t84, %t86
    %t87 =w copy 9
    %t88 =l copy 8
    %t89 =l add %t82, %t88
    storew %t87, %t89
    %t90 =w copy 99
    %t91 =w copy 1
    %t92 =l copy 4
    %t93 =l add %t82, %t92
    storew %t90, %t93
    %t94 =l copy $str7
    %t95 =w copy 1
    %t96 =l copy 4
    %t97 =l add %t82, %t96
    %t98 =w loadw %t97
    %t99 =w call $printf(l %t94, w %t98)
    %t100 =l copy $str8
    %t101 =w call $puts(l %t100)
    %t102 =w copy 0
    ret %t102
}

