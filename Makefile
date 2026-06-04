# jhyy project — top-level Makefile
CC       = /c/msys64/ucrt64/bin/gcc.exe
CFLAGS   = -std=c11 -Wall -Wextra -g
QBE      = qbe/qbe.exe
QBEFLAGS = -t amd64_win

# Directories
COMPILER_DIR = compiler
SRC_DIR      = $(COMPILER_DIR)/src
RUNTIME_DIR  = $(COMPILER_DIR)/runtime
BUILD_DIR    = $(COMPILER_DIR)/build
OBJ_DIR      = $(BUILD_DIR)/obj
BIN_DIR      = $(BUILD_DIR)/bin

# Source files (Phase 1 — added as modules are implemented)
SRCS = $(SRC_DIR)/main.c \
       $(SRC_DIR)/arena.c \
       $(SRC_DIR)/diagnostics.c \
       $(SRC_DIR)/lexer.c \
       $(SRC_DIR)/parser.c \
       $(SRC_DIR)/ast.c \
       $(SRC_DIR)/types.c \
       $(SRC_DIR)/symtab.c \
       $(SRC_DIR)/sema.c \
       $(SRC_DIR)/ir.c \
       $(SRC_DIR)/codegen.c \
       $(SRC_DIR)/util.c

OBJS = $(patsubst $(SRC_DIR)/%.c, $(OBJ_DIR)/%.o, $(SRCS))
RUNTIME_OBJ = $(OBJ_DIR)/runtime.o

.PHONY: all clean test

all: $(BIN_DIR)/jhyy

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(OBJ_DIR)/runtime.o: $(RUNTIME_DIR)/runtime.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(BIN_DIR)/jhyy: $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CC) $(CFLAGS) $^ -o $@

test:
	@echo "Running tests..."
	@echo "TODO: test runner"

clean:
	rm -rf $(BUILD_DIR)
