data $str0 = { b "x = %d\n", b 0 }
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
    %t8 =l copy $str0
    %t9 =w call $printf(l %t8, w %t7)
    %t10 =w copy 0
    ret %t10
}

