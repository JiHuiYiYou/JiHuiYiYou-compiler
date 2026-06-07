export function w $main_jhyy() {
@start0
    %t0 =w copy 0
    %t1 =l alloc4 4
    storew %t0, %t1
    %t2 =w copy 0
    %t3 =w copy 5
    %t4 =l alloc4 4
    storew %t2, %t4
    jmp @loop1
@loop1
    %t5 =w loadw %t4
    %t6 =w csltw %t5, %t3
    jnz %t6, @body2, @exit3
@body2
    %t7 =w loadw %t1
    %t8 =w loadw %t4
    %t9 =w add %t7, %t8
    storew %t9, %t1
    %t10 =w loadw %t4
    %t11 =w add %t10, 1
    storew %t11, %t4
    jmp @loop1
@exit3
    %t12 =w loadw %t1
    ret %t12
}

