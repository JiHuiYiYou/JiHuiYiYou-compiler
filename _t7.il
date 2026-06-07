export function w $main_jhyy() {
@start0
    %t0 =w copy 2
    %t1 =w copy 1
    %t2 =w ceqw %t0, %t1
    jnz %t2, @arm2, @next3
@arm2
    %t3 =w copy 10
    jmp @merge1
@next3
    %t4 =w copy 2
    %t5 =w ceqw %t0, %t4
    jnz %t5, @arm4, @next5
@arm4
    %t6 =w copy 20
    jmp @merge1
@next5
    jmp @arm6
@arm6
    %t7 =w copy 0
    jmp @merge1
@merge1
    %t8 =w phi @arm2 %t3, @arm4 %t6, @arm6 %t7
    ret %t8
}

