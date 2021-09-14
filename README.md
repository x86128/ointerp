# Oberon-0 interpreter written in Python

Минимальный набросок интерпретатора языка Оберон-0 из книги Compiler Construction созданный для того что понять на практике как строятся нисходящие парсеры для LL(1) грамматик

Структура учебной грамматики из книги такова, что не позволяет в условиях циклов(или оператора IF) вызывать процедуры, т.к. возврат значений возможен только через параметры процедур.

Реализован только парсер, практически без проверок ошибок. Выдает не всегда адекватне сообщения об ошибках :)

Создан минимальный pretty printer для AST.

Выхлоп для тестового примера выглядит примерно так:

```
MODULE Samples
   CONSTS:
     []
   TYPES:
     []
   PROCEDURES:
     Multiply is:
       CONSTS:
         []
       TYPES:
         []
       VARS:
         x,y,z, of  INTEGER
       TEXT
         ('CALL', ('IDENT', 'OpenInput'))
         ('CALL_P', ('IDENT', 'ReadInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])])])]))
         ('CALL_P', ('IDENT', 'ReadInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])])]))
         ('ASSIGN', ('IDENT', 'z'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '0'))])])]))
         WHILE ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])]), ('GTR', '>'), ('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '0'))])])]) DO
           ('IF_STAT', ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x')), ('MOD', 'MOD'), ('FACTOR', ('INTEGER', '2'))])]), ('EQL', '='), ('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '1'))])])]), 'THEN', ('STAT_SEQ', [('ASSIGN', ('IDENT', 'z'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'z'))]), ('PLUS', '+'), ('TERM', [('FACTOR', ('IDENT', 'y'))])])]))]))
           ('ASSIGN', ('IDENT', 'y'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '2')), ('TIMES', '*'), ('FACTOR', ('IDENT', 'y'))])])]))
           ('ASSIGN', ('IDENT', 'x'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x')), ('DIV', 'DIV'), ('FACTOR', ('INTEGER', '2'))])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'z'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '6'))])])])]))
         ('CALL', ('IDENT', 'WriteLn'))
     Divide is:
       CONSTS:
         [[('IDENT', 'a'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '50'))])])])]]
       TYPES:
         []
       VARS:
         x,y,r,q,w, of  INTEGER
       TEXT
         ('CALL', ('IDENT', 'OpenInput'))
         ('CALL_P', ('IDENT', 'ReadInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])])])]))
         ('CALL_P', ('IDENT', 'ReadInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])])]))
         ('ASSIGN', ('IDENT', 'r'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])])]))
         ('ASSIGN', ('IDENT', 'q'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '0'))])])]))
         ('ASSIGN', ('IDENT', 'w'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])]))
         WHILE ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'w'))])]), ('LEQ', '<='), ('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'r'))])])]) DO
           ('ASSIGN', ('IDENT', 'w'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '2')), ('TIMES', '*'), ('FACTOR', ('IDENT', 'w'))])])]))
         WHILE ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'w'))])]), ('GTR', '>'), ('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])]) DO
           ('ASSIGN', ('IDENT', 'q'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '2')), ('TIMES', '*'), ('FACTOR', ('IDENT', 'q'))])])]))
           ('ASSIGN', ('IDENT', 'w'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'w')), ('DIV', 'DIV'), ('FACTOR', ('INTEGER', '2'))])])]))
           ('IF_STAT', ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'w'))])]), ('LEQ', '<='), ('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'r'))])])]), 'THEN', ('STAT_SEQ', [('ASSIGN', ('IDENT', 'r'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'r'))]), ('MINUS', '-'), ('TERM', [('FACTOR', ('IDENT', 'w'))])])])), ('ASSIGN', ('IDENT', 'q'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'q'))]), ('PLUS', '+'), ('TERM', [('FACTOR', ('INTEGER', '1'))])])]))]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'x'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'y'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'q'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'r'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
         ('CALL', ('IDENT', 'WriteLn'))
     Sum is:
       CONSTS:
         []
       TYPES:
         []
       VARS:
         n,s, of  INTEGER
       TEXT
         ('CALL', ('IDENT', 'OpenInput'))
         ('ASSIGN', ('IDENT', 's'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '0'))])])]))
         WHILE ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('NOT', ('FACTOR', ('IDENT', 'eot'))))])])]) DO
           ('CALL_P', ('IDENT', 'ReadInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'n'))])])])]))
           ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 'n'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '4'))])])])]))
           ('ASSIGN', ('IDENT', 's'), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 's'))]), ('PLUS', '+'), ('TERM', [('FACTOR', ('IDENT', 'n'))])])]))
         ('CALL_P', ('IDENT', 'WriteInt'), ('ACTUAL_PARAMETERS', [('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('IDENT', 's'))])])]), ('EXPR', [('SEXPR', [('TERM', [('FACTOR', ('INTEGER', '6'))])])])]))
         ('CALL', ('IDENT', 'WriteLn'))

```
