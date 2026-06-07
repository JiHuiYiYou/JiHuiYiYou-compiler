data $str0 = { b "请输入一个数字: ", b 0 }
data $str1 = { b "%d", b 0 }
data $str2 = { b "你输入的是: %d\n", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =l copy $str0
    %t1 =w copy 0
    %t2 =w call $printf(l %t0, w %t1)
    %t3 =w copy 0
    %t4 =l alloc4 4
    storew %t3, %t4
    %t5 =l copy $str1
    %t6 =l copy 0
    %t7 =w call $scanf(l %t5, l %t4)
    %t8 =l copy $str2
    %t9 =w loadw %t4
    %t10 =w call $printf(l %t8, w %t9)
    %t11 =w copy 0
    ret %t11
}

