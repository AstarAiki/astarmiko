import os, yaml, textfsm, logging, re, time, sys
from pysnmp.hlapi.v3arch.asyncio import *
import asyncio
#logging.basicConfig(filename='d:/network/net_func.log',format='%(asctime)s : %(level)s - %(message)s', datefmt='%Y-%B-%d %H:%M:%S', level=logging.WARNING)

ac = '' #Global object represent configuration attributes
 
def setini(path_to_conf):
    ''' Initialize conf object ac with attributes from path_to_conf
    
    Args:
        path_to_conf (str): full path to config file ( yaml, json, format)
        
    '''
    from astarconf import  Astarconf
    global ac
    ac = Astarconf(path_to_conf)
    try:
        dict_of_cmd = ac.dict_of_cmd
        with open(dict_of_cmd) as f:
            commands = yaml.safe_load(f)
        ac.commands = commands['commands']
    except AttributeError:
        pass



async def snmp_get_oid(host: str, community: str, oid: str, port: int = 161, version: int = 2, prnerr: bool = False):
    '''Function get OID's by SNMP from device without ssh access (like russian NGFW Kontinent)
    
    Args:
        host (str): ip address of NGFW
        community (str): community string for SNMP ver.2
        oid (str): oid in ASN.1 format you want to get
        port (int): port dor SNMP access, default 161
        version (int): version of SNMP, default is 2
        prnerr (bool): selector to print or not errors in stdout
    
    Returns:
        result (str): value of oid
    '''

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
        ##print(f'DEBUG_0 in snmp_get_oid  we are here')
        if errorIndication:
            result.append(errorIndication)
            ##print(f'DEBUG_1 in snmp_get_oid  result = {result}')
        elif errorStatus:
            ##print(f'DEBUG_02 in snmp_get_oid  we are here')
            result.append(
                "{} at {}".format(
                    errorStatus.prettyPrint(),
                    errorIndex and varBinds[int(errorIndex) - 1][0] or "?",
                )
            )
            result.append(False)
            ##print(f'DEBUG_2 in snmp_get_oid  result = {result}')
        else:
            ##print(f'DEBUG_03 in snmp_get_oid  we are here {str(varBinds[0].prettyPrint())}')
            result.append(str(varBinds[0].prettyPrint()))
            ##print(f'DEBUG_3 in snmp_get_oid  result = {result}')
    #snmpEngine.close_dispatcher()
    ##print(f'DEBUG in snmp_get_oid  result = {result}')
    return result



    


def send_config_by_one(device, commands, log=False):
    '''The function connects via SSH (using netmiko) to ONE device and performs
     ONE command in configuration mode based on the arguments passed.
    
    Args:
        device (dict): dictionary in netmiko format for use with ConnectHandler(**device)
        commands (list or str): command in list ['some command'] to send to device (if string - it converted to list
        log (bool): selector to logging on or off, default is off
        
    Returns:
        result (str): answer device on command in console
    '''
    from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    )

    if type(commands) == str:
        commands = [commands]
    good = {}
    failed = {}
    errors_str = re.compile(r'Invalid input detected|Incomplete command|Ambiguous command|Unrecognized command')
    try:
        if log:
            print('Подключаюсь к {}...'.format(device['host']))
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            for command in commands:
                result = ssh.send_config_set(command)
                if not errors_str.search(result):
                    good[command] = result
                else:
                    logging.warning(f"Комманда {command} выполнилась с ошибкой: {errors_str.search(result).group()} на устройстве {device['host']}")
                    failed[command] = result
            out = (good,failed)
            return out
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        logging.warning(error)

def send_config_commands(device, commands, log=True):
    '''The function connects via SSH (using netmiko) to ONE device and performs 
    a list of commands in configuration mode based on the arguments passed.
    
    Args:
        device (dict): dictionary in netmiko format for use with ConnectHandler(**device)
        commands (list or str): command in list ['some command'] to send to device (if string - it converted to list
        log (bool): selector to logging on or off, default is off
        
    Returns:
        result (str): answer device on command in console
    '''
    from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    )

    if type(commands) == str:
        commands = [commands]
    try:
        if log:
            print(f"Подключаюсь к {device['ip']}...")
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            result = ssh.send_config_set(commands, delay_factor = 20)
            time.sleep(10)
            result += ssh.send_command_timing('write')
            return result
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        logging.warning(error)



