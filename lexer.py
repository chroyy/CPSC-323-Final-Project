import re

class Token:
    def __init__(self, type, value, line):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"<{self.type}, {self.value}>"

token_types = [
    ('TYPE',      r'\bint\b'),               # int
    ('IF',        r'\bif\b'),                # if
    ('ELSE',      r'\belse\b'),              # else
    ('WHILE',     r'\bwhile\b'),             # while
    ('NUMBER',    r'\d+'),                   # 123
    ('ASSIGN',    r'='),                     # =
    ('ID',        r'[a-zA-Z_][a-zA-Z0-9_]*'),# variable names
    ('OP',        r'[+\-*/]'),               # + - * /
    ('RELOP',     r'==|<=|>=|<|>'),          # == < >
    ('LBRACE',    r'\{'),                    # {
    ('RBRACE',    r'\}'),                    # }
    ('LPAREN',    r'\('),                    # (
    ('RPAREN',    r'\)'),                    # )
    ('SEMICOLON', r';'),                     # ;
    ('NEWLINE',   r'\n'),                    # new line
    ('SKIP',      r'[ \t]+'),                # spaces/tabs
    ('MISMATCH',  r'.'),                     # anything else/error
]

token_matcher = '|'.join('(?P<%s>%s)' % pair for pair in token_types)

def tokenize(rawInput):
    tokens = []
    lineNum = 1
    for match in re.finditer(token_matcher, rawInput):
        tokenType = match.lastgroup
        val = match.group()
        
        if tokenType == 'NEWLINE':
            lineNum += 1
        elif tokenType == 'SKIP':
            continue
        elif tokenType == 'MISMATCH':
            raise RuntimeError(f'Lexical Error: Unexpected character "{val}" on line {lineNum}')
        else:
            tokens.append(Token(tokenType, val, lineNum))
    return tokens