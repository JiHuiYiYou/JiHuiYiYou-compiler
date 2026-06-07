data $str0 = { b "x = %d\n", b 0 }
data $str1 = { b "count > 1", b 0 }
data $str2 = { b "count == 1", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =w copy 1
    %t1 =l alloc4 4
    storew %t0, %t1
    %t2 =w loadw %t1
    %t3 =w copy 0
    %t4 =w csgtw %t2, %t3
    jnz %t4, @then1, @else2
@then1
    %t5 =w copy 100
    storew %t5, %t1
    jmp @merge3
@else2
    %t6 =w copy 200
    storew %t6, %t1
    jmp @ep4
@ep4
    jmp @merge3
@merge3
    %t7 =w phi @then1 %t0, @ep4 %t0
    %t8 =l copy $str0
    %t9 =w loadw %t1
    %t10 =w call $printf(l %t8, w %t9)
    %t11 =w copy 3
    %t12 =l alloc4 4
    storew %t11, %t12
    jmp @loop5
@loop5
    %t13 =w loadw %t12
    %t14 =w copy 0
    %t15 =w csgtw %t13, %t14
    jnz %t15, @body6, @exit7
@body6
    %t16 =w loadw %t12
    %t17 =w copy 1
    %t18 =w csgtw %t16, %t17
    jnz %t18, @then8, @else9
@then8
    %t19 =l copy $str1
    %t20 =w call $puts(l %t19)
    %t21 =w loadw %t12
    %t22 =w copy 1
    %t23 =w sub %t21, %t22
    storew %t23, %t12
    jmp @merge10
@else9
    %t24 =l copy $str2
    %t25 =w call $puts(l %t24)
    %t26 =w loadw %t12
    %t27 =w copy 1
    %t28 =w sub %t26, %t27
    storew %t28, %t12
    jmp @ep11
@ep11
    jmp @merge10
@merge10
    %t29 =w phi @then8 %t20, @ep11 %t25
    jmp @loop5
@exit7
    %t30 =w copy 0
    ret %t30
}