def send_show_command(device, commands, log=False):
    '''The function connects via SSH (using netmiko) to ONE device
    and executes the specified  show (display)command.
    
    Args:
        device (dict): dictionary in netmiko format for use with ConnectHandler(**device)
        commands (str): command  to send to device 
        log (bool): selector to logging on or off, default is off
        
    Returns:
        result (str): answer device on command in console
    '''
    from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
    )
    from datetime import datetime
    if log:
        logging.getLogger("paramiko").setLevel(logging.WARNING)
        logging.basicConfig(
        filename = ac.localpath + 'net_func.log',
        format = '%(threadName)s %(name)s %(levelname)s: %(message)s',
        level=logging.INFO)
        connect_string = '===> {} Подключаюсь к {}'
        not_connect_string = '===> {}  Не могу подключиться к {}'
        logging.info(connect_string.format(datetime.now().time(), device['ip']))
    try:
        if ping_one_ip(device['ip']) == 0:
            with ConnectHandler(**device) as ssh:
                ssh.enable()
                result = ssh.send_command(commands)
                return result
        else:
            if log:
                logging.info(not_connect_string.format(datetime.now().time(),device['ip']))
            return False
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        if log:
            logging.warning(error)

def ping_one_ip(ip_address):
    '''Function get one ip address and return 0 if all is o'key or else error code
    
    Args:
        ip_address (str): ip address to ping
    
    Returns:
        return code of ping: 0 if alive other if not
    '''

    import subprocess as sp
    if os.name == 'nt':
        reply = sp.run(['ping','-n','3',ip_address], stdout = sp.DEVNULL)
    else:
        reply = sp.run(['ping','-c','3','-n',ip_address], stdout = sp.DEVNULL)
    
    return reply.returncode

def templatizator(*args, special = False):
    '''Function convert console output to dict using textfsm template
    
    Args:
        args[0] (str): output from console of device
        args[1] (str):  1. the standard command itself in the form of an abbreviation for which 
                        there is a textFSM template or 
                        2. any command, then a second positional parameter is needed 
                        - the template file name and the special variable must be set to True 
        args[2] (str):  if special = False (by default) device type in form of netmiko
                        or 'nt' or 'posix' if args[0] output from console of
                        Windows or Posix systems
                        device_type (args[1] is abbreviated command from ac.commands
                        if special = True, args[1] is not abbreviated command that one is name of file
                        with textFSM template, must be located in directory defined by ac.templpath 
    
    Returns:
        list of lists obtained using the corresponding textfsm template
    '''
    if not special:
        if args[2] == 'nt':
            tf = ac.templpath + 'nt_' + args[1] + '.template'
        elif args[2] == 'posix':
            tf = ac.templpath + 'posix_' + args[1] + '.template'
        else:
            tf = ac.templpath + args[2] + '_' + args[1] + '.template'
    else:
        tf = ac.templpath + args[1]
    with open(tf) as tmpl:
        fsm = textfsm.TextFSM(tmpl)
        result = fsm.ParseText(args[0])
    return result



def port_name_normalize(port):
    '''The function gets the port name and if it is abbreviated, returns the full name. 
       It is actually necessary to bypass the Huawei hardware property to return 
       the interface name as GE and require the input of Gi
    
    Args:
        port (str): name of port from device's console
        
    Returns:
        (str) correct long format of port name
    '''
    portnorm = []
    m = re.search(r'(Eth-Trunk|Po|10GE|100GE|GE|Gi|XGE|Fa|Ser)(\S+)', port)
    if m:
        if m.group(1) == 'Eth-Trunk' or m.group(1) == 'Po':
            portnorm = f'{m.group(0)}'
            return portnorm
        else:
            if m.group(1)[0] == '1':
                if m.group(1)[2] == '0':
                    longname = '100GE'
                else:
                    longname = '10GE'
            if m.group(1)[0] == 'G':
                longname = 'GigabitEthernet'
            if m.group(1)[0] == 'X':
                longname = 'XGigabitEthernet'
            if m.group(1)[0] == 'F':
                longname = 'FastEthernet'
            if m.group(1)[0] == 'S':
                longname = 'Serial'
            portnorm = f'{longname}{m.group(2)}'
            return portnorm

