export function w $main_jhyy() {
@start0
    %t0 =l alloc8 8
    %t1 =w copy 10
    %t2 =l add %t0, 0
    storew %t1, %t2
    %t3 =w copy 20
    %t4 =l add %t0, 4
    storew %t3, %t4
    %t5 =w loadw %t0
    %t6 =l add %t0, 4
    %t7 =w loadw %t6
    %t8 =w add %t5, %t7
    ret %t8
}

