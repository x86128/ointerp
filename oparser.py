class ASTNode:
    def __init__(self, typ, **kwargs):
        self.typ = typ
        for k in kwargs:
            self.__setattr__(k, kwargs[k])

    def __str__(self):
        res = self.typ + " ("
        for k in self.__dict__:
            res += k + ", "
        return res + ")"

    def __repr__(self):
        return f"AstNode({self.typ})"


def p_ident(src):
    if ident := src.eat('IDENT'):
        return ASTNode('IDENT', name=ident.val)
    return None


def p_integer(src):
    if integer := src.eat('INTEGER'):
        return ASTNode('INTEGER', val=int(integer.val))
    return None


# selector = {"." ident | "[" expression "]"}.
def p_selector(src):
    if src.eat('PERIOD'):
        if sname := src.eat('IDENT'):
            return ASTNode('SELECTOR_DOT', name=sname.name)
        return src.error(f"Ожидается имя селектора, получено {src.token}")
    elif src.eat('LBRAK'):
        if e1 := p_expression(src):
            if src.eat('RBRAK'):
                return ASTNode('SELECTOR_EXPR', expr=e1)
            return src.error("Ожидается ]")
        return src.error("В выражении селектора ошибка")
    return None


# factor = ident selector | integer | "(" expression ")" | "~" factor.
def p_factor(src):
    if i := src.eat('IDENT'):
        if s := p_selector(src):
            return ASTNode('FACTOR_SEL', name=i.val, selector=s)
        return ASTNode('FACTOR_IDENT', name=i.val)
    elif i := src.eat('INTEGER'):
        return ASTNode('FACTOR_INT', val=i.val)
    elif src.eat('LPAREN'):
        if e := p_expression(src):
            if src.eat('RPAREN'):
                return ASTNode('FACTOR_EXP', expr=e)
            return src.error("Ожидается )")
        return src.error("Ошибка в выражении")
    elif src.eat('NOT'):
        if f := p_factor(src):
            return ASTNode('FACTOR_NOT', factor=f)
        return src.error("Ошибка в выражении отрицания")
    return src.error("Ошибка в выражении")


# term = factor {("*" | "DIV" | "MOD" | "&") factor}.
def p_term(src):
    if f := p_factor(src):
        f_list = [f]
        while op := src.neat('TIMES', 'DIV', 'MOD', 'AND'):
            if f2 := p_factor(src):
                f_list.append(op)
                f_list.append(f2)
            else:
                return src.error("Ошибка в выражении")
        return ASTNode('TERM', f_list=f_list)
    return src.error("Ожидается корректное выражение - множитель")


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
    return ASTNode('SEXPR', e_list=e_list)


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
    return ASTNode('EXPR', expr_list=e_list)


# assignment = ident selector ":=" expression.


# ActualParameters = "(" [expression {"," expression}] ")" .
def p_actual_parameters(src):
    if src.eat('LPAREN'):
        s_list = []
        e1 = p_expression(src)
        if not e1:
            if src.eat('RPAREN'):
                return ASTNode('ACTUAL_PARAMETERS', arg_list=s_list)
            else:
                return src.error('Ожидается )')
        s_list.append(e1)
        while src.eat('COMMA'):
            if e1 := p_expression(src):
                s_list.append(e1)
            else:
                return src.error('Ошибка в параметрах')
        if src.eat('RPAREN'):
            return ASTNode('ACTUAL_PARAMETERS', arg_list=s_list)
        else:
            return src.error('Ожидается )')
    return None


# ProcedureCall = ident [ActualParameters | "*"].
def p_procedure_call(src):
    if ident := p_ident(src):
        if ap := p_actual_parameters(src):
            return ASTNode('CALL_P', name=ident.name, args=ap)
        return ASTNode('CALL', name=ident.name)
    return None


# IfStatement = "IF" expression "THEN" StatementSequence
# {"ELSIF" expression "THEN" StatementSequence}
# ["ELSE" StatementSequence] "END".
def p_if_stat(src):
    if not src.eat('IF'):
        return None
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
        elsif_block.append(ASTNode('ELSIF', expr=ex_2, st_seq=st_seq))
    else_seq = []
    if src.eat('ELSE'):
        if not (else_seq_block := p_stat_seq(src)):
            return src.error('Ожидается последовательность выражений после ELSE')
        else_seq.append(else_seq_block)
    if not src.eat('END'):
        return src.error("Ожидается завершающий END в IF")
    return ASTNode('IF_STAT', expr=ex_1, then_block=then_block, elsif_block=elsif_block, else_block=else_seq)


# WhileStatement = "WHILE" expression "DO" StatementSequence "END".
def p_while_stat(src):
    if not src.eat('WHILE'):
        return None
    if not (ex := p_expression(src)):
        return src.error("Требуется условие WHILE")
    if not src.eat("DO"):
        return src.error("Ожидается DO")
    if not (st := p_stat_seq(src)):
        return src.error("Ожидается тело цикла")
    if not src.eat('END'):
        return src.error("Ожидается END")
    return ASTNode('WHILE', expr=ex, st_seq=st)


# RepeatStatement = “REPEAT” StatementSequence “UNTIL” expression.
def p_repeat_stat(src):
    if not src.eat('REPEAT'):
        return None
    if not (st := p_stat_seq(src)):
        return src.error("Ожидается тело цикла")
    if not src.eat("UNTIL"):
        return src.error("Ожидается UNTIL")
    if not (ex := p_expression(src)):
        return src.error("Требуется условие UNTIL")
    return ASTNode('REPEAT', expr=ex, st_seq=st)


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
            return ASTNode('ASSIGN', name=ident.val, expr=ex)
        if ap := p_actual_parameters(src):
            return ASTNode('CALL_P', name=ident.val, args=ap)
        else:
            return ASTNode('CALL', name=ident.val)
    elif if_stat := p_if_stat(src):
        return if_stat
    elif while_stat := p_while_stat(src):
        return while_stat
    elif repeat_stat := p_repeat_stat(src):
        return repeat_stat
    return None


