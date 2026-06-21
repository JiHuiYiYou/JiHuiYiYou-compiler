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

/* Forward declarations */
static int resolve_imports(Node *module, const char *main_path, Arena *arena,
                           char extra_paths[16][512], char extra_names[16][256],
                           int nextra);

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

    /* resolve imports */
    if (resolve_imports(ast, input, &arena, NULL, NULL, 0) > 0) {
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

/* Resolve a single import file and return its non-import decls.
   Recursively resolves transitive imports.
   Uses two separate arrays: in_progress (for cycle detection)
   and completed (to skip modules already fully processed).
   extra_paths: paths to additional CLI-provided files; used as fallback. */
static int resolve_one_import(const char *mod_dir, const char *mod_name,
                              SourceLoc loc, Arena *arena,
                              Node ***out_decls, size_t *out_count, size_t *out_cap,
                              char in_progress[64][512], size_t *nin_progress,
                              char completed[64][512], size_t *ncompleted,
                              char extra_paths[16][512], char extra_names[16][256],
                              int nextra) {
    char mod_path[512];
    /* First check if mod_name matches a CLI-provided file (extra_paths) */
    int found_extra = 0;
    for (int e = 0; e < nextra; e++) {
        if (strcmp(extra_names[e], mod_name) == 0) {
            snprintf(mod_path, sizeof(mod_path), "%s", extra_paths[e]);
            found_extra = 1;
            break;
        }
    }
    if (!found_extra)
        snprintf(mod_path, sizeof(mod_path), "%s/%s.jhyy", mod_dir, mod_name);

    /* Already fully processed? Skip. */
    for (size_t k = 0; k < *ncompleted; k++) {
        if (strcmp(completed[k], mod_path) == 0) return 0;
    }
    /* Currently being processed? Cycle. */
    for (size_t k = 0; k < *nin_progress; k++) {
        if (strcmp(in_progress[k], mod_path) == 0) {
            fprintf(stderr, "%s:%d:%d: error: circular import '%s'\n",
                    loc.filename, loc.line, loc.col, mod_path);
            return 1;
        }
    }

    /* Read and parse the imported module */
    char *mod_source = read_file(mod_path);
    if (!mod_source) {
        fprintf(stderr, "%s:%d:%d: error: cannot open import '%s'\n",
                loc.filename, loc.line, loc.col, mod_path);
        return 1;
    }

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
        arena_free(&temp_arena);
        free(mod_source);
        return 1;
    }

    /* Push onto in_progress */
    if (*nin_progress < 64) {
        snprintf(in_progress[(*nin_progress)++], 512, "%s", mod_path);
    }

    /* Extract dir for resolving nested imports (handles mixed separators) */
    char nested_dir[512];
    snprintf(nested_dir, sizeof(nested_dir), "%s", mod_path);
    char *mslash = strrchr(nested_dir, '/');
    char *mbslash = strrchr(nested_dir, '\\');
    char *last = mslash > mbslash ? mslash : mbslash;
    if (last) *last = '\0';

    int errors = 0;
    NodeModule *imd = node_module_data(mod_ast);
    for (size_t j = 0; j < imd->ndeccls; j++) {
        Node *idecl = imd->decls[j];
        if (idecl->kind == NODE_IMPORT_DECL) {
            /* Recursively resolve transitive import */
            NodeImportDecl *iid = node_import_decl_data(idecl);
            errors += resolve_one_import(nested_dir, iid->sym->name, idecl->loc,
                                         arena, out_decls, out_count, out_cap,
                                         in_progress, nin_progress,
                                         completed, ncompleted,
                                         extra_paths, extra_names, nextra);
        } else {
            /* Tag this decl's sym with its owning module for namespacing */
            Sym *owner_sym = NULL;
            switch (idecl->kind) {
            case NODE_FUNC_DECL:
                owner_sym = node_func_decl_data(idecl)->sym;
                break;
            case NODE_TYPE_DECL:
                owner_sym = node_type_decl_data(idecl)->sym;
                break;
            case NODE_EXTERN_DECL:
                owner_sym = node_extern_decl_data(idecl)->sym;
                break;
            default:
                break;
            }
            if (owner_sym) {
                owner_sym->module = mod_name;
            }

            /* Add non-import decl to merged list */
            if (*out_count >= *out_cap) {
                *out_cap *= 2;
                Node **bigger = arena_alloc(arena, *out_cap * sizeof(Node *));
                memcpy(bigger, *out_decls, *out_count * sizeof(Node *));
                *out_decls = bigger;
            }
            (*out_decls)[(*out_count)++] = idecl;
        }
    }

    /* Pop from in_progress, push onto completed */
    for (size_t k = 0; k < *nin_progress; k++) {
        if (strcmp(in_progress[k], mod_path) == 0) {
            /* shift remaining down (preserve order) */
            char tmp[512];
            for (size_t m = k; m < *nin_progress - 1; m++) {
                snprintf(tmp, sizeof(tmp), "%s", in_progress[m + 1]);
                snprintf(in_progress[m], 512, "%s", tmp);
            }
            (*nin_progress)--;
            break;
        }
    }
    if (*ncompleted < 64) {
        snprintf(completed[(*ncompleted)++], 512, "%s", mod_path);
    }

    arena_free(&temp_arena);
    free(mod_source);
    return errors;
}

