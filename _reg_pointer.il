export function w $main_jhyy() {
@start0
    %t0 =w copy 42
    %t1 =l alloc4 4
    storew %t0, %t1
    %t2 =l copy 0
    %t3 =w copy 100
    storew %t3, %t1
    %t4 =w loadw %t1
    ret %t4
}

