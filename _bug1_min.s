.data
.balign 8
str0:
	.ascii "x = %d\n"
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
	movl $30, %edx
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

