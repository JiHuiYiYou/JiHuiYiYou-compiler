#ifndef CODEGEN_H
#define CODEGEN_H

#include "ast.h"
#include "ir.h"
#include "target/target_dispatch.h"

/* v2.0.0: cg_module takes a Target parameter for dispatcher routing.
   Amd64Win keeps full v1.x path (body unchanged); other targets fatal
   pointing at the version where they ship (v2.1.0 / v2.x M2). */
void cg_module(IRBuf *ir, Node *module, Target t);

#endif
