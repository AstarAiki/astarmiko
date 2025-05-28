YAML файл следующего формата:

Router1:
  device_type: cisco_ios
  ip: some_ip_1
Router2:
  device_type: huawei
  ip: some_ip_2
Switch1:
  device_type: huaweivrrp
  ip: some_ip_3
Switch2:
  device_type: cisco_ios
  ip: some_ip_4
LEVEL:
  Router1: R
  Router2: R
  Switch1: L3
  Switch2: L2
SEGMENT:
  Router1: SEG A
  Router2: SEG B
  Switch1: SEG C
  Switch2: SEG D


где:
  device_type - тип устройства как определено в netmiko
  ip - ip адрес этого устройства
  LEVEL - маршрутизатор, L2 или L3 коммутатор, от уровня зависит имеет ли смысл выполнять запрос arp таблицы (R), таблицы MAC адресов (L2) или и того и другого (L3) - да мало ли еще зачем вы можете использовать в логике ваших программ
  SEGMENT:
  схема нашей сети можно представить как 
  
  ![[SegmentSCHEMA.png]]
  это  разные кольца ВОЛС, есть еще много дополнительных каналов по РРЛ, спутникам, ВЧ,  но в моих программах управления (Putty + SupperPutty) оборудование разбито по каталогам SEG A ..... SEG I, на сервере, где хранятся бэкапы конфигов оборудования созданы каталоги с такими же именами
  
  Вобщем SEGMENT - это любое понятное вам разбиение вашей сети на какие то сегменты
