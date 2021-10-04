import pprint
import sys


def compile_procs(procs):
    res = {}
    if not procs:
        return res
    arg_list = []
    for proc in procs:
        if proc.name in res:
            print("Переопределение процедуры", proc.name)
            sys.exit(1)
        decls = compile_decls(proc.body.decls)
        for args in proc.head.fp.fp_list:
            for arg in args.id_list.id_list:
                if arg in decls["vars"]:
                    print("Имя аргумента не может совпадать с именем переменной", a[0])
                    sys.exit(1)
                else:
                    decls["vars"][arg] = (0, args.type.type)
                    arg_list.append((arg, args.type.type))
        # generating body text
        text = []

        for v in arg_list[::-1]:
            text.append(('STOR', v[0]))
        text += compile_statements(proc.body.st_seq)
        res[proc.name] = {"args": arg_list, "decls": decls, "text": text}
    return res


def eval_static_const_expr(consts, text):
    stack = []
    for instr in text:
        if instr[0] == 'CONST':
            stack.append(instr[1])
        elif instr[0] == 'LOAD':
            if instr[1] in consts:
                stack.append(consts[instr[1]])
            else:
                print('Undefined const', instr[1])
                sys.exit(1)
        elif instr[0] == 'BINOP':
            if instr[1] == '+':
                stack.append(stack.pop() + stack.pop())
            if instr[1] == '-':
                t = stack.pop()
                stack.append(stack.pop() - t)
            if instr[1] == '*':
                stack.append(stack.pop() * stack.pop())
            if instr[1] == 'div':
                t = stack.pop()
                stack.append(int(stack.pop() / t))
            elif instr[1] == 'mod':
                t = stack.pop()
                stack.append(stack.pop() % t)
            else:
                print('Unknown instruction in const expr', instr)
        elif instr[0] == 'UNARY':
            if instr[1] == '+':
                pass
            elif instr[1] == '-':
                stack.append(-stack.pop())
            else:
                print('Unknown unary in const expr', instr)
        else:
            print('Unknown op in const expr', instr)
    return stack.pop()


def compile_consts(consts):
    res = {}
    if not consts:
        return res
    for const in consts:
        if const.name in res:
            print("Переопределение константы", const.name)
            sys.exit(1)
        else:
            t = compile_expression(const.expr)
            res[const.name] = eval_static_const_expr(res, t)
    return res


def compile_vars(variables):
    res = {}
    if not variables:
        return res
    for v in variables:
        if v.name in res:
            print("Переопределение переменной", v.name)
            sys.exit(1)
        else:
            res[v.name] = (0, v.type.type)  # (default value, type)
    return res


def compile_decls(decls):
    consts = compile_consts(decls.c_list)
    variables = compile_vars(decls.v_list)
    procs = compile_procs(decls.p_list)
    return {"consts": consts, "vars": variables, "procs": procs}


label_counter = 0


def compile_while(st):
    global label_counter
    label = label_counter
    label_counter += 2
    text = [('LABEL', f'L{label}')]
    text += compile_expression(st.expr)
    text.append(('BR_ZERO', f'L{label + 1}'))
    text += compile_statements(st.st_seq)
    text.append(('BR', f'L{label}'))
    text.append(('LABEL', f'L{label + 1}'))
    return text

def compile_repeat(st):
    global label_counter
    label = label_counter
    label_counter += 1
    text = [('LABEL', f'L{label}')]
    text += compile_statements(st.st_seq)
    text += compile_expression(st.expr)
    text.append(('BR_ZERO', f'L{label}'))
    return text

def compile_if(st):
    global label_counter
    text = []
    # labels allocation
    label = label_counter
    # label for elsif block
    elsif_label = label
    else_label = elsif_label + len(st.elsif_block)
    exit_label = else_label + len(st.else_block)
    label_counter = exit_label + 1
    # compiling IF expression
    text += compile_expression(st.expr)
    if len(st.elsif_block) > 0:
        text.append(('BR_ZERO', f'L{elsif_label}'))
    else:
        text.append(('BR_ZERO', f'L{exit_label}'))
    text += compile_statements(st.then_block)
    if len(st.else_block) > 0 or len(st.elsif_block) > 0:
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSIF blocks if any
    for i, elsifb in enumerate(st.elsif_block):
        text.append(('LABEL', f'L{elsif_label}'))
        text += compile_expression(elsifb.expr)
        text.append(('BR_ZERO', f'L{elsif_label + i + 1}'))
        text += compile_statements(elsifb.st_seq)
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSE block if any
    if len(st.else_block) > 0:
        text.append(('LABEL', f'L{else_label}'))
        text += compile_statements(st.else_block[0])
    text.append(('LABEL', f'L{exit_label}'))
    return text


