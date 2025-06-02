import os
import yaml
import textfsm
import logging
import re
import time
import sys
from typing import Optional, Any, List, Dict, Union
from pysnmp.hlapi.v3arch.asyncio import (
        CommunityData,
        SnmpEngine,
        UdpTransportTarget,
        ObjectType,
        ObjectIdentity,
        ContextData,
        get_cmd,
        )

# from future.backports.test.pystone import TRUE
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

ac = ""  # Global object represent configuration attributes


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
            print(
                f"DEBUG: Функция {func.__name__} вернула (нормальный выход): "
                f"{result}"
            )
            return result
        except Exception as e:
            print(f"DEBUG: Функция {func.__name__} вышла с исключением: {e}")
            raise

    return wrapper


logger = logging.getLogger(__name__)
_DEFAULT_LOG_LEVEL = logging.WARNING
_DEFAULT_LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(module)s.%(funcName)s] -\
    %(message)s"
)


def setup_logging(
    level: int = _DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    format_str: str = _DEFAULT_LOG_FORMAT,
    enable_console: bool = True,
) -> None:
    """
    Logging settings for module.

    Args:
        level: Logging level (logging.DEBUG, logging.INFO и т.д.)
        log_file: Path to logging file (if None - don't write to file)
        format_str: Logging aormat
        enable_console: Enable output to console
    """
    # Delete all existing halders
    logger.handlers.clear()

    # Set log level
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format_str)

    # Tune output to console
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Tune writing to log file if enabled
    if log_file is not None:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def setup_config(path_to_conf):
    """Initialize conf object ac with attributes from path_to_conf

    Args:
        path_to_conf (str): full path to config file ( yaml, json, format)

    """
    from astarconf import Astarconf

    global ac
    ac = Astarconf(path_to_conf)
    try:
        dict_of_cmd = ac.dict_of_cmd
        with open(dict_of_cmd) as f:
            commands = yaml.safe_load(f)
        ac.commands = commands["commands"]
    except AttributeError:
        pass
    log_file = None
    format_str = _DEFAULT_LOG_FORMAT
    level = _DEFAULT_LOG_LEVEL
    enable_console = True
    if isinstance(ac.logging, bool):
        if ac.logging:
            enable_console = True
        elif isinstance(ac.logfile, str):
            if ac.logging and ac.logfile:
                log_file = ac.logfile
    if isinstance(ac.log_format_str, str):
        if ac.log_format_str:
            format_str = ac.log_format_str
    if isinstance(ac.loglevel, str):
        level = getattr(logging, ac.loglevel)
    setup_logging(
        level=level,
        log_file=log_file,
        format_str=format_str,
        enable_console=enable_console,
    )


async def snmp_get_oid(
    host: str,
    community: str,
    oid: str,
    port: int = 161,
    version: int = 2,
    prnerr: bool = False,
):
    """Function get OID's by SNMP from device without ssh access
       (like russian NGFW Kontinent)

    Args:
        host (str): ip address of NGFW
        community (str): community string for SNMP ver.2
        oid (str): oid in ASN.1 format you want to get
        port (int): port dor SNMP access, default 161
        version (int): version of SNMP, default is 2
        prnerr (bool): selector to print or not errors in stdout

    Returns:
        result (str): value of oid
    """

    if version == 1:
        snmp_engine = CommunityData(community, mpModel=0)
    else:
        snmp_engine = CommunityData(community, mpModel=1)
    snmpEngine = SnmpEngine()

    iterator = get_cmd(
        snmpEngine,
        snmp_engine,
        await UdpTransportTarget.create((host, port)),
        ContextData(),
        ObjectType(ObjectIdentity(oid)),
    )
    result = []
    errorIndication, errorStatus, errorIndex, varBinds = await iterator

    if prnerr:
        if errorIndication:
            print(errorIndication)

        elif errorStatus:
            print(
                "{} at {}".format(
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
                )
            )
    else:
        if errorIndication:
            result.append(errorIndication)
        elif errorStatus:
            result.append(
                "{} at {}".format(
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
                )
            )
            result.append(False)
        else:
            result.append(str(varBinds[0].prettyPrint()))
    return result


def ping_one_ip(ip_address):
    """Function get one ip address and return 0 if all is o'key
       or else error code

    Args:
        ip_address (str): ip address to ping

    Returns:
        return code of ping: 0 if alive other if not
    """

    import subprocess as sp

    if os.name == "nt":
        reply = sp.run(["ping", "-n", "3", ip_address], stdout=sp.DEVNULL)
    else:
        reply = sp.run(["ping", "-c", "3", "-n", ip_address],
                       stdout=sp.DEVNULL)

    return reply.returncode


