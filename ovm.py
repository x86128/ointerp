import pprint
import sys


# system internal procedures
def writeint():
    global d_mem, sp
    print(d_mem[sp - 1], end='')


def writeln():
    print()


def writespace():
    global d_mem, sp
    print(' ' * d_mem[sp - 1], end='')


# halt magic numbers
PASS = 12345
FAIL = 54321


def halt():
    global d_mem, sp
    code = d_mem[sp - 1]
    print('Program halted with code:', code)
    if code == PASS:
        print('SUCCESS')
        sys.exit(0)
    elif code == FAIL:
        print('FAIL')
        sys.exit(1)
    sys.exit(code)


system_procs = {'writeint': writeint,
                'writeln': writeln,
                'writespace': writespace,
                'halt': halt}


def exec_text(start_pc):
    global c_mem, d_mem, sp, bp, p_text, proc_tab, trace_enabled
    pc = start_pc

    op_counter = 0
    d_mem_max = 0
    # exec instructions
    while True:
        cmd = p_text[pc]
        pc_next = pc + 1
        op = cmd[0]
        if op == 'STOP':
            print(f'STOP at {pc}, CYCLES={op_counter}, max stack size: {d_mem_max}')
            code = int(cmd[1])
            if code == PASS:
                print('SUCCESS')
            elif code == FAIL:
                print('FAIL')
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
            sp += cmd[1]
        elif op == 'DEALLOC':
            sp -= cmd[1]
        elif op == 'SYSCALL':
            if cmd[1] in system_procs:
                if cmd[1] == 'halt':
                    print(f'HALT at {pc}, CYCLES={op_counter}, max stack size: {d_mem_max}')
                system_procs[cmd[1]]()
            else:
                raise RuntimeError(f'Undefined system procedure {cmd[1]}')
        elif op == 'CALL':
            d_mem[sp] = bp
            d_mem[sp + 1] = pc + 1
            bp = sp
            sp += 2
            # proc = proc_tab[cmd[1]]
            pc_next = cmd[1]
        elif op == 'RETURN':
            pc_next = d_mem[sp - 1]
            bp = d_mem[sp - 2]
            sp -= 2
        elif op == 'ADR_LOAD':
            d_mem[sp] = bp + cmd[1]
            sp += 1
        elif op == 'RLOAD':
            d_mem[sp] = d_mem[d_mem[bp + cmd[1]]]
            sp += 1
        elif op == 'RSTOR':
            sp -= 1
            d_mem[d_mem[bp + cmd[1]]] = d_mem[sp]
        elif op == 'VLOAD':
            d_mem[sp] = d_mem[bp + cmd[1]]
            sp += 1
        elif op == 'VSTOR':
            sp -= 1
            d_mem[bp + cmd[1]] = d_mem[sp]
        elif op == 'CLOAD':
            d_mem[sp] = c_mem[cmd[1]]
            sp += 1
        elif op == 'BR_ZERO':
            sp -= 1
            if not d_mem[sp]:
                pc_next = cmd[1]
        elif op == 'BR':
            pc_next = cmd[1]
        elif op == 'LABEL':
            pass
        else:
            raise RuntimeError(f'Unknown opcode: {cmd}')
        if trace_enabled:
            print(f'OP={cmd} PC={pc} BP={bp} SP={sp} D_MEM={d_mem[:sp]}')
        pc = pc_next

        op_counter += 1
        if d_mem_max < sp:
            d_mem_max = sp


c_mem = []
c_tab = {}
proc_tab = {}
p_text = []
bp = -99
d_mem = [0] * 65536
sp = 0
trace_enabled = False


def run_code(module, trace=False):
    global c_mem, c_tab, proc_tab, p_text, d_mem, bp, sp, trace_enabled

    trace_enabled = trace
    c_mem = module['c_mem']
    c_tab = module['c_tab']
    proc_tab = module['proc_tab']
    p_text = module['p_text']

    main_proc = module['main']

    start_pc = proc_tab[main_proc]['offset']
    bp = module['v_size']
    exec_text(start_pc)
