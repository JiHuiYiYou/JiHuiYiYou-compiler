.data
.balign 8
str0:
	.ascii "请输入一个数字: "
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "%d"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "你输入的是: %d\n"
	.byte 0
/* end data */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $16, %rsp
	subq $32, %rsp
	movl $0, %edx
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, -4(%rbp)
	subq $32, %rsp
	leaq -4(%rbp), %rdx
	leaq str1(%rip), %rcx
	callq scanf
	subq $-32, %rsp
	movl -4(%rbp), %edx
	subq $32, %rsp
	leaq str2(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