def _try_connect(device, func, *args, **kwargs):
    """Internal function to handle connection attempts with availability check
    """

    def is_device_available(ip):
        """Check if device is reachable"""
        try:
            return ping_one_ip(ip) == 0
        except Exception as e:
            logger.warning(f"Ping check failed for {ip}: {str(e)}")
            return False

    def connect_with_credentials(device_params):
        if not is_device_available(device_params["ip"]):
            logger.warning(
                f"Device {device_params['host']} ({device_params['ip']}) "
                f"is unreachable"
            )
            return False

        try:
            start_msg = "Connecting to {}..."
            logger.info(start_msg.format(device_params["ip"]))

            with ConnectHandler(**device_params) as ssh:
                ssh.enable()
                return func(ssh, *args, **kwargs)

        except NetmikoTimeoutException as error:
            logger.warning(
                    f"Connection timeout to {device_params['ip']}: "
                    f"{error}"
                    )
            return False
        except NetmikoAuthenticationException as error:
            logger.warning(
                f"Authentication failed for "
                f"{device_params['username']}@{device_params['ip']}"
            )
            raise  # Re-raise to handle in outer function

    # First try with original credentials
    try:
        return connect_with_credentials(device)
    except NetmikoAuthenticationException:
        pass

    # Try additional accounts if available
    if hasattr(ac, "add_account"):
        for account in ac.add_account:
            try:
                new_device = device.copy()
                new_device["username"] = account["user"]
                new_device["password"] = account["password"]
                return connect_with_credentials(new_device)
            except NetmikoAuthenticationException:
                continue

    logger.error(f"All authentication attempts failed for {device['ip']}")
    return False


def send_config_by_one(device, commands):
    """The function connects via SSH (using netmiko) to ONE device and performs
     ONE command in configuration mode based on the arguments passed.

    Args:
        device (dict): dictionary in netmiko format for use with
        ConnectHandler(**device)
        commands (list or str): command in list ['some command']
        to send to device (if string - it converted to list

    Returns:
        tuple: (good_commands, failed_commands) where each is a dict
        with command:result pairs
    """
    if isinstance(commands, str):
        commands = commands.strip().split("\n")

    good = {}
    failed = {}
    errors_str = re.compile(
        r"Invalid input detected|"
        r"Incomplete command|"
        r"Ambiguous command|"
        r"Unrecognized command"
    )

    def execute_commands(ssh):
        for command in commands:
            result = ssh.send_config_set(command)
            if not errors_str.search(result):
                good[command] = result
            else:
                error_match = errors_str.search(result)
                error_msg = (
                        error_match.group()
                        if error_match
                        else "Unknown error"
                )
                logging.warning(
                    f"Command {command} raise error: "
                    f"{errors_str.search(result).group()} "
                    f"on device {device['ip']}"
                )
                failed[command] = result
        return (good, failed)

    return _try_connect(device, execute_commands)


def send_config_commands(device, commands):
    """The function connects via SSH (using netmiko) to ONE device and performs
    a list of commands in configuration mode based on the arguments passed.

    Args:
        device (dict): dictionary in netmiko format for use with
        ConnectHandler(**device)
        commands (list or str): command in list ['some command']
        to send to device (if string - it converted to list

    Returns:
        str: device output or False if connection failed
    """
    if isinstance(commands, str):
        commands = commands.strip().split("\n")

    def execute_commands(ssh):
        result = ssh.send_config_set(commands, delay_factor=20,
                                     cmd_verify=False)
        time.sleep(10)
        result += ssh.send_command_timing("write")
        return result

    return _try_connect(device, execute_commands)


def send_show_command(device, commands):
    """The function connects via SSH (using netmiko) to ONE device
    and executes the specified show (display) command.

    Args:
        device (dict): dictionary in netmiko format for use with
        ConnectHandler(**device)
        commands (str): command to send to device

    Returns:
        str: command output or False if connection failed
    """

    def execute_command(ssh):
        return ssh.send_command(commands)

    return _try_connect(device, execute_command)


