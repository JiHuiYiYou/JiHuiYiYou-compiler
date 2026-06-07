.data
.balign 8
str0:
	.ascii "x > 5\n"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "x <= 5\n"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "result = %d\n"
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
	movl $0, %edx
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $300, %eax
	movl %eax, %edx
	subq $32, %rsp
	leaq str2(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

