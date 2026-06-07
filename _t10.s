.data
.balign 8
str0:
	.ascii "你的 HP: %d/%d\n"
	.byte 0
/* end data */

.data
.balign 8
str1:
	.ascii "怪物 HP: %d\n"
	.byte 0
/* end data */

.data
.balign 8
str2:
	.ascii "1. 攻击"
	.byte 0
/* end data */

.data
.balign 8
str3:
	.ascii "2. 喝药 (+6 HP)"
	.byte 0
/* end data */

.data
.balign 8
str4:
	.ascii "3. 逃跑"
	.byte 0
/* end data */

.data
.balign 8
str5:
	.ascii "选择行动:"
	.byte 0
/* end data */

.data
.balign 8
str6:
	.ascii "%d"
	.byte 0
/* end data */

.data
.balign 8
str7:
	.ascii "你造成了 %d 点伤害。\n"
	.byte 0
/* end data */

.data
.balign 8
str8:
	.ascii "你喝下一瓶药。"
	.byte 0
/* end data */

.data
.balign 8
str9:
	.ascii "你没有药水！"
	.byte 0
/* end data */

.data
.balign 8
str10:
	.ascii "逃跑失败！"
	.byte 0
/* end data */

.data
.balign 8
str11:
	.ascii "你逃跑了。"
	.byte 0
/* end data */

.data
.balign 8
str12:
	.ascii "你击败了怪物！"
	.byte 0
/* end data */

.data
.balign 8
str13:
	.ascii "怪物造成了 %d 点伤害。\n"
	.byte 0
/* end data */

.data
.balign 8
str14:
	.ascii "你站在地牢入口。"
	.byte 0
/* end data */

.data
.balign 8
str15:
	.ascii "一只怪物冲了出来！"
	.byte 0
/* end data */

.data
.balign 8
str16:
	.ascii "你发现了治疗泉水。"
	.byte 0
/* end data */

.data
.balign 8
str17:
	.ascii "你找到了一个宝箱。"
	.byte 0
/* end data */

.data
.balign 8
str18:
	.ascii "前方是最终 BOSS 房间。"
	.byte 0
/* end data */

.data
.balign 8
str19:
	.ascii "你看到了出口。"
	.byte 0
/* end data */

.data
.balign 8
str20:
	.ascii "你恢复了生命值。"
	.byte 0
/* end data */

.data
.balign 8
str21:
	.ascii "获得金币和药水。"
	.byte 0
/* end data */

.data
.balign 8
str22:
	.ascii "=== 地下城文字 Rogue ==="
	.byte 0
/* end data */

.data
.balign 8
str23:
	.ascii "前往下一层？(1=是 0=退出):"
	.byte 0
/* end data */

.data
.balign 8
str24:
	.ascii "%d"
	.byte 0
/* end data */

.data
.balign 8
str25:
	.ascii "你成功逃出地牢！"
	.byte 0
/* end data */

.data
.balign 8
str26:
	.ascii "你死在了地牢深处。"
	.byte 0
/* end data */

.data
.balign 8
str27:
	.ascii "最终金币：%d\n"
	.byte 0
/* end data */

.text
.balign 16
.globl randRange
randRange:
	endbr64
	pushq %rsi
	movl (%rcx), %eax
	movl %eax, (%rcx)
	movl %r8d, %ecx
	subl %edx, %ecx
	movl %ecx, %esi
	addl $1, %esi
	movl %edx, %ecx
	cltd
	idivl %esi
	movl %edx, %eax
	movl %ecx, %edx
	addl %edx, %eax
	popq %rsi
	ret
/* end function randRange */

.text
.balign 16
.globl clamp
clamp:
	endbr64
	movl %ecx, %eax
	movl %r8d, %ecx
	cmpl %edx, %eax
	jl Lbb5
	cmpl %ecx, %eax
	jle Lbb6
	movl %ecx, %eax
	jmp Lbb6
Lbb5:
	movl %edx, %eax
Lbb6:
	ret
/* end function clamp */

