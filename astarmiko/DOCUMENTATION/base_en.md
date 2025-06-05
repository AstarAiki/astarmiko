***Core Module: astarmiko***
Contains the classes Activka (base class representing all active network equipment) and its child class ActivkaBackup (base class for backing up device configurations).

***Initializing the Activka Class***
myactivka = Activka('activka_byname.yaml')  

Where 'activka_byname.yaml' is a YAML file storing information about all devices (see activka_byname_en.md).

## Activka Functions:
### choose(device, withoutname=False)
Creates a connection dictionary in Netmiko format for use with ConnectHandler(**device).

    device: Device name (from activka_byname.yaml).
    withoutname: Selects the dictionary format:
        {dictionary for connect} if False (default).
        {device_name: {dictionary for connect}} if True.

### filter(device_type=None, levels=None, segment=None)
Filters devices from activka_byname.yaml based on three parameters:
    device_type: Netmiko device type.
    levels:
        'R' – Router.
        'L3' – L3 switch.
        'L2' – L2 switch.
    segment: Network segment (see activka_byname_en.md).

### setconfig, getinfo, get_curr_config, list_of_all_ip_intf
    setconfig: Push configuration commands to a device.
    getinfo: Retrieve any information (show commands).
    get_curr_config: Fetch the current configuration.
    list_of_all_ip_intf: Get a list of all IP interfaces.

### setconfig_on_devices, execute_on_devices
setconfig_on_devices: Push configuration commands to multiple devices at once.
execute_on_devices: Retrieve information (show commands) from multiple devices.

## ActivkaBackup Functions:
\_**setup_backup_servers**
I use two servers (main and second) to store device configurations. The backup script can run on the main server via cron (where main is local) or from a workstation (where main becomes remote). Access is determined via _setup_protocol_handlers.

### compare_configs(device: str, ignore_lines: List[str] = None) -> Dict[str, Any]
Compares the current device configuration with the latest backup and returns the differences.

### get_backup_config, write_backup
get_backup_config: Retrieves the latest saved configuration from the server.
write_backup: Creates a file on the server and writes the current device configuration to it.
These functions map to _get_backup_config, _write_backup_scp, and _write_backup_sftp.

## Standalone Functions (Outside Classes)

### setup_logging
Configures logging level, format, and output destination.

### setup_config
Configures module parameters using a YAML file. Parameters may include:
    Paths for storing configuration files/templates.
    User credentials for access.
    Logging settings (enable/disable, customization).
    Interface language selection.
    Standard command dictionaries for different device types.

### snmp_get_oid

This function was added because astarmiko relies on SSH, but some devices (e.g., Russian-made *Kontinent-4* firewalls) only support SNMP for retrieving ARP/MAC tables.

### send_commands
Push one or a list of configuration commands to a device.

### port_name_normalize
Normalizes port names (e.g., Huawei devices return GE0/0/1 in output but require GI0/0/1 in commands).

### get_port_by_mac
Finds the port where a device with a specific MAC address is connected and determines if the port is:
    An endpoint (single device or IP phone).
    Connected to another switch.

### convert_mac
Converts MAC address formats between vendors (e.g., Cisco to Huawei).

### del_exeption
Ignores non-critical differences in configurations (e.g., Cisco's ntp clock-period *SOME-NUMBER*).

### check_identity
Compares two configurations for equivalence.

### templatizator
Uses TextFSM templates to parse command output into structured data. Supports:
    Standard templates for common commands (referenced by abbreviation).
    Custom templates (flag special=True + template filename).
