Directory contents - examples of configuration files

    activka_byname.yaml - description of all active network devices by type, category, and location in the network

    commands.yml - abbreviations of standard commands (most commonly used in practice) and their explanations for each brand of equipment used in your network

    log_config.yaml - logging configuration, if needed

    messages_en.yaml - file with English messages used in the fh (FindHost) program - an example of using the astarmiko library

    messages_ru.yaml - file with Russian messages used in the fh (FindHost) program - an example of using the astarmiko library

    networks_byip.yaml - an example of a reference used by fh (FindHost). It can be easily generated if you already have activka_byname.yaml.
    This reference assumes that individual objects correspond to a Class C network, while the entire enterprise network is described as a Class A or B network, even if it is subdivided into smaller subnets. Essentially, it is a dictionary of the form: {third_octet_of_IP_address: name_of_the_router_where_the_network_terminates}
