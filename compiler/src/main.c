#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "arena.h"
#include "lexer.h"
#include "parser.h"
#include "sema.h"
#include "codegen.h"

/* Convert forward slashes to backslashes for Windows cmd.exe compatibility */
static void path_to_win(char *p) {
    for (; *p; p++) if (*p == '/') *p = '\\';
}

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

static int cmd_build(int argc, char **argv) {
    const char *input = NULL, *output = NULL;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc)
            output = argv[++i];
        else if (!input) input = argv[i];
    }
    if (!input) { fprintf(stderr, "usage: jhyy build <file.jhyy> [-o output]\n"); return 1; }
    if (!output) {
        static char out[512];
        snprintf(out, sizeof(out), "%s", input);
        char *dot = strrchr(out, '.');
        if (dot) *dot = '\0';
        output = out;
    }

    char *source = read_file(input);
    if (!source) return 1;

    Arena arena;
    arena_init(&arena, 16 * 1024 * 1024);

    Lexer lexer;
    lexer_init(&lexer, source, input);
    Parser parser;
    parser_init(&parser, &lexer, &arena);
    Node *ast = parser_parse(&parser);
    if (parser.error_count > 0) {
        fprintf(stderr, "%d parse error(s)\n", parser.error_count);
        arena_free(&arena); free(source); return 1;
    }

    SemaContext sema;
    sema_init(&sema, &arena);
    if (sema_check(&sema, ast) > 0) {
        fprintf(stderr, "%d semantic error(s)\n", sema.error_count);
        arena_free(&arena); free(source); return 1;
    }

    IRBuf ir;
    ir_init(&ir, &arena);
    cg_module(&ir, ast);
    ir_flush_data(&ir);  /* prepend string data definitions */

    char il_path[1024];
    snprintf(il_path, sizeof(il_path), "%s.il", output);
    FILE *ilf = fopen(il_path, "w");
    if (!ilf) { fprintf(stderr, "cannot write '%s'\n", il_path); arena_free(&arena); free(source); return 1; }
    fwrite(ir.buf, 1, ir.len, ilf);
    fclose(ilf);

    printf("Generated: %s.il\n", output);
    arena_free(&arena);
    free(source);
    return 0;
}

/* Resolve imports: parse imported files and merge their decls into the module.
   Only processes first-level imports (no transitive resolution yet). */
static int resolve_imports(Node *module, const char *main_path, Arena *arena) {
    NodeModule *md = node_module_data(module);
    char dir[512];
    snprintf(dir, sizeof(dir), "%s", main_path);
    /* strip filename to get directory */
    char *slash = strrchr(dir, '/');
    if (!slash) slash = strrchr(dir, '\\');
    if (slash) *slash = '\0';  /* dir now contains the parent directory */

    /* Count imports and collect them */
    size_t nimports = 0;
    for (size_t i = 0; i < md->ndeccls; i++) {
        if (md->decls[i]->kind == NODE_IMPORT_DECL) nimports++;
    }
    if (nimports == 0) return 0;

    /* Build new decls array: imported decls + original non-import decls */
    size_t new_count = 0;
    size_t new_cap = md->ndeccls + nimports * 8; /* estimate */
    Node **new_decls = arena_alloc(arena, new_cap * sizeof(Node *));

    int errors = 0;

    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind != NODE_IMPORT_DECL) {
            new_decls[new_count++] = decl;
            continue;
        }

        /* Resolve this import */
        NodeImportDecl *id = node_import_decl_data(decl);
        const char *mod_name = id->sym->name;
        char mod_path[512];
        snprintf(mod_path, sizeof(mod_path), "%s/%s.jhyy", dir, mod_name);

        char *mod_source = read_file(mod_path);
        if (!mod_source) {
            fprintf(stderr, "%s:%d:%d: error: cannot open import '%s'\n",
                    decl->loc.filename, decl->loc.line, decl->loc.col, mod_path);
            errors++;
            continue;
        }

        /* Parse the imported module into the SAME arena */
        Arena temp_arena;
        arena_init(&temp_arena, 1024 * 1024);
        Lexer mod_lexer;
        lexer_init(&mod_lexer, mod_source, mod_path);
        Parser mod_parser;
        parser_init(&mod_parser, &mod_lexer, arena);
        Node *mod_ast = parser_parse(&mod_parser);

        if (mod_parser.error_count > 0) {
            fprintf(stderr, "%d parse error(s) in import '%s'\n",
                    mod_parser.error_count, mod_path);
            errors++;
            arena_free(&temp_arena);
            free(mod_source);
            continue;
        }

        /* Extract declarations from the imported module */
        NodeModule *imd = node_module_data(mod_ast);
        for (size_t j = 0; j < imd->ndeccls; j++) {
            Node *idecl = imd->decls[j];
            if (idecl->kind == NODE_IMPORT_DECL) continue; /* skip nested imports for now */
            if (new_count >= new_cap) {
                new_cap *= 2;
                Node **bigger = arena_alloc(arena, new_cap * sizeof(Node *));
                memcpy(bigger, new_decls, new_count * sizeof(Node *));
                new_decls = bigger;
            }
            new_decls[new_count++] = idecl;
        }

        arena_free(&temp_arena);
        free(mod_source);
    }

    if (errors > 0) return errors;

    /* Update module with merged declarations */
    md->decls = new_decls;
    md->ndeccls = new_count;
    return 0;
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

    /* resolve imports */
    if (resolve_imports(ast, input, &arena) > 0) {
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
    ir_flush_data(&ir);

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
             "C:/msys64/ucrt64/bin/gcc.exe %s C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/runtime/runtime.c -o %s.exe -lm",
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
    /* Derive temp output from input: "path/foo.jhyy" → "path/foo_run" */
    char tmp_out[512];
    const char *dot = strrchr(input, '.');
    const char *slash1 = strrchr(input, '/');
    const char *slash2 = strrchr(input, '\\');
    const char *slash = slash1 > slash2 ? slash1 : slash2;
    size_t baselen;
    if (dot && dot > slash)
        baselen = (size_t)(dot - input);  /* strip extension */
    else
        baselen = strlen(input);
    snprintf(tmp_out, sizeof(tmp_out), "%.*s_run", (int)baselen, input);
    int r = compile(input, tmp_out);
    if (r != 0) return r;
    char exe[1024];
    snprintf(exe, sizeof(exe), "%s.exe", tmp_out);
    path_to_win(exe);  /* fix for Windows cmd.exe */
    return system(exe);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("jhyy compiler v0.2.0\n");
        printf("usage: jhyy <command> [args]\n");
        printf("  compile <file.jhyy> [-o output]   compile to executable\n");
        printf("  build   <file.jhyy> [-o output]   compile to .il only\n");
        printf("  run     <file.jhyy>               compile and run\n");
        return 0;
    }

    if (strcmp(argv[1], "compile") == 0)
        return cmd_compile(argc - 2, argv + 2);
    if (strcmp(argv[1], "build") == 0)
        return cmd_build(argc - 2, argv + 2);
    if (strcmp(argv[1], "run") == 0)
        return cmd_run(argc - 2, argv + 2);

    fprintf(stderr, "unknown command: %s\n", argv[1]);
    return 1;
}
