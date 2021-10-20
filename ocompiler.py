import pprint
import sys

system_procs = {'writeint': {'v_size': 0, 'arg_sz': 1, 'sys_num': 0},
                'writespace': {'v_size': 0, 'arg_sz': 1, 'sys_num': 1},
                'writeln': {'v_size': 0, 'arg_sz': 0, 'sys_num': 2},
                'halt': {'v_size': 0, 'arg_sz': 1, 'sys_num': 3}}

text = []


def emit(cmd):
    global text
    text.append(cmd)


def compile_procs(env, procs):
    global proc_tab
    if not procs:
        return
    for proc in procs:
        if proc.name in proc_tab:
            print("Переопределение процедуры", proc.name)
            sys.exit(1)
        compile_decls(env, proc.body.decls)
        arg_list = {}
        arg_offset = 0
        for args in proc.head.fp.fp_list[::-1]:
            is_var = args.typ == 'FP_VAR'
            for arg in args.id_list.id_list[::-1]:
                if arg in env[-1]["vars"]:
                    print("Имя аргумента не может совпадать с именем переменной", arg)
                    sys.exit(1)
                else:
                    arg_list[arg] = {'offset': arg_offset, 'typ': args.type.type, 'var': is_var}
                    arg_offset += 1
        w_offset = 0
        w_env = {}
        for var in env[-1]["vars"]:
            w_env[var] = {'offset': w_offset, 'size': env[-1]["vars"][var]['size'],
                          'typ': env[-1]["vars"][var]['typ']}
            w_offset += env[-1]["vars"][var]['size']
        # generating body text
        env[-1]['proc'] = proc.name
        # env[-1]['proc_ptr'] = pc
        env[-1]['args'] = arg_list
        proc_tab[proc.name] = {"args": arg_list, 'arg_sz': len(arg_list),
                               'vars': w_env,
                               'v_size': w_offset}

        emit(('LABEL', proc.name))
        emit(('ENTER', proc.name))
        compile_statements(env, proc.body.st_seq)
        emit(('LEAVE', proc.name))
        emit(('RETURN', proc.name))

        env.pop()


def eval_static_const_expr(env, text):
    stack = []
    for instr in text:
        if instr[0] == 'CONST':
            stack.append(instr[1])
        elif instr[0] == 'CLOAD':
            found = False
            for scope in env[::-1]:
                if instr[2] in c_tab:
                    stack.append(c_tab[instr[2]]['val'])
                    found = True
            if not found:
                raise SyntaxError(f'Undefined const {instr[1]}')
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
                raise SyntaxError(f'Unknown unary in const expr: {instr}')
        else:
            raise SystemError(f'Unknown op in const expr {instr}')
    return stack.pop()


c_mem = []
c_tab = {}


def compile_consts(env, const_list):
    global c_mem, c_tab
    if len(const_list) < 1:
        return
    for const in const_list:
        if const.name in c_tab:
            raise SyntaxError(f"Переопределение константы `{const.name}` в строке {const.line}")
        t = compile_expression(env, const.expr)
        c_val = eval_static_const_expr(env, t)

        c_mem.append(c_val)
        c_tab[const.name] = {'val': c_val, 'line': const.line, 'offset': len(c_mem) - 1}