def get_port_by_mac(device, mac):
    '''Function searches for the port to which a device with mac address is connected 
    
    Args:
        device (dict): dictionary in netmiko format for use with ConnectHandler(**device)
        
    Returns:
        a list of [Port,Status] where Status is True if  the destination port is edge port 
        and False if there is another switch behind this port
        Port - out[2] (str): name of port 
    '''
    status = True

    command = ac.commands['mac_addr_tbl_bymac'][device['device_type']].format(mac)
    todo = send_show_command(device, command)
    out = templatizator(todo, 'mac_address_table', device['device_type'])[0]
    out[2] = port_name_normalize(out[2])
    command = ac.commands['mac_addr_tbl_byport'][device['device_type']].format(out[2])
    todo = send_show_command(device, command)
    outwhole = templatizator(todo, 'mac_address_table', device['device_type'])
    if len(outwhole) > 2:
        if len(outwhole) == 3: #если компютер включен через IP телефон то светится 2 MAC в 2-х VLAN
            for mac in ac.phone_mac:#у нас все телефоны имеют MAC начинающийся на 805e но ведь могут появиться и другие
                if mac in outwhole[2][0]:
                    return [out[2], status]
        else:
            status = False
    return [out[2], status]

def convert_mac(mac,device_type):
    '''Function converts mac address string from any known formats to format device with device_type
       MAC can be in the form of 4 by 3 or 6 by 2 separators are also different
    
    Args:
        mac (str): string of mac address
        device_type (str): string of device_type like in netmiko
    
    Returns:
        MAC string in the form accepted on this hardware with device_type = device_type
    
    '''
    mac = mac.lower()
    trudelim, digit_by_group =  ac.commands["mac_delimeters"][device_type]
    p4=re.compile(r'(?P<oct1>[0-9a-fA-F]{4})[-|.|:](?P<oct2>[0-9a-fA-F]{4})[-|.|:](?P<oct3>[0-9a-fA-F]{4})', re.ASCII)
    p6=re.compile(r'(?P<oct1>[0-9a-fA-F]{2})[-|.|:](?P<oct2>[0-9a-fA-F]{2})[-|.|:](?P<oct3>[0-9a-fA-F]{2})[-|.|:](?P<oct4>[0-9a-fA-F]{2})[-|.|:](?P<oct5>[0-9a-fA-F]{2})[-|.|:](?P<oct6>[0-9a-fA-F]{2})', re.ASCII)
    m = p4.search(mac)
    if m:
        if digit_by_group == 4:
            trumac = f'{m.group(1)}{trudelim}{m.group(2)}{trudelim}{m.group(3)}'
        else:
            trumac = f'{m.group(1)[0:2]}{trudelim}{m.group(1)[2:4]}{trudelim}{m.group(2)[0:2]}{trudelim}{m.group(2)[2:4]}{trudelim}{m.group(3)[0:2]}{trudelim}{m.group(3)[2:4]}'
    else:
        m = p6.search(mac)
        if m:
            if digit_by_group == 4:
                trumac = f'{m.group(1)}{m.group(2)}{trudelim}{m.group(3)}{m.group(4)}{trudelim}{m.group(5)}{m.group(6)}'
            else:
                trumac = f'{m.group(1)}{trudelim}{m.group(2)}{trudelim}{m.group(3)}{trudelim}{m.group(4)}{trudelim}{m.group(5)}{trudelim}{m.group(6)}'
        else:
            return False
    return trumac



def is_ip_correct(ip):
    '''Function checks  ip address fo correctness
        if there is standart error in russian layout when commas entered 
        instead of dots correct this one
    
    Args:
        ip (str): string of ip address
    
    Returns:
        string of ip address or False if ip is not correct
    '''
    if re.search(r'^(?:(?:^|\.)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4}$',ip):
        return ip
    else:
        if re.search(r'^(?:(?:^|\,)(?:2(?:5[0-5]|[0-4]\d)|1?\d?\d)){4}$',ip):
            return re.sub(',','.',ip)
        else:
            return False





def nslookup(hostname, reverse = True):
    '''The function gets the host name and returns a list of its IP addresses. 
        Or vice versa (reverse = True) finds the DNS name by IP address
    
    Args:
        hostname (str):  name or ip of host
        reverse (bool): selector of reverse lookup by ip (default) or dirrect lookup by name
    
    Returns:
        name of host
    '''
    import socket, subprocess
    
    if reverse:
        try:
            ip = socket.gethostbyname(hostname)
        except:
            ip = False 
        return ip
    else:
        if os.name == 'nt':
            code = 'cp1251'
        elif os.name == 'posix':
            code = 'utf_8'
        todo = subprocess.run(['nslookup', hostname], stdout = subprocess.PIPE, stderr = subprocess.PIPE, encoding = code)
        name = templatizator(todo.stdout, 'nslookup', os.name)
        if not name:
            return False
        return name[0][0]





