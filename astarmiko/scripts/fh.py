#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
import yaml
import argparse
import asyncio
import os
import sys
from astarmiko.base import (
    Activka,
    port_name_normalize,
    convert_mac,
    is_ip_correct,
    nslookup,
    setup_config,
    snmp_get_oid,
)


def debug_logger(func):
    """
    Декоратор, который отслеживает все точки выхода из функции.
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"DEBUG: Вызов функции {func.__name__}")
        print(f"DEBUG: Входные аргументы - args: {args}, kwargs: {kwargs}")

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            print(f"DEBUG: Функция {func.__name__} вышла с исключением: {e}")
            raise

    return wrapper


message = dict()


def check_firewall(myactivka, ip, routerstart):
    """Functions check there is firewall between host with ip and other network

    Args:
        myacrivka (obj): object of class Activka from astarmiko
        ip (str):        ip of host to find
        routerstart (str): the name of the device that is the router
        for the host network

    Returns:
        output (list):
        list [mac address of host with defined ip, ip_address_of_firewall]
        False (bool):    if firewall is not answering
    """
    OID_INTF_INDX_STR = "1.3.6.1.2.1.4.21.1.2.{}"
    OID_INFF_MAC_STR = "1.3.6.1.2.1.4.35.1.4.{}.1.4.{}"
    community = "PFV3a2Nq"
    route = myactivka.getinfo(routerstart, "ip_route_tbl_by", ip)
    if route:
        if (
            myactivka.choose(routerstart, withoutname=True)["device_type"]
            == "cisco_ios"
        ):
            fw_ip, net_ip = route[0]
        else:
            net_ip, fw_ip = route[0]
        oid = OID_INTF_INDX_STR.format(net_ip)
        koid = asyncio.run(snmp_get_oid(fw_ip, community, oid))
        if len(koid) == 1 and isinstance(koid[0], str):
            intf_indx = koid[0].split(" = ")[1]
            oid = OID_INFF_MAC_STR.format(intf_indx, ip)
            mac = asyncio.run(snmp_get_oid(fw_ip, community, oid))
            mac = mac[0].split(" = ")[1]
            mac_str = ":".join(
                f"{(int(mac, 16) >> 8*i) & 0xff:02x}"
                for i in reversed(range(6))
            )
            output = [mac_str, fw_ip]
            return output
    else:
        return False


def get_host_description_ad(hostname):
    """
    Function get name of hostname and return it description from ADDS
    if it exist or string "not found" if not.
    """
    from func_for_ad import read_ad

    scope = "OU=Ноябрьские ЭС,DC=corp,DC=te,DC=ru"
    list_fieldes = ["cn", "description"]
    typeOfObject = "computer"
    comp = read_ad(list_fieldes, typeOfObject, scope, hostname)
    if comp:
        if comp[0]["description"]:
            out = comp[0]["description"][0]
        else:
            out = message[26]
    else:
        out = message[26]
    return out


def findbehindfw(myactivka, m):
    """Function return start port for serching host if it is behind firewall

    Args:
        myacrivka (obj): object of class Activka from astarmiko
        m[0] ip (str):       ip of host to find
        m[1] mac_str (str):  mac address of host with ip = args[0]
        m[2] (condt):        'FIREWALL'
        m[3] routerstart (str):
        the name of the device that is the router for the host network
        m[4] fw_ip (str):    ip address of firewall

    Returns:
        port[0] (str): port where to start look up
    """

    if myactivka.levels[m[3]] != "R":
        # if routertostart is L3 swith lookup in his mac addres table
        # by router IP
        port = myactivka.getinfo(m[3], "mac_addr_tbl_by", m[1])
        output = [port[0], "THESAME"]
    else:
        # if routertostart is R lookup in his mac addres table by firewall IP
        out = myactivka.getinfo(m[3], "arp_by", m[4])
        output = out[0]
        # output = [fw_ip, fw_mac, port_where_this_mac_is_lit']
    return output


def findchain(myactivka, m, hostname=False):
    """
    Function get object Activka and mac address and return
    name of switch, port, IP and hostname if possible where
    host with that mac
    """
    end = []
    i = 0
    mac_to_find = m[1]
    correct_ip = m[0]
    if hostname and os.name == "nt":
        description = get_host_description_ad(hostname)
        return_text = [
            message[20].format(
                hostname, correct_ip, mac_to_find, "\n", m[3], m[2],
                "\n", description
            )
        ]
    else:
        return_text = [message[21].format(correct_ip, mac_to_find, m[3], m[2])]
    print(return_text[0])
    # теперь нам необходимо узнать  тип активки ‘R’ - маршрутизатор
    # ‘L3’ - L3 коммутатор или ‘CH’ checkpoint это необходимо чтобы понять
    # где начинать поиск по таблице MAC адресов (на роутере бессмысленно,
    # надо добраться до первого коммутатора в цепочке
    # проверяем, не светится ли искомый нами MAC на Ether-Channel
    # интерфейсе, если да, нам необходимо получить имена интерфейсов
    # в него входящих, так как и cdp и lldp оперируют физическими
    # интерфейсами
    match = re.search(r"(Eth-Trunk|Po)(\d+)", m[2])
    if match:
        m[2] = str(
            myactivka.getinfo(m[3], "ethchannel_member",
                                match.group(2))[0][0][0]
            )
        m[2] = port_name_normalize(m[2])
        # если стартовая точка - роутер, ищем первый на пути коммутатор,
        # если L3 коммутатор - начнем поиск с него
    if myactivka.levels[m[3]] == "R":
        sw = myactivka.getinfo(m[3], "neighbor_by_port", m[2])
    else:
        sw = m[3]
    # и в бесконечном цикле идем по цепочке коммутаторов,
    # пока не найдем последний, к которому подключен хост

    while True:
        match = re.search(r"([-a-zA-Z0-9]+)(\.\S+)", sw)
        if match:
            sw = match.group(1)
        end.append(sw)
        i += 1
        mac_to_find = convert_mac(
            mac_to_find, myactivka.choose(sw, withoutname=True)["device_type"]
        )
        port = myactivka.getinfo(sw, "mac_addr_tbl_by", mac_to_find)
        # port = [имя порта, Status] где Status = True если к порту
        # подключен 1 MAC или если больше то это MAC IP телефона и
        # Status = False если дальше светится много MACов
        print(message[22].format(sw, port[0]))
        return_text.append(message[22].format(sw, port[0]))
        if not port[1]:
            next_neighbor = myactivka.getinfo(sw, "neighbor_by_port", port[0])
            # если за портом много устройств но ни по CDP ни по LLDP
            # соседа не получаем, значит там “тупой” неуправляемый коммутатор,
            # останавливаемся и сообщаем об этом
            if not next_neighbor:
                return_text.append(message[23].format(sw, port[0]))
                break
            else:
                sw = next_neighbor
        else:
            return_text.append(message[24].format(sw, port[0]))
            break
    print(return_text[-1])
    out = return_text + end
    return out


def findbymac(myactivka, mac_to_find, devices, ac):
    """
    Function get object Activka, mac address to find, segment of network
    and return name of switch, port, IP and hostname if possible where
    host with that mac
    """
    return_text = []
    routers = [
        rt
        for rt in devices
        if myactivka.levels[rt] == "R" or myactivka.levels[rt] == "L3"
    ]
    for rt in routers:
        m = find_router_to_start(myactivka, mac_to_find, is_mac=True,
                                 router=rt, ac=ac)
        if m:
            hostname = nslookup(m[0], reverse=False)
            out = findchain(myactivka, m, hostname)
            if out[-1]:
                return out[0]
    switches = [
        sw
        for sw in devices
        if myactivka.levels[sw] == "L2" or myactivka.levels[sw] == "L3"
    ]
    print(message[16].format(mac_to_find))
    for sw in switches:
        print(message[17].format(sw))
        mac_to_find = convert_mac(
            mac_to_find, myactivka.choose(sw, withoutname=True)["device_type"]
        )
        port = myactivka.getinfo(sw, "mac_address_table", mac_to_find)
        if port:
            return_text.append(message[18].format(mac_to_find, sw, port[0]))
            print(return_text[0])
            return return_text
    return_text.append(message[19].format(mac_to_find))
    print(return_text[0])
    return return_text


def find_router_to_start(myactivka, ip, is_mac=False, router=None, ac=None):
    """
    Function get IP (or MAC if is_mac=True) address and lookup routers
    as start point
    and return list(IP,MAC, port_where_was _found, name_of_router)
    """
    # ищу 3-й октет адреса и по нему из файла networks_byip.yaml
    # получаю имя роутера (стартовой точки поиска)
    if not is_mac:
        ia = re.compile(
            r"(?P<OCT1>\d+)\.(?P<OCT2>\d+)\.(?P<OCT3>\d+)\.(?P<OCT4>\d+)",
            re.ASCII)
        m = ia.search(ip)
        oct3 = m.group("OCT3")
        with open(ac.localpath + "networks_byip.yaml") as f:
            nbi = yaml.safe_load(f)
        if oct3 in nbi.keys():
            routerstart = nbi[oct3]
        else:
            return False
    # и через ARP таблицу ищу MAC для этого IP
    else:
        routerstart = router
    out = myactivka.getinfo(routerstart, "arp_by", ip)
    if is_mac:
        print_string = message[14].format(ip, routerstart)
    else:
        print_string = message[15].format(routerstart, ip)

    if not out:
        print_string = message[27].format(ip)
        print(print_string)
        fw_data = check_firewall(myactivka, ip, routerstart)
        if not fw_data:
            print_string = message[28]
            print(print_string)
            sys.exit()
        else:
            output = [ip, fw_data[0], "FIREWALL", routerstart, fw_data[1]]
            return output
    # в возвращаемый список [IP, MAC, PORT] добавляю еще имя роутера,
    # find_mac_by_ip() сделал универсальной,
    # но имя роутера мне дальше необходимо
    output = out[0]
    output.append(routerstart)
    return output


def ip_routine(myactivka, ip, ac):
    if not re.match(r"[,|\.]", ip):
        ipreal = nslookup(ip)
        if not ipreal:
            print(message[10].format(ip))
            quit()
        else:
            correct_ip = ipreal
        hostname = ip
    else:
        # а вдруг команду fh вызвали из буфера а адрес ввели при
        # русской раскладке и вместо “.” у вас “,” или просто ошиблись -
        # проверяем и возвращаем правильный IP
        correct_ip = is_ip_correct(ip)
        if not correct_ip:
            print(message[11])
            quit()
        # а если ввели IP не плохо бы узнать DNS имя
        hostname = nslookup(correct_ip, reverse=False)
        if not hostname:
            hostname = message[12]
    # по IP получаем список  m = [IP, MAC, порт на котором светится,
    # имя активки]
    m = find_router_to_start(myactivka, correct_ip, ac=ac)
    # m = [ip, mac_of_this_ip, port_where_mac_is_lit, routerstart]
    if not m:
        if correct_ip in myactivka.routerbyip.keys():
            device2 = myactivka.routerbyip[correct_ip]
            int_conf = myactivka.list_of_all_ip_intf(device2.lower())
            name_mask = [
                [line[0], line[2]] for line in int_conf
                if line[1] == correct_ip
            ]
            print_string = message[25].format(
                correct_ip, name_mask[0][1], name_mask[0][0], device2.lower()
            )
            print(print_string)
            quit()
        print(message[13])
        quit()
    m[3] = m[3].lower()
    if m[2] == "FIREWALL":
        # if firewall m = [ip, mac_of_this_ip, 'FIREWALL', routerstart,
        # ip_add_of_firewall]
        bh_fw = findbehindfw(myactivka, m)
        if bh_fw:
            if bh_fw[1] == "THE_SAME":
                m[2] = bh_fw[0]
            else:
                m[2] = bh_fw[2]
    out = findchain(myactivka, m, hostname)
    return out


def mac_routine(myactivka, ip):
    segment_list = list(myactivka.segment.values())
    sl = sorted(set(segment_list))
    sl_len = [x for x in range(0, len(sl))]
    print(message[7])
    for a, b in zip(sl_len, sl):
        print(a, b)
    seg = input(message[8])
    seg_name = sl[int(seg)]
    seg_devices = [dev.lower() for dev, value in myactivka.segment.items()
                   if value == seg_name]
    out = findbymac(myactivka, ip, seg_devices)
    if not out:
        print(message[9].format(seg_name))
        return False
    else:
        return out[0]


def findhost(argv=None):
    """
    If file with this python script named fh.py it look up fh.yml
    configuration file in same directory
    """
    global message
    file_path = os.path.abspath(sys.argv[0])
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    base_dir = os.path.dirname(file_path)
    path_to_cfg = os.path.abspath(os.path.join(base_dir, f"{file_name}.yml"))
    setup_config(path_to_cfg)
    from astarmiko.base import ac

    file = ac.localpath + "messages_" + ac.language + ".yaml"
    with open(file, encoding="utf8") as f:
        message = yaml.safe_load(f)
    parser = argparse.ArgumentParser(description=message[2])
    parser.add_argument(dest="ip", help=message[3])
    parser.add_argument("-s", dest="seg", default="RPB", help=message[4])
    parser.add_argument("-r", dest="repeat", default=False, type=bool,
                        help=message[5])
    parser.add_argument("-f", dest="file_to_save", help=message[6])
    args = parser.parse_args()

    # если ввели fh без аргументов попросит ввести адрес или имя хоста

    try:
        ip = args.ip
    except IndexError:
        ip = ""
        while not ip:
            ip = input(message[0])

    print(message[1])
    myactivka = Activka("activka_byname.yaml")
    is_mac = convert_mac(ip, "cisco_ios")
    repeat_out = []
    while True:
        if not is_mac:
            out = ip_routine(myactivka, ip, ac)
            repeat_out.append(out)
        else:
            out = mac_routine(myactivka, is_mac)
            repeat_out.append(out)
        if not args.repeat:
            if args.file_to_save:
                repeat_out = "\n".join(repeat_out[0])
                with open(args.file_to_save, "w") as f:
                    f.writelines(repeat_out)
                break
            else:
                break
        else:
            ip = input(message[0])
            if ip == "q":
                if args.file_to_save:
                    repeat_out = "\n".join(repeat_out[0])
                    with open(args.file_to_save, "w") as f:
                        f.writelines(repeat_out)
                    break
            is_mac = convert_mac(ip, "cisco_ios")


def main():
    import sys
    from .fh import findhost

    findhost(sys.argv[1:])


"""
    #читаем настройки лога из конфигурационного файла
if isinstance(ac.looging, bool):
    if ac.logging:
        enable_console = True
    elif isinstance(ac.logfile, str):
        if ac.logging and ac.logfile:
            log_file = ac.logfile
if isinstance(ac.log_format_str, str):
    if ac.log_format_str:
        format_str = ac.log_format_str
"""