def compile_vars(env, variables):
    global c_tab
    if not variables:
        return
    offset = 0
    for v in variables:
        # если переменная с данным именем уже определена в текущей области видимости - падаем
        if v.name in env[-1]['vars']:
            print(f"ERR: Переопределение переменной `{v.name}` в строке {v.line}")
            sys.exit(1)
        # ищем переменную в вышестоящих областях видимости начиная с самой внутренней
        for scope in env[::-1]:
            if v.name in scope['vars']:
                print(f"WARN: Переопределение переменной `{v.name}` в строке {v.line} из внешней области видимости")
                break
        # ищем в константах и их областях видимости
        if v.name in c_tab:
            print(f"ERR: Имя переменной `{v.name}` в строке {v.line} не может совпадать с именем константы")
            sys.exit(1)
        if v.type.typ == 'TYPE':  # scalar type
            env[-1]['vars'][v.name] = {'typ': 'integer', 'offset': offset, 'size': 1}
            offset += 1
        elif v.type.typ == 'ARRAY_TYPE':
            e_const = compile_expression(env, v.type.expr)
            try:
                size = eval_static_const_expr(env, e_const)
            except ValueError:
                raise SyntaxError(f"Array size must be scalar or const")
            env[-1]['vars'][v.name] = {'typ': 'array', 'a_typ': v.type.type, 'offset': offset, 'size': size}
            offset += size
        else:
            raise SyntaxError(f"Unknown type: {v.type.typ}")


def compile_decls(env, decls):
    env.append({'vars': {}, 'args': {}})
    compile_consts(env, decls.c_list)
    compile_vars(env, decls.v_list)
    v_size = 0
    for v in env[-1]['vars']:
        v_size += env[-1]['vars'][v]['size']
    env[-1]['v_size'] = v_size
    compile_procs(env, decls.p_list)
    vars = env[-1]['vars']
    return v_size, vars


label_counter = 0
label_tab = {}


def set_label(l_name):
    global label_tab


def compile_while(env, st):
    global label_counter
    label = label_counter
    label_counter += 2
    emit(('LABEL', f'L{label}'))
    for t in compile_expression(env, st.expr):
        emit(t)
    emit(('BR_ZERO', f'L{label + 1}'))
    compile_statements(env, st.st_seq)
    emit(('BR', f'L{label}'))
    emit(('LABEL', f'L{label + 1}'))


def compile_repeat(env, st):
    global label_counter
    label = label_counter
    label_counter += 1
    emit(('LABEL', f'L{label}'))
    compile_statements(env, st.st_seq)
    for t in compile_expression(env, st.expr):
        emit(t)
    emit(('BR_ZERO', f'L{label}'))


def compile_if(env, st):
    global label_counter
    # labels allocation
    label = label_counter
    # label for elsif block
    elsif_label = label
    else_label = elsif_label + len(st.elsif_block)
    exit_label = else_label + len(st.else_block)
    label_counter = exit_label + 1
    # compiling IF expression
    for t in compile_expression(env, st.expr):
        emit(t)
    if len(st.elsif_block) > 0:
        emit(('BR_ZERO', f'L{elsif_label}'))
    elif len(st.else_block) > 0:
        emit(('BR_ZERO', f'L{else_label}'))
    else:
        emit(('BR_ZERO', f'L{exit_label}'))
    compile_statements(env, st.then_block)
    if len(st.else_block) > 0 or len(st.elsif_block) > 0:
        emit(('BR', f'L{exit_label}'))
    # compiling ELSIF blocks if any
    for i, elsifb in enumerate(st.elsif_block):
        emit(('LABEL', f'L{elsif_label}'))
        for t in compile_expression(env, elsifb.expr):
            emit(t)
        emit(('BR_ZERO', f'L{elsif_label + i + 1}'))
        compile_statements(env, elsifb.st_seq)
        emit(('BR', f'L{exit_label}'))
    # compiling ELSE block if any
    if len(st.else_block) > 0:
        emit(('LABEL', f'L{else_label}'))
        compile_statements(env, st.else_block[0])
    emit(('LABEL', f'L{exit_label}'))


def compile_args(env, ap, proc_name):
    global proc_tab
    if proc_name in system_procs:
        for i, arg in enumerate(ap.arg_list):
            for t in compile_expression(env, arg):
                emit(t)
    else:
        arg_list = [''] * len(ap.arg_list)
        for arg in proc_tab[proc_name]['args']:
            arg_list[proc_tab[proc_name]['args'][arg]['offset']] = arg
        arg_list = arg_list[::-1]
        for i, arg in enumerate(ap.arg_list):
            if proc_tab[proc_name]['args'][arg_list[i]]['var']:
                t = compile_expression(env, arg)
                emit(('ADR_LOAD', t[-1][1], t[-1][2]))
            else:
                for t in compile_expression(env, arg):
                    emit(t)


