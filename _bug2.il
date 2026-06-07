data $str0 = { b "x > 5\n", b 0 }
data $str1 = { b "x <= 5\n", b 0 }
data $str2 = { b "result = %d\n", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =w copy 10
    %t1 =l alloc4 4
    storew %t0, %t1
    %t2 =w loadw %t1
    %t3 =w copy 5
    %t4 =w csgtw %t2, %t3
    jnz %t4, @then1, @else2
@then1
    %t5 =l copy $str0
    %t6 =w copy 0
    %t7 =w call $printf(l %t5, w %t6)
    jmp @merge3
@else2
    %t8 =l copy $str1
    %t9 =w copy 0
    %t10 =w call $printf(l %t8, w %t9)
    jmp @ep4
@ep4
    jmp @merge3
@merge3
    %t11 =w phi @then1 %t7, @ep4 %t10
    %t12 =w loadw %t1
    %t13 =w copy 20
    %t14 =w csgtw %t12, %t13
    jnz %t14, @then5, @else6
@then5
    %t15 =w copy 100
    jmp @merge7
@else6
    %t16 =w loadw %t1
    %t17 =w copy 10
    %t18 =w csgtw %t16, %t17
    jnz %t18, @then8, @else9
@then8
    %t19 =w copy 200
    jmp @merge10
@else9
    %t20 =w copy 300
    jmp @ep11
@ep11
    jmp @merge10
@merge10
    %t21 =w phi @then8 %t19, @ep11 %t20
    jmp @ep12
@ep12
    jmp @merge7
@merge7
    %t22 =w phi @then5 %t15, @ep12 %t21
    %t23 =l copy $str2
    %t24 =w call $printf(l %t23, w %t22)
    %t25 =w copy 0
    ret %t25
}

