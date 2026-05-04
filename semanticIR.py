import sys
import os

# Make sure lexer.py and parser.py are importable from the same folder
sys.path.insert(0, os.path.dirname(__file__))

from lexer   import tokenize
from parser  import (
    Parser, ParseError,
    ProgramNode, DeclNode, AssignNode,
    IfNode, WhileNode, BlockNode,
    BinOpNode, NumberNode, IDNode,
)

# symbol table/scope

scope_stack = [{}]          # each dict is one scope; index 0 = global scope

def enter_scope():
    # Push a fresh empty dict onto the stack
    scope_stack.append({})

def exit_scope():
    # Pop the innermost scope when we leave a block
    if len(scope_stack) > 1:
        scope_stack.pop()

def declare_var(name, var_type):
    # Declare a variable in the *current* (innermost) scope.
    # Returns an error string on duplicate, None on success.
    current = scope_stack[-1]
    if name in current:
        return f"Duplicate declaration of '{name}' in current scope"
    current[name] = var_type
    return None

def lookup_var(name):
    # Walk the scope stack from innermost to outermost.
    # Returns the type string, or None if not found.
    for scope in reversed(scope_stack):
        if name in scope:
            return scope[name]
    return None

def dump_scope_stack():
    # Print every active scope for debugging / output
    print("  Scope stack (innermost last):")
    for i, scope in enumerate(scope_stack):
        label = "global" if i == 0 else f"level {i}"
        if scope:
            for name, t in scope.items():
                print(f"    [{label}]  {name} : {t}")
        else:
            print(f"    [{label}]  (empty)")


# semantic analysis
# Check for:
#   - undeclared variable usage
#   - duplicate declarations in the same scope
#   - basic type mismatches (int op int expected; float literals flagged)

semantic_errors = []        # list of error strings collected during the walk

_ARITH_OPS = {'+', '-', '*', '/'}
_REL_OPS   = {'<', '>', '==', '!=', '<=', '>='}

def sem_visit(node):
    # Dispatch to the right handler; returns the node's resolved type string.
    if node is None:
        return "void"
    name = type(node).__name__
    handlers = {
        "ProgramNode"  : sem_Program,
        "BlockNode"    : sem_Block,
        "DeclNode"     : sem_Decl,
        "AssignNode"   : sem_Assign,
        "IfNode"       : sem_If,
        "WhileNode"    : sem_While,
        "BinOpNode"    : sem_BinOp,
        "NumberNode"   : sem_Number,
        "IDNode"       : sem_ID,
    }
    return handlers.get(name, lambda n: "unknown")(node)

def sem_Program(node):
    for stmt in node.children:
        sem_visit(stmt)
    return "void"

def sem_Block(node):
    enter_scope()
    for stmt in node.children:
        sem_visit(stmt)
    exit_scope()
    return "void"

def sem_Decl(node):
    # The only keyword type in the lexer is 'int'
    var_type = "int"
    err = declare_var(node.name, var_type)
    if err:
        semantic_errors.append(err)
    # Check optional initialiser
    if node.expr is not None:
        rhs_type = sem_visit(node.expr)
        if rhs_type not in ("unknown", "void") and rhs_type != var_type:
            semantic_errors.append(
                f"Type mismatch in declaration of '{node.name}': "
                f"expected {var_type}, got {rhs_type}"
            )
    return "void"

def sem_Assign(node):
    sym_type = lookup_var(node.name)
    if sym_type is None:
        semantic_errors.append(f"Undeclared variable '{node.name}'")
        sem_visit(node.expr)    # still check RHS for further errors
        return "void"
    rhs_type = sem_visit(node.expr)
    if rhs_type not in ("unknown", "void") and rhs_type != sym_type:
        semantic_errors.append(
            f"Type mismatch assigning to '{node.name}': "
            f"expected {sym_type}, got {rhs_type}"
        )
    return "void"

def sem_If(node):
    sem_visit(node.cond)
    # thenBlock is a BlockNode — it opens its own scope automatically
    sem_visit(node.thenBlock)
    if node.elseBlock is not None:
        sem_visit(node.elseBlock)
    return "void"

def sem_While(node):
    sem_visit(node.cond)
    sem_visit(node.body)        # body is a BlockNode
    return "void"

def sem_BinOp(node):
    left_type  = sem_visit(node.left)
    right_type = sem_visit(node.right)
    if "unknown" in (left_type, right_type):
        return "unknown"
    if node.op in _ARITH_OPS:
        if left_type != right_type:
            semantic_errors.append(
                f"Type mismatch in '{node.op}': "
                f"cannot combine '{left_type}' and '{right_type}'"
            )
            return "unknown"
        return left_type            # int op int -> int
    if node.op in _REL_OPS:
        if left_type != right_type:
            semantic_errors.append(
                f"Type mismatch in '{node.op}': "
                f"cannot compare '{left_type}' and '{right_type}'"
            )
        return "bool"               # relational result is always bool
    return "unknown"