def del_exeption(config):
    '''Functions delete daily changeble string from device config
        example: configs from many cisco devices different day by day
        only by string with command 'ntp clock-period'
        it prevents us from knowing if the config has been changed
    
    Args:
        config (list): list of config lines from device
    
    Returns:
        config (list): list of config lines from device without exeption lines
        
    '''
    to_lookup = ['ntp clock-period']
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


class TimeMeasure:
    '''
    The class allows you to measure the execution time of a program or subroutine
    '''
    def __init__(self):
        pass
    def __enter__(self):
        self.start = time.time()
    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f'Время выполнения программы заняло: {time.time() - self.start}')




class Activka:
    '''The class represents all our network devices - routers and switches
    '''
    def __init__(self, byname, *args):
        '''Class initialisation
        
        Args:
            byname (str): file activka_byname.yaml - list of all network devices by name
           *args (str):  optional parameter, file activka_byip.yaml - list of all ip adresses of all devices
        '''
        username = ac.user
        password = ac.password
        with open(ac.localpath + byname) as fyaml:
            wholedict = yaml.safe_load(fyaml)
        if args:
            with open(ac.localpath + args[0]) as fyaml:
                allip = yaml.safe_load(fyaml)
            self.routerbyip = allip
        r_and_s ={}
        devices = list(wholedict.keys())
        devices.remove('LEVEL')
        devices.remove('SEGMENT')
        self.devices = devices
        self.levels = wholedict['LEVEL']
        self.segment = wholedict['SEGMENT']
        del wholedict['LEVEL']
        del wholedict['SEGMENT']
        for d in devices:
            wholedict[d]['username'] = username
            wholedict[d]['password'] = password
            r_and_s[d] = wholedict[d]
        self.wholedict = wholedict
        self.r_and_s = r_and_s
        
    
    def __repr__(self):
        return(f'{self.__class__.__name__}({self.__class__.__doc__})')
    
    def choose(self, *args, withoutname = False):
        '''Function prepare dictionary in netmiko format for use with ConnectHandler(**device)
        
        Args:
            device (str): device name as defined in activka_byname.yaml
            withoutname (bool): selector for return type - 
                                {dictionary for conect} if False (default)
                                {device_name:{dictionary for conect}} if True
        
        Returns:
            out (dict): {dictionary for conect} or {device_name:{dictionary for conect}}
        '''
        out = {}
        if withoutname:
            for d in args:
                out.update(self.wholedict[d])
        else:
            for d in args:
                out[d] = self.wholedict[d]
        return out

    def filter(self, device_type = None, levels = None, segment = None):
        '''Function select devices from our device filtered by 3 parameters
        
        Args:
            device_type (str):  device_type like in netmiko 
            levels (list): type of device - 
                            'R' - router
                            'L3' - L3 swith
                            'L2' - L2 switch
            segment (list): segmennts of networks (see documentation for activka_byname.yaml)
        
        Returns:
            cycle2 (dict): dictionary of the form {device_name:{dictionary for conect},} 
            filtered from wholedict by parameters device_type, levels or segment
        '''
        cycle1 = {}
        cycle2 = {}
        if segment:
            device_by_seg = [key for key in self.segment.keys() if self.segment[key] == segment]
        if device_type:
            if not segment:
                list_to_lookup = list(self.wholedict.keys())
            else:
                list_to_lookup = device_by_seg
            cycle1 = {d: self.wholedict[d] for d in list_to_lookup if self.wholedict[d]['device_type'] in device_type}
        else:
            if not segment:
                cycle1 = self.wholedict
            else:
                cycle1 =  {d: self.wholedict[d] for d in device_by_seg}
        if levels:
            cycle2 = {d: cycle1[d] for d in cycle1.keys() if self.levels[d] in levels}
        else:
            cycle2 = cycle1
        return cycle2
    
    def setconfig(self, device, commands, log = False):
        '''Functions change configuration by commands
        
        Args:
            device (str): device name as defined in activka_byname.yaml
            commands (list): list of commands to transmit to device console
            log (bool): selector of loggin is on (True) or off (False) by default
        
        Returns:
            result (str): output from device console
        '''
        dev = self.choose(device, withoutname = True)
        result = send_config_commands(dev, commands, log)
        return result
    
    def _get_neighbor_by_port(self, device, func, *args):
        '''Function get cdp or lldp neighbor on device's port 
        
        Args:
            device (str): device's name
            func (str): abbreviated command 'neighbor_by_port'
            args[0] (str): name of port in normolize form
        
        Returns:
            neighbor[0] (str): name of other switch connected to port
        
        '''
        port = args[0]
        m = re.search(r'(Eth-Trunk|Po)(\S+)', port)
        if m:
            port = self.getinfo(device, 'ethchannel_member', m.group(2))[0][0][0]
            port = port_name_normalize(port)
        nblist = self.getinfo(device,'neighbor_br', 'pusto')
        subintf = re.compile(r'\.\d+')
        p = subintf.search(port)
        if p:
            intf = port[0:p.start(0)]
        else:
            intf = port
        for neighbor in nblist:
            lp =  subintf.search(neighbor[1])
            if lp:
                intl = neighbor[1][0:lp.start(0)]
            else:
                intl = neighbor[1]
            if intf == intl:
                return neighbor[0]
        return False        

    def _mac_addr_tbl_byport(self, dev, outlist, status):
        '''
        
        '''
        outlist[0][2] = port_name_normalize(outlist[0][2])
        command = ac.commands['mac_addr_tbl_byport'][dev['device_type']].format(outlist[0][2])
        todo = send_show_command(dev, command)
        outwhole = templatizator(todo, 'mac_address_table', dev['device_type'])
        if len(outwhole) > 2:
            if len(outwhole) == 3: #если компютер включен через IP телефон то светится 2 MAC в 2-х VLAN
                for mac in ac.phone_mac:#у нас все телефоны имеют MAC начинающийся на 805e но ведь могут появиться и другие
                    if mac in outwhole[2][0]:
                        return [outlist[0][2], status]
            else:
                status = False
        #print(f'DEBUG getinfo return  mac_add_table outlist[0][2] = {outlist[0][2]} status = {status}')
        return [outlist[0][2], status]
    
    
    def getinfo(self, device, func, *args, othercmd = False, txtFSMtmpl = False):
        '''The function receives the output of a command (func) from network equipment 'device' 
            command maybe "standard" (see dictionary 'commands') with arguments if they needed, or
            maybe ANY command then the 'othercmd variable must be set to True
        
        Args:
            device (str): device's name from activka_byname.yaml
            func (str): 1. standard abbreviated command (see commands.yml and DOCUMENTAITION.md;
                        2. any command, selector othercmd must be True
            *args (str): if standard func requires arguments, this is place for it
            othercmd (bool, optional): flag that defines  'func' is "standard command" (default False)
                                        or any commands (True)
            txtFSMtmpl (str, optional): A template file for FSM based text parsing, if othercmd = True.
                                        Defaults to None
        
        Returns:
            outlist (list): list of list obtained using the corresponding textfsm template
            outlist (str):  the direct output of the entered command if textfsm template not defined 

        '''

        if not othercmd:
            commands ={
                'neighbor_br': {'cisco_ios':f'show cdp neighbor detail','huawei':f'display lldp neighbor', 'eltex':f'show lldp neighbor detail'},
                'arp': {'cisco_ios':f'show arp | in {args[0]}  +','huawei':f'display  arp | in {args[0]}  +','checkpoint_gaia': 'arp -an', 'eltex':f'show arp | in {args[0]}  +'},
                'neighbor_by_port': {'port': args[0]},
                'ethchannel_member': {'cisco_ios':f'show etherchannel {args[0]} port','huawei':f'display eth-trunk {args[0]}', 'eltex':f'show interfaces Port-Channel {args[0]}'},
                'mac_address_table': {'cisco_ios':f'show mac address-table | in {args[0]}','huawei':f'display mac-address | in {args[0]}', 'eltex':f'show mac address-table | in {args[0]}'},
                'in_route_tbl': {'cisco_ios':f'show ip route {args[0]}','huawei':f'display ip routing-table {args[0]}', 'eltex':f'show ip route address {args[0]}'}
                }
        if func == 'neighbor_by_port':
            return self._get_neighbor_by_port(self, device, func, args[0])
            
        else:
            status = True
            dev = self.choose(device, withoutname = True)
            if not othercmd:

                command = ac.commands[func][dev['device_type']]
            else:
                command = func
                #print(f'DEBUG: getinfo по идее должны оказаться здесь command = {command}')
            todo = send_show_command(dev, command)
            if not todo:
                return False
            if not txtFSMtmpl:
                if not othercmd:
                    if func == 'ethchannel_member':
                        if 'WorkingMode: LACP' in todo:
                            func = 'ethchannel_member_lacp'
                    outlist = templatizator(todo, func, dev['device_type'])
                else:
                    outlist = todo
            else:
                outlist = templatizator(todo, txtFSMtmpl, special = True)
            if func == 'mac_addr_tbl_by':
                return self._mac_addr_tbl_byport(dev, outlist, status)
            if not outlist:
                #print(f'DEBUG getinfo return  false becouse not outlist ')
                return False
            else:
                #print(f'DEBUG getinfo return  outlist = {outlist} status = {status}')
                return outlist

    def _unnecessary_truncate(self, lines):
        i = 0
        for line in lines:
            if not line.startswith('Current configuration :'):
                i +=1
            else:
                break
        del lines[0:i]
        lines[0] = ''
        return lines
            
    def get_curr_config(self, device, list_ = True):
        '''Function returns the current configuration of device
        
        Args:
            device (str): name of device
            list_ (bool, optional): flag to define type of return
        Returns:
            config (list): current config as list of lists; if list_=True (default)
            content (str): current config as string; if list_= False
        '''
        device_type = self.choose(device, withoutname = True)['device_type']
        command = ac.commands['current_config'][device_type]
        _config = self.getinfo(device, command, othercmd = True)
        config = [line for line in _config.split('\n')]
        if device_type == 'cisco_ios':
            config = self._unnecessary_truncate(config) # first string is not config on cisco
            config = del_exeption(config) #delete variable string saved to config
        if list_:
            return config
        else:
            content = str()
            for line in config:
                content += '\n'.join(line)
            return content

    def list_of_all_ip_intf(self, device):
        '''Function get all ip interface on device
        
        Args:
            device (str): name of device
        
        Returns:
            todo (list): list of [interface, ip_address, mask, status(up|down), protocol(up|down)]
        '''
        mask = {
            '255.255.255.255': '32',
            '255.255.255.252': '30',
            '255.255.255.248': '29',
            '255.255.255.240': '28',
            '255.255.255.224': '27',
            '255.255.255.192': '26',
            '255.255.255.128': '25',
            '255.255.255.0': '24',
            '255.255.254.0': '23',
            }
        exclude_intf = ['NVI0']
        dev = self.choose(device,  withoutname = True)
        regexp = r'ip address \S+\s+(\S+)'
        command = ac.commands['ip_int_br'][dev['device_type']]
        template = f'{dev['device_type']}_ip_int_br.template' 
        todo = self.getinfo(device, command, othercmd = True, txtFSMtmpl = template)
        if todo:
            if dev['device_type'] == 'cisco_ios':
                for line in todo:
                    if line[0] in exclude_intf:
                        continue
                    int_conf = self.getinfo(device, f'sh runn int {line[0]}', othercmd = True)
                    mask_long = re.search(regexp, int_conf).group(1)
                    line.insert(2, mask[mask_long])
        return todo




