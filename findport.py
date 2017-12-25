#!/usr/bin/env python

"""
Created on 11.04.2017.
:author: Konishev Dmitry
"""

import ciscoios
import parseconf
import getpass
import sys
import argparse
import re
import textwrap


def search_port_by_mac(config, host, mac, domain='', trace=False):
    """
    Find switch and port by mac address.
    Tested with cisco 2960, 3750, 6503, 6504. cdp must be enabled!
    :param host: - root switch
    :param mac: - mac address or path of mac
    :param domain: - domain name from ip domain-name - must be equal for all device!
    :param trace: - print find results recursive
    :return: - switch name and port or "port not found" message
    """

    hostname = host['hostname']
    cisco = None
    try:
        cisco = ciscoios.CiscoIOS(host)
    except ciscoios.NetMikoAuthenticationException:
        print('bad password')
    if cisco:
        port = cisco.find_port_by_mac(mac)
        if not port:
            # TODO - переделать на обработку исключений
            port = 'port not found'
        if trace:
            print(hostname + '\t' + port)
        if cisco.is_port_access(port):
            return hostname, port
        if cisco.is_port_trunk(port):
            sw = cisco.find_sw_by_port(port)
            if sw:
                if domain:
                    sw = sw[0:sw.find(domain)-1]
                return search_port_by_mac(config, config.get_host_by_name(sw), mac, domain, trace)
            else:
                print('switch not found')


def mac_normalize(mac):
    """
    Normalize mac from any format to aaaa.bbbb.cccc
    :param mac: - mac address or path of mac address in any format
    :return: - mac address or path of mac address in cisco format: aaaa.bbbb.cccc
    """
    mac = re.sub(r'\s', '', mac)
    mac = mac.lower()
    mac = re.sub(r'[^abcdef0123456789]', '', mac)
    if len(mac) > 4:
        mac = mac[::-1]  # inverse
        newmac = ''
        for m4 in textwrap.wrap(mac, 4):
            newmac += m4 + '.'
        mac = newmac[::-1][1:]
    return mac


def create_parser():
    parser = argparse.ArgumentParser(prog='findport.py',
                                     description='Find switch and port by mac address',
                                     epilog='Author: Konishev Dmitry, 11.04.2017')
    parser.add_argument('-r', '--root', nargs='?', default='msk101-sw-root', help='root switch')
    parser.add_argument('-m', '--mac', nargs='?', required=True, help='mac address - required')
    parser.add_argument('-d', '--domain', nargs='?', help='domain in "ip domain-name" option')
    parser.add_argument('-t', '--trace', const=True, action='store_const', default=False, help='show trace path')
    parser.add_argument('-e', '--enable', const=True, action='store_const', default=False, help='enable password')
    return parser


if __name__ == '__main__':
    pars = create_parser()
    nmsp = pars.parse_args(sys.argv[1:])
    if nmsp.mac:
        mac_addr = mac_normalize(nmsp.mac)
        conf = parseconf.ParseConf()
        if not conf.password:
            password = getpass.getpass()
            conf.set_pass(password)
        if nmsp.enable:
            enable = getpass.getpass()
            conf.set_enable(enable)
        ret = search_port_by_mac(conf, conf.get_host_by_name(nmsp.root), mac_addr, nmsp.domain, nmsp.trace)
        if not nmsp.trace:
            print(ret[0], ret[1])
