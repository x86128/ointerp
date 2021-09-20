keywords = ["DIV", "MOD", "OR", "OF", "THEN", "DO", "UNTIL", "END", "ELSE", "ELSIF", "IF", "WHILE", "REPEAT",
            "ARRAY", "RECORD", "CONST", "TYPE", "VAR", "PROCEDURE", "BEGIN", "MODULE"]


class SourceReader:
    def __init__(self, input_file):
        self.input_file = input_file
        self.c = self.input_file.read(1)

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
        return 'INTEGER', integer

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
                print('Ошибка: Незакрытый коментарий в строке', tl)
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
            self.pos += 1
            return t
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

    def expect(self, tok_type):
        if self.token[0] == tok_type:
            t = self.token[1]
            self.token = self.read()
            return t
        else:
            print("Ошибка в строке:", self.line, "Ожидаем:", tok_type, "получено:", self.token)
        return ""

    def error(self, msg):
        # print(f"Ошибка в строке:", self.line, msg)
        self.errors.append(f"Ошибка в строке: {self.line}:{self.pos} {msg}")
        return False


def p_ident(src):
    return src.eat('IDENT')


def p_integer(src):
    return src.eat('INTEGER')


# selector = {"." ident | "[" expression "]"}.
def p_selector(src):
    if src.eat('PERIOD'):
        if sname := src.eat('IDENT'):
            return 'SELECTOR_DOT', sname[1]
        return src.error(f"Ожидается имя селектора, получено {src.token[0]}")
    elif src.eat('LBRAK'):
        line = src.line
        if e1 := p_expression(src):
            if src.eat('RBRAK'):
                return 'SELECTOR_EXPR', e1
            return src.error("Ожидается ]")
        return src.error(f"В выражении селектора ошибка {line}")
    return False


# factor = ident selector | integer | "(" expression ")" | "~" factor.
def p_factor(src):
    if i := src.eat('IDENT'):
        if s := p_selector(src):
            return 'FACTOR_SEL', i, s
        return 'FACTOR', i
    elif i := src.eat('INTEGER'):
        return 'FACTOR', i
    elif src.eat('LPAREN'):
        if e := p_expression(src):
            if src.eat('RPAREN'):
                return 'FACTOR', e
            return src.error("Ожидается )")
        return src.error("Ошибка в выражении")
    elif src.eat('NOT'):
        if f := p_factor(src):
            return 'FACTOR', ('NOT', f)
        return src.error("Ошибка в выражении отрицания")
    return src.error("Ошибка в выражении")


def p_term(src):
    if f := p_factor(src):
        f_list = [f]
        while True:
            op = src.npeek('TIMES', 'DIV', 'MOD', 'AND')
            if op:
                op = src.eat(op[0])
                if f2 := p_factor(src):
                    f_list.append(op)
                    f_list.append(f2)
                else:
                    return src.error("Ошибка в выражении")
            else:
                break
        return 'TERM', f_list
    return src.error("Ожидатся корректное выражение")


# SimpleExpression = ["+"|"-"] term {("+"|"-" | "OR") term}.
def p_simple_expression(src):
    e_list = []
    if op := src.npeek('PLUS', 'MINUS'):
        e_list.append(src.eat(op[0]))
    if t1 := p_term(src):
        e_list.append(t1)
        while True:
            if op := src.npeek('PLUS', 'MINUS', 'OR'):
                op = src.eat(op[0])
                if t2 := p_term(src):
                    e_list.append(op)
                    e_list.append(t2)
                else:
                    return src.error("Ожидается выражение - term")
            else:
                break
    else:
        return src.error("Ожидается выражение")
    return 'SEXPR', e_list


# expression = SimpleExpression [("=" | "#" | "<" | "<=" | ">" | ">=") SimpleExpression].
def p_expression(src):
    s1 = p_simple_expression(src)
    e_list = [s1]
    while op := src.npeek('EQL', 'NEQ', 'LSS', 'LEQ', 'GTR', 'GEQ'):
        e_list.append(src.eat(op[0]))
        if s2 := p_simple_expression(src):
            e_list.append(s2)
        else:
            return src.error("Ошибка в выражении")
    return 'EXPR', e_list


