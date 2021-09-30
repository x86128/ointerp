import pprint
from olexer import TokenStream
from oparser import parse_module
from ocompiler import compile_module

if __name__ == "__main__":
    source = TokenStream('sample/sample.o0')
    syn_tree = parse_module(source)
    if source.errors:
        print(source.errors[0])
    else:
        module = compile_module(syn_tree)
        pprint.pprint(module)