def sem_Number(node):
    # NumberNode.value is a raw string token from the lexer
    return "float" if "." in str(node.value) else "int"

def sem_ID(node):
    sym_type = lookup_var(node.name)
    if sym_type is None:
        semantic_errors.append(f"Undeclared variable '{node.name}'")
        return "unknown"
    return sym_type

# IR generation from AST
# Walk the same AST after semantic analysis and emit TAC.

temp_count  = 0         # global counter for temporaries  (t1, t2, …)
label_count = 0         # global counter for labels       (L1, L2, …)
tac_instrs  = []        # list of plain strings — the final TAC output

def new_temp():
    global temp_count
    temp_count += 1
    return f"t{temp_count}"

def new_label():
    global label_count
    label_count += 1
    return f"L{label_count}"

def emit(line):
    # Append one TAC instruction string to the output list
    tac_instrs.append(line)

def ir_visit(node):
    # Dispatch to the right IR generator; returns the temp/name holding the result.
    if node is None:
        return None
    name = type(node).__name__
    handlers = {
        "ProgramNode"  : ir_Program,
        "BlockNode"    : ir_Block,
        "DeclNode"     : ir_Decl,
        "AssignNode"   : ir_Assign,
        "IfNode"       : ir_If,
        "WhileNode"    : ir_While,
        "BinOpNode"    : ir_BinOp,
        "NumberNode"   : ir_Number,
        "IDNode"       : ir_ID,
    }
    return handlers.get(name, lambda n: None)(node)

def ir_Program(node):
    for stmt in node.children:
        ir_visit(stmt)

def ir_Block(node):
    for stmt in node.children:
        ir_visit(stmt)

def ir_Decl(node):
    # int x = 5;   → x = 5
    if node.expr is not None:
        rhs = ir_visit(node.expr)
        emit(f"    {node.name} = {rhs}")

def ir_Assign(node):
    # x = expr;   → tN = <expr> ; x = tN
    rhs = ir_visit(node.expr)
    emit(f"    {node.name} = {rhs}")

def ir_If(node):
    # if (cond) thenBlock [else elseBlock]
    # ─────────────────────────────────────
    #     if left RELOP right goto L_true
    #     goto L_false
    # L_true:
    #     <then stmts>
    #     goto L_end
    # L_false:
    #     <else stmts>   (if present)
    # L_end:
    l_true  = new_label()
    l_false = new_label()
    l_end   = new_label()

    emit_condition(node.cond, l_true, l_false)

    emit(f"{l_true}:")
    ir_visit(node.thenBlock)
    emit(f"    goto {l_end}")

    emit(f"{l_false}:")
    if node.elseBlock is not None:
        ir_visit(node.elseBlock)

    emit(f"{l_end}:")

def ir_While(node):
    # while (cond) body
    # ─────────────────────────────────────
    # L_start:
    #     if left RELOP right goto L_body
    #     goto L_end
    # L_body:
    #     <body stmts>
    #     goto L_start
    # L_end:
    l_start = new_label()
    l_body  = new_label()
    l_end   = new_label()

    emit(f"{l_start}:")
    emit_condition(node.cond, l_body, l_end)

    emit(f"{l_body}:")
    ir_visit(node.body)
    emit(f"    goto {l_start}")

    emit(f"{l_end}:")

def ir_BinOp(node):
    # Emit arithmetic into a fresh temp; return the temp name.
    left  = ir_visit(node.left)
    right = ir_visit(node.right)
    t = new_temp()
    emit(f"    {t} = {left} {node.op} {right}")
    return t

def ir_Number(node):
    # Return the literal value string directly (no temp needed)
    return str(node.value)

def ir_ID(node):
    # Return the variable name directly
    return node.name

def emit_condition(cond_node, l_true, l_false):
    # Emit the shortest TAC for a boolean condition.
    # For a relational BinOp we can emit a direct conditional jump.
    # For anything else we evaluate into a temp and branch on != 0.
    if isinstance(cond_node, BinOpNode) and cond_node.op in _REL_OPS:
        left  = ir_visit(cond_node.left)
        right = ir_visit(cond_node.right)
        emit(f"    if {left} {cond_node.op} {right} goto {l_true}")
    else:
        tmp = ir_visit(cond_node)
        emit(f"    if {tmp} != 0 goto {l_true}")
    emit(f"    goto {l_false}")