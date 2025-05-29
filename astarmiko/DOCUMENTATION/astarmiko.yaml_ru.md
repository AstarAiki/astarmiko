
Пример конфигурационного файла для скриптов, использующих модуль **astarmiko**

##### localpath: /home/mypython/astarmiko/
базовый путь относительно которого строятся пути до папок им файлов, используемых в astarmiko. Предполагалось, что другие пути будут относительными, но опыт использования показал, что иногда удобнее textFSM шаблоны или справочники (в формате YAML) удобнее хранить в несвязанных местах

##### учетные данные имя пользователя и пароль
стандартные учетные данные, используемые для подключения к оборудованию по ssh, обычно это tacacs или radius учетка
user: gAAAAABn7NmekcfGhIjrwJRXL6v0QRm3SAz4dz-GSm16gu7dpBIyw5omo-A1d3-LjaNwPwTN6Vg-1jzW5_0aPeFbwe0p6TZtsQ==
password: gAAAAABn7Nme6Kb4cI-sqsyApPFm2JsqLtp-
2Hds7Jov8MY50XBx3s1VKOIXgA3FKjIa_FjpqkbdDsG6bWwzobwhw9SOrSwHOA==
	первоначально, при создании конфигурационного файла записываете имя пользователя и пароль открытым текстом, а потом шифруете, используя CLI интерфейс модуля **[astarconf](https://github.com/astaraiki/astarconf)**
##### список первых октетов mac адресов IP телефонов
phone_mac:
- 805e
- 001a
Если у вас в сети используются IP телефоны, чтобы понять что порт на коммутаторе это конечный порт для компьютера подключенного через телефон, надо понимать какие mac адреса, которые "светятся" на порту относятся к телефонам. Так как количество брендов IP телефонов в сети не бесконечно, и у всех телефонов одного бренда mac адрес начинается одинаково, создается такой список
##### templpath: /home/mypython/astarmiko/TEMPLATES/
Путь, где хранятся textFSM шаблоны

##### dict_of_cmd: /home/mypython/astarmiko/YAML/commands.yaml
Путь к файлу commands.yaml, в котором находятся стандартные, чаще всего используемые команды. Именно для них всегда имеются шаблоны textFSM

##### logging: True
Включение/отключение логов

##### logfile: /home/mypython/astarmiko.log
Расположение лог файла

##### loglevel: DEBUG
Уровень лога

##### log_format_str:
здесь можно указать формат строки лога, если хотите отличный от дефолтного

##### add_account:
В любых правилах бывают исключения. У меня есть оборудование, где не получается настроить tacacs или какие то другие причины и приходится использовать локальные или другие учетки. Все они перечисляются здесь. модуль подключения к оборудованию из ***astarmiko*** при невозможности подключиться со стандартной учеткой, попробует ниже перечисленные и только потом вернет сообщение об ошибке
Учетные данные точно так же шифруются с помощью модуля **[astarconf](https://github.com/astaraiki/astarconf)**
- password: gAAAAABoB1JEZiWkUNiaXAs-ItSPTUrPyBCP4jyZBLWF0P9SGahWSD5ZWNK9QFxCbkPCnPFdqmigVQx8vmrMAbkz09mJRNH7HA==
  user: gAAAAABoB1JEHSOPYy3-0SAUhGgzlRnXTf56-1frsFs9d2CRYuwqRtfAQRgZYF0ohraFCN74IaR1P3Zdr1BONnNZVAa8d9Yyvw==
- password: gAAAAABoB1JEUFWn9R_rx-MaZ7QFyPiVK5mh4VgHZmpiAcTLV8EZ3QM99gK8ZVkjAqSXnOjGGOGSL3SU0e85Pcc9f33BQ-Q4og==
  user: gAAAAABoB1JE-WO-0EEjVG7-mmK1fSMGEzRaCdVxW1WW81ZBSFzxkYmMT1PvWevC7RI9Ey6b-xiv4hGLXq0wFrWifTYwDNRxgg==