.text
.balign 16
.globl monsterHp
monsterHp:
	endbr64
	cmpl $0, %ecx
	jz Lbb11
	cmpl $1, %ecx
	jz Lbb10
	movl $30, %eax
	jmp Lbb12
Lbb10:
	movl $14, %eax
	jmp Lbb12
Lbb11:
	movl $8, %eax
Lbb12:
	ret
/* end function monsterHp */

.text
.balign 16
.globl monsterAtk
monsterAtk:
	endbr64
	cmpl $0, %ecx
	jz Lbb17
	cmpl $1, %ecx
	jz Lbb16
	movl $7, %eax
	jmp Lbb18
Lbb16:
	movl $4, %eax
	jmp Lbb18
Lbb17:
	movl $2, %eax
Lbb18:
	ret
/* end function monsterAtk */

.text
.balign 16
.globl monsterGold
monsterGold:
	endbr64
	cmpl $0, %ecx
	jz Lbb23
	cmpl $1, %ecx
	jz Lbb22
	movl $50, %eax
	jmp Lbb24
Lbb22:
	movl $10, %eax
	jmp Lbb24
Lbb23:
	movl $5, %eax
Lbb24:
	ret
/* end function monsterGold */

.text
.balign 16
.globl battle
battle:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $40, %rsp
	pushq %rbx
	pushq %r12
	pushq %r13
	pushq %r14
	pushq %r15
	pushq %rsi
	pushq %rdi
	movq 88(%rbp), %rsi
	movq %rsi, -32(%rbp)
	movq 80(%rbp), %rax
	movq %rax, -24(%rbp)
	movq 72(%rbp), %r12
	movq 64(%rbp), %rdi
	movq %rdi, -16(%rbp)
	movq 56(%rbp), %r15
	movq 48(%rbp), %rdi
	movq %r9, %rbx
	movl %r8d, -8(%rbp)
	movl %edx, %r13d
	movq %rcx, %rsi
