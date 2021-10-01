import pprint
import sys


def compile_procs(ast):
    res = {}
    if not ast:
        return res
    for pdecl in ast:
        phead = pdecl[2]
        pname = phead[1][1]
        args = []
        for phblock in phead[2][1]:
            for pp in phblock[1][1]:
                # (name, type)
                args.append((pp[1], phblock[2][1]))
        pbody = pdecl[3]
        decls = compile_decls(pbody[1])
        for a in args:
            if a[0] in decls["vars"]:
                print("Имя аргумента не может совпадать с именем переменной", a[0])
                sys.exit(1)
            else:
                decls["vars"][a[0]] = (0, a[1])
        # generating body text
        text = []
        for v in args[::-1]:
            text.append(('STOR', v[0]))
        text += compile_statements(pbody[2])
        res[pname] = {"args": args, "decls": decls, "text": text}
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
    for cblock in consts:
        if cblock[0][1] in res:
            print("Переопределение константы", cblock[0][1])
            sys.exit(1)
        else:
            t = compile_expression(cblock[1])
            res[cblock[0][1]] = eval_static_const_expr(res, t)
    return res


def compile_vars(variables):
    res = {}
    if not variables:
        return res
    for vblock in variables:
        for v in vblock[1]:
            if v[1] in res:
                print("Переопределение переменной", v[1])
                sys.exit(1)
            else:
                res[v[1]] = (0, vblock[2][1])  # (default value, type)
    return res


def compile_decls(decls):
    consts = compile_consts(decls[1])
    variables = compile_vars(decls[3])
    procs = compile_procs(decls[4])
    return {"consts": consts, "vars": variables, "procs": procs}


label_counter = 0


def compile_while(st):
    global label_counter
    label = label_counter
    label_counter += 2
    text = [('LABEL', f'L{label}')]
    text += compile_expression(st[1])
    text.append(('BR_ZERO', f'L{label + 1}'))
    text += compile_statements(st[2])
    text.append(('BR', f'L{label}'))
    text.append(('LABEL', f'L{label + 1}'))
    return text


def compile_if(st):
    global label_counter
    text = []
    # labels allocation
    label = label_counter
    ex = st[1]
    then = st[3]
    # label for elsif block
    elsif_label = label
    elsif = st[5]
    else_label = elsif_label + len(elsif)
    elseb = st[7]
    exit_label = else_label + len(elseb)
    label_counter = exit_label + 1
    # compiling IF expression
    text += compile_expression(ex)
    if len(elsif) > 0:
        text.append(('BR_ZERO', f'L{elsif_label}'))
    else:
        text.append(('BR_ZERO', f'L{exit_label}'))
    text += compile_statements(then)
    if len(elseb) > 0 or len(elsif) > 0:
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSIF blocks if any
    for i, elsifb in enumerate(elsif):
        text.append(('LABEL', f'L{elsif_label}'))
        text += compile_expression(elsifb[1])
        text.append(('BR_ZERO', f'L{elsif_label + i + 1}'))
        text += compile_statements(elsifb[2])
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSE block if any
    if len(elseb) > 0:
        text.append(('LABEL', f'L{else_label}'))
        text += compile_statements(elseb)
    text.append(('LABEL', f'L{exit_label}'))
    return text


def compile_args(ap):
    text = []
    for arg in ap[1]:
        text += compile_expression(arg)
    return text


def compile_statements(st_seq):
    text = []
    if not st_seq:
        return text
    for i, st in enumerate(st_seq[1]):
        if st[0] == 'WHILE':
            text += compile_while(st)
        elif st[0] == 'CALL':
            text += ('CALL', st[1][1])
        elif st[0] == 'CALL_P':
            text += compile_args(st[2])
            text.append(('CALL', st[1][1]))
        elif st[0] == 'ASSIGN':
            for t in compile_expression(st[2]):
                text.append(t)
            text.append(('STOR', st[1][1]))
        elif st[0] == 'IF_STAT':
            text += compile_if(st)
        else:
            print('Unknown stat:', st)
    return text


def compile_expression(e):
    if e[0] == 'IDENT':
        return [('LOAD', e[1])]
    elif e[0] == 'INTEGER':
        return [('CONST', e[1])]
    elif e[0] == 'NOT':
        res = compile_expression(e[1])
        res.append(('NOT',))
        return res
    elif e[0] == 'FACTOR':
        return compile_expression(e[1])
    elif e[0] == 'TERM':
        ex_list = e[1]
        if len(ex_list) > 1:
            res = compile_expression(ex_list[0])
            res += compile_expression(('TERM', ex_list[2:]))
            res += [('BINOP', ex_list[1][1])]
            return res
        else:
            return compile_expression(ex_list[0])
    elif e[0] == 'SEXPR':
        if len(e[1]) == 1:  # SimpleExpression = term
            return compile_expression(e[1][0])
        elif len(e[1]) >= 2 and e[1][0][0] in ['PLUS', 'MINUS']:  # SimpleExpression = ["+"|"-"] term
            res = compile_expression(e[1][1])
            res.append(("UNARY", e[1][0][1]))
            for i in range(2, len(e[1]), 2):
                res += compile_expression(e[1][i+1])
                res.append(("BINOP", e[1][i][1]))
            return res
        else:  # # SimpleExpression = term { ("+"|"-"|"OR") term}
            print(e)
            res = compile_expression(e[1][0])
            print(res)
            res += compile_expression(e[1][2])
            res.append(("BINOP", e[1][1][1]))
            for i in range(3, len(e[1]), 2):
                res += compile_expression(e[1][i + 1])
                res.append(("BINOP", e[1][i][1]))
            return res
    elif e[0] == 'EXPR':
        ex_list = e[1]
        if len(ex_list) > 1:
            res = compile_expression(ex_list[0])
            res += compile_expression(('EXPR', ex_list[2:]))
            res.append(('RELOP', ex_list[1][1]))
            return res
        else:
            return compile_expression(ex_list[0])
    print("Unknown expr", e)
    return ""


def compile_module(ast):
    if not (ast[0] == 'MODULE'):
        return
    print('MODULE', ast[1])
    decls = compile_decls(ast[2])
    text = compile_statements(ast[3])
    text.append(('STOP', ''))
    return {'name': ast[1], 'decls': decls, 'text': text}
