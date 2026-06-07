.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	movl $0, %eax
	movl $0, %ecx
Lbb2:
	cmpl $5, %ecx
	jge Lbb4
	addl %ecx, %eax
	addl $1, %ecx
	jmp Lbb2
Lbb4:
	ret
/* end function main_jhyy */