/* Resolve imports: parse imported files and merge their decls into the module.
   Handles transitive imports (A imports B, B imports C) and detects cycles.
   Falls back to cwd if main_path's directory doesn't contain the import.
   extra_paths: paths to additional input files (CLI inputs) — used to
   satisfy imports when main's directory doesn't contain the file. */
static int resolve_imports(Node *module, const char *main_path, Arena *arena,
                           char extra_paths[16][512], char extra_names[16][256],
                           int nextra) {
    NodeModule *md = node_module_data(module);
    char dir[512];
    /* Extract directory of main_path. Find the LAST separator of either kind,
       so paths with mixed separators (e.g. "tests\\foo" or "tests/foo") both
       work correctly. */
    snprintf(dir, sizeof(dir), "%s", main_path);
    char *slash = strrchr(dir, '/');
    char *bslash = strrchr(dir, '\\');
    char *last_sep = slash > bslash ? slash : bslash;
    if (last_sep) {
        *last_sep = '\0';
    } else {
        /* No directory in path — assume cwd */
        snprintf(dir, sizeof(dir), ".");
    }

    /* Count initial imports */
    size_t nimports = 0;
    for (size_t i = 0; i < md->ndeccls; i++) {
        if (md->decls[i]->kind == NODE_IMPORT_DECL) nimports++;
    }
    if (nimports == 0) return 0;

    /* Main module's non-import decls */
    Node **main_decls = arena_alloc(arena, md->ndeccls * sizeof(Node *));
    size_t nmain = 0;
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind != NODE_IMPORT_DECL) {
            main_decls[nmain++] = decl;
        }
    }

    /* Build new decls: imported decls go FIRST so sema Pass 3 sets their
       types before checking main function body. */
    size_t new_count = 0;
    size_t new_cap = md->ndeccls + nimports * 8;
    Node **new_decls = arena_alloc(arena, new_cap * sizeof(Node *));

    /* Allocate in_progress + completed arrays on heap to avoid huge stack frame */
    char (*in_progress)[512] = calloc(64, 512);
    char (*completed)[512] = calloc(64, 512);
    size_t nin_progress = 0;
    size_t ncompleted = 0;

    int errors = 0;
    for (size_t i = 0; i < md->ndeccls; i++) {
        Node *decl = md->decls[i];
        if (decl->kind != NODE_IMPORT_DECL) continue;
        NodeImportDecl *id = node_import_decl_data(decl);
        errors += resolve_one_import(dir, id->sym->name, decl->loc, arena,
                                     &new_decls, &new_count, &new_cap,
                                     in_progress, &nin_progress,
                                     completed, &ncompleted,
                                     extra_paths, extra_names, nextra);
    }

    /* Also resolve CLI-provided files as if they were imported by main.
       Their decls were NOT pre-merged; this is how they get included. */
    for (int e = 0; e < nextra; e++) {
        SourceLoc loc = {1, 1, main_path};
        errors += resolve_one_import(".", extra_names[e], loc, arena,
                                     &new_decls, &new_count, &new_cap,
                                     in_progress, &nin_progress,
                                     completed, &ncompleted,
                                     extra_paths, extra_names, nextra);
    }

    if (errors > 0) { free(in_progress); free(completed); return errors; }

    /* Append main module's non-import decls after imported decls */
    for (size_t i = 0; i < nmain; i++) {
        if (new_count >= new_cap) {
            new_cap *= 2;
            Node **bigger = arena_alloc(arena, new_cap * sizeof(Node *));
            memcpy(bigger, new_decls, new_count * sizeof(Node *));
            new_decls = bigger;
        }
        new_decls[new_count++] = main_decls[i];
    }

    md->decls = new_decls;
    md->ndeccls = new_count;
    free(in_progress);
    free(completed);
    return 0;
}

