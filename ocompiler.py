import pprint
import sys

from dataclasses import dataclass


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
                    print("Имя аргумента не может совпадать с именем переменной", arg)
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


def eval_static_const_expr(text):
    global c_tbl, c_mem
    stack = []
    for instr in text:
        if instr[0] == 'CONST':
            stack.append(instr[1])
        elif instr[0] == 'LOAD':
            for scope in c_tbl[::-1]:
                if instr[1] in scope:
                    c_ind = scope[instr[1]]['ind']
                    stack.append(c_mem[c_ind])
                else:
                    print('Undefined const', instr[1])
                    sys.exit(1)
        elif instr[0] == 'BINOP':
            if instr[1] == '+':
                stack.append(stack.pop() + stack.pop())
            elif instr[1] == 'OR':
                stack.append(stack.pop() or stack.pop())
            elif instr[1] == '&':
                stack.append(stack.pop() and stack.pop())
            elif instr[1] == '-':
                t = stack.pop()
                stack.append(stack.pop() - t)
            elif instr[1] == '*':
                stack.append(stack.pop() * stack.pop())
            elif instr[1] == 'DIV':
                t = stack.pop()
                stack.append(int(stack.pop() / t))
            elif instr[1] == 'MOD':
                t = stack.pop()
                stack.append(stack.pop() % t)
            else:
                raise RuntimeError(f'Unknown instruction in const expr {instr}')
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


# define global constant and variable tables for scope tracking
c_tbl = []
v_tbl = []

# constant memory
c_mem = []


def compile_consts(consts):
    global c_tbl, c_mem
    res = {}
    if not consts:
        return res
    for const in consts:
        if const.name in res:
            print(f"Переопределение константы `{const.name}` в строке {const.line}")
            sys.exit(1)
        for scope in c_tbl[::-1]:
            if const.name in scope:
                print(f"Переопределение константы `{const.name}` в строке {const.line} вышестоящей области видимости")
                break
        t = compile_expression(const.expr)
        c_val = eval_static_const_expr(t)

        c_ind = len(c_mem)
        c_mem.append(c_val)
        res[const.name] = {'ind': c_ind, 'line': const.line}
        c_tbl[-1][const.name] = res[const.name]
    return res


def compile_vars(variables):
    global c_tbl, v_tbl
    res = {}
    if not variables:
        return res
    for v in variables:
        # если переменная с данным именем уже определена в текущей области видимости - падаем
        if v.name in res:
            print(f"ERR: Переопределение переменной `{v.name}` в строке {v.line}")
            sys.exit(1)
        # ищем переменную в вышестоящих областях видимости начиная с самой внутренней
        for scope in v_tbl[::-1]:
            if v.name in scope:
                print(f"WARN: Переопределение переменной `{v.name}` в строке {v.line} из внешней области видимости")
                break
        if v.type.typ == 'TYPE':  # scalar type
            res[v.name] = (0, v.type.type)  # (default value, type)
        elif v.type.typ == 'ARRAY_TYPE':
            e_const = compile_expression(v.type.expr)
            try:
                e_val = eval_static_const_expr(e_const)
            except ValueError:
                raise SyntaxError(f"Array size must be scalar or const")
            res[v.name] = ([0] * e_val, v.type.type)  # (default value, type)
            v_tbl[-1][v.name] = True
        else:
            raise SyntaxError(f"Unknown type: {v.type.typ}")
    return res


def compile_decls(decls):
    global c_tbl, v_tbl
    # перед компиляцией констант и переменных создаем область видимости
    # в соответствующих глобальных таблицах
    c_tbl.append({})
    v_tbl.append({})
    # компилируем
    consts = compile_consts(decls.c_list)
    variables = compile_vars(decls.v_list)
    procs = compile_procs(decls.p_list)
    # чистим таблицы видимости
    c_tbl.pop()
    v_tbl.pop()
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
    elif e.typ == 'FACTOR_EXP':
        return compile_expression(e.expr)
    elif e.typ == 'FACTOR_INT':
        return [('CONST', e.val)]
    elif e.typ == 'FACTOR_IDENT':
        return [('LOAD', e.name)]
    elif e.typ == 'FACTOR_NOT':
        res = compile_expression(e.factor)
        res.append(('UNARY', '~'))
        return res
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
    raise RuntimeError(f"Unknown expr: {e}")


def compile_module(ast):
    global c_mem
    if ast.typ != 'MODULE':
        raise "Module required"
    decls = compile_decls(ast.decls)
    text = compile_statements(ast.st_seq)
    text.append(('STOP', '12345'))
    return {'name': ast.name, 'decls': decls, 'text': text, 'c_mem': c_mem}
