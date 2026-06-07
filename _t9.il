data $str0 = { b "Hello from return test!\n", b 0 }
data $str1 = { b "10 + 20 = %d\n", b 0 }
export function w $add(w %a, w %b) {
@start0
    %t0 =w copy %a
    %t1 =w copy %b
    %t2 =w add %t0, %t1
    ret %t2
}

export function w $greet() {
@start1
    %t3 =l copy $str0
    %t4 =w copy 0
    %t5 =w call $printf(l %t3, w %t4)
    %t6 =w copy 100
    ret %t6
}

export function w $main_jhyy() {
@start2
    %t7 =w copy 10
    %t8 =w copy 20
    %t9 =w call $add(w %t7, w %t8)
    %t10 =l copy $str1
    %t11 =w call $printf(l %t10, w %t9)
    %t12 =w call $greet()
    ret %t12
}

