import pprint
import sys

system_procs = {'writeint': {'v_size': 0, 'arg_sz': 1},
                'writespace': {'v_size': 0, 'arg_sz': 1},
                'writeln': {'v_size': 0, 'arg_sz': 0},
                'halt': {'v_size': 0, 'arg_sz': 1}}


def compile_procs(env, procs):
    global proc_ptr, proc_tab, program_mem
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
        text = []
        env[-1]['proc'] = proc.name
        env[-1]['proc_ptr'] = proc_ptr
        env[-1]['args'] = arg_list
        proc_tab[proc.name] = {'offset': proc_ptr, "args": arg_list, 'arg_sz': len(arg_list),
                               'vars': w_env,
                               'v_size': w_offset}

        text += compile_statements(env, proc.body.st_seq)
        text.append(('RETURN', ''))

        program_mem += text
        proc_ptr += len(text)
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


def compile_while(env, st):
    global label_counter
    label = label_counter
    label_counter += 2
    text = [('LABEL', f'L{label}')]
    text += compile_expression(env, st.expr)
    text.append(('BR_ZERO', f'L{label + 1}'))
    text += compile_statements(env, st.st_seq)
    text.append(('BR', f'L{label}'))
    text.append(('LABEL', f'L{label + 1}'))
    return text


def compile_repeat(env, st):
    global label_counter
    label = label_counter
    label_counter += 1
    text = [('LABEL', f'L{label}')]
    text += compile_statements(env, st.st_seq)
    text += compile_expression(env, st.expr)
    text.append(('BR_ZERO', f'L{label}'))
    return text


def compile_if(env, st):
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
    text += compile_expression(env, st.expr)
    if len(st.elsif_block) > 0:
        text.append(('BR_ZERO', f'L{elsif_label}'))
    else:
        text.append(('BR_ZERO', f'L{exit_label}'))
    text += compile_statements(env, st.then_block)
    if len(st.else_block) > 0 or len(st.elsif_block) > 0:
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSIF blocks if any
    for i, elsifb in enumerate(st.elsif_block):
        text.append(('LABEL', f'L{elsif_label}'))
        text += compile_expression(env, elsifb.expr)
        text.append(('BR_ZERO', f'L{elsif_label + i + 1}'))
        text += compile_statements(env, elsifb.st_seq)
        text.append(('BR', f'L{exit_label}'))
    # compiling ELSE block if any
    if len(st.else_block) > 0:
        text.append(('LABEL', f'L{else_label}'))
        text += compile_statements(env, st.else_block[0])
    text.append(('LABEL', f'L{exit_label}'))
    return text


def compile_args(env, ap, proc_name):
    global proc_tab
    text = []
    if proc_name in system_procs:
        for i, arg in enumerate(ap.arg_list):
            text += compile_expression(env, arg)
    else:
        arg_list = [''] * len(ap.arg_list)
        for arg in proc_tab[proc_name]['args']:
            arg_list[proc_tab[proc_name]['args'][arg]['offset']] = arg
        arg_list = arg_list[::-1]
        for i, arg in enumerate(ap.arg_list):
            if proc_tab[proc_name]['args'][arg_list[i]]['var']:
                t = compile_expression(env, arg)
                text.append(('ADR_LOAD', t[-1][1], t[-1][2]))
            else:
                text += compile_expression(env, arg)
    return text


def compile_statements(env, st_seq):
    global system_procs
    text = []
    if not st_seq:
        return text

    for i, st in enumerate(st_seq.st_seq):
        if st.typ == 'WHILE':
            text += compile_while(env, st)
        elif st.typ == 'REPEAT':
            text += compile_repeat(env, st)
        elif st.typ == 'CALL':
            if st.name in system_procs:
                if system_procs[st.name]['arg_sz'] > 0:
                    raise SyntaxError(f'В процедуру {st.name} не переданы параметры')
                text.append(('SYSCALL', st.name))
            else:
                if proc_tab[st.name]['arg_sz'] > 0:
                    raise SyntaxError(f'В процедуру {st.name} не переданы параметры')
                text.append(('CALL', st.name))
        elif st.typ == 'CALL_P':
            if st.name in system_procs:
                if len(st.args.arg_list) != system_procs[st.name]['arg_sz']:
                    raise SyntaxError(f'Процедура {st.name} ожидает {system_procs[st.name]["arg_sz"]} параметров')
            elif st.name in proc_tab:
                if len(st.args.arg_list) != proc_tab[st.name]['arg_sz']:
                    raise SyntaxError(f'Процедура {st.name} ожидает {proc_tab[st.name]["arg_sz"]} параметров')
            text += compile_args(env, st.args, st.name)
            if st.name in system_procs:
                v_sz = system_procs[st.name]['v_size']
                arg_sz = system_procs[st.name]['arg_sz']
            else:
                v_sz = proc_tab[st.name]['v_size']
                arg_sz = proc_tab[st.name]['arg_sz']
                p_ptr = proc_tab[st.name]['offset']
            if v_sz > 0:
                text.append(('ALLOC', v_sz))
            if st.name in system_procs:
                text.append(('SYSCALL', st.name))
            else:
                text.append(('CALL', p_ptr, st.name))
            if v_sz + arg_sz > 0:
                text.append(('DEALLOC', v_sz + arg_sz))
        elif st.typ == 'ASSIGN':
            for t in compile_expression(env, st.expr):
                text.append(t)
            v_offset = -len(env[-1]['vars'])
            if st.name in env[-1]['vars']:
                v_offset += env[-1]['vars'][st.name]['offset']
                text.append(('VSTOR', v_offset, st.name))
            elif st.name in env[-1]['args']:
                v_offset -= (1 + env[-1]['args'][st.name]['offset'])
                if env[-1]['args'][st.name]['var']:
                    text.append(('RSTOR', v_offset, st.name))
                else:
                    text.append(('VSTOR', v_offset, st.name))
            else:
                raise SystemError(f'Ошибка в строке {st.line}: Присваивание позволено только локальным переменным')
        elif st.typ == 'IF_STAT':
            text += compile_if(env, st)
        else:
            raise SyntaxError(f'Unknown stat: {st}')
    return text


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
            res = compile_expression(env, e.expr_list[0])
            res += compile_expression(env, e.expr_list[2])
            res.append(('RELOP', e.expr_list[1].val))
            return res
        else:
            return compile_expression(env, e.expr_list[0])
    raise RuntimeError(f"Unknown expr: {e}")


program_mem = []
proc_tab = {}
proc_ptr = 0


def compile_module(ast):
    global proc_tab, proc_ptr, program_mem, c_mem
    if ast.typ != 'MODULE':
        raise "Module required"
    env = [{'vars': {}, 'args': {}}]
    v_size, vars = compile_decls(env, ast.decls)
    text = compile_statements(env, ast.st_seq)
    env.pop()
    text.append(('STOP', '12345'))
    if proc_ptr + len(text) > 65536:
        print(f"При компиляции модуля {ast.name} вышли за пределы памяти:", proc_ptr + len(text))
    if v_size > 0:
        program_mem.append(('ALLOC', v_size))
    program_mem += text
    main_name = ast.name + "_main"
    if main_name in proc_tab:
        print(f"Модуль {ast.name} не может содержать процедуру с именем `{main_name}`")
        sys.exit(1)
    proc_tab[main_name] = {'offset': proc_ptr}
    proc_ptr += len(text)
    return {'name': ast.name, 'main': main_name, 'c_tab': c_tab, 'vars': vars,
            'v_size': v_size, 'p_text': program_mem, 'c_mem': c_mem,
            'proc_tab': proc_tab}
