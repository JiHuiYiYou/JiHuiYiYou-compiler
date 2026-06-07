data $str0 = { b "Float literal test (hardware check)", b 0 }
data $str1 = { b "Float test compiled OK", b 0 }
export function w $main_jhyy() {
@start0
    %t0 =l copy $str0
    %t1 =w call $puts(l %t0)
    %t2 =d copy d_3.1400000000000001
    %t3 =d copy d_2.5
    %t4 =l copy $str1
    %t5 =w call $puts(l %t4)
    %t6 =w copy 0
    ret %t6
}

