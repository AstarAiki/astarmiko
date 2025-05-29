In their daily work, any network administrator frequently executes similar commands—such as checking the ARP table, the general MAC address table, MAC addresses on a specific port, listing all IP interfaces, etc.

The astarmiko library itself allows automating the execution of these commands across multiple devices, while the dictionary in commands.yaml stores the mapping between the purpose of a command and its specific implementation for each brand of equipment.

Additionally, this file includes the mac_delimiters parameter, which defines the style of MAC address output (and input) in the equipment console. This can vary between brands, not only in the format (6 groups of 2 or 3 groups of 4) but also in the separator used—such as a dot, hyphen, or colon.
