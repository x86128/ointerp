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


def compile_consts(consts):
    res = {}
    if not consts:
        return res
    for cblock in consts:
        if cblock[0][1] in res:
            print("Переопределение константы", cblock[0][1])
            sys.exit(1)
        else:
            res[cblock[0][1]] = compile_expression(cblock[1])
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


# def pprint_if(indent, st):
#     print(indent, "IF", pprint_expr(st[1]))
#     if len(st) >= 4:
#         print(indent + "  ", st[2])
#         pprint_st_seq(indent + " " * 4, st[3])
#     if len(st) >= 6 and st[4] == 'ELSIF_BLOCK':
#         print(indent + "  ", st[4])
#         for elsif in st[5]:
#             print(indent + "    ", "ELSIF", pprint_expr(elsif[1]))
#             pprint_st_seq(indent + " " * 6, elsif[2])
#         if len(st) >= 8:
#             print(indent + "    ", "ELSE")
#             pprint_st_seq(indent + " " * 6, st[7])
#     if len(st) >= 6 and st[4] == 'ELSE':
#         print(indent + "  ", st[4])
#         pprint_st_seq(indent + " " * 4, st[5])


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
            text += ('IF_STAT', 'zzz')
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
        elif len(e[1]) == 2:  # SimpleExpression = ["+"|"-"] term
            res = compile_expression(e[1][1])
            res.append(("UNARY", e[1][0][1]))
            return res
        else:
            res = compile_expression(e[1][0])
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