def compile_args(ap):
    text = []
    for arg in ap.arg_list:
        text += compile_expression(arg)
    return text


def compile_statements(st_seq):
    text = []
    if not st_seq:
        return text
    for i, st in enumerate(st_seq.st_seq):
        if st.typ == 'WHILE':
            text += compile_while(st)
        elif st.typ == 'REPEAT':
            text += compile_repeat(st)
        elif st.typ == 'CALL':
            text.append(('CALL', st.name))
        elif st.typ == 'CALL_P':
            text += compile_args(st.args)
            text.append(('CALL', st.name))
        elif st.typ == 'ASSIGN':
            for t in compile_expression(st.expr):
                text.append(t)
            text.append(('STOR', st.name))
        elif st.typ == 'IF_STAT':
            text += compile_if(st)
        else:
            print('Unknown stat:', st)
    return text


def compile_expression(e):
    if e.typ == 'IDENT':
        return [('LOAD', e.val)]
    elif e.typ == 'INTEGER':
        return [('CONST', e.val)]
    elif e.typ == 'NOT':
        res = compile_expression(e[1])
        res.append(('NOT',))
        return res
    elif e.typ == 'FACTOR_EXP':
        return compile_expression(e.expr)
    elif e.typ == 'FACTOR_INT':
        return [('CONST', e.val)]
    elif e.typ == 'FACTOR_IDENT':
        return [('LOAD', e.name)]
    elif e.typ == 'TERM':
        f_list = e.f_list
        if len(f_list) == 1:  # term = factor
            res = compile_expression(f_list[0])
            return res
        else:  # term = factor {("*" | "DIV" | "MOD" | "&") factor}.
            res = compile_expression(f_list[0])
            res += compile_expression(f_list[2])
            res += [('BINOP', f_list[1].val)]
            for i in range(3, len(f_list), 2):
                res += compile_expression(f_list[i + 1])
                res += [('BINOP', f_list[i].val)]
            return res
    elif e.typ == 'SEXPR':
        if len(e.e_list) == 1:  # SimpleExpression = term
            return compile_expression(e.e_list[0])
        elif len(e.e_list) >= 2 and e.e_list[0].typ in ['PLUS', 'MINUS']:  # SimpleExpression = ["+"|"-"] term
            res = compile_expression(e.e_list[1])
            res.append(("UNARY", e.e_list[0].val))
            for i in range(2, len(e.e_list), 2):
                res += compile_expression(e.e_list[i + 1])
                res.append(("BINOP", e.e_list[i].val))
            return res
        else:  # # SimpleExpression = term { ("+"|"-"|"OR") term}
            res = compile_expression(e.e_list[0])
            res += compile_expression(e.e_list[2])
            res.append(("BINOP", e.e_list[1].val))
            for i in range(3, len(e.e_list), 2):
                res += compile_expression(e.e_list[i + 1])
                res.append(("BINOP", e.e_list[i].val))
            return res
    elif e.typ == 'EXPR':  # expression = SimpleExpression [("=" | "#" | "<" | "<=" | ">" | ">=") SimpleExpression].
        if len(e.expr_list) > 1:
            res = compile_expression(e.expr_list[0])
            res += compile_expression(e.expr_list[2])
            res.append(('RELOP', e.expr_list[1].val))
            return res
        else:
            return compile_expression(e.expr_list[0])
    print("Unknown expr:", e)
    return ""


def compile_module(ast):
    if ast.typ != 'MODULE':
        raise "Module required"
    decls = compile_decls(ast.decls)
    text = compile_statements(ast.st_seq)
    text.append(('STOP', '12345'))
    return {'name': ast.name, 'decls': decls, 'text': text}
