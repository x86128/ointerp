import pprint


def writeint(stack):
    print(stack.pop())


system_procs = {'writeint': writeint}


def exec_text(frame_stack, data_stack, module):
    pc = 0
    pc_next = 0
    text = module['text']
    labels = dict()
    for i, v in enumerate(text):
        if v[0] == 'LABEL':
            labels[v[1]] = i
    while pc < len(text):
        cmd = text[pc]
        pc_next = pc + 1
        op = cmd[0]
        if op == 'STOP':
            print(f'STOP at {pc}')
            break
        elif op == 'CONST':
            data_stack.append(int(cmd[1]))
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
            else:
                print('Unknown BINOP', cmd)
        elif op == 'CALL':
            if cmd[1] in system_procs:
                system_procs[cmd[1]](data_stack)
            elif cmd[1] in module['decls']['procs']:
                proc = module['decls']['procs'][cmd[1]]
                frame_stack.append(proc['decls']['vars'])
                exec_text(frame_stack, data_stack, proc)
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
                print(f'Variable {cmd[1]} undefined')
                break
        elif op == 'RELOP':
            if cmd[1] == '>':
                t = data_stack.pop()
                if data_stack.pop() > t:
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
    exec_text([module['decls']['vars']], [], module)