def compile_statements(env, st_seq):
    global system_procs
    if not st_seq:
        return

    for i, st in enumerate(st_seq.st_seq):
        if st.typ == 'WHILE':
            compile_while(env, st)
        elif st.typ == 'REPEAT':
            compile_repeat(env, st)
        elif st.typ == 'CALL':
            if st.name in system_procs:
                if system_procs[st.name]['arg_sz'] > 0:
                    raise SyntaxError(f'В процедуру {st.name} не переданы параметры')
                emit(('SYSCALL', st.name))
            else:
                if proc_tab[st.name]['arg_sz'] > 0:
                    raise SyntaxError(f'В процедуру {st.name} не переданы параметры')
                emit(('CALL', st.name))
        elif st.typ == 'CALL_P':
            if st.name in system_procs:
                if len(st.args.arg_list) != system_procs[st.name]['arg_sz']:
                    raise SyntaxError(f'Процедура {st.name} ожидает {system_procs[st.name]["arg_sz"]} параметров')
            elif st.name in proc_tab:
                if len(st.args.arg_list) != proc_tab[st.name]['arg_sz']:
                    raise SyntaxError(f'Процедура {st.name} ожидает {proc_tab[st.name]["arg_sz"]} параметров')
            compile_args(env, st.args, st.name)
            if st.name in system_procs:
                v_sz = system_procs[st.name]['v_size']
                arg_sz = system_procs[st.name]['arg_sz']
            else:
                v_sz = proc_tab[st.name]['v_size']
                arg_sz = proc_tab[st.name]['arg_sz']
            if v_sz > 0:
                emit(('ALLOC', v_sz))
            if st.name in system_procs:
                emit(('SYSCALL', st.name))
            else:
                emit(('CALL', st.name))
            if v_sz + arg_sz > 0:
                emit(('DEALLOC', v_sz + arg_sz))
        elif st.typ == 'ASSIGN':
            for t in compile_expression(env, st.expr):
                emit(t)
            v_offset = -len(env[-1]['vars'])
            if st.name in env[-1]['vars']:
                v_offset += env[-1]['vars'][st.name]['offset']
                emit(('VSTOR', v_offset, st.name))
            elif st.name in env[-1]['args']:
                v_offset -= (1 + env[-1]['args'][st.name]['offset'])
                if env[-1]['args'][st.name]['var']:
                    emit(('RSTOR', v_offset, st.name))
                else:
                    emit(('VSTOR', v_offset, st.name))
            else:
                raise SystemError(f'Ошибка в строке {st.line}: Присваивание позволено только локальным переменным')
        elif st.typ == 'IF_STAT':
            compile_if(env, st)
        else:
            raise SyntaxError(f'Unknown stat: {st}')


