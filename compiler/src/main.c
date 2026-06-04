#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "arena.h"
#include "lexer.h"
#include "parser.h"
#include "sema.h"
#include "codegen.h"

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (!f) { fprintf(stderr, "cannot open '%s'\n", path); return NULL; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz + 1);
    if (!buf) { fclose(f); return NULL; }
    fread(buf, 1, sz, f);
    buf[sz] = '\0';
    fclose(f);
    return buf;
}

static int compile(const char *input, const char *output) {
    char *source = read_file(input);
    if (!source) return 1;

    Arena arena;
    arena_init(&arena, 16 * 1024 * 1024); /* 16 MB */

    /* lex */
    Lexer lexer;
    lexer_init(&lexer, source, input);

    /* parse */
    Parser parser;
    parser_init(&parser, &lexer, &arena);
    Node *ast = parser_parse(&parser);
    if (parser.error_count > 0) {
        fprintf(stderr, "%d parse error(s)\n", parser.error_count);
        arena_free(&arena);
        free(source);
        return 1;
    }

    /* semantic analysis */
    SemaContext sema;
    sema_init(&sema, &arena);
    int errs = sema_check(&sema, ast);
    if (errs > 0) {
        fprintf(stderr, "%d semantic error(s)\n", errs);
        arena_free(&arena);
        free(source);
        return 1;
    }

    /* codegen */
    IRBuf ir;
    ir_init(&ir, &arena);
    cg_module(&ir, ast);

    /* write .il file */
    char il_path[1024];
    snprintf(il_path, sizeof(il_path), "%s.il", output);
    FILE *ilf = fopen(il_path, "w");
    if (!ilf) {
        fprintf(stderr, "cannot write '%s'\n", il_path);
        arena_free(&arena); free(source); return 1;
    }
    fwrite(ir.buf, 1, ir.len, ilf);
    fclose(ilf);

    /* invoke QBE */
    char asm_path[1024];
    snprintf(asm_path, sizeof(asm_path), "%s.s", output);
    char cmd[2048];
    snprintf(cmd, sizeof(cmd),
             "C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/qbe/qbe.exe -t amd64_win -o %s %s",
             asm_path, il_path);
    if (system(cmd) != 0) {
        fprintf(stderr, "QBE failed\n");
        arena_free(&arena); free(source); return 1;
    }

    /* link with gcc */
    snprintf(cmd, sizeof(cmd),
             "C:/msys64/ucrt64/bin/gcc.exe %s compiler/runtime/runtime.c -o %s.exe -lm",
             asm_path, output);
    if (system(cmd) != 0) {
        fprintf(stderr, "gcc link failed\n");
        arena_free(&arena); free(source); return 1;
    }

    printf("Compiled: %s.exe\n", output);
    arena_free(&arena);
    free(source);
    return 0;
}

static int cmd_compile(int argc, char **argv) {
    const char *input = NULL, *output = NULL;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            output = argv[++i];
        } else if (!input) {
            input = argv[i];
        }
    }
    if (!input) { fprintf(stderr, "usage: jhyy compile <file.jhyy> [-o output]\n"); return 1; }
    if (!output) {
        /* derive output from input name */
        static char out[512];
        snprintf(out, sizeof(out), "%s", input);
        char *dot = strrchr(out, '.');
        if (dot) *dot = '\0';
        output = out;
    }
    return compile(input, output);
}

static int cmd_run(int argc, char **argv) {
    if (argc < 1) { fprintf(stderr, "usage: jhyy run <file.jhyy>\n"); return 1; }
    const char *input = argv[0];
    char tmp_out[512];
    snprintf(tmp_out, sizeof(tmp_out), "compiler/build/bin/_run_tmp");
    int r = compile(input, tmp_out);
    if (r != 0) return r;
    char exe[1024];
    snprintf(exe, sizeof(exe), "%s.exe", tmp_out);
    return system(exe);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("jhyy compiler v0.1.0\n");
        printf("usage: jhyy <command> [args]\n");
        printf("  compile <file.jhyy> [-o output]\n");
        printf("  run     <file.jhyy>\n");
        return 0;
    }

    if (strcmp(argv[1], "compile") == 0)
        return cmd_compile(argc - 2, argv + 2);
    if (strcmp(argv[1], "run") == 0)
        return cmd_run(argc - 2, argv + 2);

    fprintf(stderr, "unknown command: %s\n", argv[1]);
    return 1;
}
