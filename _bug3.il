data $str0 = { b "positive", b 0 }
data $str1 = { b "not positive", b 0 }
data $str2 = { b "result = %d\n", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =w copy 1
    %t1 =w copy 0
    %t2 =w csgtw %t0, %t1
    jnz %t2, @then1, @else2
@then1
    %t3 =l copy $str0
    %t4 =w call $puts(l %t3)
    jmp @merge3
@else2
    %t5 =l copy $str1
    %t6 =w call $puts(l %t5)
    jmp @ep4
@ep4
    jmp @merge3
@merge3
    %t7 =w phi @then1 %t4, @ep4 %t6
    %t8 =w copy 0
    %t9 =w csgtw %t0, %t8
    jnz %t9, @then5, @else6
@then5
    %t10 =w copy 100
    jmp @merge7
@else6
    %t11 =w copy 200
    jmp @ep8
@ep8
    jmp @merge7
@merge7
    %t12 =w phi @then5 %t10, @ep8 %t11
    %t13 =l copy $str2
    %t14 =w call $printf(l %t13, w %t12)
    %t15 =w copy 0
    ret %t15
}