def compile_expression(env, e):
    global c_mem, c_tab
    if e.typ == 'IDENT':
        raise RuntimeError('Unreachable')
    elif e.typ == 'INTEGER':
        return [('CONST', e.val)]
    elif e.typ == 'FACTOR_EXP':
        return compile_expression(env, e.expr)
    elif e.typ == 'FACTOR_INT':
        return [('CONST', e.val)]
    elif e.typ == 'FACTOR_IDENT':
        # ищем в переменных
        scope = env[-1]
        v_offset = -len(scope['vars'])
        if e.name in scope['vars']:
            return [('VLOAD', v_offset + scope['vars'][e.name]['offset'], e.name)]
        elif e.name in c_tab:
            return [('CLOAD', c_tab[e.name]['offset'], e.name)]
        elif e.name in scope['args']:
            v_offset -= (1 + scope['args'][e.name]['offset'])
            if scope['args'][e.name]['var']:
                return [('RLOAD', v_offset, e.name)]
            else:
                return [('VLOAD', v_offset, e.name)]
        return [('GLOAD', e.name)]
    elif e.typ == 'FACTOR_NOT':
        res = compile_expression(env, e.factor)
        res.append(('UNARY', '~'))
        return res
    elif e.typ == 'TERM':
        f_list = e.f_list
        if len(f_list) == 1:  # term = factor
            res = compile_expression(env, f_list[0])
            return res
        else:  # term = factor {("*" | "DIV" | "MOD" | "&") factor}.
            res = compile_expression(env, f_list[0])
            res += compile_expression(env, f_list[2])
            res += [('BINOP', f_list[1].val)]
            for i in range(3, len(f_list), 2):
                res += compile_expression(env, f_list[i + 1])
                res += [('BINOP', f_list[i].val)]
            return res
    elif e.typ == 'SEXPR':
        if len(e.e_list) == 1:  # SimpleExpression = term
            return compile_expression(env, e.e_list[0])
        elif len(e.e_list) >= 2 and e.e_list[0].typ in ['PLUS', 'MINUS']:  # SimpleExpression = ["+"|"-"] term
            res = compile_expression(env, e.e_list[1])
            res.append(("UNARY", e.e_list[0].val))
            for i in range(2, len(e.e_list), 2):
                res += compile_expression(env, e.e_list[i + 1])
                res.append(("BINOP", e.e_list[i].val))
            return res
        else:  # # SimpleExpression = term { ("+"|"-"|"OR") term}
            res = compile_expression(env, e.e_list[0])
            res += compile_expression(env, e.e_list[2])
            res.append(("BINOP", e.e_list[1].val))
            for i in range(3, len(e.e_list), 2):
                res += compile_expression(env, e.e_list[i + 1])
                res.append(("BINOP", e.e_list[i].val))
            return res
    elif e.typ == 'EXPR':  # expression = SimpleExpression [("=" | "#" | "<" | "<=" | ">" | ">=") SimpleExpression].
        if len(e.expr_list) > 1:
            res = []
            a = compile_expression(env, e.expr_list[0])
            b = compile_expression(env, e.expr_list[2])
            r = e.expr_list[1].val
            if r == '<' or r == '>=':
                # a - b < 0, a - b >= 0
                res += a
                res += b
                res.append(('BINOP', '-'))
            elif r == '>' or r == '<=':
                res += b
                res += a
                res.append(('BINOP', '-'))
            elif r == '=' or r == '#':
                res += a
                res += b
                res.append(('BINOP', 'XOR'))
            else:
                raise SyntaxError(f"Unknown BINOP: {r}")
            res.append(('RELOP', r))
            return res
        else:
            return compile_expression(env, e.expr_list[0])
    raise RuntimeError(f"Unknown expr: {e}")


proc_tab = {}
main_ptr = 0


def optimize_int_const(text):
    done = False
    while not done:
        done = True
        for i in range(2, len(text)):
            op3 = text[i]
            if op3[0] == 'BINOP':
                op1 = text[i - 2]
                if op1[0] != 'CONST':
                    continue
                op2 = text[i - 1]
                if op2[0] != 'CONST':
                    continue
                head = text[:i - 2]
                if op3[1] == '+':
                    head.append(('CONST', op1[1] + op2[1]))
                elif op3[1] == '-':
                    head.append(('CONST', op1[1] - op2[1]))
                elif op3[1] == '*':
                    head.append(('CONST', op1[1] * op2[1]))
                elif op3[1] == 'DIV':
                    head.append(('CONST', int(op1[1] / op2[1])))
                elif op3[1] == 'MOD':
                    head.append(('CONST', op1[1] % op2[1]))
                else:
                    raise SyntaxError(f'Unknown BINOP in optimizer {op3}')
                head += text[i + 1:]
                done = False
                text = head
                break
    return text


