# Oberon-0 interpreter written in Python

Минимальный набросок интерпретатора языка Оберон-0 из книги Compiler Construction созданный для того что понять на практике как строятся нисходящие парсеры для LL(1) грамматик

Структура учебной грамматики из книги такова, что не позволяет в условиях циклов(или оператора IF) вызывать процедуры, т.к. возврат значений возможен только через параметры процедур.

Реализован парсер, практически без проверок ошибок, транслятор разобранной грамматики в код виртуальной машины (или промежуточный IR-код) и транслятор IR-кода в код МЭСМ-6.

Поддерживаются VAR-аргументы процедур. В целях упрощения ввдена псевод команда `A%X` которой в реальной МЭСМ-6 нет.

Для тестового примера:

```pascal
MODULE Samples;
const
    pass = 12345;
    fail = 54321;

var
    t : integer;

procedure gcd(a,b : integer; var res : integer);
begin
    while b > 0 do
        res := b;
        b := a mod b;
        a := res
    end
end gcd;

begin
    gcd(27+25*3-(10 div 5),15, t);
    writeint(t); writeln;
    if t = 5 then
        halt(pass)
    else
        halt(fail)
    end

END Samples.
```

Интерпретатор генерирует такой код (абстрактной виртуальной машины):

```
[('LABEL', 'gcd'),
 ('ENTER', 'gcd'),
 ('LABEL', 'L0'),
 ('CONST', 0),
 ('VLOAD', -2, 'b'),
 ('BINOP', '-'),
 ('RELOP', '>'),
 ('BR_ZERO', 'L1'),
 ('VLOAD', -2, 'b'),
 ('RSTOR', -1, 'res'),
 ('VLOAD', -3, 'a'),
 ('VLOAD', -2, 'b'),
 ('BINOP', 'MOD'),
 ('VSTOR', -2, 'b'),
 ('RLOAD', -1, 'res'),
 ('VSTOR', -3, 'a'),
 ('BR', 'L0'),
 ('LABEL', 'L1'),
 ('LEAVE', 'gcd'),
 ('RETURN', 'gcd'),
 ('LABEL', 'Samples_main'),
 ('ALLOC', 1),
 ('CONST', 27),
 ('CONST', 25),
 ('CONST', 3),
 ('BINOP', '*'),
 ('BINOP', '+'),
 ('CONST', 10),
 ('CONST', 5),
 ('BINOP', 'DIV'),
 ('BINOP', '-'),
 ('CONST', 15),
 ('ADR_LOAD', -1, 't'),
 ('CALL', 'gcd'),
 ('DEALLOC', 3),
 ('VLOAD', -1, 't'),
 ('SYSCALL', 'writeint'),
 ('DEALLOC', 1),
 ('SYSCALL', 'writeln'),
 ('VLOAD', -1, 't'),
 ('CONST', 5),
 ('BINOP', 'XOR'),
 ('RELOP', '='),
 ('BR_ZERO', 'L2'),
 ('CLOAD', 0, 'pass'),
 ('SYSCALL', 'halt'),
 ('DEALLOC', 1),
 ('BR', 'L3'),
 ('LABEL', 'L2'),
 ('CLOAD', 1, 'fail'),
 ('SYSCALL', 'halt'),
 ('DEALLOC', 1),
 ('LABEL', 'L3'),
 ('STOP', '12345')]
```

Далее компилятор производит вычисление константных выражений и формирование таблицы констант.
Затем выполняет трансляцию кода виртуальной машины в код МЭСМ-6:

```
TEXT:
00000:              VTM      63        ,M1
00001:              VTM      63        ,M15
00002:              VTM      56        ,M2
00003:              UJ       24        
00004:          gcd ITA      14        
00005:              ATX      0         ,M15
00006:              XTA      2         ,M2
00007:              A-X      -2        ,M1
00008:              UZA      19        
00009:              XTA      -2        ,M1
00010:              WTC      -1        ,M1
00011:              ATX      0         
00012:              XTA      -3        ,M1
00013:              A%X      -2        ,M1
00014:              ATX      -2        ,M1
00015:              WTC      -1        ,M1
00016:              XTA      0         
00017:              ATX      -3        ,M1
00018:              UJ       6         
00019:              XTA      0         ,M15
00020:              ATI      14        
00021:              XTA      0         ,M15
00022:              ATI      1         
00023:              UJ       0         ,M14
00024: Samples_main UTM      1         ,M15
00025:              XTA      3         ,M2
00026:              XTS      4         ,M2
00027:              ATX      0         ,M15
00028:              MTJ      3         ,M1
00029:              UTM      -1        ,M3
00030:              ITA      3         
00031:              ATX      0         ,M15
00032:              ITA      1         
00033:              ATX      0         ,M15
00034:              MTJ      1         ,M15
00035:              UTM      -1        ,M1
00036:              VJM      4         ,M14
00037:              UTM      -3        ,M15
00038:              XTA      -1        ,M1
00039:              ATX      0         ,M15
00040:              *77      0         
00041:              UTM      -1        ,M15
00042:              *77      2         
00043:              XTA      -1        ,M1
00044:              AEX      5         ,M2
00045:              U1A      51        
00046:              XTA      0         ,M2
00047:              ATX      0         ,M15
00048:              *77      3         
00049:              UTM      -1        ,M15
00050:              UJ       55        
00051:              XTA      1         ,M2
00052:              ATX      0         ,M15
00053:              *77      3         
00054:              UTM      -1        ,M15
00055:              STOP     12345     
00056:              WORD     12345     
00057:              WORD     54321     
00058:              WORD     0         
00059:              WORD     100       
00060:              WORD     15        
00061:              WORD     5         
00062:              WORD     0         

CONSTANT TABLE:
00000:     pass    12345
00001:     fail    54321
00002:        0        0
00003:      100      100
00004:       15       15
00005:        5        5

PROCEDURE TABLE
         gcd: 4
Samples_main: 24
```

Результат работы на целочисленной МЭСМ-6:

```
5
SYS STOP: 12345
```
