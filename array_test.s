.data
.balign 8
str0:
	.ascii "=== Array Test ==="
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "arr[0] = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "arr[2] = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str3:
	.ascii "arr[4] = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str4:
	.ascii "arr2[0] before: %d\n"
	.byte 0
/* end data */

.data
.balign 8
str5:
	.ascii "arr2[0] after: %d\n"
	.byte 0
/* end data */

.data
.balign 8
str6:
	.ascii "sum = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str7:
	.ascii "typed[1] = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str8:
	.ascii "All array tests passed!"
	.byte 0
/* end data */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	leaq str0(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $32, %rsp
	movl $10, %edx
	leaq str1(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $30, %edx
	leaq str2(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $50, %edx
	leaq str3(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $1, %edx
	leaq str4(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $100, %edx
	leaq str5(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $30, %edx
	leaq str6(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $99, %edx
	leaq str7(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	leaq str8(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