def convert_expressions(text):
    output = []
    acc_busy = False
    M2 = 2
    M1 = 1
    text_sz = len(text)
    for i in range(text_sz):
        t = text[i]
        if t[0] == 'CLOAD':
            if not acc_busy:
                output.append(('XTA', t[1], M2))
                acc_busy = True
            else:
                output.append(('XTS', t[1], M2))
        elif t[0] == 'VLOAD':
            if not acc_busy:
                if len(output) > 0:
                    o = output[-1]
                    if o[0] == 'ATX' and t[1] == o[1] and o[2] == M1:
                        pass
                    else:
                        output.append(('XTA', t[1], M1))
                else:
                    output.append(('XTA', t[1], M1))
                acc_busy = True
            else:
                output.append(('XTS', t[1], M1))
        elif t[0] == 'VSTOR':
            if not acc_busy:
                raise SyntaxError(f"Стек пустой")
            acc_busy = False
            output.append(('ATX', t[1], M1))
        elif acc_busy and t[0] in ['SYSCALL', 'CALL']:
            output.append(('ATX', 0, 15))
            if t[0] == 'SYSCALL':
                output.append(('*77', system_procs[t[1]]['sys_num'], 0))
            elif t[0] == 'CALL':
                # save M1
                output.append(('ITA', 1, 0))
                output.append(('ATX', 0, 15))
                # set M1 = SP - 1
                output.append(('MTJ', 1, 15))
                output.append(('UTM', -1, 1))
                # call
                output.append(('VJM', t[1], 14))
            else:
                output.append(t)
            acc_busy = False
        elif t[0] == 'BINOP':
            if output[-1][0] in ['XTA', 'XTS']:
                p = output.pop()
                if t[1] == '+':
                    output.append(('A+X', p[1], p[2]))
                if t[1] == '-':
                    output.append(('A-X', p[1], p[2]))
                if t[1] == '*':
                    output.append(('A*X', p[1], p[2]))
                if t[1] == 'DIV':
                    output.append(('A/X', p[1], p[2]))
            elif output[-1][0] in ['A+X', 'A-X', 'A*X', 'A/X', 'X-A']:
                if t[1] == '-':
                    output.append(('X-A', 0, 15))
                else:
                    raise SyntaxError(f"Unreachable: {t} {output[-1]}")
            else:
                output.append(t)
        elif t[0] == 'ALLOC':
            output.append(('UTM', t[1], 15))
        elif t[0] == 'DEALLOC':
            output.append(('UTM', -t[1], 15))
        elif t[0] == 'SYSCALL':
            output.append(('*77', system_procs[t[1]]['sys_num'], 0))
        elif t[0] == 'CALL':
            # save M1
            output.append(('ITA', 1, 0))
            output.append(('ATX', 0, 15))
            # set M1 = SP - 1
            output.append(('MTJ', 1, 15))
            output.append(('UTM', -1, 1))
            # call
            output.append(('VJM', t[1], 14))
        elif t[0] == 'STOP':
            output.append(('STOP', int(t[1]), 0))
        elif t[0] == 'ENTER':
            # save return address M14
            output.append(('ITA', 14, 0))
            output.append(('ATX', 0, 15))
        elif t[0] == 'LEAVE':
            # get return address to M14
            output.append(('XTA', 0, 15))
            output.append(('ATI', 14, 0))
        elif t[0] == 'RETURN':
            # restore M1 address
            output.append(('XTA', 0, 15))
            output.append(('ATI', 1, 0))
            output.append(('UJ', 0, 14))
        elif t[0] == 'BR_ZERO':
            o = output.pop()
            print(o)
            if o[1] == '>':
                output.append(('UZA', t[1], 0))
            elif o[1] == '<=':
                output.append(('U1A', t[1], 0))
            elif o[1] == '<':
                output.append(('UZA', t[1], 0))
            elif o[1] == '>=':
                output.append(('U1A', t[1], 0))
            elif o[1] == '=':
                output.append(('U1A', t[1], 0))
            elif o[1] == '#':
                output.append(('UZA', t[1], 0))
            acc_busy = False
        else:
            output.append(t)

    return output


