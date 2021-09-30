# Oberon-0 interpreter written in Python

Минимальный набросок интерпретатора языка Оберон-0 из книги Compiler Construction созданный для того что понять на практике как строятся нисходящие парсеры для LL(1) грамматик

Структура учебной грамматики из книги такова, что не позволяет в условиях циклов(или оператора IF) вызывать процедуры, т.к. возврат значений возможен только через параметры процедур.

Реализован **только парсер**, практически без проверок ошибок. Выдает не всегда адекватне сообщения об ошибках :)

Для тестового примера:

```pascal
MODULE Samples;

procedure gcd(a,b : integer);
    var t : integer;
begin
    while b > 0 do
        t := b;
        b := a mod b;
        a := t
    end;

    writeint(a)
end gcd;

begin
    gcd(15+6*2-(5 div 8),3)

END Samples.
```

Интерпретатор генерирует такой код (абстрактной виртуальной машины):

```
MODULE Samples
{'consts': {},
 'procs': {'gcd': {'args': [('a', 'integer'), ('b', 'integer')],
                   'decls': {'consts': {},
                             'procs': {},
                             'vars': {'a': (0, 'integer'),
                                      'b': (0, 'integer'),
                                      't': (0, 'integer')}},
                   'text': [('STOR', 'b'),
                            ('STOR', 'a'),
                            ('LABEL', 'L0'),
                            ('LOAD', 'b'),
                            ('CONST', '0'),
                            ('RELOP', '>'),
                            ('BR_NONZERO', 'L1'),
                            ('LOAD', 'b'),
                            ('STOR', 't'),
                            ('LOAD', 'a'),
                            ('LOAD', 'b'),
                            ('BINOP', 'mod'),
                            ('STOR', 'b'),
                            ('LOAD', 't'),
                            ('STOR', 'a'),
                            ('BR', 'L0'),
                            ('LABEL', 'L1'),
                            ('LOAD', 'a'),
                            ('CALL', 'writeint')]}},
 'vars': {}}
{'text': [('CONST', '15'),
          ('CONST', '6'),
          ('CONST', '2'),
          ('BINOP', '*'),
          ('BINOP', '+'),
          ('CONST', '5'),
          ('CONST', '8'),
          ('BINOP', 'div'),
          ('BINOP', '-'),
          ('CONST', '3'),
          ('CALL', 'gcd')]}
```
