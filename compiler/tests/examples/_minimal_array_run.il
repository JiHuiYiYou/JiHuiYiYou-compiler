data $str0 = { b "A: %d\n", b 0 }
data $str1 = { b "B: %d\n", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =l alloc16 16
    %t1 =w copy 10
    storew %t1, %t0
    %t2 =w copy 20
    %t3 =l copy 4
    %t4 =l add %t0, %t3
    storew %t2, %t4
    %t5 =w copy 30
    %t6 =l copy 8
    %t7 =l add %t0, %t6
    storew %t5, %t7
    %t8 =w copy 0
    %t9 =l copy 0
    %t10 =l add %t0, %t9
    %t11 =w loadw %t10
    %t12 =l copy $str0
    %t13 =w call $printf(l %t12, w %t11)
    %t14 =l copy $str1
    %t15 =w copy 0
    %t16 =l copy 0
    %t17 =l add %t0, %t16
    %t18 =w loadw %t17
    %t19 =w call $printf(l %t14, w %t18)
    %t20 =w copy 0
    ret %t20
}