class ActivkaBackup(Activka):
    '''
    Class is child of class Activka, used for config backup
    '''
    
    data = []
    def __init__(self, byname):
        super().__init__(byname)
        import socket
        self.main_backup_server = {}
        self.second_backup_server = {}
        self.main_backup_server['name'] = ac.main_backup_server['name']
        self.main_backup_server['protocol'] = 'local'
        self.main_backup_server['ftp_root'] = ac.main_backup_server['ftp_root']
        self.main_backup_server['ftp_user'] = ac.main_backup_server['user']
        self.main_backup_server['ftp_password'] = ac.main_backup_server['password']
        self.main_backup_server['local_root'] = ac.main_backup_server['local_root']
        self.second_backup_server['name'] = ac.second_backup_server['name']
        self.second_backup_server['protocol'] = 'ftp'
        self.second_backup_server['ftp_root'] = ac.second_backup_server['ftp_root']
        self.second_backup_server['ftp_user'] = ac.second_backup_server['user']
        self.second_backup_server['ftp_password'] = ac.second_backup_server['password']
        self.get_backup_list = self._get_backup_list_local
        self.get_backup_config = self._get_backup_config_local
        self.write_backup = self._write_backup_local
        
        
        if not socket.gethostname() == self.main_backup_server['name']:
            self.main_backup_server['protocol'] = 'ftp'
            self.get_backup_list = self._get_backup_list_ftp
            self.get_backup_config = self._get_backup_config_ftp
            self.write_backup = self._write_backup_ftp
    
    def _set_ftp_var(self, second):
        '''Function set parameters for ftp connection
        
        Args:
            second (bool): flag to define main backup server (second is False)
                            or second backup server (second is True)
        
        Returns:
            ftp_root (str): path to ftp root
            ftp_params (dict): dictionary for ftp connection
        '''
        if second:
            ftp_params = {
                'host': self.second_backup_server['name'],           
                'user': self.second_backup_server['ftp_user'],       
                'passwd': self.second_backup_server['ftp_password'],
                'acct' : self.second_backup_server['ftp_user'],
                } 
            ftp_root  = self.second_backup_server['ftp_root']
        else:
            ftp_params = {
                'host': self.main_backup_server['name'],           
                'user': self.main_backup_server['ftp_user'],       
                'passwd': self.main_backup_server['ftp_password'],
                'acct' : self.main_backup_server['ftp_user'],
                } 
            ftp_root  = self.main_backup_server['ftp_root']
        return (ftp_root, ftp_params)
    

        
    
    def _get_backup_list_local(self, segment, device= None):
        '''The function returns a list of backup files in the segment folder
        
        Args:
            segment (str): segment (folder) under ftp_root  (ftp_root/segment/)
            device (str, optional): name of device
        
        Returns:
            out (list): list of all backup files in the segment folder if device= None
                        or list of  backup files only for this device
        '''
        from os import  path
        where = path.join(self.main_backup_server['local_root'], segment)
        files = [f for _, _, f in os.walk(where)][0]
        out = self._get_files_of_dir(files, device)
        return out
    

    def _get_backup_list_ftp(self, segment, device= None, second = False):
        '''The function returns a list of backup files in the segment folder
        
        Args:
            segment (str): segment (folder) under ftp_root  (ftp_root/segment/)
            device (str, optional): name of device
            second (bool, optional): flag defined using main (default) backup server
                                    or second (second = True) backup server
        
        Returns:
            out (list): list of all backup files in the segment folder if device= None
                        or list of  backup files only for this device
        '''
        from ftplib import FTP
        ftp_root, ftp_params = self._set_ftp_var(second)
        
        with FTP(**ftp_params) as con:
            con.cwd(ftp_root + segment)
            files = con.nlst()
        out = self._get_files_of_dir(files, device)
        return out
    
    def _get_files_of_dir(self, *args):
        '''the function searches the list of files from a certain catalogue 
            for files related to a certain device
            All files name have format f'{device}-YYYYMMDD' 
            where YYYYMMDD - date of creating backup
        
        Args:
            args[0] = files (list): list off files in certain catalogue
            args[1] = device (str): name of device to search them backups in args[0]
        Returns:
            out (list): = [file_list, date_list] where - 
                        file_list - list of backup files for certain device
                        date_list - list of all "date part" of file's names
                        = ['STOP LOSHADKA', 19000101] if the device has never been backed up
            out (list) = file_list if args[1] = None
        '''
        file_list = []
        date_list = []
        for filename in args[0]:
            if not args[1]:
                file_list.append(filename)
            else:
                if f'{args[1].lower()}-' in filename.lower():
                    file_list.append(filename)
                    date_list.append(int(filename[-8:]))
        if args[1]:
            if not file_list:
                file_list = ['STOP LOSHADKA']
                date_list = [19000101]
            out = [file_list, date_list]
            return out
        else:
            return file_list
    
    
    def _get_backup_config_local(self, *args, list_ = True, date_ = -1):
        '''Function get last config backup from last (by date) file for defined device
            when script is running on main backup server
        
        Args:
            args[0] = segment (str): segment (folder) under ftp_root or local_root  (./segment/)
            args[1] = device (str, optional): name of device
            list_ (bool, optional): flag defined type of output - 
                                    list of list (config lines)- if True (default)
                                    string - if False
            date_ (int, optional): default -1 to get last (by date) file or next-to-last or next-next-ro-last
                                    but I haven't figured out what it would be for.
        
        Returns:
            out (list): list of lines of config file if list_ = True
            out (str): config files as string if list_ = False
        '''
        from os import path
        f = self._get_backup_list_local(args[0], args[1])
        if not f:
            return False
        filename = path.join(self.main_backup_server['local_root'], args[0], f[0][date_])
        out = []
        with open(filename) as fr:
            for line in fr:
                line = line.rstrip('\n')
                out.append(line)
        if list_:
            return out
        else:
            return '\n'.join(out)
    

    def _get_backup_config_ftp(self, segment, device= False, list_ = True, date_ = -1, second = False):
       '''Function get last config backup from last (by date) file for defined device
            when script is not running on main backup server
            and get files from server over ftp
        
        Args:
            args[0] = segment (str): segment (folder) under ftp_root or local_root  (./segment/)
            args[1] = device (str, optional): name of device
            list_ (bool, optional): flag defined type of output - 
                                    list of list (config lines)- if True (default)
                                    string - if False
            date_ (int, optional): default -1 to get last (by date) file or next-to-last or next-next-ro-last
                                    but I haven't figured out what it would be for.
        
        Returns:
            out (list): list of lines of config file if list_ = True
            out (str): config files as string if list_ = False
        '''
        from ftplib import FTP

        f = self._get_backup_list_ftp(segment, device)
    
        if f[0][date_] == 'STOP LOSHADKA':
            return False
        cmd = 'RETR ' + f[0][date_]
        if cmd == 'RETR STOP LOSHADKA':
            return False
        data = []
        ftp_root, ftp_params = self._set_ftp_var(second)
        
        def handleDownload(more_data):
            data.append(more_data)
        with FTP(**ftp_params) as con:
            con.cwd(ftp_root + segment)
            con.retrbinary(cmd, callback = handleDownload)
        out = b''.join(data)
        out = out.decode(encoding = 'utf-8').split('\n')
        for i, line in enumerate(out):
            if '\x03' in line:
                out[i] = line.replace('\x03', '^C')
        out = [line.rsplit('\r')[0] for line in out] 
        if list_:
            return out
        else:
            content = str()
            for line in out:
                content += '\n'.join(line)
            return content


    def save_config_backup(self, *args, rewrite = False):
        '''Function save current device configuration to backup file
            if it differs from the last saved configuration
        
        Args:
            args[0] = segment (str): segment (folder) under ftp_root or local_root  (./segment/)
            args[1] = device (str): name of device
            rewrite (bool): flag to rewrite (if True) or not (if False - default) 
                            backup file if it is exists
        Returns:
            exit_code (int): 0 - configuration is the same as last backup, no write
                             1 - confifurattions are different, write backup
                             2 - confifurattions are different and flag rewrite was set, rewrite backup
                             10 - new device, it was first backup. Writed 
        '''
        import datetime
        td = datetime.date.today()
        today = f'{td.year}' + f'{td.month:02d}' + f'{td.day:02d}'
        curr_config = self.get_curr_config(args[1])
        last_backup = self.get_backup_config(*args)
        filename = args[1] + '-' + today
        exit_code = int()
        if not last_backup:
            self.write_backup(args[0], filename, curr_config)
            exit_code = 10
            sys.exit(exit_code)
        if check_identity(curr_config, last_backup):
            exit_code = 0
            sys.exit(exit_code)
        filename_last = self.get_backup_list(*args)[0][-1]
        if filename == filename_last:
            if rewrite:
                self.write_backup(args[0], filename, curr_config)
                exit_code = 2
        else:
            self.write_backup(args[0], filename, curr_config)
            exit_code = 1
        return exit_code 
    
    

    def _write_backup_local(self, *args):
        '''Function create backup file on disk when running on main backup server
        
        Args:
            args[0] = segment (str): segment (folder) under ftp_root or local_root  (./segment/)
            args[1] = filename (str): name of file
            args[2] = curr_config (list): current configuration in type of list
        
        Returns:
            none
        '''
        from os import  path
        segment = args[0]
        filename = args[1]
        curr_config = args[2]
        content = '\n'.join(curr_config)
        where = path.abspath(path.join(self.main_backup_server['local_root'], segment, filename))
        with open(where, 'w') as fw:
            fw.write(content)
        self._write_backup_ftp(*args, second = True)
    

    def _write_backup_ftp(self, segment, filename, curr_config, second = False  ):
        '''Function create backup file on disk when not running on main backup server
        
        Args:
            args[0] = segment (str): segment (folder) under ftp_root or local_root  (./segment/)
            args[1] = filename (str): name of file
            args[2] = curr_config (list): current configuration in type of list
        
        Returns:
            none
        '''
        from ftplib import FTP
        from tempfile import gettempdir
        from os import path
        
        curr_config = '\n'.join(curr_config)
        cmd = f"STOR {filename}"
        tmpfile = path.abspath(path.join(gettempdir(), filename))
        ftp_root, ftp_params = self._set_ftp_var(second)
        with open(tmpfile, 'w') as fw:
            fw.write(curr_config)
        with FTP(**ftp_params) as con:
            con.cwd(ftp_root + segment)
            con.storlines(cmd, open(tmpfile, 'rb'))
        os.remove(tmpfile)