# assignment = ident selector ":=" expression.


# ActualParameters = "(" [expression {"," expression}] ")" .
def p_actual_parameters(src):
    if src.eat('LPAREN'):
        s_list = []
        e1 = p_expression(src)
        if not e1:
            if src.eat('RPAREN'):
                return 'ACTUAL_PARAMETERS', s_list
            else:
                return src.error('Ожидается )')
        s_list.append(e1)
        while src.eat('COMMA'):
            if e1 := p_expression(src):
                s_list.append(e1)
            else:
                return src.error('Ошибка в параметрах')
        if src.eat('RPAREN'):
            return 'ACTUAL_PARAMETERS', s_list
        else:
            return src.error('Ожидается )')
    return False


# ProcedureCall = ident [ActualParameters | "*"].
def p_procedure_call(src):
    if ident := p_ident(src):
        if ap := p_actual_parameters(src):
            return 'CALL_P', ident, ap
        return 'CALL', ident
    return False


# IfStatement = "IF" expression "THEN" StatementSequence
# {"ELSIF" expression "THEN" StatementSequence}
# ["ELSE" StatementSequence] "END".
def p_if_stat(src):
    if not src.eat('IF'):
        return False
    if not (ex_1 := p_expression(src)):
        return src.error("Требуется условие IF")
    if not src.eat('THEN'):
        return src.error("Ожидается THEN")
    if not (then_block := p_stat_seq(src)):
        return src.error('Ожидается последовательность выражений после THEN')
    elsif_block = []
    while src.eat('ELSIF'):
        if not (ex_2 := p_expression(src)):
            return src.error('Ожидается условие в ELSIF')
        if not src.eat('THEN'):
            return src.error('Ожидается THEN')
        if not (st_seq := p_stat_seq(src)):
            return src.error('Ожидается последовательность выражений после THEN')
        elsif_block.append(('ELSIF', ex_2, st_seq))
    if src.eat('ELSE'):
        if not (st_seq := p_stat_seq(src)):
            return src.error('Ожидается последовательность выражений после ELSE')
        if not src.eat('END'):
            return src.error("Ожидается завершающий END в IF")
        if elsif_block:
            return 'IF_STAT', ex_1, 'THEN', then_block, 'ELSIF_BLOCK', elsif_block, 'ELSE', st_seq
        else:
            return 'IF_STAT', ex_1, 'THEN', then_block, 'ELSE', st_seq
    if not src.eat('END'):
        return src.error("Ожидается завершающий END в IF")
    if elsif_block:
        return 'IF_STAT', ex_1, 'THEN', then_block, 'ELSIF_BLOCK', elsif_block
    else:
        return 'IF_STAT', ex_1, 'THEN', then_block


# WhileStatement = "WHILE" expression "DO" StatementSequence "END".
def p_while_stat(src):
    if not src.eat('WHILE'):
        return False
    if not (ex := p_expression(src)):
        return src.error("Требуется условие WHILE")
    if not src.eat("DO"):
        return src.error("Ожидается DO")
    if not (st := p_stat_seq(src)):
        return src.error("Ожидается тело цикла")
    if not src.eat('END'):
        return src.error("Ожидается END")
    return 'WHILE', ex, st


# RepeatStatement = “REPEAT” StatementSequence “UNTIL” expression.
def p_repeat_stat(src):
    if not src.eat('REPEAT'):
        return False
    if not (st := p_stat_seq(src)):
        return src.error("Ожидается тело цикла")
    if not src.eat("UNTIL"):
        return src.error("Ожидается UNTIL")
    if not (ex := p_expression(src)):
        return src.error("Требуется условие UNTIL")
    return 'REPEAT', st, ex


