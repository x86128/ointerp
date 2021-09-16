# Oberon-0 interpreter written in Python

Минимальный набросок интерпретатора языка Оберон-0 из книги Compiler Construction созданный для того что понять на практике как строятся нисходящие парсеры для LL(1) грамматик

Структура учебной грамматики из книги такова, что не позволяет в условиях циклов(или оператора IF) вызывать процедуры, т.к. возврат значений возможен только через параметры процедур.

Реализован **только парсер**, практически без проверок ошибок. Выдает не всегда адекватне сообщения об ошибках :)

Создан минимальный pretty printer для AST.

Выхлоп для тестового примера выглядит примерно так:

```
MODULE Samples
   TYPES:
     []
   PROCEDURES:
     Multiply is:
       TYPES:
         []
       VARS:
         x,y,z, of  INTEGER
       TEXT
         CALL OpenInput
         CALL_P ReadInt (x , )
         CALL_P ReadInt (y , )
         z := 0
         WHILE x 0 > DO
           TEXT
             IF x 2 MOD 1 =
               THEN
                 TEXT
                   z := z y +
             y := 2 y *
             x := x 2 DIV
         CALL_P WriteInt (x , 4 , )
         CALL_P WriteInt (y , 4 , )
         CALL_P WriteInt (z , 6 , )
         CALL WriteLn
     Divide is:
       CONSTS:
         a = 50
       TYPES:
         []
       VARS:
         x,y,r,q,w, of  INTEGER
       TEXT
         CALL OpenInput
         CALL_P ReadInt (x , )
         CALL_P ReadInt (y , )
         r := x
         q := 0
         w := y
         WHILE w r <= DO
           TEXT
             w := 2 w *
         WHILE w y > DO
           TEXT
             q := 2 q *
             w := w 2 DIV
             IF w r <=
               THEN
                 TEXT
                   r := r w -
                   q := q 1 +
               ELSIF_BLOCK
                 ELSIF q 10 <
                   TEXT
                     q := 6
                 ELSE
                   TEXT
                     q := 5
         CALL_P WriteInt (x , 4 , )
         CALL_P WriteInt (y , 4 , )
         CALL_P WriteInt (q , 4 , )
         CALL_P WriteInt (r , 4 , )
         CALL WriteLn
     Sum is:
       TYPES:
         []
       VARS:
         n,s, of  INTEGER
       TEXT
         CALL OpenInput
         s := 0
         WHILE eot ~ DO
           TEXT
             CALL_P ReadInt (n , )
             CALL_P WriteInt (n , 4 , )
             s := s n +
         CALL_P WriteInt (s , 6 , )
         CALL WriteLn
         IF w r <
           THEN
             TEXT
               a := b
           ELSE
             TEXT
               c := d
```
