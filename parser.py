from lexer import tokenize


class ParseError(Exception):
    def __init__(self, msg, line):
        self.line = line
        super().__init__(f"Syntax Error on line {line}: {msg}")

class ASTNode:
    def __init__(self, nodeType, children=None):
        self.nodeType = nodeType
        self.children = children or []

    def _tree(self, indent=0):
        pad = "  " * indent
        result = f"{pad}{self.nodeType}\n"
        for child in self.children:
            if isinstance(child, ASTNode):
                result += child._tree(indent + 1)
        return result

    def __repr__(self):
        return self._tree()


class ProgramNode(ASTNode):
    def __init__(self, stmts):
        super().__init__('Program', stmts)


class DeclNode(ASTNode):                 # int x; or int x = expr;
    def __init__(self, name, expr=None):
        children = [expr] if expr is not None else []
        super().__init__(f'Decl({name})', children)
        self.name = name
        self.expr = expr


class AssignNode(ASTNode):               # x = expr;
    def __init__(self, name, expr):
        super().__init__(f'Assign({name})', [expr])
        self.name = name
        self.expr = expr


class IfNode(ASTNode):                   # if (cond) block [else block]
    def __init__(self, cond, thenBlock, elseBlock=None):
        children = [cond, thenBlock]
        if elseBlock is not None:
            children.append(elseBlock)
        super().__init__('If', children)
        self.cond = cond
        self.thenBlock = thenBlock
        self.elseBlock = elseBlock


class WhileNode(ASTNode):                # while (cond) block
    def __init__(self, cond, body):
        super().__init__('While', [cond, body])
        self.cond = cond
        self.body = body


class BlockNode(ASTNode):                # { stmt_list }
    def __init__(self, stmts):
        super().__init__('Block', stmts)


class BinOpNode(ASTNode):                # expr OP|RELOP expr
    def __init__(self, op, left, right):
        super().__init__(f'BinOp({op})', [left, right])
        self.op = op
        self.left = left
        self.right = right


class NumberNode(ASTNode):               # NUMBER literal
    def __init__(self, value):
        super().__init__(f'Number({value})')
        self.value = value


class IDNode(ASTNode):                   # ID reference
    def __init__(self, name):
        super().__init__(f'ID({name})')
        self.name = name


# Parser

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _last_line(self):
        if self.tokens:
            return self.tokens[-1].line
        return 0

    def consume(self):
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, tokenType):
        tok = self.current()
        if tok is None:
            raise ParseError(
                f"expected {tokenType} but reached end of input",
                self._last_line()
            )
        if tok.type != tokenType:
            raise ParseError(
                f"expected {tokenType} but got '{tok.value}'",
                tok.line
            )
        return self.consume()

    def parse(self):
        stmts = self._parse_stmt_list()
        if self.current() is not None:
            tok = self.current()
            raise ParseError(f"unexpected token '{tok.value}'", tok.line)
        return ProgramNode(stmts)

    def _parse_stmt_list(self):
        stmts = []
        while self.current() is not None and self.current().type != 'RBRACE':
            stmts.append(self._parse_stmt())
        return stmts

    def _parse_stmt(self):
        tok = self.current()
        if tok is None:
            raise ParseError("unexpected end of input", self._last_line())

        if tok.type == 'TYPE':           # int x; or int x = expr;
            return self._parse_decl_stmt()
        elif tok.type == 'ID':           # x = expr;
            return self._parse_assign_stmt()
        elif tok.type == 'IF':           # if (cond) block [else block]
            return self._parse_if_stmt()
        elif tok.type == 'WHILE':        # while (cond) block
            return self._parse_while_stmt()
        elif tok.type == 'LBRACE':       # { stmt_list }
            return self._parse_block()
        else:
            raise ParseError(f"unexpected token '{tok.value}'", tok.line)

    def _parse_decl_stmt(self):
        self.expect('TYPE')
        nameTok = self.expect('ID')
        expr = None
        if self.current() is not None and self.current().type == 'ASSIGN':
            self.consume()
            expr = self._parse_expr()
        self.expect('SEMICOLON')
        return DeclNode(nameTok.value, expr)

    def _parse_assign_stmt(self):
        nameTok = self.expect('ID')
        self.expect('ASSIGN')
        expr = self._parse_expr()
        self.expect('SEMICOLON')
        return AssignNode(nameTok.value, expr)

    def _parse_if_stmt(self):
        self.expect('IF')
        self.expect('LPAREN')
        cond = self._parse_expr()
        self.expect('RPAREN')
        thenBlock = self._parse_block()
        elseBlock = None
        if self.current() is not None and self.current().type == 'ELSE':
            self.consume()
            elseBlock = self._parse_block()
        return IfNode(cond, thenBlock, elseBlock)

    def _parse_while_stmt(self):
        self.expect('WHILE')
        self.expect('LPAREN')
        cond = self._parse_expr()
        self.expect('RPAREN')
        body = self._parse_block()
        return WhileNode(cond, body)

    def _parse_block(self):
        self.expect('LBRACE')
        stmts = self._parse_stmt_list()
        self.expect('RBRACE')
        return BlockNode(stmts)

    def _parse_expr(self):
        left = self._parse_term()
        while self.current() is not None and self.current().type in ('OP', 'RELOP'):
            opTok = self.consume()
            right = self._parse_term()
            left = BinOpNode(opTok.value, left, right)
        return left

    def _parse_term(self):
        tok = self.current()
        if tok is None:
            raise ParseError("unexpected end of input in expression", self._last_line())
        if tok.type == 'NUMBER':
            self.consume()
            return NumberNode(tok.value)
        elif tok.type == 'ID':
            self.consume()
            return IDNode(tok.value)
        elif tok.type == 'LPAREN':
            self.consume()
            expr = self._parse_expr()
            self.expect('RPAREN')
            return expr
        else:
            raise ParseError(f"unexpected token '{tok.value}' in expression", tok.line)


if __name__ == "__main__":
    print("--- Testing Valid Input: decl + while ---")

    # test 1: declaration and while loop
    good_test = "int x = 10; while (x > 0) { x = x - 1; }"
    try:
        tokens = tokenize(good_test)
        tree = Parser(tokens).parse()
        print(tree)
    except ParseError as e:
        print(e)

    print("--- Testing Valid Input: if/else ---")

    # test 2: if/else with nested assignment
    if_test = "int y = 5; if (y > 0) { y = y - 1; } else { y = 0; }"
    try:
        tokens = tokenize(if_test)
        tree = Parser(tokens).parse()
        print(tree)
    except ParseError as e:
        print(e)

    print("--- Testing Valid Input: bare declaration ---")

    # test 3: declaration without initializer
    bare_test = "int x; int y; x = 5;"
    try:
        tokens = tokenize(bare_test)
        tree = Parser(tokens).parse()
        print(tree)
    except ParseError as e:
        print(e)

    print("--- Testing Syntax Error: missing semicolon ---")

    # test 3: missing semicolon
    bad_test = "int x = 10"
    try:
        tokens = tokenize(bad_test)
        Parser(tokens).parse()
    except ParseError as e:
        print(f"Caught expected error: {e}")

    print("--- Testing Syntax Error: unexpected token ---")

    # test 4: unexpected token in statement position
    bad_test2 = "int x = 10; } x = 5;"
    try:
        tokens = tokenize(bad_test2)
        Parser(tokens).parse()
    except ParseError as e:
        print(f"Caught expected error: {e}")
