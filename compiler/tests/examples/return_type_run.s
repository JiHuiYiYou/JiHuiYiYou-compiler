.data
.balign 8
str0:
	.ascii "Hello from return test!\n"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "10 + 20 = %d\n"
	.byte 0
/* end data */

.text
.balign 16
.globl add
add:
	endbr64
	movl %ecx, %eax
	addl %edx, %eax
	ret
/* end function add */

.text
.balign 16
.globl greet
greet:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	movl $0, %edx
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $100, %eax
	leave
	ret
/* end function greet */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	movl $20, %edx
	movl $10, %ecx
	callq add
	movl %eax, %edx
	subq $-32, %rsp
	subq $32, %rsp
	leaq str1(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	callq greet
	subq $-32, %rsp
	leave
	ret
/* end function main_jhyy */

