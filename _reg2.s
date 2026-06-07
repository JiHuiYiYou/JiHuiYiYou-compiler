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
.globl fibonacci
fibonacci:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $8, %rsp
	pushq %rsi
	movl %ecx, %esi
	cmpl $1, %esi
	jle Lbb7
	movl %esi, %ecx
	subl $1, %ecx
	subq $32, %rsp
	callq fibonacci
	xchgl %eax, %esi
	subq $-32, %rsp
	movl %eax, %ecx
	subl $2, %ecx
	subq $32, %rsp
	callq fibonacci
	subq $-32, %rsp
	addl %esi, %eax
	jmp Lbb8
Lbb7:
	movl %esi, %eax
Lbb8:
	popq %rsi
	leave
	ret
/* end function fibonacci */

.text
.balign 16
.globl gcd
gcd:
	endbr64
	movl %ecx, %eax
	movl %edx, %ecx
	movl %ecx, %edx
	movl %eax, %ecx
Lbb11:
	cmpl $0, %edx
	jz Lbb14
	movl %ecx, %eax
	movl %edx, %ecx
	cltd
	idivl %ecx
	xchgl %edx, %ecx
	xchgl %edx, %ecx
	jmp Lbb11
Lbb14:
	movl %ecx, %eax
	ret
/* end function gcd */

.text
.balign 16
.globl sum_range
sum_range:
	endbr64
	movl $0, %eax
Lbb18:
	cmpl %edx, %ecx
	jg Lbb20
	addl %ecx, %eax
	addl $1, %ecx
	jmp Lbb18
Lbb20:
	ret
/* end function sum_range */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	pushq %rsi
	pushq %rdi
	subq $32, %rsp
	movl $5, %ecx
	callq factorial
	movl %eax, %esi
	subq $-32, %rsp
	subq $32, %rsp
	movl $10, %ecx
	callq fibonacci
	subq $-32, %rsp
	movl %esi, %edi
	addl %eax, %edi
	subq $32, %rsp
	movl $18, %edx
	movl $48, %ecx
	callq gcd
	movl %eax, %esi
	subq $-32, %rsp
	subq $32, %rsp
	movl $10, %edx
	movl $1, %ecx
	callq sum_range
	subq $-32, %rsp
	addl %esi, %eax
	movl %edi, %esi
	addl %eax, %esi
	negl %eax
	addl %edi, %eax
	movl %esi, %ecx
	imull %eax, %ecx
	movl $10, %edi
	movl %ecx, %eax
	cltd
	idivl %edi
	cmpl %ecx, %esi
	subq $16, %rsp
	movq %rsp, %rax
	movl $1, (%rax)
	movl $3, (%rax)
	movl $9, (%rax)
	movl $8, (%rax)
	movl $0, %eax
	movq %rbp, %rsp
	subq $16, %rsp
	popq %rdi
	popq %rsi
	leave
	ret
/* end function main_jhyy */

