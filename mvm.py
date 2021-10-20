import sys


class MCPU:
    def __init__(self, text):
        self.pc = 0
        self.m = [0] * 16
        self.mem = text
        self.mem += [(0, 0, 0)] * (32768-len(text))
        self.c = 0
        self.acc = 0
        self.mode = 'none'
        self.tracing = False

    def get_m(self, i):
        if (i & 0xf) == 0:
            return 0
        return self.m[i & 0xf]

    def set_m(self, i, v):
        if (i & 0xf) != 0:
            if self.tracing:
                print(f'M{i}={v}')
            self.m[i & 0xf] = v & 0x7fff

    def set_acc(self, v):
        self.acc = v
        if self.tracing:
            print('ACC=', self.acc)

    def run(self):
        running = True

        while running:
            # fetch
            cmd = self.mem[self.pc]
            pc_next = self.pc + 1

            # decode
            op = cmd[0]
            addr = cmd[1]
            mod = cmd[2]

            vaddr = (addr + self.c) & 0x7fff
            if self.c != 0:
                self.c = 0
            uaddr = (self.get_m(mod) + vaddr) & 0x7fff

            stack = False
            if mod == 15:
                if vaddr == 0:
                    stack = True
                elif op == 'STI' and uaddr == 15:
                    stack = True

            omega = True
            if self.mode == 'log':
                omega = self.acc != 0
            elif self.mode == 'mul':
                omega = abs(self.acc) < 0x7fffffff  # don't care
            elif self.mode == 'add':
                omega = self.acc < 0

            # execute
            if self.tracing:
                print(cmd)
            if op == 'ATX':
                self.mem[uaddr] = ('WORD', self.acc, 0)
                if self.tracing:
                    print(f'MEM[{uaddr}]={self.acc}')
                if stack:
                    self.set_m(15, self.get_m(15) + 1)
            elif op == 'XTA':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                self.set_acc(self.mem[uaddr][1])
                self.mode = 'log'
            elif op == 'XTS':
                self.mem[self.get_m(15)] = ('WORD', self.acc, 0)
                self.set_m(15, self.get_m(15) + 1)
                uaddr = (self.get_m(mod) + vaddr) & 0x7fff
                self.set_acc(self.mem[uaddr][1])
                self.mode = 'log'
            elif op == 'STX':
                self.mem[uaddr] = ('WORD', self.acc, 0)
                self.set_m(15, self.get_m(15) - 1)
                self.set_acc(self.mem[self.get_m(15)][1])
            elif op == 'VTM':
                self.set_m(mod, vaddr)
            elif op == 'UTM':
                self.set_m(mod, uaddr)
            elif op == 'ITA':
                self.set_acc(self.get_m(uaddr))
                self.mode = 'log'
            elif op == 'UJ':
                pc_next = uaddr
            elif op == 'VJM':
                pc_next = vaddr
                self.set_m(mod, self.pc + 1)
            elif op == 'STOP':
                print(f'STOP at PC={self.pc} code={addr} ir={mod}')
                running = False
            elif op == 'UZA':
                if not omega:
                    pc_next = uaddr
            elif op == 'U1A':
                if omega:
                    pc_next = uaddr
            elif op == 'A+X':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(self.acc + x)
                self.mode = 'add'
            elif op == 'A-X':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(self.acc - x)
                self.mode = 'add'
            elif op == 'X-A':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(x - self.acc)
                self.mode = 'add'
            elif op == 'A*X':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(self.acc * x)
                self.mode = 'mul'
            elif op == 'A/X':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(int(self.acc / x))
                self.mode = 'mul'
            elif op == 'A%X':
                if stack:
                    self.set_m(15, self.get_m(15) - 1)
                    uaddr = (self.get_m(15) + vaddr) & 0x7fff
                x = self.mem[uaddr][1]
                self.set_acc(self.acc % x)
                self.mode = 'mul'
            elif op == 'MTJ':
                self.set_m(vaddr, self.get_m(mod))
            elif op == 'ATI':
                self.set_m(uaddr, self.acc)
            elif op == '*77':
                if addr == 0:
                    print(self.mem[self.get_m(15) - 1][1], end='')
                elif addr == 1:
                    print(' ' * self.mem[self.get_m(15) - 1][1], end='')
                elif addr == 2:
                    print()
                elif addr == 3:
                    print(f'SYS STOP: {self.mem[self.get_m(15) - 1][1]}')
                    sys.exit(0)
                else:
                    raise RuntimeError(f"Unknown extracode *77 op: {cmd}")
            else:
                raise RuntimeError(f'Unknown OP={cmd}')
            self.pc = pc_next
            if self.tracing:
                print(self.mem[35:45])
