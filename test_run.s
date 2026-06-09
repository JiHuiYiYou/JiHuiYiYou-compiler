.data
.balign 8
str0:
	.ascii "B: %d\n"
	.byte 0
/* end data */

.text
.balign 16
.globl factorial
factorial:
	endbr64
	movl $1, %eax
	movl $1, %edx
Lbb2:
	cmpl %ecx, %edx
	jg Lbb4
	imull %edx, %eax
	addl $1, %edx
	jmp Lbb2
Lbb4:
	ret
/* end function factorial */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	movl $5, %ecx
	callq factorial
	movl %eax, %edx
	subq $-32, %rsp
	subq $32, %rsp
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

