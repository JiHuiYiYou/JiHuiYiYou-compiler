.data
.balign 8
str0:
	.ascii "BUG: short-circuit failed!\n"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "Test1 (false && X): %d (expect 0)\n"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "Test2 (true || X): %d (expect 1)\n"
	.byte 0
/* end data */

.data
.balign 8
str3:
	.ascii "Test3 (true && true): %d (expect 1)\n"
	.byte 0
/* end data */

.data
.balign 8
str4:
	.ascii "Test4 (false || true): %d (expect 1)\n"
	.byte 0
/* end data */

.data
.balign 8
str5:
	.ascii "Test5 (false || false): %d (expect 0)\n"
	.byte 0
/* end data */

.text
.balign 16
.globl crash_if_called
crash_if_called:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	movl $0, %edx
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $99, %eax
	leave
	ret
/* end function crash_if_called */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	movl $0, %edx
	subq $32, %rsp
	leaq str1(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $1, %edx
	subq $32, %rsp
	leaq str2(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $1, %edx
	subq $32, %rsp
	leaq str3(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	movl $1, %edx
	leaq str4(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %edx
	subq $32, %rsp
	leaq str5(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	leave
	ret
/* end function main_jhyy */