# statement = [assignment | ProcedureCall | IfStatement | WhileStatement | RepeatStatement].
def p_statement(src):
    if ident := src.eat('IDENT'):
        if sel := p_selector(src):
            if not src.eat('BECOMES'):
                return src.error('Ожидается :=')
            if not (ex := p_expression(src)):
                return src.error('Ожидается правая часть выражения')
            return 'ASSIGN_SEL', ident, sel, ex
        elif src.eat('BECOMES'):
            if not (ex := p_expression(src)):
                return src.error('Ожидается правая часть выражения')
            return 'ASSIGN', ident, ex
        if ap := p_actual_parameters(src):
            return 'CALL_P', ident, ap
        else:
            return 'CALL', ident
    elif if_stat := p_if_stat(src):
        return if_stat
    elif while_stat := p_while_stat(src):
        return while_stat
    elif repeat_stat := p_repeat_stat(src):
        return repeat_stat
    return False


# StatementSequence = statement {";" statement}.
def p_stat_seq(src):
    st_list = []
    if st := p_statement(src):
        st_list.append(st)
        while src.eat('SEMICOLON'):
            if st := p_statement(src):
                st_list.append(st)
            else:
                return src.error("Ошибка в выражении")
    else:
        return False
    return 'STAT_SEQ', st_list


# IdentList = ident {"," ident}.
def p_ident_list(src):
    id_list = []
    if ident := p_ident(src):
        id_list.append(ident)
        while src.eat('COMMA'):
            if ident := p_ident(src):
                id_list.append(ident)
            else:
                return src.error("Ожидается список идентификаторов")
    else:
        return False
    return 'ID_LIST', id_list


# ArrayType = "ARRAY" expression "OF" type.
def p_array_type(src):
    if not src.eat('ARRAY'):
        return False
    if e := p_expression(src):
        if not src.eat('OF'):
            return src.error("Ожидается OF")
        if t := p_type(src):
            return 'ARRAY_TYPE', e, t
        else:
            return False
    return False


# FieldList = [IdentList ":" type].
def p_field_list(src):
    if not src.peek('IDENT'):
        return False
    if id_list := p_ident_list(src):
        if not src.eat('COLON'):
            return src.error("Ожидается :")
        if t := p_type(src):
            return 'FIELD_LIST', id_list, t
        return src.err('Ожидается тип')
    return src.err("Ожидается список полей")


# RecordType = "RECORD" FieldList {";" FieldList} "END".
def p_record_type(src):
    if not src.eat('RECORD'):
        return False
    fl_lists = []
    if fl := p_field_list(src):
        fl_lists.append(fl)
        while src.eat('SEMICOLON'):
            if fl := p_field_list(src):
                fl_lists.append(fl)
            else:
                return src.error("Ошибка описания RECORD")
        return 'RECORD', fl_lists
    return False


# type = ident | ArrayType | RecordType.
def p_type(src):
    if ident := src.eat('IDENT'):
        return 'TYPE', ident[1]
    elif at := p_array_type(src):
        return 'TYPE', at
    elif rt := p_record_type(src):
        return 'TYPE', rt
    return False


# FPSection = ["VAR"] IdentList ":" type.
def p_fpsection(src):
    var_fp = False
    if src.eat('VAR'):
        var_fp = True
    if il := p_ident_list(src):
        if not src.eat('COLON'):
            return src.error('Ожидется :')
        if t := p_type(src):
            if var_fp:
                return 'FP_VAR', il, t
            else:
                return 'FP', il, t
        else:
            return src.error('Ожидется тип параметра')
    return src.error('Ожидаются параметры')


# FormalParameters = "(" [FPSection {";" FPSection}] ")"
def p_formal_parameters(src):
    fp_list = []
    if not src.eat('LPAREN'):
        return False
    if fp := p_fpsection(src):
        fp_list.append(fp)
        while src.eat('SEMICOLON'):
            if fp := p_fpsection(src):
                fp_list.append(fp)
            else:
                return src.error('Ошибка в объявлении параметров')
    if not src.eat('RPAREN'):
        return src.error('Ожидается )')
    return 'FP_LIST', fp_list


# ProcedureHeading = "PROCEDURE" ident [FormalParameters].
def p_procedure_heading(src):
    if not src.eat('PROCEDURE'):
        return False
    if pname := p_ident(src):
        if fp := p_formal_parameters(src):
            return 'PROC_HEAD', pname, fp
        else:
            return 'PROC_HEAD', pname
    return src.error('Ожидается имя процедуры')