def templatizator(*args, special=False):
    """Function convert console output to dict using textfsm template

    Args:
        args[0] (str): output from console of device
        args[1] (str):  1. the standard command itself in the form of
                        an abbreviation for which there is a textFSM template
                        or
                        2. any command, then a second positional parameter
                        is needed - the template file name and the special
                        variable must be set to True
        args[2] (str):  if special = False (by default) device type
                        in form of netmiko or 'nt' or 'posix' if args[0]
                        output from console of Windows or Posix systems
                        device_type (args[1] is abbreviated command from
                        ac.commands if special = True, args[1] is not
                        abbreviated command that one is name of file
                        with textFSM template, must be located
                        in directory defined by ac.templpath

    Returns:
        list of lists obtained using the corresponding textfsm template
    """
    if not special:
        if args[2] == "nt":
            tf = ac.templpath + "nt_" + args[1] + ".template"
        elif args[2] == "posix":
            tf = ac.templpath + "posix_" + args[1] + ".template"
        else:
            tf = ac.templpath + args[2] + "_" + args[1] + ".template"
    else:
        tf = ac.templpath + args[1]
    with open(tf) as tmpl:
        fsm = textfsm.TextFSM(tmpl)
        result = fsm.ParseText(args[0])
    return result


def port_name_normalize(port):
    """The function gets the port name and if it is abbreviated,
       returns the full name.
       It is actually necessary to bypass the Huawei hardware property
       to return the interface name as GE and require the input of Gi

    Args:
        port (str): name of port from device's console

    Returns:
        (str) correct long format of port name
    """
    portnorm = []
    m = re.search(r"(Eth-Trunk|Po|10GE|100GE|GE|Gi|XGE|Fa|Ser)(\S+)", port)
    if m:
        if m.group(1) == "Eth-Trunk" or m.group(1) == "Po":
            portnorm = f"{m.group(0)}"
            return portnorm
        else:
            if m.group(1)[0] == "1":
                if m.group(1)[2] == "0":
                    longname = "100GE"
                else:
                    longname = "10GE"
            if m.group(1)[0] == "G":
                longname = "GigabitEthernet"
            if m.group(1)[0] == "X":
                longname = "XGigabitEthernet"
            if m.group(1)[0] == "F":
                longname = "FastEthernet"
            if m.group(1)[0] == "S":
                longname = "Serial"
            portnorm = f"{longname}{m.group(2)}"
            return portnorm


def get_port_by_mac(device, mac):
    """Function searches for the port to which a device with mac address
       is connected

    Args:
        device (dict): dictionary in netmiko format for use with
        ConnectHandler(**device)

    Returns:
        a list of [Port,Status] where Status is True if  the destination port
        is edge port and False if there is another switch behind this port
        Port - out[2] (str): name of port
    """
    isEdgedPort = True

    command = (
            ac.commands["mac_addr_tbl_bymac"][device["device_type"]]
            .format(mac)
    )
    todo = send_show_command(device, command)
    out = templatizator(todo, "mac_address_table", device["device_type"])[0]
    out[2] = port_name_normalize(out[2])
    command = (
            ac.commands["mac_addr_tbl_byport"][device["device_type"]]
            .format(out[2])
    )
    todo = send_show_command(device, command)
    outwhole = templatizator(todo, "mac_address_table", device["device_type"])
    if len(outwhole) > 2:
        if (
            len(outwhole) == 3
        ):  # If the computer is switched on via IP phone,
            # 2 MAC in 2 VLANs are lit up
            for (
                mac
            ) in (
                ac.phone_mac
            ):  # All our phones have a MAC starting with 805e,
                # but there could be others.
                if mac in outwhole[2][0]:
                    return [out[2], isEdgedPort]
        else:
            isEdgedPort = False
    return [out[2], isEdgedPort]


def convert_mac(mac, device_type):
    """Function converts mac address string from any known formats to format
       device with device_type
       MAC can be in the form of 4 by 3 or 6 by 2
       separators are also different

    Args:
        mac (str): string of mac address
        device_type (str): string of device_type like in netmiko

    Returns:
        MAC string in the form accepted on this hardware
        with device_type = device_type

    """
    mac = mac.lower()
    trudelim, digit_by_group = ac.commands["mac_delimeters"][device_type]
    p4 = re.compile(
        r"(?P<oct1>[0-9a-fA-F]{4})[-|.|:]"
        r"(?P<oct2>[0-9a-fA-F]{4})[-|.|:]"
        r"(?P<oct3>[0-9a-fA-F]{4})",
        re.ASCII,
    )
    p6 = re.compile(
        (
            r"(?P<oct1>[0-9a-fA-F]{2})[-|.|:]"
            r"(?P<oct2>[0-9a-fA-F]{2})[-|.|:]"
            r"(?P<oct3>[0-9a-fA-F]{2})[-|.|:]"
            r"(?P<oct4>[0-9a-fA-F]{2})[-|.|:]"
            r"(?P<oct5>[0-9a-fA-F]{2})[-|.|:]"
            r"(?P<oct6>[0-9a-fA-F]{2})"
        ),
        re.ASCII,
    )
    m = p4.search(mac)
    if m:
        if digit_by_group == 4:
            trumac = f"{m.group(1)}{trudelim}{m.group(2)}{trudelim}"
            f"{m.group(3)}"
        else:
            trumac = f"{m.group(1)[0:2]}{trudelim}{m.group(1)[2:4]}{trudelim}"
            f"{m.group(2)[0:2]}{trudelim}{m.group(2)[2:4]}{trudelim}"
            f"{m.group(3)[0:2]}{trudelim}{m.group(3)[2:4]}"
    else:
        m = p6.search(mac)
        if m:
            if digit_by_group == 4:
                trumac = f"{m.group(1)}{m.group(2)}{trudelim}{m.group(3)}"
                f"{m.group(4)}{trudelim}{m.group(5)}{m.group(6)}"
            else:
                trumac = f"{m.group(1)}{trudelim}{m.group(2)}{trudelim}"
                f"{m.group(3)}{trudelim}{m.group(4)}{trudelim}{m.group(5)}"
                f"{trudelim}{m.group(6)}"
        else:
            return False
    return trumac


