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



if __name__ == "__main__":
    print("--- Testing Valid Input ---")
    
    # test 1: passable test
    good_test = "int x = 10; while (x > 0) { x = x - 1; }"
    try:
        tokens = tokenize(good_test)
        for t in tokens:
            print(t)
    except RuntimeError as e:
        print(e)

    print("\n--- Testing Lexical Error --- ")
    
    # test 2: invalid character @
    bad_test = "int y = 5 @;"
    try:
        tokenize(bad_test)
    except RuntimeError as e:
        print(f"Caught expected error: {e}")
