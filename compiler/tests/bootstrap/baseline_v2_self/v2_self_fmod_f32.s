.text
.balign 16
.globl main_jhyy
main_jhyy:
	pushq %rbp
	movq %rsp, %rbp
	subq $104, %rsp
.Lstart0_b0_fn1:
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movabsq $1088421888, %rax
	movq %rax, -40(%rbp)
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movabsq $1073741824, %rax
	movq %rax, -48(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movss -40(%rbp), %xmm0
	divss -48(%rbp), %xmm0
	movss %xmm0, -64(%rbp)
	movss -64(%rbp), %xmm0
	cvttss2si %xmm0, %eax
	movl %eax, -72(%rbp)
	movl -72(%rbp), %eax
	cltq
	cvtsi2ss %rax, %xmm0
	movss %xmm0, -80(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movss -80(%rbp), %xmm0
	mulss -48(%rbp), %xmm0
	movss %xmm0, -88(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movss -40(%rbp), %xmm0
	subss -88(%rbp), %xmm0
	movss %xmm0, -56(%rbp)
	movss -56(%rbp), %xmm0
	cvttss2si %xmm0, %eax
	movl %eax, -96(%rbp)
	movl -96(%rbp), %eax
	movq %rbp, %rsp
	popq %rbp
	ret