def is_ip_correct(ip):
    """Function checks  ip address fo correctness
        if there is standart error in russian layout when commas entered
        instead of dots correct this one

    Args:
        ip (str): string of ip address

    Returns:
        string of ip address or False if ip is not correct
    """
    if re.search(r"^(?:(?:^|\.)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4}$", ip):
        return ip
    else:
        if re.search(r"^(?:(?:^|\,)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4}$", ip):
            return re.sub(",", ".", ip)
        else:
            return False


def nslookup(hostname, reverse=True):
    """The function gets the host name and returns a list of its IP addresses.
        Or vice versa (reverse = True) finds the DNS name by IP address

    Args:
        hostname (str):  name or ip of host
        reverse (bool): selector of reverse lookup by ip (default) or dirrect
        lookup by name

    Returns:
        name of host
    """
    import socket
    import subprocess

    if reverse:
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip = False
        return ip
    else:
        if os.name == "nt":
            code = "cp1251"
        elif os.name == "posix":
            code = "utf_8"
        todo = subprocess.run(
            ["nslookup", hostname],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding=code,
        )
        name = templatizator(todo.stdout, "nslookup", os.name)
        if not name:
            return False
        return name[0][0]


def del_exeption(config):
    """Functions delete daily changeble string from device config
        example: configs from many cisco devices different day by day
        only by string with command 'ntp clock-period'
        it prevents us from knowing if the config has been changed

    Args:
        config (list): list of config lines from device

    Returns:
        config (list): list of config lines from device without exeption lines

    """
    to_lookup = ["ntp clock-period"]
    for i, line in enumerate(config):
        for tl in to_lookup:
            if tl in line:
                config.pop(i)
    return config


def check_identity(curr_config, last_backup):
    if curr_config == last_backup:
        return True
    else:
        return False