# ProcedureBody = declarations ["BEGIN" StatementSequence] "END".
def p_procedure_body(src):
    decls = p_declarations(src)
    if src.eat('BEGIN'):
        st_seq = p_stat_seq(src)
    else:
        st_seq = []
    if not src.eat('END'):
        return src.error('Ожидается END')
    return 'PBODY', decls, st_seq


# ProcedureDeclaration = ProcedureHeading ";" ProcedureBody ident.
def p_procedure_declaration(src):
    if not (ph := p_procedure_heading(src)):
        return False
    if not src.eat('SEMICOLON'):
        return src.error('Ожидается ;')
    if pb := p_procedure_body(src):
        if pname := p_ident(src):
            return 'PDECL', pname, ph, pb
    else:
        return src.error("Ожидается тело процедуры")


# declarations = ["CONST" {ident "=" expression ";"}]
# ["TYPE" {ident "=" type ";"}]
# ["VAR" {IdentList ":" type ";"}]
# {ProcedureDeclaration ";"}.
def p_declarations(src):
    c_list = []
    t_list = []
    v_list = []
    p_list = []
    if src.eat('CONST'):
        while src.peek('IDENT'):
            if c_name := src.eat('IDENT'):
                if not src.eat('EQL'):
                    return src.error('Ожидается =')
                if c_exp := p_expression(src):
                    c_list.append((c_name, c_exp))
                else:
                    return src.error('Ожидается выражение')
                if not src.eat('SEMICOLON'):
                    return src.error('Ожидается ;')
    if src.eat('TYPE'):
        while src.peek('IDENT'):
            if t_name := src.eat('IDENT'):
                if not src.eat('EQL'):
                    return src.error('Ожидается =')
                if t_type := p_type(src):
                    t_list.append([t_name, t_type])
                else:
                    return src.error('Ожидается выражение')
                if not src.eat('SEMICOLON'):
                    return src.error('Ожидается ;')
    if src.eat('VAR'):
        while True:
            if id_list := p_ident_list(src):
                if not src.eat('COLON'):
                    return src.error('Ожидается :')
                if id_type := p_type(src):
                    v_list.append((id_list[0], id_list[1], id_type))
                else:
                    return src.error('Ожидается тип')
                if not src.eat('SEMICOLON'):
                    return src.error('Ожидается ;')
            else:
                break
    while True:
        if pd := p_procedure_declaration(src):
            if not src.eat('SEMICOLON'):
                return src.error("Ожидается ;")
            p_list.append(pd)
        else:
            break
    return 'DECLS', c_list, t_list, v_list, p_list


# module = "MODULE" ident ";" declarations ["BEGIN" StatementSequence] "END" ident ".".
def p_module(src):
    if not src.eat('MODULE'):
        return src.error('Ожидается определение модуля')
    if not (m_name := src.eat('IDENT')):
        return src.error('Ожидается имя модуля')
    if not src.eat('SEMICOLON'):
        return src.error("Ожидается ;")
    m_decls = p_declarations(src)
    if src.eat('BEGIN'):
        st_seq = p_stat_seq(src)
    else:
        st_seq = []
    if not src.eat('END'):
        return src.error('Ожидается END')
    if m_end := src.eat('IDENT'):
        if m_name[1] != m_end[1]:
            return src.error('Неожиданный END модуля')
        if not src.eat('PERIOD'):
            return src.error('Ожидается .')
        return 'MODULE', m_name[1], m_decls, st_seq


def pprint_procs(indent, procs):
    if not procs:
        return
    print(indent, "PROCEDURES:")
    for pdecl in procs:
        print(indent + "  ", pdecl[1][1], "is:")
        pbody = pdecl[3]
        pprint_decls(indent + "    ", pbody[1])
        pprint_st_seq(indent + "    ", pbody[2])


def pprint_consts(indent, consts):
    if not consts:
        return
    print(indent, "CONSTS:")
    for cblock in consts:
        print(indent + "  ", cblock[0][1], "=", pprint_expr(cblock[1]))


