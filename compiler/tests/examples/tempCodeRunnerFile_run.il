export function w $factorial(w %n) {
@start0
    %t0 =w copy %n
    %t1 =w copy 1
    %t2 =l alloc4 4
    storew %t1, %t2
    %t3 =w copy 1
    %t4 =l alloc4 4
    storew %t3, %t4
    jmp @loop1
@loop1
    %t5 =w loadw %t4
    %t6 =w cslew %t5, %t0
    jnz %t6, @body2, @exit3
@body2
    %t7 =w loadw %t2
    %t8 =w loadw %t4
    %t9 =w mul %t7, %t8
    storew %t9, %t2
    %t10 =w loadw %t4
    %t11 =w copy 1
    %t12 =w add %t10, %t11
    storew %t12, %t4
    jmp @loop1
@exit3
    %t13 =w loadw %t2
    ret %t13
}