class Activka:
    """The class represents all our network devices - routers and switches"""

    def __init__(self, byname, *args):
        """Class initialisation

        Args:
            byname (str): file activka_byname.yaml -
            list of all network devices by name
           *args (str):  optional parameter, file activka_byip.yaml -
           list of all ip adresses of all devices
        """
        username = ac.user
        password = ac.password
        with open(ac.localpath + byname) as fyaml:
            wholedict = yaml.safe_load(fyaml)
        if args:
            with open(ac.localpath + args[0]) as fyaml:
                allip = yaml.safe_load(fyaml)
            self.routerbyip = allip
        dev_type = {}
        by_ip = {}
        devices = list(wholedict.keys())
        devices.remove("LEVEL")
        devices.remove("SEGMENT")
        self.devices = devices
        self.levels = wholedict["LEVEL"]
        self.segment = wholedict["SEGMENT"]
        del wholedict["LEVEL"]
        del wholedict["SEGMENT"]
        for d in devices:
            wholedict[d]["username"] = username
            wholedict[d]["password"] = password
            dev_type[d] = wholedict[d]["device_type"]
            by_ip[wholedict[d]["ip"]] = d
        self.wholedict = wholedict
        self.dev_type = dev_type
        self.by_ip = by_ip

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__class__.__doc__})"

    def choose(self, device, withoutname=False):
        """Function prepare dictionary in netmiko format for use with
           ConnectHandler(**device)

        Args:
            device (str): device name as defined in activka_byname.yaml
            withoutname (bool, optional): selector for return type -
                            {dictionary for conect} if False (default)
                            {device_name:{dictionary for conect}} if True

        Returns:
            out (dict): {dictionary for conect}
                        or {device_name:{dictionary for conect}}
        """
        out = {}
        if withoutname:
            out.update(self.wholedict[device])
        else:
            out[device] = self.wholedict[device]
        return out

    def filter(self, device_type=None, levels=None, segment=None):
        """Function select devices from our device filtered by 3 parameters

        Args:
            device_type (str):  device_type like in netmiko
            levels (list): type of device -
                            'R' - router
                            'L3' - L3 swith
                            'L2' - L2 switch
            segment (list): segments of networks
            (see documentation for activka_byname.yaml)

        Returns:
            cycle2 (dict): dictionary of the form
                           {device_name:{dictionary for conect},}
                           filtered from wholedict by parameters device_type,
                           levels or segment
        """
        cycle1 = {}
        cycle2 = {}
        if segment:
            device_by_seg = [
                key for key in self.segment.keys() if
                self.segment[key] == segment
            ]
        if device_type:
            if not segment:
                list_to_lookup = list(self.wholedict.keys())
            else:
                list_to_lookup = device_by_seg
            cycle1 = {
                d: self.wholedict[d]
                for d in list_to_lookup
                if self.wholedict[d]["device_type"] in device_type
            }
        else:
            if not segment:
                cycle1 = self.wholedict
            else:
                cycle1 = {d: self.wholedict[d] for d in device_by_seg}
        if levels:
            cycle2 = {d: cycle1[d] for d in cycle1.keys() if
                      self.levels[d] in levels}
        else:
            cycle2 = cycle1
        return cycle2

    def setconfig(self, device, commands):
        """Functions change configuration by commands

        Args:
            device (str): device name as defined in activka_byname.yaml
            commands (list): list of commands to transmit to device console

        Returns:
            result (str): output from device console
        """
        dev = self.choose(device, withoutname=True)
        result = send_config_commands(dev, commands)
        return result

    def _get_neighbor_by_port(self, device, func, *args):
        """Function get cdp or lldp neighbor on device's port

        Args:
            device (str): device's name
            func (str): abbreviated command 'neighbor_by_port'
            args[0] (str): name of port in normolize form

        Returns:
            neighbor[0] (str): name of other switch connected to port

        """
        port = args[0]
        m = re.search(r"(Eth-Trunk|Po)(\S+)", port)
        if m:
            port = self.getinfo(device, "ethchannel_member",
                                m.group(2))[0][0][0]
            port = port_name_normalize(port)
        nblist = self.getinfo(device, "neighbor", "pusto")
        subintf = re.compile(r"\.\d+")
        p = subintf.search(port)
        if p:
            intf = port[0: p.start(0)]
        else:
            intf = port
        for neighbor in nblist:
            lp = subintf.search(neighbor[1])
            if lp:
                intl = neighbor[1][0: lp.start(0)]
            else:
                intl = neighbor[1]
            if intf == intl:
                return neighbor[0]
        return False

    def _mac_addr_tbl_byport(self, dev, outlist, isEdgedPort):
        """Sub-Function for self.getinfo()  Get mac address table
           for defined port

        Args:
            dev (dict): dictionary in netmiko format for ConnectHandler(**dev)
            outlist (list): otput of self.getinfo(device, 'mac_addr_tbl_by'
            isEdgedPort (bool): status of this port is edge port (True) or
                                there is other switch behind tis port
        Returns:
            list [outlist[0][2], isEdgedPort]
        """
        outlist[0][2] = port_name_normalize(outlist[0][2])
        command = (
                ac.commands["mac_addr_tbl_byport"][dev["device_type"]]
                .format(outlist[0][2])
        )
        todo = send_show_command(dev, command)
        outwhole = templatizator(todo, "mac_addr_tbl_byport",
                                 dev["device_type"])
        if len(outwhole) > 2:
            if (
                len(outwhole) == 3
            ):  # If the computer is switched on via IP phone,
                # 2 MAC in 2 VLANs are lit up
                for (
                    mac
                ) in (
                    ac.phone_mac
                ):  # All our phones have a MAC starting with 805e,
                    # but there could be others.
                    if mac in outwhole[2][0]:
                        return [outlist[0][2], isEdgedPort]
            else:
                isEdgedPort = False
        return [outlist[0][2], isEdgedPort]

    def getinfo(self, device, func, *args, othercmd=False, txtFSMtmpl=False):
        """The function receives the output of a command (func)
           from network equipment 'device'
           command maybe "standard" (see dictionary 'commands')
           with arguments if they needed, or maybe ANY command
           then the 'othercmd variable must be set to True

        Args:
            device (str): device's name from activka_byname.yaml
            func (str): 1. standard abbreviated command (see commands.yml
                           and DOCUMENTAITION.md;
                        2. any command, selector othercmd must be True
            *args (str): if standard func requires arguments,
                         this is place for it
            othercmd (bool, optional): flag that defines  'func' is
                                       "standard command" (default False)
                                        or any commands (True)
            txtFSMtmpl (str, optional): A template file for FSM based text
                             parsing, if othercmd = True. Defaults to None

        Returns:
            outlist (list): list of list obtained using the corresponding
                            textfsm template
            outlist (str):  the direct output of the entered command if
                            textfsm template not defined

        """
        if func == "neighbor_by_port":
            return self._get_neighbor_by_port(device, func, args[0])

        else:
            status = True
            dev = self.choose(device, withoutname=True)
            if not othercmd:
                if args[0]:
                    command = (
                            ac.commands[func][dev["device_type"]]
                            .format(args[0])
                    )
                else:
                    command = ac.commands[func][dev["device_type"]]
            else:
                command = func
            todo = send_show_command(dev, command)
            if not todo:
                return False
            if not txtFSMtmpl:
                if not othercmd:
                    if func == "ethchannel_member":
                        if "WorkingMode: LACP" in todo:
                            func = "ethchannel_member_lacp"
                    outlist = templatizator(todo, func, dev["device_type"])
                else:
                    outlist = todo
            else:
                outlist = templatizator(todo, txtFSMtmpl, special=True)
            if func == "mac_addr_tbl_by":
                return self._mac_addr_tbl_byport(dev, outlist, status)
            if not outlist:
                return False
            else:
                return outlist

    def _unnecessary_truncate(self, lines):
        i = 0
        for line in lines:
            if not line.startswith("Current configuration :"):
                i += 1
            else:
                break
        del lines[0:i]
        lines[0] = ""
        return lines

    def get_curr_config(self, device, list_=True):
        """Function returns the current configuration of device

        Args:
            device (str): name of device
            list_ (bool, optional): flag to define type of return
        Returns:
            config (list): current config as list of lists;
                           if list_=True (default)
            content (str): current config as string; if list_= False
        """
        device_type = self.choose(device, withoutname=True)["device_type"]
        command = ac.commands["current_config"][device_type]
        _config = self.getinfo(device, command, othercmd=True)
        config = [line for line in _config.split("\n")]
        if device_type == "cisco_ios":
            config = self._unnecessary_truncate(
                config
            )  # first string is not config on cisco
            # delete variable string saved to config
            config = del_exeption(config)
        if list_:
            return config
        else:
            content = str()
            for line in config:
                content += "\n".join(line)
            return content

    def list_of_all_ip_intf(self, device):
        """Function get all ip interface on device

        Args:
            device (str): name of device

        Returns:
            todo (list): list of [interface, ip_address, mask, status(up|down),
                         protocol(up|down)]
        """
        mask = {
            "255.255.255.255": "32",
            "255.255.255.252": "30",
            "255.255.255.248": "29",
            "255.255.255.240": "28",
            "255.255.255.224": "27",
            "255.255.255.192": "26",
            "255.255.255.128": "25",
            "255.255.255.0": "24",
            "255.255.254.0": "23",
        }
        exclude_intf = ["NVI0"]
        dev = self.choose(device, withoutname=True)
        regexp = r"ip address \S+\s+(\S+)"
        command = ac.commands["ip_int_br"][dev["device_type"]]
        template = f"{dev['device_type']}_ip_int_br.template"
        todo = self.getinfo(device, command, othercmd=True,
                            txtFSMtmpl=template)
        if todo:
            if dev["device_type"] == "cisco_ios":
                for line in todo:
                    if line[0] in exclude_intf:
                        continue
                    int_conf = self.getinfo(
                        device, f"sh runn int {line[0]}", othercmd=True
                    )
                    mask_long = re.search(regexp, int_conf).group(1)
                    line.insert(2, mask[mask_long])
        return todo

    def execute_on_devices(
        self,
        devices: Union[str, List[str]],
        commands: Union[str, List[str]],
        timeout: int = 30,
        delay_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Execute commands on multiple devices

        Args:
            devices: Single device name or list of device names
            commands: Command or list of commands to execute
            timeout: Timeout per device in seconds
            delay_factor: Factor to adjust delays for slow devices

        Returns:
            Dictionary with results:
            {
                'success': {device: output},
                'failed': {device: error},
                'unreachable': [devices]
            }
        """
        if isinstance(devices, str):
            devices = [devices]

        if isinstance(commands, str):
            commands = [commands]

        results = {"success": {}, "failed": {}, "unreachable": []}

        for device_name in devices:
            device = self.choose(device_name, withoutname=True)

            if not self._is_device_available(device):
                results["unreachable"].append(device_name)
                continue

            try:
                output = []
                for cmd in commands:
                    result = self.getinfo(device_name, cmd, othercmd=True)
                    output.append(result)

                results["success"][device_name] = (
                    "\n".join(output) if len(output) > 1 else output[0]
                )
            except Exception as e:
                results["failed"][device_name] = str(e)

        return results

    def setconfig_on_devices(
        self,
        devices: Union[str, List[str]],
        commands: Union[str, List[str]],
        timeout: int = 30,
        delay_factor: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Change config on multiple devices

        Args:
            devices: Single device name or list of device names
            commands: Command or list of commands to execute
            timeout: Timeout per device in seconds
            delay_factor: Factor to adjust delays for slow devices

        Returns:
            Dictionary with results:
            {
                'success': {device: output},
                'failed': {device: error},
                'unreachable': [devices]
            }
        """
        if isinstance(devices, str):
            devices = [devices]

        if isinstance(commands, str):
            commands = [commands]

        results = {"success": {}, "failed": {}, "unreachable": []}

        for device_name in devices:
            device = self.choose(device_name, withoutname=True)

            if not self._is_device_available(device):
                results["unreachable"].append(device_name)
                continue

            try:
                output = []
                result = send_config_commands(device, commands)
                output.append(result)

                results["success"][device_name] = (
                    "\n".join(output) if len(output) > 1 else output[0]
                )
            except Exception as e:
                results["failed"][device_name] = str(e)

        return results

    def _is_device_available(self, device: dict) -> bool:
        """Check if device is reachable and responsive"""
        try:
            # First check basic ping
            if ping_one_ip(device["ip"]) != 0:
                return False

            # Then check if we can establish TCP connection to SSH port
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5)
                return s.connect_ex((device["ip"], 22)) == 0
        except Exception as e:
            logger.warning(
                f"Device availability check failed for "
                f"{device['host']}: {str(e)}"
            )
            return False


