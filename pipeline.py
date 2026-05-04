from lexer   import tokenize
from parser  import (
    Parser, ParseError,
    ProgramNode, DeclNode, AssignNode,
    IfNode, WhileNode, BlockNode,
    BinOpNode, NumberNode, IDNode,
)

from semanticIR import *

# reset button — reset all global state between test runs

def reset():
    global temp_count, label_count, semantic_errors, tac_instrs, scope_stack
    temp_count      = 0
    label_count     = 0
    semantic_errors = []
    tac_instrs      = []
    scope_stack     = [{}]


# ------------------------------------------------------------
# FULL PIPELINE — lex -> parse -> semantic -> IR
# ------------------------------------------------------------

def run_pipeline(source, label):
    reset()

    print(f"\n{'='*55}")
    print(f"  {label}")
    print(f"{'='*55}")

    # lexer
    print("\n===== Token Stream =====")
    try:
        tokens = tokenize(source)
    except RuntimeError as e:
        print(f"[LEXER ERROR] {e}")
        return
    for tok in tokens:
        print(" ", tok)

    # parser
    print("\n===== Abstract Syntax Tree =====")
    try:
        ast = Parser(tokens).parse()
    except ParseError as e:
        print(f"[PARSE ERROR] {e}")
        return
    print(ast)

    # semantic analysis
    print("===== Semantic Analysis =====")
    sem_visit(ast)
    if semantic_errors:
        for err in semantic_errors:
            print(f"  [SEMANTIC ERROR] {err}")
    else:
        print("  No semantic errors detected.")

    # symbols used
    print("\n===== Symbol Table =====")
    dump_scope_stack()

    # Skip IR if there were semantic errors
    if semantic_errors:
        return

    # IR
    ir_visit(ast)
    print("\n===== Three-Address Code =====")
    if tac_instrs:
        for line in tac_instrs:
            print(line)
    else:
        print("  (no instructions)")

    print("\n===== Explanation =====")
    print("  Semantic analysis verified all variables are declared and types match.")
    print("  TAC flattens the AST into simple assignments and conditional jumps.")

# test functions and expected results

if __name__ == "__main__":

    # Valid programs

    run_pipeline(
        "int x; int y; x = 5; y = x + 3;",
        "Test 1 - Basic Declaration and Assignment"
    )

    run_pipeline(
        "int a = 10; int b = 20; a = a + b;",
        "Test 2 - Declaration with Initialiser"
    )

    run_pipeline(
        "int x = 10; int y = 20; int result; "
        "if (x < y) { result = y; } else { result = x; }",
        "Test 3 - If / Else Statement"
    )

    run_pipeline(
        "int x = 10; while (x > 0) { x = x - 1; }",
        "Test 4 - While Loop"
    )

    run_pipeline(
        "int x = 1; { int y; y = x + 2; }",
        "Test 5 - Nested Block Scope"
    )

    run_pipeline(
        "int x = 3; int y = 4; int z; z = x + y * 2;",
        "Test 6 - Complex Arithmetic Expression"
    )

    # Error cases

    run_pipeline(
        "int x; x = z + 1;",
        "Test 7 - ERROR: Undeclared Variable"
    )

    run_pipeline(
        "int x; int x;",
        "Test 8 - ERROR: Duplicate Declaration"
    )

    run_pipeline(
        "{ int inner; inner = 5; } inner = 10;",
        "Test 9 - ERROR: Variable Used Outside Its Scope"
    )

    run_pipeline(input("Enter your own test program (or press Enter to skip): "), "Custom Test")