static int compile(const char **inputs, int ninputs, const char *output) {
    if (ninputs < 1) { fprintf(stderr, "no input files\n"); return 1; }

    Arena arena;
    arena_init(&arena, 16 * 1024 * 1024); /* 16 MB */

    /* Parse first file as main module */
    char *main_source = read_file(inputs[0]);
    if (!main_source) { arena_free(&arena); return 1; }

    Lexer lexer;
    lexer_init(&lexer, main_source, inputs[0]);
    Parser parser;
    parser_init(&parser, &lexer, &arena);
    Node *ast = parser_parse(&parser);
    if (parser.error_count > 0) {
        fprintf(stderr, "%d parse error(s)\n", parser.error_count);
        arena_free(&arena); free(main_source); return 1;
    }

    NodeModule *md = node_module_data(ast);
    (void)md;

    /* Parse additional input files. Their decls are NOT pre-merged into main.
   Instead, they're treated as if they were imported by main (their decls
   go through the same import-resolution code path). This avoids the
   "duplicate decl with same mangled name" issue. */
    char extra_paths[16][512];
    char extra_names[16][256];
    int nextra = 0;
    for (int fi = 1; fi < ninputs; fi++) {
        /* Derive module name from basename (without extension).
           Find the LAST separator of either kind so mixed paths work. */
        const char *s1 = strrchr(inputs[fi], '/');
        const char *s2 = strrchr(inputs[fi], '\\');
        const char *base = s1 > s2 ? s1 : s2;
        base = base ? base + 1 : inputs[fi];
        snprintf(extra_names[nextra], 256, "%s", base);
        char *dot = strrchr(extra_names[nextra], '.');
        if (dot) *dot = '\0';
        /* Derive directory (same logic) */
        char dir_buf[512];
        snprintf(dir_buf, sizeof(dir_buf), "%s", inputs[fi]);
        char *slash = strrchr(dir_buf, '/');
        char *bslash = strrchr(dir_buf, '\\');
        char *last = slash > bslash ? slash : bslash;
        if (last) *last = '\0';
        else snprintf(dir_buf, sizeof(dir_buf), ".");
        /* Build path with explicit size check to silence -Wformat-truncation */
        size_t needed = strlen(dir_buf) + 1 + strlen(extra_names[nextra]) + 6;
        if (needed >= 512) {
            /* path too long, just use module name as fallback */
            snprintf(extra_paths[nextra], 512, "%s.jhyy", extra_names[nextra]);
        } else {
            /* Use GCC suppression pragma for the format string */
            #pragma GCC diagnostic push
            #pragma GCC diagnostic ignored "-Wformat-truncation"
            snprintf(extra_paths[nextra], 512, "%s/%s.jhyy", dir_buf, extra_names[nextra]);
            #pragma GCC diagnostic pop
        }
        nextra++;
    }

    /* resolve imports (uses main file's directory as base) */
    if (resolve_imports(ast, inputs[0], &arena, extra_paths, extra_names, nextra) > 0) {
        arena_free(&arena); free(main_source); return 1;
    }

    /* semantic analysis */
    SemaContext sema;
    sema_init(&sema, &arena);
    int errs = sema_check(&sema, ast);
    if (errs > 0) {
        fprintf(stderr, "%d semantic error(s)\n", errs);
        arena_free(&arena); free(main_source); return 1;
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
        arena_free(&arena); free(main_source); return 1;
    }
    fwrite(ir.buf, 1, ir.len, ilf);
    fclose(ilf);

    /* invoke QBE */
    char asm_path[1024];
    snprintf(asm_path, sizeof(asm_path), "%s.s", output);
    path_to_win(il_path);
    path_to_win(asm_path);
    char cmd[4096];
    snprintf(cmd, sizeof(cmd),
             "C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/qbe/qbe.exe -t amd64_win -o %s %s",
             asm_path, il_path);
    if (system(cmd) != 0) {
        fprintf(stderr, "QBE failed\n");
        arena_free(&arena); free(main_source); return 1;
    }

    /* link with gcc */
    char exe_path[1024];
    snprintf(exe_path, sizeof(exe_path), "%s.exe", output);
    path_to_win(exe_path);
    snprintf(cmd, sizeof(cmd),
             "C:/msys64/ucrt64/bin/gcc.exe %s C:/Users/liuzhen/Desktop/coding/JiHuiYiYou/compiler/runtime/runtime.c -o %s -lm",
             asm_path, exe_path);
    if (system(cmd) != 0) {
        fprintf(stderr, "gcc link failed\n");
        arena_free(&arena); free(main_source); return 1;
    }

    printf("Compiled: %s.exe\n", output);
    arena_free(&arena);
    free(main_source);
    return 0;
}

static int cmd_compile(int argc, char **argv) {
    const char *inputs[128];
    int ninputs = 0;
    const char *output = NULL;
    for (int i = 0; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            output = argv[++i];
        } else {
            inputs[ninputs++] = argv[i];
        }
    }
    if (ninputs < 1) { fprintf(stderr, "usage: jhyy compile <file.jhyy> ... [-o output]\n"); return 1; }
    if (!output) {
        /* derive output from first input name */
        static char out[512];
        snprintf(out, sizeof(out), "%s", inputs[0]);
        char *dot = strrchr(out, '.');
        if (dot) *dot = '\0';
        output = out;
    }
    return compile(inputs, ninputs, output);
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
    int r = compile(&input, 1, tmp_out);
    if (r != 0) return r;
    char exe[1024];
    snprintf(exe, sizeof(exe), "%s.exe", tmp_out);
    path_to_win(exe);  /* fix for Windows cmd.exe */
    return system(exe);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("jhyy compiler v0.4.0\n");
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
