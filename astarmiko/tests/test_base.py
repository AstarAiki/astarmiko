# tests/test_base.py
import unittest
from unittest.mock import patch, MagicMock
from astarmiko import base

class TestBaseModule(unittest.TestCase):

    def setUp(self):
        base.ac = MagicMock()
        base.ac.commands = {
            'mac_delimeters': {
                'cisco_ios': ['.', 4]
            }
        }

    def test_convert_mac_format_4_by_4(self):
        mac = "aabb.ccdd.eeff"
        result = base.convert_mac(mac, 'cisco_ios')
        self.assertEqual(result, 'aabb.ccdd.eeff')

    def test_is_ip_correct_valid(self):
        ip = "192.168.0.1"
        self.assertEqual(base.is_ip_correct(ip), ip)

    def test_is_ip_correct_comma(self):
        ip = "192,168,0,1"
        self.assertEqual(base.is_ip_correct(ip), "192.168.0.1")

    def test_is_ip_correct_invalid(self):
        ip = "300.168.0.1"
        self.assertFalse(base.is_ip_correct(ip))

    def test_port_name_normalize(self):
        port = "Gi0/1"
        result = base.port_name_normalize(port)
        self.assertEqual(result, "GigabitEthernet0/1")

if __name__ == '__main__':
    unittest.main()
