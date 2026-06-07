.data
.balign 8
str0:
	.ascii "Float literal test (hardware check)"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "Float test compiled OK"
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
	leaq str1(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

