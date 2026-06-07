export function w $add(w %a, w %b) {
@start0
    %t0 =w copy %a
    %t1 =w copy %b
    %t2 =w add %t0, %t1
    ret %t2
}

export function w $get_answer() {
@start1
    %t3 =w copy 42
    ret %t3
}

export function w $main_jhyy() {
@start2
    %t4 =w copy 10
    %t5 =w copy 20
    %t6 =w call $add(w %t4, w %t5)
    %t7 =w call $get_answer()
    %t8 =w add %t6, %t7
    ret %t8
}

