data $str0 = { b "val after *p = *p - 20: %d\n", b 0 }
data $str1 = { b "val2 after workaround: %d\n", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =w copy 50
    %t1 =l alloc4 4
    storew %t0, %t1
    %t2 =l copy 0
    %t3 =l alloc8 8
    storel %t1, %t3
    %t4 =l loadl %t3
    %t5 =w loadw %t4
    %t6 =w copy 20
    %t7 =w sub %t5, %t6
    %t8 =l loadl %t3
    storew %t7, %t8
    %t9 =l copy $str0
    %t10 =w loadw %t1
    %t11 =w call $printf(l %t9, w %t10)
    %t12 =w copy 50
    %t13 =l alloc4 4
    storew %t12, %t13
    %t14 =l copy 0
    %t15 =l alloc8 8
    storel %t13, %t15
    %t16 =l loadl %t15
    %t17 =w loadw %t16
    %t18 =w copy 20
    %t19 =w sub %t17, %t18
    %t20 =l loadl %t15
    storew %t19, %t20
    %t21 =l copy $str1
    %t22 =w loadw %t13
    %t23 =w call $printf(l %t21, w %t22)
    %t24 =w copy 0
    ret %t24
}

