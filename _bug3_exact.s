.data
.balign 8
str0:
	.ascii "x = %d\n"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "count > 1"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "count == 1"
	.byte 0
/* end data */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $24, %rsp
	pushq %rsi
	movl $100, %edx
	subq $32, %rsp
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $3, -4(%rbp)
	movl $3, %esi
Lbb2:
	cmpl $0, %esi
	jle Lbb6
	cmpl $1, %esi
	setg %al
	movzbl %al, %eax
	subl $1, %esi
	cmpl $0, %eax
	jnz Lbb5
	subq $32, %rsp
	leaq str2(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl %esi, -4(%rbp)
	jmp Lbb2
Lbb5:
	subq $32, %rsp
	leaq str1(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl %esi, -4(%rbp)
	jmp Lbb2
Lbb6:
	movl $0, %eax
	popq %rsi
	leave
	ret
/* end function main_jhyy */