Lbb26:
	movl (%rsi), %edx
	cmpl $0, %edx
	jle Lbb44
	subq $32, %rsp
	movl %r13d, %r8d
	leaq str0(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl (%rdi), %edx
	subq $32, %rsp
	leaq str1(%rip), %rcx
	callq printf
	subq $-32, %rsp
	subq $32, %rsp
	leaq str2(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $32, %rsp
	leaq str3(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $32, %rsp
	leaq str4(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $32, %rsp
	leaq str5(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $16, %rsp
	movq %rsp, %r14
	movl $0, (%r14)
	subq $32, %rsp
	movq %r14, %rdx
	leaq str6(%rip), %rcx
	callq scanf
	movl -8(%rbp), %eax
	subq $-32, %rsp
	movl (%r14), %ecx
	cmpl $1, %ecx
	jnz Lbb29
	subq $32, %rsp
	movl $1, %r8d
	movl $4294967295, %edx
	movq %r12, %rcx
	callq randRange
	movl %eax, %ecx
	movl -8(%rbp), %eax
	subq $-32, %rsp
	movl %eax, %edx
	addl %ecx, %edx
	movl (%rdi), %eax
	subl %edx, %eax
	movl %eax, (%rdi)
	subq $32, %rsp
	leaq str7(%rip), %rcx
	callq printf
	movl -8(%rbp), %eax
	subq $-32, %rsp
Lbb29:
	movl (%r14), %ecx
	cmpl $2, %ecx
	jnz Lbb33
	movl (%rbx), %eax
	cmpl $0, %eax
	jg Lbb32
	subq $32, %rsp
	leaq str9(%rip), %rcx
	callq puts
	movl -8(%rbp), %eax
	subq $-32, %rsp
	jmp Lbb33
Lbb32:
	movl (%rsi), %eax
	movl %eax, %ecx
	addl $6, %ecx
	movl %ecx, (%rsi)
	subq $32, %rsp
	movl %r13d, %r8d
	movl $0, %edx
	callq clamp
	subq $-32, %rsp
	movl %eax, (%rsi)
	movl (%rbx), %eax
	subl $1, %eax
	movl %eax, (%rbx)
	subq $32, %rsp
	leaq str8(%rip), %rcx
	callq puts
	movl -8(%rbp), %eax
	subq $-32, %rsp
Lbb33:
	movl (%r14), %ecx
	cmpl $3, %ecx
	jz Lbb35
	movl %eax, %r14d
	jmp Lbb40
Lbb35:
	subq $32, %rsp
	movl $1, %r8d
	movl $0, %edx
	movq %r12, %rcx
	callq randRange
	movl %eax, %r14d
	subq $-32, %rsp
	cmpl $0, %r14d
	jz Lbb38
	subq $32, %rsp
	leaq str11(%rip), %rcx
	callq puts
	movl %r14d, %eax
	movl %eax, %r14d
	movl -8(%rbp), %eax
	subq $-32, %rsp
	xchgl %r14d, %eax
	jmp Lbb39
Lbb38:
	subq $32, %rsp
	leaq str10(%rip), %rcx
	callq puts
	movl %r14d, %eax
	movl -8(%rbp), %r14d
	subq $-32, %rsp
Lbb39:
	cmpl $0, %eax
	jnz Lbb46
Lbb40:
	movl (%rdi), %eax
	cmpl $0, %eax
	jle Lbb42
	subq $32, %rsp
	movl $1, %r8d
	movl $4294967295, %edx
	movq %r12, %rcx
	callq randRange
	subq $-32, %rsp
	movl %r15d, %edx
	addl %eax, %edx
	movl (%rsi), %eax
	subl %edx, %eax
	movl %eax, (%rsi)
	subq $32, %rsp
	leaq str13(%rip), %rcx
	callq printf
	subq $-32, %rsp
	jmp Lbb26
Lbb42:
	movq -32(%rbp), %rsi
	movq -16(%rbp), %rdi
	subq $32, %rsp
	leaq str12(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl (%rsi), %eax
	addl %edi, %eax
	movl %eax, (%rsi)
	jmp Lbb46
Lbb44:
	movq -24(%rbp), %rax
	movl $2, (%rax)
Lbb46:
	movq %rbp, %rsp
	subq $96, %rsp
	popq %rdi
	popq %rsi
	popq %r15
	popq %r14
	popq %r13
	popq %r12
	popq %rbx
	leave
	ret
/* end function battle */

.text
.balign 16
.globl describeRoom
describeRoom:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $8, %rsp
	pushq %rsi
	cmpl $0, %ecx
	jnz Lbb49
	subq $32, %rsp
	movl %ecx, %esi
	leaq str14(%rip), %rcx
	callq puts
	movl %esi, %ecx
	subq $-32, %rsp
Lbb49:
	cmpl $1, %ecx
	jnz Lbb51
	subq $32, %rsp
	movl %ecx, %esi
	leaq str15(%rip), %rcx
	callq puts
	movl %esi, %ecx
	subq $-32, %rsp
Lbb51:
	cmpl $2, %ecx
	jnz Lbb53
	subq $32, %rsp
	movl %ecx, %esi
	leaq str16(%rip), %rcx
	callq puts
	movl %esi, %ecx
	subq $-32, %rsp
Lbb53:
	cmpl $3, %ecx
	jnz Lbb55
	subq $32, %rsp
	movl %ecx, %esi
	leaq str17(%rip), %rcx
	callq puts
	movl %esi, %ecx
	subq $-32, %rsp
Lbb55:
	cmpl $4, %ecx
	jnz Lbb57
	subq $32, %rsp
	movl %ecx, %esi
	leaq str18(%rip), %rcx
	callq puts
	movl %esi, %ecx
	subq $-32, %rsp
Lbb57:
	cmpl $5, %ecx
	jnz Lbb59
	subq $32, %rsp
	leaq str19(%rip), %rcx
	callq puts
	subq $-32, %rsp
Lbb59:
	popq %rsi
	leave
	ret
/* end function describeRoom */

.text
.balign 16
.globl processRoom
processRoom:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $40, %rsp
	pushq %rbx
	pushq %r12
	pushq %r13
	pushq %r14
	pushq %r15
	pushq %rsi
	pushq %rdi
	movq 72(%rbp), %rdi
	movq 64(%rbp), %r13
	movq 56(%rbp), %rsi
	movq 48(%rbp), %r12
	movq %r9, %r15
	movl %r8d, -32(%rbp)
	movl %edx, %r14d
	subq $32, %rsp
	movq %rcx, %rbx
	movl %edi, %ecx
	callq describeRoom
	movl %r14d, %edx
	movq %rbx, %rcx
	subq $-32, %rsp
	cmpl $2, %edi
	jz Lbb62
	movl %edx, %r14d
	jmp Lbb63
Lbb62:
	movl (%rcx), %eax
	movq %rcx, %rbx
	movl %eax, %ecx
	addl $8, %ecx
	movl %ecx, (%rbx)
	subq $32, %rsp
	movl %edx, %r8d
	movl %edx, %r14d
	movl $0, %edx
	callq clamp
	movq %rbx, %rcx
	subq $-32, %rsp
	movl %eax, (%rcx)
	subq $32, %rsp
	movq %rcx, %rbx
	leaq str20(%rip), %rcx
	callq puts
	movq %rbx, %rcx
	subq $-32, %rsp
Lbb63:
	cmpl $3, %edi
	jnz Lbb65
	movl (%r13), %eax
	addl $20, %eax
	movl %eax, (%r13)
	movl (%r15), %eax
	addl $1, %eax
	movl %eax, (%r15)
	subq $32, %rsp
	movq %rcx, %rbx
	leaq str21(%rip), %rcx
	callq puts
	movq %rbx, %rcx
	subq $-32, %rsp
Lbb65:
	cmpl $1, %edi
	jnz Lbb67
	subq $32, %rsp
	movq %rcx, %rbx
	movl $0, %ecx
	callq monsterHp
	movq %rbx, %rcx
	movl %eax, -16(%rbp)
	subq $-32, %rsp
	subq $32, %rsp
	movq %rcx, %rbx
	movl $0, %ecx
	callq monsterAtk
	movq %rbx, %rcx
	movl %eax, -20(%rbp)
	subq $-32, %rsp
	subq $32, %rsp
	movq %rcx, %rbx
	movl $0, %ecx
	callq monsterGold
	movq %r15, %r9
	movl %r14d, %edx
	movq %rbx, %rcx
	movl %eax, %ebx
	movl -20(%rbp), %r11d
	movl -16(%rbp), %r10d
	movl -32(%rbp), %r8d
	subq $-32, %rsp
	subq $16, %rsp
	movq %rsp, %rax
	movl %r10d, (%rax)
	subq $80, %rsp
	movq %rsp, %r10
	movq %r13, 72(%r10)
	movq %rsi, 64(%r10)
	movq %r12, 56(%r10)
	movq %rbx, 48(%r10)
	movq %r11, 40(%r10)
	movq %rax, 32(%r10)
	movq %r9, %r15
	movl %edx, %r14d
	movq %rcx, %rbx
	callq battle
	movq %rbx, %rcx
	subq $-80, %rsp
Lbb67:
	cmpl $4, %edi
	jnz Lbb69
	subq $32, %rsp
	movq %rcx, %rbx
	movl $2, %ecx
	callq monsterHp
	movq %rbx, %rcx
	movl %eax, -24(%rbp)
	subq $-32, %rsp
	subq $32, %rsp
	movq %rcx, %rbx
	movl $2, %ecx
	callq monsterAtk
	movq %rbx, %rcx
	movl %eax, -28(%rbp)
	subq $-32, %rsp
	subq $32, %rsp
	movq %rcx, %rbx
	movl $2, %ecx
	callq monsterGold
	movq %r15, %r9
	movl %r14d, %edx
	movq %rbx, %rcx
	movl %eax, %ebx
	movl -28(%rbp), %r11d
	movl -24(%rbp), %r10d
	movl -32(%rbp), %r8d
	subq $-32, %rsp
	subq $16, %rsp
	movq %rsp, %rax
	movl %r10d, (%rax)
	subq $80, %rsp
	movq %rsp, %r10
	movq %r13, 72(%r10)
	movq %rsi, 64(%r10)
	movq %r12, 56(%r10)
	movq %rbx, 48(%r10)
	movq %r11, 40(%r10)
	movq %rax, 32(%r10)
	callq battle
	subq $-80, %rsp
Lbb69:
	cmpl $5, %edi
	jnz Lbb71
	movl $1, (%rsi)
Lbb71:
	movq %rbp, %rsp
	subq $96, %rsp
	popq %rdi
	popq %rsi
	popq %r15
	popq %r14
	popq %r13
	popq %r12
	popq %rbx
	leave
	ret
/* end function processRoom */

.text
.balign 16
.globl main_jhyy
main_jhyy:
	endbr64
	pushq %rbp
	movq %rsp, %rbp
	subq $32, %rsp
	pushq %rsi
	pushq %rdi
	subq $32, %rsp
	leaq str22(%rip), %rcx
	callq puts
	subq $-32, %rsp
	movl $20, -20(%rbp)
	movl $2, -16(%rbp)
	movl $0, -12(%rbp)
	movl $0, -8(%rbp)
	movl $12345, -4(%rbp)
	movl $0, %esi
Lbb74:
	movl -12(%rbp), %eax
	cmpl $0, %eax
	jnz Lbb90
	cmpl $0, %esi
	jz Lbb85
	cmpl $1, %esi
	jz Lbb84
	cmpl $2, %esi
	jz Lbb83
	cmpl $3, %esi
	jz Lbb82
	cmpl $4, %esi
	jz Lbb81
	movl $5, %eax
	jmp Lbb86
Lbb81:
	movl $4, %eax
	jmp Lbb86
Lbb82:
	movl $3, %eax
	jmp Lbb86
Lbb83:
	movl $1, %eax
	jmp Lbb86
Lbb84:
	movl $2, %eax
	jmp Lbb86
Lbb85:
	movl $0, %eax
Lbb86:
	subq $64, %rsp
	movq %rsp, %rcx
	movq %rax, 56(%rcx)
	leaq -8(%rbp), %rax
	movq %rax, 48(%rcx)
	leaq -12(%rbp), %rax
	movq %rax, 40(%rcx)
	leaq -4(%rbp), %rax
	movq %rax, 32(%rcx)
	leaq -16(%rbp), %r9
	movl $4, %r8d
	movl $20, %edx
	leaq -20(%rbp), %rcx
	callq processRoom
	subq $-64, %rsp
	movl -12(%rbp), %eax
	cmpl $0, %eax
	jnz Lbb74
	subq $32, %rsp
	leaq str23(%rip), %rcx
	callq puts
	subq $-32, %rsp
	subq $16, %rsp
	movq %rsp, %rdi
	movl $0, (%rdi)
	subq $32, %rsp
	movq %rdi, %rdx
	leaq str24(%rip), %rcx
	callq scanf
	subq $-32, %rsp
	movl (%rdi), %eax
	cmpl $0, %eax
	jz Lbb89
	addl $1, %esi
	jmp Lbb74
Lbb89:
	movl $1, -12(%rbp)
	jmp Lbb74
Lbb90:
	cmpl $1, %eax
	jz Lbb92
	subq $32, %rsp
	leaq str26(%rip), %rcx
	callq puts
	subq $-32, %rsp
	jmp Lbb93
Lbb92:
	subq $32, %rsp
	leaq str25(%rip), %rcx
	callq puts
	subq $-32, %rsp
Lbb93:
	movl -8(%rbp), %edx
	subq $32, %rsp
	leaq str27(%rip), %rcx
	callq printf
	subq $-32, %rsp
	movl $0, %eax
	movq %rbp, %rsp
	subq $48, %rsp
	popq %rdi
	popq %rsi
	leave
	ret
/* end function main_jhyy */

