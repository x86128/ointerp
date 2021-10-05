keywords = ["DIV", "MOD", "OR", "OF", "THEN", "DO", "UNTIL", "END", "ELSE",
            "ELSIF", "IF", "WHILE", "REPEAT", "ARRAY", "RECORD", "CONST",
            "TYPE", "VAR", "PROCEDURE", "BEGIN", "MODULE"]


class SourceReader:
    def __init__(self, input_file):
        self.input_file = input_file
        self.c = self.read()

    def read(self):
        self.c = self.input_file.read(1)
        return self.c

    def peek(self):
        return self.c


class Token:
    def __init__(self, typ, val, line=1, pos=1):
        self.typ = typ
        self.val = val
        self.line = line
        self.pos = pos


class TokenStream:
    def __init__(self, source_file):
        self.src = SourceReader(open(source_file, 'r'))
        self.line = 1
        self.pos = 0
        self.errors = []
        self.token = self.read()

    def get_int(self):
        integer = self.src.peek()
        pos = self.pos
        while c := self.src.read():
            if c.isdecimal():
                integer += c
            else:
                break
        return Token('INTEGER', int(integer), self.line, pos)

    def get_ident(self):
        ident = self.src.peek()
        pos = self.pos
        while c := self.src.read():
            if c.isalnum():
                ident += c
            else:
                break
        if ident.upper() in keywords:
            return Token(ident.upper(), ident.upper(), self.line, pos)
        else:
            return Token("IDENT", ident, self.line, pos)

    def skip_comment(self):
        tl = self.line
        while c := self.src.peek():
            self.src.read()
            if c == '(' and self.src.peek() == '*':
                self.skip_comment()
            elif c == '*' and self.src.peek() == ')':
                self.src.read()
                return
            elif len(self.src.peek()) < 1:
                print('Ошибка: Незакрытый комментарий в строке', tl)
                return

    def read(self):
        while c := self.src.peek():
            self.pos += 1
            if c == '\n':
                self.line += 1
                self.pos = 0
                self.src.read()
                continue
            elif c.isspace():
                self.src.read()
                continue
            elif c.isalpha():
                return self.get_ident()
            elif c.isdecimal():
                return self.get_int()
            elif c == ';':
                self.src.read()
                return Token('SEMICOLON', ';', self.line, self.pos)
            elif c == '*':
                self.src.read()
                return Token('TIMES', '*', self.line, self.pos)
            elif c == ',':
                self.src.read()
                return Token('COMMA', ',', self.line, self.pos)
            elif c == ':':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return Token('BECOMES', ':=', self.line, self.pos - 1)
                else:
                    return Token('COLON', ':', self.line, self.pos)
            elif c == '(':
                self.src.read()
                if self.src.peek() == '*':
                    self.skip_comment()
                else:
                    return Token('LPAREN', '(', self.line, self.pos)
            elif c == ')':
                self.src.read()
                return Token('RPAREN', ')', self.line, self.pos)
            elif c == '[':
                self.src.read()
                return Token('LBRAK', '[', self.line, self.pos)
            elif c == ']':
                self.src.read()
                return Token('RBRAK', ']', self.line, self.pos)
            elif c == '>':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return Token('GEQ', '>=', self.line, self.pos - 1)
                else:
                    return Token('GTR', '>', self.line, self.pos)
            elif c == '=':
                self.src.read()
                return Token('EQL', '=', self.line, self.pos)
            elif c == '#':
                self.src.read()
                return Token('NEQ', '#', self.line, self.pos)
            elif c == '<':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return Token('LEQ', '<=', self.line, self.pos - 1)
                else:
                    return Token('LSS', '<', self.line, self.pos)
            elif c == '+':
                self.src.read()
                return Token('PLUS', '+', self.line, self.pos)
            elif c == '-':
                self.src.read()
                return Token('MINUS', '-', self.line, self.pos)
            elif c == '.':
                self.src.read()
                return Token('PERIOD', '.', self.line, self.pos)
            elif c == '~':
                self.src.read()
                return Token('NOT', '~', self.line, self.pos)
            elif c == '&':
                self.src.read()
                return Token('AND', '&', self.line, self.pos)
            else:
                msg = f"Неожиданный символ: {c} в строке {self.line}:{self.pos}"
                raise SyntaxError(msg)
        else:
            t = Token("EOF", "EOF", self.line, self.pos)
        return t

    def get(self):
        self.token = self.read()
        return self.token

    def eat(self, tok_type):
        if self.token.typ == tok_type:
            t = self.token
            self.token = self.read()
            return t
        return None

    def neat(self, *toks):
        for t in toks:
            if self.token.typ == t:
                temp = self.token
                self.token = self.read()
                return temp
        return None

    def peek(self, what):
        if self.token.typ == what:
            return self.token
        return None

    def npeek(self, *toks):
        for t in toks:
            if self.token.typ == t:
                return self.token
        return None

    def error(self, msg):
        self.errors.append(f"Ошибка в строке: {self.line}:{self.pos} {msg}")
        return None