def pprint_vars(indent, variables):
    if not variables:
        return
    print(indent, "VARS:")
    for vblock in variables:
        print(indent + "  ", end=' ')
        for v in vblock[1]:
            print(v[1], end=',')
        print(' of ', vblock[2][1])


def pprint_decls(indent, decls):
    pprint_consts(indent, decls[1])
    print(indent, "TYPES:")
    print(indent + "  ", decls[2])

    pprint_vars(indent, decls[3])
    pprint_procs(indent, decls[4])


def pprint_while(indent, st):
    print(indent, 'WHILE', pprint_expr(st[1]), 'DO')
    pprint_st_seq(indent + "  ", st[2])


def pprint_if(indent, st):
    print(indent, "IF", pprint_expr(st[1]))
    if len(st) >= 4:
        print(indent + "  ", st[2])
        pprint_st_seq(indent + " " * 4, st[3])
    if len(st) >= 6 and st[4] == 'ELSIF_BLOCK':
        print(indent + "  ", st[4])
        for elsif in st[5]:
            print(indent + "    ", "ELSIF", pprint_expr(elsif[1]))
            pprint_st_seq(indent + " " * 6, elsif[2])
        if len(st) >= 8:
            print(indent + "    ", "ELSE")
            pprint_st_seq(indent + " " * 6, st[7])
    if len(st) >= 6 and st[4] == 'ELSE':
        print(indent + "  ", st[4])
        pprint_st_seq(indent + " " * 4, st[5])


def pprint_actual_pars(ap):
    res = "("
    for arg in ap[1]:
        res += pprint_expr(arg) + " , "
    return res + ")"


def pprint_st_seq(indent, st_seq):
    if not st_seq:
        return
    print(indent, 'TEXT')
    for st in st_seq[1]:
        if st[0] == 'WHILE':
            pprint_while(indent + "  ", st)
        elif st[0] == 'CALL':
            print(indent + "   CALL", st[1][1])
        elif st[0] == 'CALL_P':
            print(indent + "   CALL_P", st[1][1], pprint_actual_pars(st[2]))
        elif st[0] == 'ASSIGN':
            print(indent + "  ", st[1][1], ":=", pprint_expr(st[2]))
        elif st[0] == 'IF_STAT':
            pprint_if(indent + "  ", st)
        else:
            print(indent + "  ", st)


def pprint_expr(e):
    if e[0] == 'IDENT':
        return e[1]
    elif e[0] == 'INTEGER':
        return e[1]
    elif e[0] == 'NOT':
        return pprint_expr(e[1]) + " ~"
    elif e[0] == 'FACTOR':
        return pprint_expr(e[1])
    elif e[0] == 'TERM':
        ex_list = e[1]
        if len(ex_list) > 1:
            return pprint_expr(ex_list[0]) + " " + pprint_expr(('TERM', ex_list[2:])) + " " + ex_list[1][1]
        else:
            return pprint_expr(ex_list[0][1])
    elif e[0] == 'SEXPR':
        if len(e[1]) == 1:  # SimpleExpression = term
            return pprint_expr(e[1][0])
        elif len(e[1]) == 2:  # SimpleExpression = ["+"|"-"] term
            return pprint_expr(e[1][1]) + " " + "unary" + e[1][0][1]
        else:
            return pprint_expr(e[1][0]) + " " + pprint_expr(e[1][2]) + " " + e[1][1][1]
    elif e[0] == 'EXPR':
        ex_list = e[1]
        if len(ex_list) > 1:
            return pprint_expr(ex_list[0]) + " " + pprint_expr(('EXPR', ex_list[2:])) + " " + ex_list[1][1]
        else:
            return pprint_expr(ex_list[0])
    print(e)
    return ""


def pprint_ast(ast):
    indent = ""
    if not (ast[0] == 'MODULE'):
        return
    print('MODULE', ast[1])
    pprint_decls(indent + "  ", ast[2])
    pprint_st_seq(indent + "  ", ast[3])


if __name__ == "__main__":
    source = TokenStream('sample/sample.o0')
    syn_tree = p_module(source)
    if source.errors:
        print(source.errors[0])
    else:
        pprint_ast(syn_tree)
