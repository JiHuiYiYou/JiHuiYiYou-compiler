data $str0 = { b "BUG: short-circuit failed!\n", b 0 }
data $str1 = { b "Test1 (false && X): %d (expect 0)\n", b 0 }
data $str2 = { b "Test2 (true || X): %d (expect 1)\n", b 0 }
data $str3 = { b "Test3 (true && true): %d (expect 1)\n", b 0 }
data $str4 = { b "Test4 (false || true): %d (expect 1)\n", b 0 }
data $str5 = { b "Test5 (false || false): %d (expect 0)\n", b 0 }
export function w $crash_if_called() {
@start0
    %t0 =l copy $str0
    %t1 =w copy 0
    %t2 =w call $printf(l %t0, w %t1)
    %t3 =w copy 99
    ret %t3
}

export function w $main_jhyy() {
@start1
    %t4 =w copy 0
    %t5 =w copy 0
    %t6 =w cnew %t4, %t5
    jnz %t6, @sc_eval2, @sc_false4
@sc_false4
    %t8 =w copy 0
    jmp @sc_merge3
@sc_eval2
    %t9 =w call $crash_if_called()
    %t10 =w copy 0
    %t11 =w cnew %t9, %t10
    %t12 =w cnew %t11, 0
    jmp @sc_merge3
@sc_merge3
    %t7 =w phi @sc_false4 %t8, @sc_eval2 %t12
    %t13 =l copy $str1
    %t14 =w call $printf(l %t13, w %t7)
    %t15 =w copy 1
    %t16 =w copy 0
    %t17 =w cnew %t15, %t16
    jnz %t17, @sc_true7, @sc_eval5
@sc_true7
    %t19 =w copy 1
    jmp @sc_merge6
@sc_eval5
    %t20 =w call $crash_if_called()
    %t21 =w copy 0
    %t22 =w cnew %t20, %t21
    %t23 =w cnew %t22, 0
    jmp @sc_merge6
@sc_merge6
    %t18 =w phi @sc_true7 %t19, @sc_eval5 %t23
    %t24 =l copy $str2
    %t25 =w call $printf(l %t24, w %t18)
    %t26 =w copy 1
    %t27 =w copy 0
    %t28 =w cnew %t26, %t27
    jnz %t28, @sc_eval8, @sc_false10
@sc_false10
    %t30 =w copy 0
    jmp @sc_merge9
@sc_eval8
    %t31 =w copy 1
    %t32 =w copy 0
    %t33 =w cnew %t31, %t32
    %t34 =w cnew %t33, 0
    jmp @sc_merge9
@sc_merge9
    %t29 =w phi @sc_false10 %t30, @sc_eval8 %t34
    %t35 =l copy $str3
    %t36 =w call $printf(l %t35, w %t29)
    %t37 =w copy 0
    %t38 =w copy 0
    %t39 =w cnew %t37, %t38
    jnz %t39, @sc_true13, @sc_eval11
@sc_true13
    %t41 =w copy 1
    jmp @sc_merge12
@sc_eval11
    %t42 =w copy 1
    %t43 =w copy 0
    %t44 =w cnew %t42, %t43
    %t45 =w cnew %t44, 0
    jmp @sc_merge12
@sc_merge12
    %t40 =w phi @sc_true13 %t41, @sc_eval11 %t45
    %t46 =l copy $str4
    %t47 =w call $printf(l %t46, w %t40)
    %t48 =w copy 0
    %t49 =w copy 0
    %t50 =w cnew %t48, %t49
    jnz %t50, @sc_true16, @sc_eval14
@sc_true16
    %t52 =w copy 1
    jmp @sc_merge15
@sc_eval14
    %t53 =w copy 0
    %t54 =w copy 0
    %t55 =w cnew %t53, %t54
    %t56 =w cnew %t55, 0
    jmp @sc_merge15
@sc_merge15
    %t51 =w phi @sc_true16 %t52, @sc_eval14 %t56
    %t57 =l copy $str5
    %t58 =w call $printf(l %t57, w %t51)
    %t59 =w copy 0
    ret %t59
}