def convert_to_besm(text):
    done = False
    while not done:
        done = True
        l = len(text)
        for i in range(l):
            if text[i][0] == 'ALLOC':
                text[i] = ('UTM', text[i][1], 15)
                done = False
                break
            elif text[i][0] == 'DEALLOC':
                text[i] = ('UTM', -text[i][1], 15)
                done = False
                break
            elif text[i][0] == 'VLOAD':
                addr = text[i][1]
                text.pop(i)
                text.insert(i, ('XTA', addr, 1))
                text.insert(i + 1, ('ATX', 0, 15))
                done = False
                break
            elif text[i][0] == 'VSTOR':
                addr = text[i][1]
                text.pop(i)
                text.insert(i, ('XTA', 0, 15))
                text.insert(i + 1, ('ATX', addr, 1))
                done = False
                break
            elif text[i][0] == 'CLOAD':
                addr = text[i][1]
                text.pop(i)
                text.insert(i, ('XTA', addr, 2))
                text.insert(i + 1, ('ATX', 0, 15))
                done = False
                break
            elif text[i][0] == 'SYSCALL':
                text[i] = ('*77', system_procs[text[i][1]]['sys_num'], 0)
                done = False
                break
            elif text[i][0] == 'STOP':
                text[i] = ('STOP', int(text[i][1]), 0)
            elif text[i][0] == 'CALL':
                t = text[i]
                text.pop(i)
                # save M1
                text.insert(i, ('ITA', 1, 0))
                text.insert(i + 1, ('ATX', 0, 15))
                # set M1 = SP - 1
                text.insert(i + 2, ('MTJ', 1, 15))
                text.insert(i + 3, ('UTM', -1, 1))
                # call
                text.insert(i + 4, ('VJM', t[1], 14))
                done = False
                break
            elif text[i][0] == 'ENTER':
                t = text[i]
                text.pop(i)
                # save return address M14
                text.insert(i, ('ITA', 14, 0))
                text.insert(i + 1, ('ATX', 0, 15))
                done = False
                break
            elif text[i][0] == 'LEAVE':
                t = text[i]
                text.pop(i)
                # get return address to M14
                text.insert(i, ('XTA', 0, 15))
                text.insert(i + 1, ('ATI', 14, 0))
                done = False
                break
            elif text[i][0] == 'RETURN':
                t = text[i]
                text.pop(i)
                # restore M1 address
                text.insert(i, ('XTA', 0, 15))
                text.insert(i + 1, ('ATI', 1, 0))
                text.insert(i + 2, ('UJ', 0, 14))
                done = False
                break
            elif text[i][0] == 'RELOP':
                r = text.pop(i)
                b = text.pop(i)
                if r[1] == '>':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('X-A', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('UZA', b[1], 0))
                elif r[1] == '<=':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('X-A', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('U1A', b[1], 0))
                elif r[1] == '<':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A-X', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('UZA', b[1], 0))
                elif r[1] == '>=':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A-X', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('U1A', b[1], 0))
                elif r[1] == '=':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('AEX', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('U1A', b[1], 0))
                elif r[1] == '#':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('AEX', -1, 15))
                    text.insert(i + 2, ('ATX', -2, 15))
                    text.insert(i + 3, ('UTM', -2, 15))
                    text.insert(i + 4, ('UZA', b[1], 0))
                else:
                    raise RuntimeError(f"Unknown RELOP {r}")
                done = False
                break
            elif text[i][0] == 'BINOP':
                b = text.pop(i)
                if b[1] == '-':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A-X', -1, 15))
                elif b[1] == '+':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A+X', -1, 15))
                elif b[1] == '*':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A*X', -1, 15))
                elif b[1] == 'DIV':
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A/X', -1, 15))
                elif b[1] == 'MOD':
                    # fantasy instruction
                    text.insert(i, ('XTA', -2, 15))
                    text.insert(i + 1, ('A%X', -1, 15))
                else:
                    raise SyntaxError(f"Unknown BINOP: {b}")
                text.insert(i + 2, ('ATX', -2, 15))
                text.insert(i + 3, ('UTM', -1, 15))
                done = False
                break

    print()
    # pprint.pp(text)
    return text


