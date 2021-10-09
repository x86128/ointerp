import pprint
import sys


# system internal procedures
def writeint():
    global d_mem, sp
    sp -= 1
    print(d_mem[sp])


# halt magic numbers
PASS = 12345
FAIL = 54321


def halt():
    global d_mem, sp
    sp -= 1
    code = d_mem[sp]
    print('Program halted with code:', code)
    if code == PASS:
        print('SUCCESS')
        sys.exit(0)
    elif code == FAIL:
        print('FAIL')
        sys.exit(1)
    sys.exit(code)


system_procs = {'writeint': writeint, 'halt': halt}


def exec_text(start_pc, env):
    global c_mem, d_mem, sp, bp, p_text, proc_tab
    pc = start_pc
    op_counter = 0
    # fill labels with addresses
    labels = dict()
    for i, v in enumerate(p_text):
        if v[0] == 'LABEL':
            labels[v[1]] = i
    # exec instructions
    while True:
        cmd = p_text[pc]
        pc_next = pc + 1
        op = cmd[0]
        if op == 'STOP':
            print(f'STOP at {pc}')
            break
        elif op_counter > 1000:
            print("Executed more then", op_counter, "instructions")
            break
        elif op == 'CONST':
            d_mem[sp] = cmd[1]
            sp += 1
        elif op == 'UNARY':
            if cmd[1] == '-':
                d_mem[sp - 1] = -d_mem[sp - 1]
            elif cmd[1] == '+':
                pass
            elif cmd[1] == '~':
                d_mem[sp - 1] = ~d_mem[sp - 1]
            else:
                raise RuntimeError(f'Unknown unary OP {cmd[1]}')
        elif op == 'BINOP' or op == 'RELOP':
            sp -= 1
            if cmd[1] == '+':
                d_mem[sp - 1] = d_mem[sp - 1] + d_mem[sp]
            elif cmd[1] == '*':
                d_mem[sp - 1] = d_mem[sp - 1] * d_mem[sp]
            elif cmd[1] == 'MOD':
                d_mem[sp - 1] = d_mem[sp - 1] % d_mem[sp]
            elif cmd[1] == 'DIV':
                d_mem[sp - 1] = int(d_mem[sp - 1] / d_mem[sp])
            elif cmd[1] == '-':
                d_mem[sp - 1] = d_mem[sp - 1] - d_mem[sp]
            elif cmd[1] == 'OR':
                d_mem[sp - 1] = d_mem[sp - 1] or d_mem[sp]
            elif cmd[1] == '&':
                d_mem[sp - 1] = d_mem[sp - 1] and d_mem[sp]
            elif cmd[1] == '>':
                d_mem[sp - 1] = d_mem[sp - 1] > d_mem[sp]
            elif cmd[1] == '>=':
                d_mem[sp - 1] = d_mem[sp - 1] >= d_mem[sp]
            elif cmd[1] == '<':
                d_mem[sp - 1] = d_mem[sp - 1] < d_mem[sp]
            elif cmd[1] == '<=':
                d_mem[sp - 1] = d_mem[sp - 1] <= d_mem[sp]
            elif cmd[1] == '#':
                d_mem[sp - 1] = d_mem[sp - 1] != d_mem[sp]
            elif cmd[1] == '=':
                d_mem[sp - 1] = d_mem[sp - 1] == d_mem[sp]
            else:
                raise RuntimeError(f'Unknown OP: {cmd}')
        elif op == 'ALLOC':
            d_mem[sp] = bp
            bp = sp - 1
            sp += cmd[1]
        elif op == 'DEALLOC':
            sp -= cmd[1]
            bp = d_mem[sp]
        elif op == 'SYSCALL':
            if cmd[1] in system_procs:
                system_procs[cmd[1]]()
            else:
                raise RuntimeError(f'Undefined system procedure {cmd[1]}')
        elif op == 'CALL':
            if cmd[1] in proc_tab:
                d_mem[sp] = pc + 1
                sp += 1
                proc = proc_tab[cmd[1]]
                pc_next = proc['offset']
            else:
                raise RuntimeError(f'Undefined procedure {cmd[1]}')
        elif op == 'STOR':
            found = False
            scope = env[-1]['vars']
            if cmd[1] in scope:
                sp -= 1
                d_mem[bp + scope[cmd[1]]['offset']] = d_mem[sp]
                found = True
            if not found:
                raise RuntimeError(f'Variable {cmd[1]} undefined')
        elif op == 'ALOAD':
            d_mem[sp] = d_mem[bp - cmd[1]]
            sp += 1
        elif op == 'LOAD':
            d_mem[sp] = d_mem[bp + cmd[1]]
            sp += 1
        elif op == 'CLOAD':
            d_mem[sp] = c_mem[cmd[1]]
            sp += 1
        elif op == 'BR_ZERO':
            sp -= 1
            if not d_mem[sp]:
                pc_next = labels[cmd[1]]
        elif op == 'BR':
            pc_next = labels[cmd[1]]
        elif op == 'RETURN':
            sp -= 1
            pc_next = d_mem[sp]
        elif op == 'LABEL':
            pass
        else:
            raise RuntimeError(f'Unknown opcode: {cmd}')
        pc = pc_next


c_mem = []
proc_tab = {}
p_text = []
env = []
bp = 0
d_mem = [0] * 65536
sp = 0


def run_code(module):
    global c_mem, proc_tab, p_text, env, d_mem, bp, sp

    c_mem = module['c_mem']
    proc_tab = module['proc_tab']
    p_text = module['p_text']

    main_proc = module['main']

    start_pc = proc_tab[main_proc]['offset']
    env.append({'consts': module['consts'], 'vars': module['vars']})
    sp = module['v_size']  # выделяем место для локальных переменных модуля
    bp = sp - 1

    exec_text(start_pc, env)