class ActivkaBackup(Activka):
    """The class bassed on Activka for get config backup"""

    def __init__(self, byname):
        """Class initialisation

        Args:
            byname (str): file activka_byname.yaml -
            list of all network devices by name
        """
        super().__init__(byname)

        self._setup_backup_servers()
        self._setup_protocol_handlers()

    def _setup_backup_servers(self):
        """Initialize backup server configurations"""
        self.main_backup_server = {
            "name": ac.main_backup_server["name"],
            "protocol": "local",
            "ftp_root": ac.main_backup_server["ftp_root"],
            "scp_root": getattr(ac.main_backup_server, "scp_root", ""),
            "sftp_root": getattr(ac.main_backup_server, "sftp_root", ""),
            "user": ac.main_backup_server["user"],
            "password": ac.main_backup_server["password"],
            "local_root": ac.main_backup_server["local_root"],
        }

        self.second_backup_server = {
            "name": ac.second_backup_server["name"],
            "protocol": "ftp",
            "ftp_root": ac.second_backup_server["ftp_root"],
            "scp_root": getattr(ac.second_backup_server, "scp_root", ""),
            "sftp_root": getattr(ac.second_backup_server, "sftp_root", ""),
            "user": ac.second_backup_server["user"],
            "password": ac.second_backup_server["password"],
        }

    def _setup_protocol_handlers(self):
        """Setup protocol handlers based on current host"""
        import socket

        is_main_server = (
                socket.gethostname() == self.main_backup_server["name"]
                )

        # Default to local handlers
        self.get_backup_list = self._get_backup_list_local
        self.get_backup_config = self._get_backup_config_local
        self.write_backup = self._write_backup_local

        if not is_main_server:
            # Use remote handlers
            self.get_backup_list = self._get_backup_list_remote
            self.get_backup_config = self._get_backup_config_remote
            self.write_backup = self._write_backup_remote

    def compare_configs(
        self, device: str, ignore_lines: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare current configuration with last backup

        Args:
            device: Device name to compare configs for
            ignore_lines: List of regex patterns to ignore in comparison

        Returns:
            Dictionary with comparison results:
            {
                'changed': bool,
                'added': list,
                'removed': list,
                'changed_lines': list
            }
        """
        current = self.get_curr_config(device)
        backup = self.get_backup_config(self.segment[device], device)

        if not backup:
            return {
                "changed": True,
                "added": current,
                "removed": [],
                "changed_lines": [],
            }

        return self._config_diff(current, backup, ignore_lines)

    def _config_diff(
        self,
        config1: List[str],
        config2: List[str],
        ignore_lines: List[str] = None
    ) -> Dict[str, Any]:
        """
        Compare two configurations and return differences

        Args:
            config1: First configuration (lines)
            config2: Second configuration (lines)
            ignore_lines: List of regex patterns to ignore

        Returns:
            Dictionary with diff results
        """
        if ignore_lines is None:
            ignore_lines = []

        def should_ignore(line):
            for pattern in ignore_lines:
                if re.search(pattern, line):
                    return True
            return False

        clean1 = [
            line.strip()
            for line in config1
            if line.strip() and not should_ignore(line)
        ]
        clean2 = [
            line.strip()
            for line in config2
            if line.strip() and not should_ignore(line)
        ]

        set1 = set(clean1)
        set2 = set(clean2)

        added = list(set1 - set2)
        removed = list(set2 - set1)

        # Find changed lines (same context but different content)
        changed_lines = []
        context = 3
        for i in range(len(clean1)):
            if i < len(clean2) and clean1[i] != clean2[i]:
                start = max(0, i - context)
                end = min(len(clean1), i + context + 1)
                changed_lines.append(
                    {
                        "line_num": i,
                        "current": clean1[i],
                        "backup": clean2[i],
                        "context": {
                            "before": clean1[start:i],
                            "after": clean1[(i + 1): end],
                        },
                    }
                )

        return {
            "changed": bool(added or removed or changed_lines),
            "added": added,
            "removed": removed,
            "changed_lines": changed_lines,
        }

    def _write_backup_scp(
        self, segment: str, filename: str, content: str, second: bool = False
    ):
        """Write backup using SCP protocol"""
        import paramiko
        from io import StringIO

        server = (
                self.second_backup_server
                if second
                else self.main_backup_server
                )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=server["name"],
                username=server["user"],
                password=server["password"],
            )

            with ssh.open_sftp() as sftp:
                remote_path = f"{server['scp_root']}{segment}/{filename}"
                with sftp.file(remote_path, "w") as f:
                    f.write(content)
        except Exception as e:
            logger.error(f"SCP backup failed: {str(e)}")
            raise
        finally:
            ssh.close()

    def _write_backup_sftp(
        self, segment: str, filename: str, content: str, second: bool = False
    ):
        """Write backup using SFTP protocol"""
        import paramiko
        from io import StringIO

        server = (
                self.second_backup_server
                if second
                else self.main_backup_server
                )
        transport = paramiko.Transport((server["name"], 22))

        try:
            transport.connect(username=server["user"],
                              password=server["password"])
            sftp = paramiko.SFTPClient.from_transport(transport)

            remote_path = f"{server['sftp_root']}{segment}/{filename}"
            with sftp.file(remote_path, "w") as f:
                f.write(content)
        except Exception as e:
            logger.error(f"SFTP backup failed: {str(e)}")
            raise
        finally:
            transport.close()

    def _get_backup_config_scp(
        self, segment: str, device: str, second: bool = False
    ) -> List[str]:
        """Get backup config using SCP protocol"""
        import paramiko
        from io import StringIO

        server = (
                self.second_backup_server
                if second
                else self.main_backup_server
                )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            ssh.connect(
                hostname=server["name"],
                username=server["user"],
                password=server["password"],
            )

            with ssh.open_sftp() as sftp:
                remote_path = f"{server['scp_root']}{segment}/{device}-*"
                files = sorted(sftp.listdir(remote_path), reverse=True)
                if not files:
                    return []

                with sftp.file(f"{remote_path}/{files[0]}", "r") as f:
                    content = f.read().decode("utf-8")
                    return content.splitlines()
        except Exception as e:
            logger.error(f"SCP config retrieval failed: {str(e)}")
            return []
        finally:
            ssh.close()

    def _get_backup_config(self, segment: str, device: str) -> List[str]:
        """The function returns a list of backup files in the segment folder

        Args:
            segment (str): segment (folder) under ftp_root  (ftp_root/segment/)
            device (str, optional): name of device

        Returns:
            out (list): list of all backup files in the segment folder if
                        device= None
                        or list of  backup files only for this device
        """
        from os import path

        local_path = (
                f"{self.main_backup_server['local_root']}"
                f"{segment}/{device}-*"
                )
        files = [f for _, _, f in os.walk(where)][0]
        out = self._get_files_of_dir(files, device)
        return out
