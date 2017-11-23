#!/usr/bin/env python

"""Created on 20.02.2017.

:author: Konishev

"""

from netmiko import ConnectHandler, NetMikoAuthenticationException, NetMikoTimeoutException
import textwrap
import getpass
import re
from os.path import expanduser


class CiscoIOS:
    """Class for cisco ios device"""

    def __init__(self, device_param):
        """constructor

        :param device_param: dict with option for netmiko

        """
        del (device_param['hostname'])  # delete external for netmiko key
        self.device_param = device_param
        try:
            self.ssh = ConnectHandler(**device_param)
        except NetMikoAuthenticationException:
            raise
        except NetMikoTimeoutException:
            raise

        if not self.ssh.check_enable_mode() and \
                self.device_param['secret']:
            self.ssh.enable()

    def load_ssh_key(self, id_rsa=None, user=None):
        """load id_rsa.pub key on cisco device

        :param id_rsa: path for ket, default use: .ssh/id_rsa.pub
        :param user: username, default use: running username

        """
        if not id_rsa:
            id_rsa = expanduser('~') + '/.ssh/id_rsa.pub'
        if not user:
            user = getpass.getuser()
        pubkey = open(id_rsa, 'r').read()
        pubkey = textwrap.wrap(pubkey, 80)

        commands = ['ip ssh pubkey-chain',
                    'username ' + user,
                    'key-string'] + pubkey + ['exit']
        ret = self.ssh.send_config_set(commands)
        print(ret)
        if ret.find('Invalid input detected') != -1:
            ret = 'invalid input error'
        return ret

    def del_ssh_key(self, user):
        commands = ['ip ssh pubkey-chain',
                    'no username ' + user,
                    'exit']
        return self.ssh.send_config_set(commands)

    def get_all_interfaces(self, search_filter=None):
        if search_filter:
            command = 'sh int status |' + search_filter
        else:
            command = 'sh int status'
        p = re.compile(r"""
                        (?P<name>[GFT]\D+\d/\d/\d+|[GFT]\D+\d/\d+)
                        (?P<description>.*)
                        (?P<status>connected|notconnect|disabled|err-disabled)
                        \s*
                        (?P<vlan>\d+|trunk)
                        """, re.VERBOSE)
        ports = []
        for line in self.ssh.send_command(command).split('\n'):

            interface = {}
            if p.search(line):
                interface['name'] = p.search(line).group('name')
                interface['description'] = p.search(line).group('description')
                interface['status'] = p.search(line).group('status')
                interface['vlan'] = p.search(line).group('vlan')
                ports.append(interface)
        return ports

    def get_all_acc_int(self):
        for c in self.get_all_interfaces():
            if c['vlan'] != 'trunk':
                yield c

    def get_all_vlans(self):
        vlans = []
        for line in self.ssh.send_command('show vlan brief | i ^[0-9].*active').split('\n'):
            vlan = {}
            vlan['vlan'] = line[:line.find(' ')]
            vlan['name'] = line[line.find(' '):line.find(' active')]
            vlans.append(vlan)
        return vlans

    def is_port_trunk(self, port):
        ret = False
        if (self.ssh.send_command('show interface status | i ' + port)
                    .find('trunk') != -1):
            ret = True
        return ret

    def is_port_access(self, port):
        ret = False
        if (self.ssh.send_command('show interface status | i ' + port)
                .find('trunk') == -1):
            ret = True
        return ret

    def switch_access_vlan(self, port, vlan):
        commands = ['interface ' + port,
                    'switchport access vlan ' + vlan]
        return self.ssh.send_config_set(commands)

    def show_priv(self):
        ret = self.ssh.send_command('show privilege')
        return int(ret[ret.rfind(' '):])

    def find_port_by_mac(self, mac):
        """
        Find port by mac add on local switch

        :param mac: - mac add in format: aaaa.bbbb.cccc
        :return: - port name, if port exist and it only one
        """
        if not mac:
            return None
        ports = []
        for line in self.ssh.send_command('sh mac add | i ' + mac).split('\n'):
            port = line[line.rfind(' '):]
            port = port.strip()
            ports.append(port)
        if len(ports) == 1:
            return ports[0]
        else:
            return None

    def find_sw_by_port(self, port):
        """
        Find neighbors by local port name, if port in etherchannel, firs find one of physical interface
        WARNING: all device must have identical domain name!

        :param port: - local switch port name, may be Po interface!
        :return: - neighbors name or null if find error
        """
        if not port:
            return None

        if port.find('Po') != -1:
            # find any physical interface in portchannel
            # msk101-sw-root#sh etherchannel summary | i Po31
            # 31     Po31(SU)        LACP      Te1/2/3(P)     Te1/2/4(P)     Te2/2/3(P)
            # newport = Te2/2/3
            newport = self.ssh.send_command('show etherchannel summary | i ' + port)
            if newport:
                newport = newport.rstrip()
                port = newport[newport.rfind(' '):newport.rfind('(')]  # Te2/2/3(P) -> Te2/2/3
                port = port.strip()

        # Te2/2/3 -> Ten 2/2/3
        if port[0:2] == 'Te':
            port = 'Ten ' + port[2:]
        elif port[0:2] == 'Gi':
            port = 'Gig ' + port[2:]
        elif port[0:2] == 'Fa':
            port = 'Fas ' + port[2:]

        # find neighbour on physical interface: show cdp neighbors
        # Device ID        Local Intrfce     Holdtme    Capability  Platform  Port ID
        # AP881d.fcd5.cf2a Gig 4/0/47        168              R T   AIR-CAP36 Gig 0.1
        # agg-sw-1.medsigroup.ru
        #                  Ten 2/2/3         171             R S I  WS-C6503- Ten 1/2/1
        # agg-sw-1.medsigroup.ru
        #                  Ten 3/0/1         175             R S I  WS-C6503- Ten 1/2/3
        # ...
        # sw = agg-sw-1.medsigroup.ru
        p = re.compile(r"""
                        (?P<dev>^.*?\ +?)
                        (?P<port>[Ten|Gig|Fas]+\ [\d{1,2}/\d{1,2}/\d{1,2}|\d{1,2}/\d{1,2}]+\ )  # only Local Interface
                        """, re.VERBOSE)
        cdp = self.ssh.send_command('show cdp neighbors | begin Device ID')
        sw = None
        tmp = ''
        for line in cdp.split('\n'):
            if line.find('Local Intrfce') != -1:
                continue  # always discard first line
            if len(line.split(' ')) == 1:
                tmp = line  # long device name on first line
                continue
            if tmp:
                line = tmp + ' ' + line  # concat long device name with base string
                tmp = ''
            if p.search(line):
                prt = p.search(line).group('port')
                prt = prt.strip()
                if prt == port:
                    sw = p.search(line).group('dev')
                    break
        return sw

    def write_memory(self):
        return self.ssh.send_command('write mem')
