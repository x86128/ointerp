def p_ident(src):
    return src.eat('IDENT')


def p_integer(src):
    if integer := src.eat('INTEGER'):
        return 'INTEGER', int(integer[1])
    return False


# selector = {"." ident | "[" expression "]"}.
def p_selector(src):
    if src.eat('PERIOD'):
        if sname := src.eat('IDENT'):
            return 'SELECTOR_DOT', sname[1]
        return src.error(f"Ожидается имя селектора, получено {src.token[0]}")
    elif src.eat('LBRAK'):
        if e1 := p_expression(src):
            if src.eat('RBRAK'):
                return 'SELECTOR_EXPR', e1
            return src.error("Ожидается ]")
        return src.error("В выражении селектора ошибка")
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
        while op := src.neat('TIMES', 'DIV', 'MOD', 'AND'):
            if f2 := p_factor(src):
                f_list.append(op)
                f_list.append(f2)
            else:
                return src.error("Ошибка в выражении")
        return 'TERM', f_list
    return src.error("Ожидается корректное выражение")


# SimpleExpression = ["+"|"-"] term {("+"|"-" | "OR") term}.
def p_simple_expression(src):
    e_list = []
    if op := src.neat('PLUS', 'MINUS'):
        e_list.append(op)
    if t1 := p_term(src):
        e_list.append(t1)
        while op := src.neat('PLUS', 'MINUS', 'OR'):
            if t2 := p_term(src):
                e_list.append(op)
                e_list.append(t2)
            else:
                return src.error("Ожидается выражение - term")
    else:
        return src.error("Ожидается выражение")
    return 'SEXPR', e_list


# expression = SimpleExpression [("=" | "#" | "<" | "<=" | ">" | ">=") SimpleExpression].
def p_expression(src):
    s1 = p_simple_expression(src)
    e_list = [s1]
    if op := src.neat('EQL', 'NEQ', 'LSS', 'LEQ', 'GTR', 'GEQ'):
        e_list.append(op)
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
    else_seq = []
    if src.eat('ELSE'):
        if not (else_seq := p_stat_seq(src)):
            return src.error('Ожидается последовательность выражений после ELSE')
    if not src.eat('END'):
        return src.error("Ожидается завершающий END в IF")
    return 'IF_STAT', ex_1, 'THEN', then_block, 'ELSIF_BLOCK', elsif_block, 'ELSE', else_seq


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
            return 'PROC_HEAD', pname, ('FP_LIST', [])
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
        while c_name := src.eat('IDENT'):
            if not src.eat('EQL'):
                return src.error('Ожидается =')
            if c_exp := p_expression(src):
                c_list.append((c_name, c_exp))
            else:
                return src.error('Ожидается выражение')
            if not src.eat('SEMICOLON'):
                return src.error('Ожидается ;')
    if src.eat('TYPE'):
        while t_name := src.eat('IDENT'):
            if not src.eat('EQL'):
                return src.error('Ожидается =')
            if t_type := p_type(src):
                t_list.append((t_name, t_type))
            else:
                return src.error('Ожидается выражение')
            if not src.eat('SEMICOLON'):
                return src.error('Ожидается ;')
    if src.eat('VAR'):
        while id_list := p_ident_list(src):
            if not src.eat('COLON'):
                return src.error('Ожидается :')
            if id_type := p_type(src):
                v_list.append((id_list[0], id_list[1], id_type))
            else:
                return src.error('Ожидается тип')
            if not src.eat('SEMICOLON'):
                return src.error('Ожидается ;')
    while True:
        if pd := p_procedure_declaration(src):
            if not src.eat('SEMICOLON'):
                return src.error("Ожидается ;")
            p_list.append(pd)
        else:
            break
    return 'DECLS', c_list, t_list, v_list, p_list


# module = "MODULE" ident ";" declarations ["BEGIN" StatementSequence] "END" ident ".".
def parse_module(src):
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
