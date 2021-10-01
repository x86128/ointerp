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


class TokenStream:
    def __init__(self, source_file):
        self.src = SourceReader(open(source_file, 'r'))

        self.line = 1
        self.pos = 0
        self.errors = []

        self.token = self.read()

    def get_int(self):
        integer = self.src.peek()
        while c := self.src.read():
            if c.isdecimal():
                integer += c
            else:
                break
        return 'INTEGER', int(integer)

    def get_ident(self):
        ident = self.src.peek()
        while c := self.src.read():
            if c.isalnum():
                ident += c
            else:
                break
        if ident.upper() in keywords:
            return ident.upper(), ident
        else:
            return "IDENT", ident

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
        t = ("NULL", "NULL")
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
                return 'SEMICOLON', ';', self.line, self.pos
            elif c == '*':
                self.src.read()
                return 'TIMES', '*', self.line, self.pos
            elif c == ',':
                self.src.read()
                return 'COMMA', ',', self.line, self.pos
            elif c == ':':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return 'BECOMES', ':=', self.line, self.pos - 1
                else:
                    return 'COLON', ':', self.line, self.pos
            elif c == '(':
                self.src.read()
                if self.src.peek() == '*':
                    self.skip_comment()
                else:
                    return 'LPAREN', '(', self.line, self.pos
            elif c == ')':
                self.src.read()
                return 'RPAREN', ')', self.line, self.pos
            elif c == '[':
                self.src.read()
                return 'LBRAK', '[', self.line, self.pos
            elif c == ']':
                self.src.read()
                return 'RBRAK', ']', self.line, self.pos
            elif c == '>':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return 'GEQ', '>=', self.line, self.pos - 1
                else:
                    return 'GTR', '>', self.line, self.pos
            elif c == '=':
                self.src.read()
                return 'EQL', '=', self.line, self.pos
            elif c == '#':
                self.src.read()
                return 'NEQ', '#', self.line, self.pos
            elif c == '<':
                self.src.read()
                if self.src.peek() == '=':
                    self.src.read()
                    return 'LEQ', '<=', self.line, self.pos - 1
                else:
                    return 'LSS', '<', self.line, self.pos
            elif c == '+':
                self.src.read()
                return 'PLUS', '+', self.line, self.pos
            elif c == '-':
                self.src.read()
                return 'MINUS', '-', self.line, self.pos
            elif c == '.':
                self.src.read()
                return 'PERIOD', '.', self.line, self.pos
            elif c == '~':
                self.src.read()
                return 'NOT', '~', self.line, self.pos
            elif c == '&':
                self.src.read()
                return 'AND', '&', self.line, self.pos
            else:
                print("Неожиданный символ:", c, "в строке", self.line, ":", self.pos)
                break
        else:
            t = ("EOF", "EOF", self.line, self.pos)
        return t

    def get(self):
        self.token = self.read()
        return self.token

    def eat(self, tok_type):
        if self.token[0] == tok_type:
            t = self.token
            self.token = self.read()
            return t
        return False

    def neat(self, *toks):
        for t in toks:
            if self.token[0] == t:
                temp = self.token
                self.token = self.read()
                return temp
        return False

    def peek(self, what):
        if self.token[0] == what:
            return self.token[1]
        return ""

    def npeek(self, *toks):
        for t in toks:
            if self.token[0] == t:
                return self.token
        return False

    def error(self, msg):
        # print(f"Ошибка в строке:", self.line, msg)
        self.errors.append(f"Ошибка в строке: {self.line}:{self.pos} {msg}")
        return False
