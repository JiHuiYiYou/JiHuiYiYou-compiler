.text
.balign 16
.globl main_jhyy
main_jhyy:
	pushq %rbp
	movq %rsp, %rbp
	subq $136, %rsp
.Lstart0_b0_fn1:
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movabsq $4620130267728707584, %rax
	movq %rax, -40(%rbp)
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movabsq $0, %rax
	movq %rax, -56(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movsd -56(%rbp), %xmm0
	subsd -40(%rbp), %xmm0
	movsd %xmm0, -48(%rbp)
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movabsq $4611686018427387904, %rax
	movq %rax, -64(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movsd -48(%rbp), %xmm0
	divsd -64(%rbp), %xmm0
	movsd %xmm0, -80(%rbp)
	cvttsd2si -80(%rbp), %eax
	movl %eax, -88(%rbp)
	movl -88(%rbp), %eax
	cltq
	cvtsi2sd %rax, %xmm0
	movsd %xmm0, -96(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movsd -96(%rbp), %xmm0
	mulsd -64(%rbp), %xmm0
	movsd %xmm0, -104(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movsd -48(%rbp), %xmm0
	subsd -104(%rbp), %xmm0
	movsd %xmm0, -72(%rbp)
	cvttsd2si -72(%rbp), %eax
	movl %eax, -112(%rbp)
# emit_copy: 1-to-1 简化栈分配 (per L4 § 3.5 E7)
	movl $100, -120(%rbp)
# emit_binop: add/sub/mul/div/mod via %rax (per L4 § 3.5 E8) [v2.11.2: cast 真修 T1-c + '-' drop T2-a]
	movl -112(%rbp), %eax
	addl -120(%rbp), %eax
	movl %eax, -128(%rbp)
	movl -128(%rbp), %eax
	movq %rbp, %rsp
	popq %rbp
	ret
