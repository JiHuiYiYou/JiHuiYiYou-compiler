#ifndef CODEGEN_H
#define CODEGEN_H

#include "ast.h"
#include "ir.h"

void cg_module(IRBuf *ir, Node *module);

#endif
