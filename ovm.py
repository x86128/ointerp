import sys


def writeint(stack):
    print(stack.pop())


system_procs = {'writeint': writeint}


def exec_text(frame_stack, const_stack, data_stack, module):
    pc = 0
    text = module['text']
    # fill labels with addresses
    labels = dict()
    for i, v in enumerate(text):
        if v[0] == 'LABEL':
            labels[v[1]] = i
    # exec instructions
    while pc < len(text):
        cmd = text[pc]
        pc_next = pc + 1
        op = cmd[0]
        if op == 'STOP':
            print(f'STOP at {pc}')
            break
        elif op == 'CONST':
            data_stack.append(cmd[1])
        elif op == 'UNARY':
            if cmd[1] == '-':
                data_stack.append(-data_stack.pop())
            elif cmd[1] == '+':
                pass
            else:
                print('Unknown unary OP', cmd[1])
                break
        elif op == 'BINOP':
            if cmd[1] == '+':
                t = data_stack.pop()
                t = data_stack.pop() + t
                data_stack.append(t)
            elif cmd[1] == '*':
                t = data_stack.pop()
                t = data_stack.pop() * t
                data_stack.append(t)
            elif cmd[1] == 'mod':
                t = data_stack.pop()
                t = data_stack.pop() % t
                data_stack.append(t)
            elif cmd[1] == 'div':
                t = data_stack.pop()
                t = int(data_stack.pop() / t)
                data_stack.append(t)
            elif cmd[1] == '-':
                t = data_stack.pop()
                t = data_stack.pop() - t
                data_stack.append(t)
            else:
                print('Unknown BINOP', cmd)
                break
        elif op == 'CALL':
            if cmd[1] in system_procs:
                system_procs[cmd[1]](data_stack)
            elif cmd[1] in module['decls']['procs']:
                proc = module['decls']['procs'][cmd[1]]
                frame_stack.append(proc['decls']['vars'])
                const_stack.append(proc['decls']['consts'])
                exec_text(frame_stack, const_stack, data_stack, proc)
            else:
                print('Undefined procedure', cmd[1])
                break
        elif op == 'STOR':
            found = False
            for env in frame_stack[::-1]:
                if cmd[1] in env:
                    env[cmd[1]] = (data_stack.pop(), env[cmd[1]][1])
                    found = True
            if not found:
                print(f'Variable {cmd[1]} undefined')
                break
        elif op == 'LOAD':
            found = False
            for env in frame_stack[::-1]:
                if cmd[1] in env:
                    data_stack.append(env[cmd[1]][0])
                    found = True
            if not found:
                for env in const_stack[::-1]:
                    if cmd[1] in env:
                        data_stack.append(env[cmd[1]])
                        found = True
            if not found:
                print(f'Variable or constant: {cmd[1]} undefined')
                break
        elif op == 'RELOP':
            if cmd[1] == '>':
                t = data_stack.pop()
                if data_stack.pop() > t:
                    data_stack.append(1)
                else:
                    data_stack.append(0)
            elif cmd[1] == '<':
                t = data_stack.pop()
                if data_stack.pop() < t:
                    data_stack.append(1)
                else:
                    data_stack.append(0)
            elif cmd[1] == '#':
                t = data_stack.pop()
                if data_stack.pop() != t:
                    data_stack.append(1)
                else:
                    data_stack.append(0)
            elif cmd[1] == '=':
                t = data_stack.pop()
                if data_stack.pop() == t:
                    data_stack.append(1)
                else:
                    data_stack.append(0)
            else:
                print('Unknown RELOP', cmd[1])
        elif op == 'BR_ZERO':
            if not data_stack.pop():
                pc_next = labels[cmd[1]]
        elif op == 'BR':
            pc_next = labels[cmd[1]]
        elif op == 'LABEL':
            labels[cmd[1]] = pc + 1
        else:
            print('Unknown opcode:', cmd)
            break
        pc = pc_next


def run_code(module):
    exec_text([module['decls']['vars']], [module['decls']['consts']], [], module)