# StatementSequence = statement {";" statement}.
def p_stat_seq(src):
    st_seq = []
    if st := p_statement(src):
        st_seq.append(st)
        while src.eat('SEMICOLON'):
            if st := p_statement(src):
                st_seq.append(st)
            else:
                return src.error("Ошибка в выражении")
    else:
        return None
    return ASTNode('STAT_SEQ', st_seq=st_seq)


# IdentList = ident {"," ident}.
def p_ident_list(src):
    id_list = []
    if ident := p_ident(src):
        id_list.append(ident.name)
        while src.eat('COMMA'):
            if ident := p_ident(src):
                id_list.append(ident.name)
            else:
                return src.error("Ожидается список идентификаторов")
    else:
        return None
    return ASTNode('ID_LIST', id_list=id_list)


# ArrayType = "ARRAY" expression "OF" type.
def p_array_type(src):
    if not src.eat('ARRAY'):
        return None
    if e := p_expression(src):
        if not src.eat('OF'):
            return src.error("Ожидается OF")
        if t := p_type(src):
            return 'ARRAY_TYPE', e, t
        else:
            return None
    return None


# FieldList = [IdentList ":" type].
def p_field_list(src):
    if not src.peek('IDENT'):
        return None
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
        return None
    fl_lists = []
    if fl := p_field_list(src):
        fl_lists.append(fl)
        while src.eat('SEMICOLON'):
            if fl := p_field_list(src):
                fl_lists.append(fl)
            else:
                return src.error("Ошибка описания RECORD")
        return 'RECORD', fl_lists
    return None


# type = ident | ArrayType | RecordType.
def p_type(src):
    if ident := src.eat('IDENT'):
        return ASTNode('TYPE', type=ident.val)
    elif at := p_array_type(src):
        return ASTNode('TYPE_ARRAY', at=at)
    elif rt := p_record_type(src):
        return ASTNode('TYPE_RECORD', rt=rt)
    return None


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
                return ASTNode('FP_VAR', id_list=il, type=t)
            else:
                return ASTNode('FP', id_list=il, type=t)
        else:
            return src.error('Ожидается тип параметра')
    return src.error('Ожидаются параметры')


# FormalParameters = "(" [FPSection {";" FPSection}] ")"
def p_formal_parameters(src):
    fp_list = []
    if not src.eat('LPAREN'):
        return ASTNode('FP_LIST', fp_list=[])
    if fp := p_fpsection(src):
        fp_list.append(fp)
        while src.eat('SEMICOLON'):
            if fp := p_fpsection(src):
                fp_list.append(fp)
            else:
                return src.error('Ошибка в объявлении параметров')
    if not src.eat('RPAREN'):
        return src.error('Ожидается )')
    return ASTNode('FP_LIST', fp_list=fp_list)


# ProcedureHeading = "PROCEDURE" ident [FormalParameters].
def p_procedure_heading(src):
    if not src.eat('PROCEDURE'):
        return None
    if pname := p_ident(src):
        if fp := p_formal_parameters(src):
            return ASTNode('PROC_HEAD', name=pname.name, fp=fp)
        else:
            return ASTNode('PROC_HEAD', name=pname.name, fp=[])
    return src.error('Ожидается имя процедуры')


# ProcedureBody = declarations ["BEGIN" StatementSequence] "END".
def p_procedure_body(src):
    decls = p_declarations(src)
    st_seq = None
    if src.eat('BEGIN'):
        st_seq = p_stat_seq(src)
    if not src.eat('END'):
        return src.error('Ожидается END')
    return ASTNode('PBODY', decls=decls, st_seq=st_seq)


# ProcedureDeclaration = ProcedureHeading ";" ProcedureBody ident.
def p_procedure_declaration(src):
    if not (ph := p_procedure_heading(src)):
        return None
    if not src.eat('SEMICOLON'):
        return src.error('Ожидается ;')
    if pb := p_procedure_body(src):
        if pname := p_ident(src):
            return ASTNode('PDECL', name=pname.name, head=ph, body=pb)
    else:
        return src.error("Ожидается тело процедуры")


# declarations = ["CONST" {ident "=" expression ";"}]
# ["TYPE" {ident "=" type ";"}]
# ["VAR" {IdentList ":" type ";"}]
# {ProcedureDeclaration ";"}.
def p_declarations(src):
    c_list = []
    v_list = []
    p_list = []
    if src.eat('CONST'):
        while c_name := src.eat('IDENT'):
            if not src.eat('EQL'):
                return src.error('Ожидается =')
            if c_exp := p_expression(src):
                c_list.append(ASTNode('CONST', name=c_name.val, expr=c_exp))
            else:
                return src.error('Ожидается выражение')
            if not src.eat('SEMICOLON'):
                return src.error('Ожидается ;')
    if src.eat('VAR'):
        while id_list := p_ident_list(src):
            if not src.eat('COLON'):
                return src.error('Ожидается :')
            if id_type := p_type(src):
                for v_id in id_list.id_list:
                    v_list.append(ASTNode('VAR', name=v_id, type=id_type))
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
    return ASTNode('DECLS', c_list=c_list, v_list=v_list, p_list=p_list)


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
        if m_name.val != m_end.val:
            return src.error('Неожиданный END модуля')
        if not src.eat('PERIOD'):
            return src.error('Ожидается .')
        return ASTNode('MODULE', name=m_name.val, decls=m_decls, st_seq=st_seq)
