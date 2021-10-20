import pprint
import sys

from olexer import TokenStream
from oparser import parse_module
from ocompiler import compile_module
from ovm import run_code
from mvm import MCPU


def print_listing(module):
    m_main = module['main']
    name_max = max([len(t) for t in module['proc_tab']])
    labels = {module['proc_tab'][p]['offset']: p for p in module['proc_tab']}
    for i, t in enumerate(module['p_text']):
        if t[0] == 'LABEL':
            labels[i] = t[1]
    print("TEXT:")
    for i, t in enumerate(module['p_text']):
        print(f'{i:>05}:', end='')
        if i in labels:
            print(f'{labels[i]:>{name_max + 1}} ', end='')
        else:
            print(f'{" " * (name_max + 1)} ', end='')
        if len(t) > 2 and t[2] != 0:
            print(f'{t[0]:<8} {t[1]:<10},M{t[2]}', end='')
        else:
            print(f'{t[0]:<8} {t[1]:<10}', end='')
        print()
    print("\nCONSTANT TABLE:")
    consts = {module['c_tab'][c]['offset']: c for c in module['c_tab']}
    for i, t in enumerate(consts):
        print(f'{i:>05}: {consts[t]:>8} {module["c_tab"][consts[t]]["val"]:>8}')

    print('\nPROCEDURE TABLE')
    for p in module['proc_tab']:
        print(f'{p:>12}: {module["proc_tab"][p]["offset"]}')
    print()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        source = TokenStream(sys.argv[1])
    else:
        source = TokenStream('sample/arith.o0')
    syn_tree = parse_module(source)
    if source.errors:
        print(source.errors[0])
    else:
        module = compile_module(syn_tree)
        print_listing(module)
        cpu = MCPU(module['p_text'])
        cpu.run()
        # run_code(module)