def compile_module(ast):
    global proc_tab, c_mem, pc, text, label_tab, expressions
    if ast.typ != 'MODULE':
        raise "Module required"
    env = [{'vars': {}, 'args': {}}]
    v_size, vars = compile_decls(env, ast.decls)

    main_name = ast.name + "_main"
    emit(('LABEL', main_name))
    if v_size > 0:
        emit(('ALLOC', v_size))
    compile_statements(env, ast.st_seq)
    env.pop()

    emit(('STOP', '12345'))

    # move constants from expressions to const_tab
    for i in range(len(text)):
        if text[i][0] == 'CONST':
            if text[i][1] in c_tab:
                text[i] = ('CLOAD', c_tab[text[i][1]]['offset'])
            else:
                c_mem.append(text[i][1])
                c_tab[text[i][1]] = {'offset': len(c_mem) - 1, 'val': text[i][1]}
                text[i] = ('CLOAD', c_tab[text[i][1]]['offset'])
    emit(('LABEL', 'const_table'))
    for c in c_tab:
        emit(('WORD', c_tab[c]['val']))

    for i in range(v_size):
        emit(('WORD', 0))
    emit(('LABEL', 'locals_base'))

    emit(('LABEL', 'stack_base'))
    if main_name in proc_tab:
        print(f"Модуль {ast.name} не может содержать процедуру с именем `{main_name}`")
        sys.exit(1)

    pprint.pp(text)
    # do optimisations on IR code
    # text = optimize(text)

    # pprint.pprint(text)
    # convert IR to BESM-6 instructions
    crt0 = []
    crt0.append(('VTM', 'locals_base', 1))  # M1 - locals base
    crt0.append(('VTM', 'stack_base', 15))  # M15 - stack base
    crt0.append(('VTM', 'const_table', 2))  # M2 - constant base
    crt0.append(('UJ', main_name, 0))

    text = crt0 + text
    # text = convert_to_besm(text)
    text = convert_expressions(text)

    # resolve labels
    pc = 0
    text_wo_labels = []
    for i in range(len(text)):
        cmd = text[i]
        if cmd[0] == 'LABEL':
            label_tab[cmd[1]] = pc
        else:
            text_wo_labels.append(text[i])
            pc += 1

    text = text_wo_labels

    # replace branch labels with addresses from label table
    for i in range(len(text)):
        cmd = text[i]
        if cmd[0] in ['BR', 'BR_ZERO', 'CALL', 'UJ', 'VTM', 'VJM', 'UZA', 'U1A']:
            if cmd[1] in label_tab:
                t = 0
                if len(cmd) == 3:
                    t = cmd[2]
                text[i] = (cmd[0], label_tab[cmd[1]], t)
            elif isinstance(cmd[1], int):
                continue
            else:
                raise SyntaxError(f'Переход на неизвестную метку {cmd}')

    for p in proc_tab:
        pp = proc_tab[p]
        pp['offset'] = label_tab[p]
        proc_tab[p] = pp
    proc_tab[main_name] = {'offset': label_tab[main_name]}

    return {'name': ast.name, 'main': main_name, 'c_tab': c_tab, 'vars': vars,
            'v_size': v_size, 'p_text': text, 'c_mem': c_mem,
            'proc_tab': proc_tab}
