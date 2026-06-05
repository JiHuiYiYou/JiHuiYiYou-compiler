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

