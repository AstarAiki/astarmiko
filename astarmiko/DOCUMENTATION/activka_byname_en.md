YAML file of the following format:

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


Where:
  device_type - the device type as defined in netmiko
  ip - the IP address of the device
  LEVEL - router, L2 or L3 switch. The level determines whether it makes sense to query the ARP table (R), MAC address table (L2), or both (L3) - or for any other purpose you might use in your program logic.
  SEGMENT:
  Our network can be visualized as:
  
  ![[SegmentSCHEMA.png]]
  These are different fiber-optic rings. There are also many additional channels via microwave links, satellites, high-frequency, etc. However, in my management programs (Putty + SuperPutty), the equipment is organized into directories SEG A ..... SEG I. On the server where equipment configuration backups are stored, directories with the same names are created.
  
  In general, SEGMENT is any logical division of your network into segments that makes sense to you.
