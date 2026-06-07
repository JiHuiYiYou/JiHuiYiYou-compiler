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
.globl get_answer
get_answer:
	endbr64
	movl $42, %eax
	ret
/* end function get_answer */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $8, %rsp
	pushq %rsi
	subq $32, %rsp
	movl $20, %edx
	movl $10, %ecx
	callq add
	movl %eax, %esi
	subq $-32, %rsp
	subq $32, %rsp
	callq get_answer
	subq $-32, %rsp
	addl %esi, %eax
	popq %rsi
	leave
	ret
/* end function main_jhyy */

