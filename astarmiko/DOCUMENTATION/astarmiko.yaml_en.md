Example configuration file for scripts using the astarmiko module
localpath: /home/mypython/astarmiko/

Base path used to construct paths to folders and files used in astarmiko. Originally designed to use relative paths, but usage experience showed that sometimes it's more convenient to store TextFSM templates or reference files (in YAML format) in unrelated locations.
Credentials - username and password

Default credentials used for SSH connections to network equipment, typically TACACS or RADIUS accounts:
yaml

user: gAAAAABn7NmekcfGhIjrwJRXL6v0QRm3SAz4dz-GSm16gu7dpBIyw5omo-A1d3-LjaNwPwTN6Vg-1jzW5_0aPeFbwe0p6TZtsQ==
password: gAAAAABn7Nme6Kb4cI-sqsyApPFm2JsqLtp-2Hds7Jov8MY50XBx3s1VKOIXgA3FKjIa_FjpqkbdDsG6bWwzobwhw9SOrSwHOA==

Initially, you enter username and password in plain text when creating the config file, then encrypt them using the CLI interface of the astarconf module.
List of first MAC octets for IP phones
yaml

phone_mac:
- 805e
- 001a

If your network uses IP phones, to determine whether a switch port connects to a computer through a phone, you need to know which MAC addresses visible on the port belong to phones. Since the number of IP phone brands in a network is limited, and all phones of the same brand share the same MAC address prefix, this list is created.
templpath: /home/mypython/astarmiko/TEMPLATES/

Path where TextFSM templates are stored
dict_of_cmd: /home/mypython/astarmiko/YAML/commands.yaml

Path to commands.yaml file containing standard, most frequently used commands. These always have corresponding TextFSM templates.
logging: True

Enable/disable logging
logfile: /home/mypython/astarmiko.log

Log file location
loglevel: DEBUG

Log level
log_format_str:

Custom log format string (if different from default)
add_account:

Exceptions exist in all rules. Some equipment can't use TACACS or has other limitations requiring local or alternative credentials. These are listed here. The connection module in astarmiko will attempt these if the standard credentials fail before returning an error message.
Credentials are similarly encrypted using the astarconf module.
yaml

- password: gAAAAABoB1JEZiWkUNiaXAs-ItSPTUrPyBCP4jyZBLWF0P9SGahWSD5ZWNK9QFxCbkPCnPFdqmigVQx8vmrMAbkz09mJRNH7HA==
  user: gAAAAABoB1JEHSOPYy3-0SAUhGgzlRnXTf56-1frsFs9d2CRYuwqRtfAQRgZYF0ohraFCN74IaR1P3Zdr1BONnNZVAa8d9Yyvw==
- password: gAAAAABoB1JEUFWn9R_rx-MaZ7QFyPiVK5mh4VgHZmpiAcTLV8EZ3QM99gK8ZVkjAqSXnOjGGOGSL3SU0e85Pcc9f33BQ-Q4og==
  user: gAAAAABoB1JE-WO-0EEjVG7-mmK1fSMGEzRaCdVxW1WW81ZBSFzxkYmMT1PvWevC7RI9Ey6b-xiv4hGLXq0wFrWifTYwDNRxgg==
